#!/usr/bin/env python3
"""Read-only template-pack audit over the exported Guangzhou batch ledger.

Input : data/exports/batch_audit_latest.json (built by scripts/ops/export_guangzhou_batch_audit.py)
Output: markdown tables on stdout. Never touches the network, SQLite, or the platform.

Scope and limits (do not over-read the output):
- Granularity is the BATCH (8 FULL sims), not the template. A batch row lists template names
  (first three + "(+N)") but not per-template outcomes. A pack here = the batch's template_summary.
- Stage-1 packs run each template plus its reverse, so pass rates are bounded well below 100%.
- Refinement batches (S3-*, PC*-*) are hill-climbs from already-good parents. Compare packs only
  inside the generic RA-* Stage-1/2 population and only after matching on dataset+settings.
- Observational data: matched differences are descriptive, not causal estimates.
- stage3_pass is Sharpe>=1.58 & Fitness>=1.0; zero_fail_s3 inherits the PENDING caveat in TODO T04.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
from typing import Any, Iterable

DEFAULT_PATH = Path("data/exports/batch_audit_latest.json")
BASE_PACK = "RA-ADM-01-sub-gz-m22-pos"


def load_batches(path: Path = DEFAULT_PATH) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))["batches"]


def is_generic(batch: dict[str, Any]) -> bool:
    ts = batch.get("template_summary") or ""
    return ts.startswith("RA-") and int(batch.get("done") or 0) > 0


def pack_key(batch: dict[str, Any]) -> str:
    first = (batch.get("template_summary") or "").split(",")[0].strip()
    return first if "DUAL" in first else first[:40]


def _rates(rows: Iterable[dict[str, Any]]) -> tuple[float, float, int]:
    rows = list(rows)
    done = sum(int(r["done"]) for r in rows)
    if done <= 0:
        return 0.0, 0.0, 0
    return (
        sum(int(r["stage1_pass"]) for r in rows) / done,
        sum(int(r["stage2_pass"]) for r in rows) / done,
        done,
    )


def matched_pack_diff(
    batches: list[dict[str, Any]], base: str = BASE_PACK, min_batches: int = 2
) -> list[dict[str, Any]]:
    """Weighted mean (pack - base) of stage1/stage2 pass rates inside (region,dataset,settings) cells."""
    cells: dict[tuple, dict[str, list]] = collections.defaultdict(lambda: collections.defaultdict(list))
    for b in batches:
        if is_generic(b):
            cells[(b["region"], b["dataset_id"], b["settings_compact"])][pack_key(b)].append(b)
    acc: dict[str, list[float]] = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0, 0])
    for packs in cells.values():
        base_rows = packs.get(base, [])
        if len(base_rows) < min_batches:
            continue
        b1, b2, _ = _rates(base_rows)
        for name, rows in packs.items():
            if name == base or len(rows) < min_batches:
                continue
            r1, r2, done = _rates(rows)
            w = min(len(rows), len(base_rows))
            a = acc[name]
            a[0] += (r1 - b1) * w
            a[1] += (r2 - b2) * w
            a[2] += w
            a[3] += 1
            a[4] += done
    out = [
        {
            "pack": name,
            "cells": int(a[3]),
            "weight": a[2],
            "full": int(a[4]),
            "d_stage1": a[0] / a[2],
            "d_stage2": a[1] / a[2],
        }
        for name, a in acc.items()
        if a[2] > 0
    ]
    return sorted(out, key=lambda r: -r["cells"])


def dataset_concentration(batches: list[dict[str, Any]], top: int = 5) -> dict[str, Any]:
    by_ds: dict[tuple, dict[str, int]] = collections.defaultdict(lambda: {"s3": 0, "full": 0})
    for b in batches:
        k = (b["region"], b["dataset_id"])
        by_ds[k]["s3"] += int(b.get("stage3_pass") or 0)
        by_ds[k]["full"] += int(b.get("done") or 0)
    total_s3 = sum(v["s3"] for v in by_ds.values())
    total_full = sum(v["full"] for v in by_ds.values())
    ranked = sorted(by_ds.items(), key=lambda kv: -kv[1]["s3"])[:top]
    return {
        "datasets": len(by_ds),
        "total_stage3": total_s3,
        "total_full": total_full,
        "top": [{"dataset": k, **v} for k, v in ranked],
        "top_hit_share": sum(v["s3"] for _, v in ranked) / total_s3 if total_s3 else 0.0,
        "top_budget_share": sum(v["full"] for _, v in ranked) / total_full if total_full else 0.0,
    }


def pack_yield_split(
    batches: list[dict[str, Any]], pack: str, hit_datasets: set[tuple]
) -> dict[str, dict[str, float]]:
    """Yield of one generic pack on hit datasets vs the rest (dataset-effect check)."""
    res: dict[str, dict[str, float]] = {}
    rows = [b for b in batches if is_generic(b) and pack_key(b) == pack]
    for name, sel in (
        ("hit_datasets", [b for b in rows if (b["region"], b["dataset_id"]) in hit_datasets]),
        ("other_datasets", [b for b in rows if (b["region"], b["dataset_id"]) not in hit_datasets]),
    ):
        if not sel:
            continue
        done = sum(int(r["done"]) for r in sel)
        res[name] = {
            "batches": len(sel),
            "full": done,
            "stage1": sum(int(r["stage1_pass"]) for r in sel) / done,
            "stage2": sum(int(r["stage2_pass"]) for r in sel) / done,
            "stage3": sum(int(r["stage3_pass"]) for r in sel) / done,
        }
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", default=str(DEFAULT_PATH))
    ap.add_argument("--base", default=BASE_PACK)
    args = ap.parse_args()
    batches = load_batches(Path(args.path))
    conc = dataset_concentration(batches)
    print(f"batches={len(batches)} datasets={conc['datasets']} stage3_hits={conc['total_stage3']}")
    print(f"top{len(conc['top'])} datasets: {conc['top_hit_share']:.1%} of hits, {conc['top_budget_share']:.1%} of FULL budget")
    for t in conc["top"]:
        print(f"  {t['dataset']}: s3={t['s3']} FULL={t['full']}")
    print(f"\nMatched (region,dataset,settings) vs base {args.base}:")
    print("| pack | cells | FULL | d_stage1 | d_stage2 |")
    print("| --- | ---: | ---: | ---: | ---: |")
    for r in matched_pack_diff(batches, args.base):
        print(f"| {r['pack']} | {r['cells']} | {r['full']} | {r['d_stage1']:+.1%} | {r['d_stage2']:+.1%} |")
    hit = {tuple(t["dataset"]) for t in conc["top"]}
    print(f"\nBase pack on top-{len(hit)} hit datasets vs others:")
    for k, v in pack_yield_split(batches, args.base, hit).items():
        print(f"  {k}: batches={v['batches']} FULL={v['full']} s1={v['stage1']:.1%} s2={v['stage2']:.1%} s3={v['stage3']:.1%}")


if __name__ == "__main__":
    main()
