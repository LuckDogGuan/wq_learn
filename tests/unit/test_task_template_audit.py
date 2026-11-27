"""Synthetic tests for scripts/analysis/task_template_audit.py (no real data)."""
import importlib.util
import json
from pathlib import Path

import pandas as pd

_SPEC = importlib.util.spec_from_file_location(
    "task_template_audit",
    Path(__file__).resolve().parents[2] / "scripts" / "analysis" / "task_template_audit.py",
)
tta = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(tta)

T = {
    "F1": ["RA-ADM-01-sub-gz-m22-pos_SUBINDUSTRY", "RA-ADM-02-rev-sub-gz-m22_SUBINDUSTRY"],
    "F2": ["RA-ADM-03-sub-grank-dec10-pos_SUBINDUSTRY", "RA-ADM-04-rev-sub-grank-dec10_SUBINDUSTRY"],
    "F3": ["RA-TOP-01-sub-grank-z66-pos_SUBINDUSTRY", "RA-TOP-02-rev-sub-grank-z66_SUBINDUSTRY"],
    "F4": ["RA-TOP-03-ind-gz-raw-pos_SUBINDUSTRY", "RA-TOP-04-rev-ind-gz-raw_SUBINDUSTRY"],
}


def _rows(field, sh_pos, sh_rev, mode="QUICK", region="EUR", neut="SUBINDUSTRY"):
    out = []
    for fam, (pos, rev) in T.items():
        for tid, sh in ((pos, sh_pos[fam]), (rev, sh_rev[fam])):
            out.append({
                "task_id": f"{field}-{tid}", "template_id": tid, "simulation_mode": mode, "region": region,
                "universe": "TOP2500", "dataset_id": "d", "primary_field_id": field, "sharpe": sh, "fitness": 1.0,
                "settings_json": json.dumps({"neutralization": neut, "decay": 0, "truncation": 0.04}),
                "fail_checks": "",
            })
    return out


def _df(rows, tmp_path):
    p = tmp_path / "t.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    return tta.load(p)


def test_family_mapping():
    assert tta._family("RA-ADM-01-sub-gz-m22-pos_SUBINDUSTRY").startswith("F1")
    assert tta._family("RA-ADM-04-rev-sub-grank-dec10_CROWDING").startswith("F2")
    assert tta._family("RA-TOP-02-rev-sub-grank-z66_COUNTRY").startswith("F3")
    assert tta._family("RA-TOP-03-ind-gz-raw-pos_INDUSTRY").startswith("F4")
    assert tta._family("RA-DUAL-GRANK-MIN-CROWDING") is None


def test_best_direction_and_paired_diff(tmp_path):
    rows = _rows("f1", {"F1": 0.5, "F2": 0.2, "F3": 0.1, "F4": 1.4}, {"F1": -0.5, "F2": 0.9, "F3": -0.1, "F4": -1.4})
    df = _df(rows, tmp_path)
    cells = tta.family_cells(df, "QUICK")
    assert len(cells) == 1
    vals = cells.iloc[0].to_dict()
    assert abs(vals[list(tta.FAMILIES)[1]] - 0.9) < 1e-9  # best of the two directions
    s = tta.summarize_families(cells)
    f4 = s[s.family.str.startswith("F4")].iloc[0]
    assert f4["alive_is_cell_best"] == 1.0 and f4["vs_F1_win"] == 1.0


def test_incomplete_cells_dropped(tmp_path):
    rows = _rows("f1", {k: 1.0 for k in T}, {k: 0.0 for k in T})
    rows = [r for r in rows if "ind-gz-raw" not in r["template_id"]]
    df = _df(rows, tmp_path)
    assert len(tta.family_cells(df, "QUICK")) == 0


def test_modes_not_mixed(tmp_path):
    rows = _rows("f1", {k: 1.0 for k in T}, {k: 0.0 for k in T}, mode="FULL")
    df = _df(rows, tmp_path)
    assert len(tta.family_cells(df, "QUICK")) == 0 and len(tta.family_cells(df, "FULL")) == 1


def test_full_gate_hits_counts_fail_free(tmp_path):
    rows = _rows("f1", {k: 2.0 for k in T}, {k: 0.0 for k in T}, mode="FULL")
    rows[0]["fail_checks"] = "LOW_2Y_SHARPE"
    df = _df(rows, tmp_path)
    h = tta.full_gate_hits(df)
    assert int(h.hits.sum()) == 4 and int(h.hits_nofail.sum()) == 3
