"""Automated per-batch funnel logger, Stage 1/2/3/4 pass counter, and BEST/BAD batch postmortem engine.

Designed for low-memory execution on both Windows local & Guangzhou (1.9 GiB RAM):
- Reads SQLite `sim_tasks`, `sc_evaluations`, `pc_poll_queue` in read-only / streaming fashion
- Produces concise per-batch rows: (batch_id, region, universe, dataset, field, template_family,
  settings, total_done, unobs, stage1_pass, stage2_pass, stage3_pass, zero_fail, sc_pass, pc_pass,
  max_sh, avg_sh, max_2y, avg_mgn_bp, grade)
- Summarizes overall & per-region Stage 1 / Stage 2 / Stage 3 / Stage 4 cumulative funnel totals
- Automatically flags BEST batches (for replication) & BAD/TIMEOUT batches (with root-cause hints)
- Exports machine-readable JSON + concise Markdown ledger so every 2-hour audit & future run loads it directly.
"""
from __future__ import annotations

import datetime
import json
import sqlite3
from pathlib import Path
from typing import Any, Optional


def _parse_checks_zero_fail(checks_json: Optional[str]) -> tuple[bool, list[str]]:
    """Return (is_verified_zero_fail, fail_names). Empty/missing checks is NEVER treated as verified pass."""
    if not checks_json:
        return False, []
    try:
        checks = json.loads(checks_json)
    except Exception:
        return False, []
    if not isinstance(checks, list) or not checks:
        return False, []
    fails = [str(c.get("name") or "UNKNOWN") for c in checks if isinstance(c, dict) and c.get("result") == "FAIL"]
    return (len(fails) == 0), fails


def _extract_settings_compact(settings_json: Optional[str]) -> str:
    if not settings_json:
        return "?"
    try:
        s = json.loads(settings_json)
        neut = s.get("neutralization", "?")
        dec = s.get("decay", 0)
        tr = s.get("truncation", 0.04)
        return f"{neut}|d={dec}|tr={tr}"
    except Exception:
        return "?"


def classify_batch_grade(row: dict[str, Any]) -> tuple[str, str]:
    """Classify batch into BEST / GOOD / NORMAL / BAD / TIMEOUT_BUG with root-cause hint."""
    done = int(row.get("done", 0))
    unobs = int(row.get("unobs", 0))
    s1 = int(row.get("stage1_pass", 0))
    s2 = int(row.get("stage2_pass", 0))
    s3 = int(row.get("stage3_pass", 0))
    zf = int(row.get("zero_fail_s3", 0))
    max_sh = row.get("max_sh")
    min_sh = row.get("min_sh")
    region = str(row.get("region") or "").upper()
    settings_compact = str(row.get("settings_compact") or "")

    if unobs > 0 and done == 0:
        if "STATISTICAL" in settings_compact or "SLOW_AND_FAST" in settings_compact or "FAST" in settings_compact:
            return "TIMEOUT_BUG", "Risk-model neutralization timeout/429 on wide universe; lower concurrency or raise timeout"
        return "TIMEOUT_BUG", "All tasks unobserved (check HTTP 429 or poll timeout)"

    if done == 0:
        return "NORMAL", "No completed simulations yet"

    if zf >= 1 or s3 >= 2 or (max_sh is not None and max_sh >= 1.80):
        return "BEST", "Strong POOL_S / 0-FAIL hit — check reproducibility & SC/PC"
    if s3 >= 1 or s2 >= 1 or (max_sh is not None and max_sh >= 1.25):
        return "GOOD", "Reached Stage-2/3 ladder (Sharpe >= 1.25) — candidate for single-axis refinement"
    if region == "CHN" and s1 == 0 and min_sh is not None and min_sh <= -1.20:
        return "BAD", "MARKET_MICROSTRUCTURE_TRAP: CHN short-borrow double-negative mirage (0 positive hits)"
    if done >= 8 and s1 == 0 and (max_sh is None or max_sh < 0.60):
        return "BAD", "DATA_OR_LOGIC_WEAK: 0 Stage-1 hits (max Sharpe < 0.60) — verify field coverage/logic or early-stop"
    return "NORMAL", "Mixed/baseline exploration"


def build_batch_audit_report(
    db_path: Path | str,
    *,
    stage1_sh: float = 0.80,
    stage2_sh: float = 1.25,
    stage3_sh: float = 1.58,
    stage3_fit: float = 1.00,
) -> dict[str, Any]:
    """Build complete per-batch funnel ledger, global/regional stage counts, and BEST/BAD postmortems."""
    p = Path(db_path)
    conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Optional SC & PC maps if tables exist
    sc_pass_ids: set[str] = set()
    pc_pass_ids: set[str] = set()
    pc_map: dict[str, dict[str, Any]] = {}
    tables = {r["name"] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "sc_evaluations" in tables:
        for r in cur.execute("SELECT alpha_id, sc_state FROM sc_evaluations"):
            if r["sc_state"] == "SC_READY_PASS":
                sc_pass_ids.add(str(r["alpha_id"]))
    if "pc_poll_queue" in tables:
        for r in cur.execute("SELECT alpha_id, status, pc_max, check_status FROM pc_poll_queue"):
            aid = str(r["alpha_id"])
            pc_map[aid] = dict(r)
            if r["status"] == "PC_READY_PASS":
                pc_pass_ids.add(aid)

    rows = cur.execute(
        """
        SELECT batch_id, region, universe, COALESCE(dataset_id, 'unknown') AS dataset_id,
               COALESCE(primary_field_id, 'unknown') AS primary_field_id,
               COALESCE(template_id, 'unknown') AS template_id,
               status, alpha_id, sharpe, fitness, sharpe_2y, margin, turnover,
               settings_json, checks_json, error_reason, est_platform_date
        FROM sim_tasks
        """
    ).fetchall()
    conn.close()

    batches: dict[str, dict[str, Any]] = {}
    region_totals: dict[str, dict[str, int]] = {}
    overall = {
        "total_rows": 0,
        "completed_full": 0,
        "unobserved": 0,
        "dedup_skipped": 0,
        "stage1_pass_sh080": 0,
        "stage2_pass_sh125": 0,
        "stage3_pass_sh158_fit1": 0,
        "stage3_verified_zero_fail": 0,
        "stage4_sc_pass": 0,
        "stage4_pc_pass": 0,
    }

    for r in rows:
        bid = str(r["batch_id"])
        reg = str(r["region"] or "?").upper()
        st = str(r["status"] or "")
        overall["total_rows"] += 1

        rt = region_totals.setdefault(
            reg,
            {
                "total_rows": 0,
                "completed_full": 0,
                "unobserved": 0,
                "stage1_pass": 0,
                "stage2_pass": 0,
                "stage3_pass": 0,
                "zero_fail_s3": 0,
                "sc_pass": 0,
                "pc_pass": 0,
            },
        )
        rt["total_rows"] += 1

        b = batches.setdefault(
            bid,
            {
                "batch_id": bid,
                "region": reg,
                "universe": str(r["universe"] or "?"),
                "dataset_id": str(r["dataset_id"]),
                "fields": set(),
                "templates": set(),
                "settings_compact": _extract_settings_compact(r["settings_json"]),
                "total": 0,
                "done": 0,
                "unobs": 0,
                "dedup": 0,
                "stage1_pass": 0,
                "stage2_pass": 0,
                "stage3_pass": 0,
                "zero_fail_s3": 0,
                "sc_pass": 0,
                "pc_pass": 0,
                "sharpes": [],
                "two_ys": [],
                "mgns_bp": [],
                "top_alpha_id": None,
                "top_sh": None,
                "error_reasons": set(),
            },
        )
        b["total"] += 1
        b["fields"].add(str(r["primary_field_id"]))
        # Compact template prefix
        tpl = str(r["template_id"])
        b["templates"].add(tpl.split("_")[0] if "_" in tpl else tpl)

        if st == "RESULTS_UNOBSERVED":
            b["unobs"] += 1
            overall["unobserved"] += 1
            rt["unobserved"] += 1
            if r["error_reason"]:
                b["error_reasons"].add(str(r["error_reason"])[:80])
            continue
        if st == "DEDUP_SKIPPED":
            b["dedup"] += 1
            overall["dedup_skipped"] += 1
            continue
        if st not in ("COMPLETED_FULL", "COMPLETED_QUICK"):
            continue

        b["done"] += 1
        overall["completed_full"] += 1
        rt["completed_full"] += 1

        sh = r["sharpe"]
        fit = r["fitness"]
        s2y = r["sharpe_2y"]
        mgn = r["margin"]
        aid = str(r["alpha_id"] or "")

        if sh is not None:
            sh_f = float(sh)
            b["sharpes"].append(sh_f)
            if b["top_sh"] is None or sh_f > b["top_sh"]:
                b["top_sh"] = sh_f
                b["top_alpha_id"] = aid
            if sh_f >= stage1_sh:
                b["stage1_pass"] += 1
                overall["stage1_pass_sh080"] += 1
                rt["stage1_pass"] += 1
            if sh_f >= stage2_sh:
                b["stage2_pass"] += 1
                overall["stage2_pass_sh125"] += 1
                rt["stage2_pass"] += 1
            if sh_f >= stage3_sh and fit is not None and float(fit) >= stage3_fit:
                b["stage3_pass"] += 1
                overall["stage3_pass_sh158_fit1"] += 1
                rt["stage3_pass"] += 1
                zf_ok, _ = _parse_checks_zero_fail(r["checks_json"])
                if zf_ok:
                    b["zero_fail_s3"] += 1
                    overall["stage3_verified_zero_fail"] += 1
                    rt["zero_fail_s3"] += 1
        if s2y is not None:
            b["two_ys"].append(float(s2y))
        if mgn is not None:
            b["mgns_bp"].append(float(mgn) * 10000.0)
        if aid and aid in sc_pass_ids:
            b["sc_pass"] += 1
            overall["stage4_sc_pass"] += 1
            rt["sc_pass"] += 1
        if aid and aid in pc_pass_ids:
            b["pc_pass"] += 1
            overall["stage4_pc_pass"] += 1
            rt["pc_pass"] += 1

    batch_records: list[dict[str, Any]] = []
    for b in batches.values():
        sharpes = b.pop("sharpes")
        two_ys = b.pop("two_ys")
        mgns = b.pop("mgns_bp")
        fields_sorted = sorted(b.pop("fields"))
        tpls_sorted = sorted(b.pop("templates"))
        errs_sorted = sorted(b.pop("error_reasons"))

        rec = {
            **b,
            "primary_field_summary": ", ".join(fields_sorted[:3]) + (f" (+{len(fields_sorted)-3})" if len(fields_sorted) > 3 else ""),
            "template_summary": ", ".join(tpls_sorted[:3]) + (f" (+{len(tpls_sorted)-3})" if len(tpls_sorted) > 3 else ""),
            "max_sh": round(max(sharpes), 2) if sharpes else None,
            "min_sh": round(min(sharpes), 2) if sharpes else None,
            "avg_sh": round(sum(sharpes) / len(sharpes), 2) if sharpes else None,
            "max_2y": round(max(two_ys), 2) if two_ys else None,
            "avg_mgn_bp": round(sum(mgns) / len(mgns), 2) if mgns else None,
            "error_reasons": errs_sorted[:2],
        }
        grade, diagnosis = classify_batch_grade(rec)
        rec["grade"] = grade
        rec["diagnosis"] = diagnosis
        batch_records.append(rec)

    batch_records.sort(key=lambda x: (x["region"], -(x["max_sh"] if x["max_sh"] is not None else -99.0), x["batch_id"]))

    best_batches = [x for x in batch_records if x["grade"] == "BEST"]
    best_batches.sort(key=lambda x: -(x["max_sh"] or -99.0))
    bad_batches = [x for x in batch_records if x["grade"] in ("BAD", "TIMEOUT_BUG")]
    bad_batches.sort(key=lambda x: (-x["unobs"], x["max_sh"] if x["max_sh"] is not None else 99.0))

    return {
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "db_path": str(p),
        "thresholds": {
            "stage1_sh": stage1_sh,
            "stage2_sh": stage2_sh,
            "stage3_sh": stage3_sh,
            "stage3_fit": stage3_fit,
        },
        "overall_funnel": overall,
        "region_funnel": dict(sorted(region_totals.items(), key=lambda kv: -kv[1]["completed_full"])),
        "total_batches": len(batch_records),
        "grade_counts": {
            g: sum(1 for x in batch_records if x["grade"] == g)
            for g in ("BEST", "GOOD", "NORMAL", "BAD", "TIMEOUT_BUG")
        },
        "best_batches": best_batches[:30],
        "bad_or_timeout_batches": bad_batches[:30],
        "batches": batch_records,
    }


def render_batch_audit_markdown(report: dict[str, Any], *, max_rows: int = 120) -> str:
    """Render concise human-readable Markdown ledger for quick review and next-session loading."""
    ov = report["overall_funnel"]
    lines = [
        "# WorldQuant BRAIN D1 RA 批次复盘与阶段漏斗总账（自动生成）",
        "",
        f"- **生成时间 (UTC)**：`{report['generated_at_utc']}`",
        f"- **总批次数**：`{report['total_batches']}`（等级分布：`{report['grade_counts']}`）",
        f"- **全库阶段过关统计**：有效完成 `{ov['completed_full']}` · 未观测 `{ov['unobserved']}` · "
        f"**一阶段 (`Sh≥0.80`) 过 `{ov['stage1_pass_sh080']}` 个** · "
        f"**二阶段 (`Sh≥1.25`) 过 `{ov['stage2_pass_sh125']}` 个** · "
        f"**三阶段 (`Sh≥1.58 & Fit≥1.0`) 过 `{ov['stage3_pass_sh158_fit1']}` 个**（已核 0-FAIL `{ov['stage3_verified_zero_fail']}` 个）",
        "",
        "## 1. 分地区阶段漏斗统计",
        "",
        "| 地区 | 完成数 | 未观测 | 一阶段过 (`≥0.80`) | 二阶段过 (`≥1.25`) | 三阶段过 (`≥1.58 & Fit≥1`) | 已核 0-FAIL |",
        "| :-: | :-: | :-: | :-: | :-: | :-: | :-: |",
    ]
    for reg, st in report["region_funnel"].items():
        lines.append(
            f"| **{reg}** | {st['completed_full']} | {st['unobserved']} | {st['stage1_pass']} | "
            f"{st['stage2_pass']} | {st['stage3_pass']} | {st['zero_fail_s3']} |"
        )

    lines.extend([
        "",
        "## 2. 过好批次（BEST · 重点核查可复现性与推广）",
        "",
        "| 批次 ID | 地区/池 | 数据集 | 主字段 | 模板族 | 配置 | 过 S1/S2/S3 (0-FAIL) | Max Sh / 2Y / Mgn | 冠军 ID |",
        "| --- | :-: | --- | --- | --- | --- | :-: | :-: | :-: |",
    ])
    for b in report["best_batches"][:20]:
        lines.append(
            f"| `{b['batch_id']}` | {b['region']}/{b['universe']} | `{b['dataset_id']}` | `{b['primary_field_summary']}` | "
            f"`{b['template_summary']}` | `{b['settings_compact']}` | {b['stage1_pass']}/{b['stage2_pass']}/{b['stage3_pass']} ({b['zero_fail_s3']}) | "
            f"`{b['max_sh']}` / `{b['max_2y']}` / `{b['avg_mgn_bp']}bp` | `{b['top_alpha_id']}` |"
        )

    lines.extend([
        "",
        "## 3. 过差与超时异常批次（BAD / TIMEOUT_BUG · 排雷与逻辑复盘）",
        "",
        "| 等级 | 批次 ID | 地区/数据集 | 主字段 | 配置 | 完成/未观测 | Max Sh | 根因诊断与避坑建议 |",
        "| :-: | --- | --- | --- | --- | :-: | :-: | --- |",
    ])
    for b in report["bad_or_timeout_batches"][:25]:
        err_note = f" ({'; '.join(b['error_reasons'])})" if b.get("error_reasons") else ""
        lines.append(
            f"| **{b['grade']}** | `{b['batch_id']}` | {b['region']}/`{b['dataset_id']}` | `{b['primary_field_summary']}` | "
            f"`{b['settings_compact']}` | {b['done']}/{b['unobs']} | `{b['max_sh']}` | {b['diagnosis']}{err_note} |"
        )

    lines.extend([
        "",
        f"## 4. 全批次精简台账（展示前 {min(max_rows, len(report['batches']))} / {len(report['batches'])} 批）",
        "",
        "| 等级 | 地区 | 数据集 | 主字段 | 模板 | 配置 | 完成/未观测 | S1/S2/S3 | Max Sh | Avg Mgn |",
        "| :-: | :-: | --- | --- | --- | --- | :-: | :-: | :-: | :-: |",
    ])
    for b in report["batches"][:max_rows]:
        lines.append(
            f"| {b['grade']} | {b['region']} | `{b['dataset_id']}` | `{b['primary_field_summary']}` | "
            f"`{b['template_summary']}` | `{b['settings_compact']}` | {b['done']}/{b['unobs']} | "
            f"{b['stage1_pass']}/{b['stage2_pass']}/{b['stage3_pass']} | `{b['max_sh']}` | `{b['avg_mgn_bp']}bp` |"
        )

    return "\n".join(lines) + "\n"
