import sys
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

RA_DIR = Path(__file__).resolve().parents[1] / "代码" / "优化代码" / "区分RA并标记"
sys.path.insert(0, str(RA_DIR))
import filter_ra_alphas_v6 as v6
import filter_ra_alphas_core as core


class EmptySnapshotTest(unittest.TestCase):
    def test_v5_v6_shared_module_contract_has_no_missing_attributes(self):
        import ast
        for filename in ("filter_ra_alphas_v5.py", "filter_ra_alphas_v6.py"):
            tree = ast.parse((RA_DIR / filename).read_text(encoding="utf-8-sig"))
            referenced = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
                          and isinstance(node.value, ast.Name) and node.value.id == "core"}
            self.assertEqual(sorted(name for name in referenced if not hasattr(core, name)), [], filename)

    def run_input(self, frame):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "output").mkdir()
            source = root / "output" / "filtered_RAs_20261005.xlsx"
            frame.to_excel(source, index=False)
            original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            with patch.object(v6, "__file__", str(root / "filter_ra_alphas_v6.py")), patch.object(core, "configure_run_logging"), patch.object(v6, "fetch_platform_options") as platform, patch.object(core, "get_core_client") as client:
                v6.run_job()
                platform.assert_not_called()
                client.assert_not_called()
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), original_hash)

    def test_real_empty_export_missing_headers_is_safe(self):
        self.run_input(pd.DataFrame())

    def test_nonempty_legacy_export_missing_tag_column_is_safe(self):
        self.run_input(pd.DataFrame([{"Expression": "rank(foo)", "alpha_id_raw": "abc"}]))

    def test_pending_alpha_fetch_sentinel_missing_candidate_headers_is_safe(self):
        self.run_input(pd.DataFrame([{
            "alpha_id": "FETCH_PENDING", "alpha_id_raw": "FETCH_PENDING",
            "Processing_Status": "PENDING_ALPHA_FETCH", "Fetch_Status": "PENDING",
            "Fetch_Detail": "slice 1/2 offset 1100: response not observed",
            "Category_Status": "PENDING", "PC_Status": "PENDING", "SC_Status": "PENDING",
            "Platform_Update_Status": "PENDING", "Date Created": "2026-10-05",
        }]))

    def test_save_snapshot_preserves_pending_evidence_and_adds_required_headers(self):
        frame = pd.DataFrame([{"alpha_id": "FETCH_PENDING", "Processing_Status": "PENDING_ALPHA_FETCH",
                               "Fetch_Status": "PENDING", "Fetch_Detail": "slice 1/2 offset 1100"}])
        original = frame.copy(deep=True)
        with patch.object(core, "save_excel") as save:
            core.save_snapshot(frame, Path("unused.xlsx"))
        saved = save.call_args.args[0]
        self.assertTrue({"Expression", "Region", "Universe", "Delay", "Margin", "Platform_Tags"}.issubset(saved.columns))
        self.assertEqual(saved.loc[0, "Platform_Tags"], "")
        self.assertEqual(saved.loc[0, "Processing_Status"], "PENDING_ALPHA_FETCH")
        self.assertEqual(saved.loc[0, "Fetch_Detail"], "slice 1/2 offset 1100")
        pd.testing.assert_frame_equal(frame, original)

    def test_save_snapshot_empty_output_also_has_candidate_headers(self):
        with patch.object(core, "save_excel") as save:
            core.save_snapshot(pd.DataFrame(), Path("unused.xlsx"))
        saved = save.call_args.args[0]
        self.assertTrue(saved.empty)
        self.assertIn("Platform_Tags", saved.columns)
        self.assertIn("Expression", saved.columns)
