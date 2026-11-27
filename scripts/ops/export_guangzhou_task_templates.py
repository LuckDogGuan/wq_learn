#!/usr/bin/env python3
"""Remote-runnable, strictly READ-ONLY per-task exporter for template/operator screening.

Usage (PowerShell; binary-safe redirect via cmd):
    cmd /c "type scripts\\ops\\export_guangzhou_task_templates.py | ssh guangzhou /root/miniconda3/bin/python - > data\\exports\\task_template_rows.csv"
    (schema only)  ... python - --schema

Safety: opens the ledger with mode=ro, streams rows (low-memory host), writes CSV to stdout only,
never writes to the DB, never touches credentials. Compact FAIL/WARNING names are derived from checks_json
so the raw JSON blob is not shipped.
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys

DB = "/root/worldquont/data/wq_v2_ledger.db"
WANT = [
    "task_id", "batch_id", "template_id", "source_side", "author_id", "canonical_post_id", "atlas_layer",
    "parent_baseline_alpha_id", "parent_family_id", "single_changed_axis", "queue_type",
    "region", "universe", "dataset_id", "primary_field_id", "simulation_mode", "status",
    "expression", "settings_json", "alpha_id",
    "sharpe", "fitness", "turnover", "margin", "returns", "sharpe_2y", "rn_sharpe", "rn_fitness",
    "gate_status", "error_reason", "completed_at_utc", "est_platform_date",
]


def _names(checks_json, result):
    if not checks_json:
        return "", False
    try:
        checks = json.loads(checks_json)
    except Exception:
        return "", False
    if not isinstance(checks, list) or not checks:
        return "", False
    names = [str(c.get("name")) for c in checks if isinstance(c, dict) and c.get("result") == result]
    return "|".join(names), True


def main() -> None:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    cols = [r[1] for r in con.execute("PRAGMA table_info(sim_tasks)")]
    if "--schema" in sys.argv:
        total = con.execute("select count(*) from sim_tasks").fetchone()[0]
        by = con.execute("select status, simulation_mode, count(*) from sim_tasks group by 1,2").fetchall()
        sys.stdout.write(json.dumps({"columns": cols, "rows": total, "by_status_mode": by}, ensure_ascii=False) + "\n")
        return
    use = [c for c in WANT if c in cols]
    missing = [c for c in WANT if c not in cols]
    if missing:
        sys.stderr.write(f"missing columns skipped: {missing}\n")
    sel = ", ".join(use + (["checks_json"] if "checks_json" in cols else []))
    import io

    w = csv.writer(io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="", write_through=True))
    w.writerow(use + ["fail_checks", "warn_checks", "checks_present"])
    n = 0
    cur = con.execute(f"select {sel} from sim_tasks where status in ('COMPLETED_FULL','COMPLETED_QUICK')")
    for row in cur:
        row = list(row)
        cj = row.pop() if "checks_json" in cols else None
        fails, present = _names(cj, "FAIL")
        warns, _ = _names(cj, "WARNING")
        w.writerow(row + [fails, warns, int(present)])
        n += 1
    sys.stderr.write(f"exported rows: {n}\n")


if __name__ == "__main__":
    main()
