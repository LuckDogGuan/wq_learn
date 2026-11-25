"""Offline contracts: no credentials, live HTTP, simulation, or submission."""
import asyncio
import importlib
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from zoneinfo import ZoneInfo

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "legacy_core"))
sys.path.insert(0, str(ROOT / "tests" / "core_regression"))
sys.path.insert(0, str(ROOT / "tests" / "unit"))
from Core.api.alpha_retrieval import fetch_alpha_window, COMPLETE, PENDING
from Core.api.client import BrainClient
from Core.api.submission import wait_submission_check, classify_submission_check
from Core.data.catalog_db import CatalogDB
from Core.catalog_sync import sync_catalog
from Core.sim.sim_engine import load_task_pool
from test_alpha_retrieval import FakeClient, Response


class Contracts(unittest.TestCase):
    start = datetime(2026, 8, 31, tzinfo=timezone(timedelta(hours=8)))

    def test_invalid_or_unobserved_pages_never_complete(self):
        payloads = [None, {}, [], {"results": []},
                    {"count": 0}, {"results": [], "count": True},
                    {"results": [], "count": 1},
                    {"results": [{"id": "x"}], "count": 0},
                    {"results": [{}], "count": 1}]
        for payload in payloads:
            with self.subTest(payload=payload):
                client = Mock()
                client.get.return_value = Response(payload)
                result = fetch_alpha_window(client, self.start, self.start + timedelta(days=1))
                self.assertEqual(result.status, PENDING)
        for code in (401, 429, 500, 503):
            client = Mock()
            client.get.return_value = Response({}, code)
            self.assertEqual(fetch_alpha_window(client, self.start, self.start + timedelta(days=1)).status, PENDING)
        client = Mock()
        client.get.return_value.json.side_effect = ValueError("bad JSON")
        client.get.return_value.status_code = 200
        self.assertEqual(fetch_alpha_window(client, self.start, self.start + timedelta(days=1)).status, PENDING)

    def test_month_end_and_dst_half_open_boundaries(self):
        for zone, day in (
            (ZoneInfo("Asia/Shanghai"), datetime(2026, 8, 31)),
            (ZoneInfo("America/New_York"), datetime(2026, 3, 8)),
            (ZoneInfo("America/New_York"), datetime(2026, 11, 1)),
        ):
            start = day.replace(tzinfo=zone)
            end = start + timedelta(days=1)
            records = [
                {"id": "before", "dateCreated": (start - timedelta(microseconds=1)).isoformat()},
                {"id": "start", "dateCreated": start.isoformat()},
                {"id": "last", "dateCreated": (end - timedelta(microseconds=1)).isoformat()},
                {"id": "end", "dateCreated": end.isoformat()},
            ]
            result = fetch_alpha_window(FakeClient(records), start, end)
            self.assertEqual(result.status, COMPLETE)
            self.assertEqual({x["id"] for x in result.records}, {"start", "last"})

    def test_corrupt_checkpoint_is_refetched(self):
        client = FakeClient([])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            fetch_alpha_window(client, self.start, self.start + timedelta(days=1), checkpoint_path=path)
            document = json.loads(path.read_text(encoding="utf-8"))
            document["alpha_fetch"]["windows"] = [{"complete": True}]
            path.write_text(json.dumps(document), encoding="utf-8")
            result = fetch_alpha_window(client, self.start, self.start + timedelta(days=1), checkpoint_path=path)
            self.assertEqual(result.status, COMPLETE)
            self.assertEqual(result.request_count, 1)

    def test_shared_transport_retry_is_bounded(self):
        session = Mock(cookies=[])
        session.request.side_effect = requests.exceptions.Timeout()
        client = BrainClient(session)
        with patch("Core.api.client.time.sleep"), patch.object(client, "_pace_get"):
            self.assertIsNone(client.get("/read"))
        self.assertEqual(session.request.call_count, 4)
        session.request.reset_mock()
        with patch("Core.api.client.time.sleep"):
            self.assertIsNone(client.post("/simulations"))
        self.assertEqual(session.request.call_count, 1)

    def test_401_only_refreshes_once(self):
        session = Mock(cookies=[])
        session.request.return_value = Mock(status_code=401, headers={})
        client = BrainClient(session)
        with patch.object(client, "_refresh_authentication", return_value=True) as refresh, patch.object(client, "_pace_get"):
            self.assertEqual(client.get("/read").status_code, 401)
        refresh.assert_called_once()
        self.assertEqual(session.request.call_count, 2)

    def test_retry_after_cannot_exceed_check_budget(self):
        session = Mock(cookies=[])
        session.request.return_value = Mock(status_code=429, headers={"Retry-After": "3600"})
        client = BrainClient(session)
        import time
        with patch("Core.api.client.time.sleep") as sleep:
            self.assertEqual(client.get("/read", deadline=time.monotonic() + 1).status_code, 429)
        sleep.assert_not_called()
        self.assertEqual(session.request.call_count, 1)

    def test_submission_invalid_delay_stays_pending(self):
        for delay in ("nan", "inf", "-1", "broken"):
            client = Mock()
            client.get.return_value = Mock(status_code=200, headers={"Retry-After": delay})
            with patch("Core.api.submission.asyncio.sleep", new_callable=AsyncMock) as sleep:
                status, _ = asyncio.run(wait_submission_check(client, "A"))
            self.assertEqual(status, PENDING)
            sleep.assert_not_awaited()
            client.post.assert_not_called()
        response = Mock(status_code=200, json=Mock(return_value={"checks": [{"result": "PASS"}], "is": None}))
        self.assertEqual(classify_submission_check(response)[0], "PASS")

    def test_batch_tail_never_single_or_more_than_eight(self):
        for count in range(2, 40):
            for size in range(2, 9):
                pools = load_task_pool(list(range(count)), size, 3)
                batches = [batch for pool in pools for batch in pool]
                self.assertTrue(all(2 <= len(batch) <= 8 for batch in batches))
                self.assertEqual([item for batch in batches for item in batch], list(range(count)))
        for args in (([1], 8, 1), ([1, 2], True, 1), ([1, 2], 8, 0)):
            with self.assertRaises(ValueError):
                load_task_pool(*args)

    def test_catalog_sync_explicit_and_skip_flag_respected(self):
        with tempfile.TemporaryDirectory() as directory:
            db = CatalogDB(Path(directory) / "catalog.db")
            db.upsert_datasets([{"id": "d", "fieldCount": 1, "category": {"id": "analyst"}}], "USA", "TOP3000")
            with patch("Core.catalog_sync.get_day1_universe_map", return_value={"USA": ["TOP3000"]}), \
                 patch("Core.catalog_sync.get_datasets") as datasets, \
                 patch("Core.catalog_sync.login") as login, \
                 patch("Core.catalog_sync.get_datafields", return_value=pd.DataFrame([{"id": "f"}])):
                report = sync_catalog(db, client=Mock(), skip_datasets=True)
            self.assertEqual(report["status"], COMPLETE)
            datasets.assert_not_called()
            login.assert_not_called()
            self.assertEqual(list(db.query_factors(region="USA", universe="TOP3000")["id"]), ["f"])
            from Core.factor.filter.alpha_evaluator import get_all_categories_local
            self.assertEqual(list(get_all_categories_local(db)[1]), ["analyst"])

    def test_public_exports_do_not_offer_single_simulation(self):
        import Core.api as api
        import Core.machine_lib as lib
        for module in (api, lib):
            self.assertFalse(hasattr(module, "post_simulation"))
        self.assertFalse(hasattr(lib, "single_simulate"))
        self.assertTrue(callable(lib.post_multi_simulation))

    def test_new_and_frozen_old_ra_have_same_ids(self):
        sys.path.insert(0, str(ROOT / "legacy_core/pipelines/ra_screening"))
        core = importlib.import_module("filter_ra_alphas_core")
        start = self.start.astimezone(timezone.utc)
        end = start + timedelta(days=2)
        records = [
            {"id": str(i), "dateCreated": (start + timedelta(minutes=i * 2)).isoformat()}
            for i in range(501)
        ] + [{"id": "end-excluded", "dateCreated": end.isoformat()}]
        class Client(BrainClient):
            def __init__(self):
                self.fake = FakeClient(records)
            def mark_authenticated(self):
                pass
            def get(self, url, **kwargs):
                return self.fake.get(url)
        with patch.object(core, "beijing_date_window_utc", return_value=(start, end)), \
             patch.object(core, "CONFIG_FETCH_SLICE_HOURS", 24), \
             patch.object(core, "progress"):
            namespace = dict(vars(core))
            namespace["get_alpha_page_with_retry"] = lambda client, url, context: client.get(url)
            fixture = Path(__file__).with_name("legacy_ra_fetch_fixture.py").read_text(encoding="utf-8")
            exec(compile(fixture, "legacy_ra_fetch_fixture.py", "exec"), namespace)
            old, old_failures = namespace["fetch_recent_alphas"](Client())
            new, new_failures = core.fetch_recent_alphas(Client())
        self.assertEqual(old_failures, [])
        self.assertEqual(new_failures, [])
        self.assertEqual({x["id"] for x in old}, {x["id"] for x in new})
        self.assertEqual(len(new), 501)

    def test_new_and_old_ra_preserve_same_failed_page(self):
        sys.path.insert(0, str(ROOT / "legacy_core/pipelines/ra_screening"))
        core = importlib.import_module("filter_ra_alphas_core")
        start = self.start.astimezone(timezone.utc)
        end = start + timedelta(days=1)
        records = [{"id": str(i), "dateCreated": (start + timedelta(minutes=i)).isoformat()}
                   for i in range(101)]
        class Client(BrainClient):
            def __init__(self):
                self.fake = FakeClient(records, fail_once_at=100)
            def mark_authenticated(self):
                pass
            def get(self, url, **kwargs):
                return self.fake.get(url)
        def load(client, url, context):
            response = client.get(url)
            return response if response.status_code == 200 else None
        with patch.object(core, "beijing_date_window_utc", return_value=(start, end)), patch.object(core, "CONFIG_FETCH_SLICE_HOURS", 24), patch.object(core, "progress"):
            namespace = dict(vars(core))
            namespace["get_alpha_page_with_retry"] = load
            fixture = Path(__file__).with_name("legacy_ra_fetch_fixture.py").read_text(encoding="utf-8")
            exec(compile(fixture, "legacy_ra_fetch_fixture.py", "exec"), namespace)
            old, old_failures = namespace["fetch_recent_alphas"](Client())
            new, new_failures = core.fetch_recent_alphas(Client())
        self.assertEqual({x["id"] for x in old}, {x["id"] for x in new})
        self.assertEqual(old_failures, new_failures)
        self.assertEqual(new_failures, ["slice=1/1 offset=100"])

    def test_ppa_legacy_cache_untouched_and_query_change_refetches(self):
        from test_filter_ppa_local_ppac import FILTER
        client = Mock()
        client.get.return_value = Response({"results": [], "count": 0})
        start = self.start
        with tempfile.TemporaryDirectory() as directory:
            legacy = Path(directory) / f"{start.date().isoformat()}.json"
            legacy.write_text('[{"id":"legacy"}]', encoding="utf-8")
            before = legacy.read_bytes()
            with patch.object(FILTER, "CACHE_DIR", Path(directory)), patch.object(FILTER, "generate_daily_windows", return_value=[(start, start + timedelta(days=1))]), patch.object(FILTER, "build_query_params", return_value="status=UNSUBMITTED"):
                self.assertEqual(FILTER.fetch_recent_alphas(client, now=start + timedelta(days=2)), [])
                self.assertEqual(FILTER.fetch_recent_alphas(client, now=start + timedelta(days=2)), [])
                self.assertEqual(client.get.call_count, 1)
            with patch.object(FILTER, "CACHE_DIR", Path(directory)), patch.object(FILTER, "generate_daily_windows", return_value=[(start, start + timedelta(days=1))]), patch.object(FILTER, "build_query_params", return_value="status=UNSUBMITTED&settings.region=GLB"):
                FILTER.fetch_recent_alphas(client, now=start + timedelta(days=2))
            self.assertEqual(client.get.call_count, 2)
            self.assertEqual(legacy.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
