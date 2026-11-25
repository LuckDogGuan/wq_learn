import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, unquote, urlsplit

sys.path.append(str(Path(__file__).resolve().parents[2] / "legacy_core"))

from Core.api.alpha_retrieval import COMPLETE, PARTIAL, fetch_alpha_window


class Response:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, records, fail_once_at=None):
        self.records = records
        self.fail_once_at = fail_once_at
        self.calls = []

    def get(self, url, timeout=30):
        self.calls.append(url)
        query = parse_qs(urlsplit(url).query)
        offset = int(query["offset"][0])
        limit = int(query["limit"][0])
        if self.fail_once_at == offset:
            self.fail_once_at = None
            return Response({}, 500)
        clauses = [unquote(part) for part in urlsplit(url).query.split("&")]
        start = datetime.fromisoformat(next(
            item.split(">=", 1)[1] for item in clauses
            if item.startswith("dateCreated>=")
        ))
        end = datetime.fromisoformat(next(
            item.split("<", 1)[1] for item in clauses
            if item.startswith("dateCreated<")
        ))
        selected = [
            item for item in self.records
            if start <= datetime.fromisoformat(item["dateCreated"]) < end
        ]
        selected.sort(key=lambda item: item["dateCreated"], reverse=True)
        return Response({
            "results": selected[offset:offset + limit],
            "count": len(selected),
        })


class AlphaRetrievalTests(unittest.TestCase):
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    def records(self, count):
        step = timedelta(days=1) / max(1, count)
        return [
            {
                "id": f"a-{index}",
                "dateCreated": (self.start + step * index).isoformat(),
            }
            for index in range(count)
        ]

    def test_exact_page_and_dense_window_boundaries(self):
        for count in (0, 99, 100, 101, 499, 500, 501, 999, 1000, 1001):
            with self.subTest(count=count):
                result = fetch_alpha_window(
                    FakeClient(self.records(count)), self.start, self.end,
                    query=("status=UNSUBMITTED",), dense_window_threshold=500,
                )
                self.assertEqual(result.status, COMPLETE)
                self.assertEqual(len(result.records), count)
                self.assertEqual(
                    len({item["id"] for item in result.records}), count
                )

    def test_checkpoint_resumes_only_failed_page(self):
        records = self.records(101)
        with TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "fetch.json"
            first = fetch_alpha_window(
                FakeClient(records, fail_once_at=100), self.start, self.end,
                checkpoint_path=checkpoint,
            )
            self.assertEqual(first.status, PARTIAL)
            self.assertEqual(len(first.records), 100)

            resumed_client = FakeClient(records)
            resumed = fetch_alpha_window(
                resumed_client, self.start, self.end,
                checkpoint_path=checkpoint,
            )
            self.assertEqual(resumed.status, COMPLETE)
            self.assertEqual(len(resumed.records), 101)
            self.assertEqual(len(resumed_client.calls), 1)
            self.assertIn("offset=100", resumed_client.calls[0])

    def test_half_open_boundary_deduplicates_adjacent_windows(self):
        boundary = self.start + timedelta(hours=12)
        records = [
            {
                "id": "before",
                "dateCreated": (boundary - timedelta(seconds=1)).isoformat(),
            },
            {"id": "boundary", "dateCreated": boundary.isoformat()},
        ]
        result = fetch_alpha_window(
            FakeClient(records), self.start, self.end,
            slice_size=timedelta(hours=12),
        )
        self.assertEqual(result.status, COMPLETE)
        self.assertEqual(
            {item["id"] for item in result.records}, {"before", "boundary"}
        )

    def test_unsplittable_dense_timestamp_is_explicit_partial(self):
        same_time = self.start + timedelta(seconds=1)
        records = [
            {"id": f"same-{index}", "dateCreated": same_time.isoformat()}
            for index in range(501)
        ]
        result = fetch_alpha_window(
            FakeClient(records), self.start, self.start + timedelta(seconds=2),
            dense_window_threshold=500,
            min_window_size=timedelta(seconds=1),
        )
        self.assertEqual(result.status, PARTIAL)
        self.assertTrue(any(
            item["reason"] == "DENSE_WINDOW_UNSPLITTABLE"
            for item in result.failures
        ))


if __name__ == "__main__":
    unittest.main()
