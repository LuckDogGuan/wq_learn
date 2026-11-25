#!/usr/bin/env python3
"""Read-only live inspector for Guangzhou wq_research_v2 SQLite ledger & systemd service.

Usage (PowerShell-safe, zero nested quoting):
    Get-Content scripts/ops/check_guangzhou_v2.py | ssh guangzhou "/root/miniconda3/bin/python -"

Never reads credentials, never modifies remote state, minimal RAM footprint.
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from datetime import datetime, timezone


DB_PATH = os.environ.get("WQ_V2_DB", "/root/worldquont/data/wq_v2_ledger.db")
LOG_PATH = os.environ.get("WQ_V2_LOG", "/root/worldquont/data/deu_ra_runner.log")
EXPORT_DIR = os.environ.get("WQ_V2_EXPORT_DIR", "/root/worldquont/data/exports")
SERVICE_NAME = os.environ.get("WQ_V2_SERVICE", "worldquant-v2-deu-ra.service")


def _run_cmd(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=10)
        return out.strip()
    except Exception as exc:
        return f"<err: {exc}>"


def main() -> None:
    print(f"=== GUANGZHOU V2 LIVE AUDIT @ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} ===")
    print(f"\n[1] SYSTEMD SERVICE ({SERVICE_NAME}):")
    print(_run_cmd([
        "systemctl", "show", SERVICE_NAME,
        "--property=ActiveState,SubState,MainPID,MemoryCurrent,CPUUsageNSec,ExecStart"
    ]))

    print("\n[2] SYSTEM RESOURCES:")
    print(_run_cmd(["free", "-m"]))
    print(_run_cmd(["df", "-h", "/"]))

    if not os.path.exists(DB_PATH):
        print(f"\n[3] LEDGER DB NOT FOUND: {DB_PATH}")
        return

    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("\n[3] OVERALL SIM_TASKS STATUS COUNTS:")
    for r in cur.execute("SELECT status, COUNT(*) as cnt FROM sim_tasks GROUP BY status ORDER BY cnt DESC"):
        print(f"  {r['status']}: {r['cnt']}")

    print("\n[4] PER-(REGION, UNIVERSE, DATASET, QUEUE, MODE) PERFORMANCE BREAKDOWN:")
    query = """
        SELECT
            region,
            universe,
            COALESCE(dataset_id, 'unknown') AS ds,
            queue_type,
            simulation_mode AS sim_mode,
            COUNT(*) AS total,
            SUM(CASE WHEN status IN ('COMPLETED_FULL','COMPLETED_QUICK') THEN 1 ELSE 0 END) AS done,
            SUM(CASE WHEN status IN ('COMPLETED_FULL','COMPLETED_QUICK') AND ABS(COALESCE(sharpe,0)) >= 0.80 THEN 1 ELSE 0 END) AS abs_ge_08,
            SUM(CASE WHEN status IN ('COMPLETED_FULL','COMPLETED_QUICK') AND COALESCE(sharpe,0) >= 1.25 THEN 1 ELSE 0 END) AS sh_ge_125,
            SUM(CASE WHEN status IN ('COMPLETED_FULL','COMPLETED_QUICK') AND COALESCE(sharpe,0) >= 1.58 THEN 1 ELSE 0 END) AS sh_ge_158,
            SUM(CASE WHEN status IN ('COMPLETED_FULL','COMPLETED_QUICK') AND COALESCE(sharpe,0) <= -1.20 THEN 1 ELSE 0 END) AS flip_le_m12,
            ROUND(AVG(CASE WHEN status IN ('COMPLETED_FULL','COMPLETED_QUICK') THEN sharpe END), 3) AS avg_sh,
            ROUND(MAX(CASE WHEN status IN ('COMPLETED_FULL','COMPLETED_QUICK') THEN sharpe END), 3) AS max_sh,
            ROUND(MIN(CASE WHEN status IN ('COMPLETED_FULL','COMPLETED_QUICK') THEN sharpe END), 3) AS min_sh,
            ROUND(AVG(CASE WHEN status IN ('COMPLETED_FULL','COMPLETED_QUICK') THEN turnover END), 4) AS avg_to,
            ROUND(AVG(CASE WHEN status IN ('COMPLETED_FULL','COMPLETED_QUICK') THEN margin END) * 10000.0, 2) AS avg_mgn_bp,
            ROUND(MAX(CASE WHEN status IN ('COMPLETED_FULL','COMPLETED_QUICK') THEN fitness END), 3) AS max_fit
        FROM sim_tasks
        GROUP BY region, universe, ds, queue_type, sim_mode
        ORDER BY region, ds, total DESC
    """
    for r in cur.execute(query):
        print(
            f"  {r['region']}/{r['universe']} | ds={r['ds']} ({r['queue_type']},{r['sim_mode']}) | "
            f"tot={r['total']} done={r['done']} | |sh|>=0.8:{r['abs_ge_08']} sh>=1.25:{r['sh_ge_125']} "
            f"sh>=1.58:{r['sh_ge_158']} flip<=-1.2:{r['flip_le_m12']} | "
            f"avg_sh={r['avg_sh']} max={r['max_sh']} min={r['min_sh']} | "
            f"avg_to={r['avg_to']} avg_mgn={r['avg_mgn_bp']}bp max_fit={r['max_fit']}"
        )

    print("\n[5] PER-TEMPLATE SUMMARY (COMPLETED ONLY):")
    tpl_q = """
        SELECT
            region,
            COALESCE(dataset_id, 'unknown') AS ds,
            COALESCE(template_id, 'unknown') AS tpl,
            source_side,
            COUNT(*) AS done,
            ROUND(AVG(sharpe), 3) AS avg_sh,
            ROUND(MAX(sharpe), 3) AS max_sh,
            ROUND(MIN(sharpe), 3) AS min_sh,
            ROUND(AVG(turnover), 4) AS avg_to,
            SUM(CASE WHEN ABS(COALESCE(sharpe,0)) >= 0.80 THEN 1 ELSE 0 END) AS hits_08
        FROM sim_tasks
        WHERE status IN ('COMPLETED_FULL','COMPLETED_QUICK')
        GROUP BY region, ds, tpl, source_side
        ORDER BY region, ds, hits_08 DESC, max_sh DESC
        LIMIT 30
    """
    for r in cur.execute(tpl_q):
        print(
            f"  {r['region']}/{r['ds']} | {r['tpl']} ({r['source_side'][:5]}) | "
            f"n={r['done']} | hits08={r['hits_08']} | avg={r['avg_sh']} max={r['max_sh']} min={r['min_sh']} to={r['avg_to']}"
        )

    print("\n[6] TOP 20 COMPLETED ALPHAS BY ABS(SHARPE):")
    top_q = """
        SELECT alpha_id, region, universe, COALESCE(dataset_id, 'unknown') AS ds,
               primary_field_id, template_id, sharpe, fitness, turnover, margin,
               sharpe_2y, rn_sharpe, expression
        FROM sim_tasks
        WHERE status IN ('COMPLETED_FULL','COMPLETED_QUICK') AND sharpe IS NOT NULL
        ORDER BY ABS(sharpe) DESC
        LIMIT 20
    """
    for r in cur.execute(top_q):
        mgn_bp = round(r["margin"] * 10000.0, 2) if r["margin"] is not None else None
        expr = (r["expression"] or "").replace("\n", " ")[:90]
        print(
            f"  {r['alpha_id']} | {r['region']}/{r['universe']}/{r['ds']} | "
            f"sh={r['sharpe']} 2y={r['sharpe_2y']} fit={r['fitness']} to={r['turnover']} "
            f"mgn={mgn_bp}bp | {expr}"
        )

    print("\n[7] RATELIMIT / HTTP EVENTS SUMMARY:")
    for r in cur.execute(
        "SELECT http_status, COUNT(*) AS cnt, MIN(remaining_val) AS min_rem, MAX(limit_val) AS max_lim "
        "FROM ratelimit_events GROUP BY http_status ORDER BY cnt DESC"
    ):
        print(f"  HTTP {r['http_status']}: cnt={r['cnt']} min_remaining={r['min_rem']} limit={r['max_lim']}")

    print("\n[8] DAILY VOLUME SNAPSHOTS:")
    for r in cur.execute("SELECT * FROM daily_volume_snapshots ORDER BY est_platform_date DESC LIMIT 5"):
        d = dict(r)
        print(
            f"  EST {d['est_platform_date']}: full={d['full_valid_completed_count']} "
            f"quick={d['quick_screened_count']} sub={d['submitted_count']} "
            f"unobs={d['unobserved_count']} alpha0={d['alpha0_completed']} "
            f"normal={d['normal_completed']} g1={d['gate1_count']} t1={d['tier1_pass_count']}"
        )

    conn.close()

    if os.path.isdir(EXPORT_DIR):
        print("\n[9] EXPORTED FUNNEL SNAPSHOTS:")
        for fn in sorted(os.listdir(EXPORT_DIR)):
            if fn.endswith(".json"):
                fp = os.path.join(EXPORT_DIR, fn)
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    print(
                        f"  {fn}: region={data.get('region')} total={data.get('total_completed')} "
                        f"counts={data.get('counts')}"
                    )
                except Exception as exc:
                    print(f"  {fn}: <parse err: {exc}>")

    if os.path.exists(LOG_PATH):
        print("\n[10] RUNNER LOG TAIL (last 20 lines):")
        with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-20:]
        for ln in lines:
            print("  " + ln.rstrip())


if __name__ == "__main__":
    main()
