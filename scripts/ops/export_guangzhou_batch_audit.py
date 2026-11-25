#!/usr/bin/env python3
"""Remote-runnable Guangzhou per-batch funnel & BEST/BAD postmortem exporter.

Usage (PowerShell):
    Get-Content -Raw 'scripts/ops/export_guangzhou_batch_audit.py' | ssh guangzhou '/root/miniconda3/bin/python -'
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "/root/worldquont/wq_research_v2/src")
from wq_research_v2.batch_audit_logger import build_batch_audit_report, render_batch_audit_markdown


def main() -> None:
    db_path = Path("/root/worldquont/data/wq_v2_ledger.db")
    rep = build_batch_audit_report(db_path)
    out_dir = Path("/root/worldquont/data/exports")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "batch_audit_latest.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    md = render_batch_audit_markdown(rep)
    (out_dir / "batch_audit_latest.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
