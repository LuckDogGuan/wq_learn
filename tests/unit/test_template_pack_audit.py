"""Unit tests for scripts/analysis/template_pack_audit.py (synthetic batches, no I/O)."""
import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "template_pack_audit",
    Path(__file__).resolve().parents[2] / "scripts" / "analysis" / "template_pack_audit.py",
)
tpa = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(tpa)

BASE = tpa.BASE_PACK
OTHER = "RA-DUAL-GRANK-MIN-COUNTRY, RA-DUAL-REV-GRANK-MIN-COUNTRY"


def _b(pack, ds="m1", region="EUR", s1=0, s2=0, s3=0, done=8, settings="COUNTRY|d=0|tr=0.04"):
    return {
        "batch_id": "x", "region": region, "dataset_id": ds, "settings_compact": settings,
        "template_summary": pack, "done": done,
        "stage1_pass": s1, "stage2_pass": s2, "stage3_pass": s3,
    }


def test_matched_diff_only_inside_same_cell():
    batches = [
        _b(BASE + ", x", s1=2), _b(BASE + ", x", s1=2),          # base rate 4/16 = 25%
        _b(OTHER, s1=4), _b(OTHER, s1=4),                         # other rate 8/16 = 50%
        _b(OTHER, ds="m2", s1=8), _b(OTHER, ds="m2", s1=8),      # other cell without base -> ignored
    ]
    rows = tpa.matched_pack_diff(batches)
    assert len(rows) == 1
    assert rows[0]["pack"] == "RA-DUAL-GRANK-MIN-COUNTRY" and rows[0]["cells"] == 1
    assert abs(rows[0]["d_stage1"] - 0.25) < 1e-9


def test_matched_diff_requires_min_batches():
    batches = [_b(BASE + ", x", s1=2), _b(OTHER, s1=4), _b(OTHER, s1=4)]
    assert tpa.matched_pack_diff(batches) == []


def test_refinement_batches_are_excluded():
    batches = [_b("PC22-A1-str2", s1=8), _b("PC22-A1-str2", s1=8), _b(BASE + ", x", s1=1), _b(BASE + ", x", s1=1)]
    assert tpa.matched_pack_diff(batches) == []


def test_dataset_concentration_shares():
    batches = [_b(BASE, ds="hit", s3=9, done=8), _b(BASE, ds="low", s3=1, done=80)]
    c = tpa.dataset_concentration(batches, top=1)
    assert c["total_stage3"] == 10 and c["datasets"] == 2
    assert abs(c["top_hit_share"] - 0.9) < 1e-9
    assert c["top_budget_share"] < 0.1


def test_pack_yield_split():
    batches = [_b(BASE + ", x", ds="hit", s2=2), _b(BASE + ", x", ds="low", s2=0)]
    r = tpa.pack_yield_split(batches, tpa.pack_key(batches[0]), {("EUR", "hit")})
    assert r["hit_datasets"]["stage2"] == 0.25 and r["other_datasets"]["stage2"] == 0.0
