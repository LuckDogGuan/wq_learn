#!/usr/bin/env python3
"""Task-level template audit (read-only) over data/exports/task_template_rows.csv.

Input is produced by scripts/ops/export_guangzhou_task_templates.py (COMPLETED_FULL + COMPLETED_QUICK rows).

Design: the Stage-1 pack runs 8 templates (4 families x {pos, reverse}) on the SAME field and settings, so
templates can be compared inside a field cell (paired), which removes the dataset/field effect that dominates
batch-level numbers. Within a cell a family's score is the better of its two directions (max Sharpe), because
the pair is x and reverse(x).

Limits: observational; QUICK and FULL are kept apart; fields that are dead for every template add only noise
(report 'alive' cells separately); zero-fail uses FAIL names only (WARNING/PENDING caveat, TODO T04).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

DEFAULT_PATH = Path("data/exports/task_template_rows.csv")

# Stage-1 template families. Order matters only for display.
FAMILIES = {
    "F1_ADM_gz_ts_mean22_subind": r"^RA-ADM-0[12]-(?:rev-)?sub-gz-m22",
    "F2_ADM_grank_decay10_subind": r"^RA-ADM-0[34]-(?:rev-)?sub-grank-dec10",
    "F3_TOP_grank_zs66_mean5_subind": r"^RA-TOP-0[12]-(?:rev-)?sub-grank-z66",
    "F4_TOP_gz_industry_raw": r"^RA-TOP-0[34]-(?:rev-)?ind-gz-raw",
}
_FAM_RE = {k: re.compile(v) for k, v in FAMILIES.items()}
CELL_KEYS = ["simulation_mode", "region", "universe", "dataset_id", "primary_field_id", "neutralization", "decay", "truncation"]


def load(path: Path = DEFAULT_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    st = df["settings_json"].apply(lambda s: json.loads(s) if isinstance(s, str) else {})
    df["neutralization"] = st.apply(lambda d: d.get("neutralization"))
    df["decay"] = st.apply(lambda d: d.get("decay"))
    df["truncation"] = st.apply(lambda d: d.get("truncation"))
    df["family"] = df["template_id"].apply(_family)
    return df


def _family(tid: str) -> str | None:
    base = str(tid).rsplit("_", 1)[0] if "_" in str(tid) else str(tid)
    for name, rx in _FAM_RE.items():
        if rx.search(base) or rx.search(str(tid)):
            return name
    return None


def family_cells(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    """One row per (cell, family) with the better of the two directions; keep cells with all 4 families."""
    d = df[(df.simulation_mode == mode) & df.family.notna() & df.sharpe.notna()]
    if d.empty:
        return pd.DataFrame(columns=list(FAMILIES), index=pd.MultiIndex.from_arrays([[]] * len(CELL_KEYS), names=CELL_KEYS))
    g = d.groupby(CELL_KEYS + ["family"], dropna=False).sharpe.max().unstack("family")
    g = g.reindex(columns=list(FAMILIES))
    g = g.dropna(subset=list(FAMILIES))
    return g


def summarize_families(cells: pd.DataFrame, alive_thr: float = 0.8) -> pd.DataFrame:
    rows = []
    alive = cells[cells.max(axis=1) >= alive_thr]
    base = list(FAMILIES)[0]
    for name in FAMILIES:
        s = cells[name]
        sa = alive[name]
        diff = (cells[name] - cells[base])
        rows.append({
            "family": name,
            "cells": len(s),
            "mean_best_sh": s.mean(),
            "ge0.8": (s >= 0.8).mean(),
            "ge1.25": (s >= 1.25).mean(),
            "alive_cells": len(sa),
            "alive_mean_sh": sa.mean() if len(sa) else float("nan"),
            "alive_ge1.25": (sa >= 1.25).mean() if len(sa) else float("nan"),
            "alive_is_cell_best": (alive[list(FAMILIES)].idxmax(axis=1) == name).mean() if len(alive) else float("nan"),
            "vs_F1_mean_diff": diff.mean(),
            "vs_F1_win": (diff > 0.05).mean(),
            "vs_F1_loss": (diff < -0.05).mean(),
        })
    return pd.DataFrame(rows)


def neutralization_paired(df: pd.DataFrame, mode: str, base: str = "SUBINDUSTRY", min_cells: int = 20) -> pd.DataFrame:
    """Same field, same family set, different neutralization: best-over-families Sharpe difference vs base."""
    d = df[(df.simulation_mode == mode) & df.family.notna() & df.sharpe.notna()]
    keys = ["region", "universe", "dataset_id", "primary_field_id", "decay", "truncation"]
    g = d.groupby(keys + ["neutralization"], dropna=False).sharpe.max().unstack("neutralization")
    out = []
    if base not in g.columns:
        return pd.DataFrame()
    for col in g.columns:
        if col == base:
            continue
        pair = g[[base, col]].dropna()
        if len(pair) >= min_cells:
            diff = pair[col] - pair[base]
            out.append({"neutralization": col, "cells": len(pair), "mean_diff_vs_" + base: diff.mean(),
                        "win": (diff > 0.05).mean(), "loss": (diff < -0.05).mean(),
                        "alive_cells": int((pair.max(axis=1) >= 0.8).sum())})
    return pd.DataFrame(out)


def by_region(cells: pd.DataFrame, min_cells: int = 25, alive_thr: float = 0.8) -> pd.DataFrame:
    """Per-region family comparison (guards against a region mix driving the pooled ordering)."""
    rows = []
    for region, sub in cells.groupby(level="region"):
        if len(sub) < min_cells:
            continue
        alive = sub[sub.max(axis=1) >= alive_thr]
        best = alive[list(FAMILIES)].idxmax(axis=1) if len(alive) else pd.Series(dtype=str)
        row = {"region": region, "cells": len(sub), "alive": len(alive)}
        for name in FAMILIES:
            short = name.split("_")[0]
            row[f"{short}_mean"] = sub[name].mean()
            row[f"{short}_best%"] = (best == name).mean() if len(best) else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def full_gate_hits(df: pd.DataFrame) -> pd.DataFrame:
    """FULL-only Stage-3 style hits by dataset (Sharpe>=1.58, Fitness>=1.0), and the FAIL-free subset."""
    f = df[(df.simulation_mode == "FULL") & df.sharpe.notna()].copy()
    f["hit"] = (f.sharpe >= 1.58) & (f.fitness >= 1.0)
    f["hit_nofail"] = f.hit & f.fail_checks.fillna("").eq("")
    out = f.groupby(["region", "dataset_id"]).agg(full=("task_id", "size"), hits=("hit", "sum"), hits_nofail=("hit_nofail", "sum"))
    return out.sort_values("hits", ascending=False)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", default=str(DEFAULT_PATH))
    args = ap.parse_args()
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    df = load(Path(args.path))
    print(df.groupby("simulation_mode").size().to_string())
    for mode in ("FULL", "QUICK"):
        cells = family_cells(df, mode)
        print(f"\n== {mode}: paired field cells with all 4 families = {len(cells)}")
        if len(cells):
            print(summarize_families(cells).round(3).to_string(index=False))
            br = by_region(cells)
            if len(br):
                print(f"\n-- {mode} by region (mean best Sharpe per family; best% = share of alive cells where the family wins)")
                print(br.round(3).to_string(index=False))
        nz = neutralization_paired(df, mode)
        if len(nz):
            print(f"\n-- {mode} neutralization vs SUBINDUSTRY (same field/decay/trunc)")
            print(nz.round(3).to_string(index=False))
    h = full_gate_hits(df)
    tot = h.hits.sum()
    print(f"\n== FULL-only hits (Sh>=1.58 & Fit>=1.0): {int(tot)} of {int(h.full.sum())} FULL; FAIL-free {int(h.hits_nofail.sum())}")
    top = h.head(8)
    print(top.to_string())
    print(f"top5 datasets share of hits: {h.hits.head(5).sum()/tot:.1%}; share of FULL: {h.full.head(5).sum()/h.full.sum():.1%}; datasets={len(h)}")


if __name__ == "__main__":
    main()
