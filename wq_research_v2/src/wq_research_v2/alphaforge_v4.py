"""Route ④ (`alphaforge_agy_dsh_v4`) — AlphaForge AGY-DSH Closed-Loop Research Engine.

Built strictly on top of Baseline v1 (`d1_ra_baseline_v1_frozen.json`) and `wq_research_v2`,
implementing the P0/P1/P2 review recommendations from `doc/ALPHAFORGE_WORKFLOW_REVIEW_20261128.md`:
- Main controller: Antigravity CLI (`agy`) owning preflight, direction selection, verification,
  state writes, and Margin-first auto-PATCH (ZERO `/submit` calls).
- Subagent delegation: DSH Crew MCP (`dsh-opencode-go/deepseek-v4.1-flash`, `tier=flash`,
  `effort=high`, probe-first, max 2 concurrent read-only workers, max 4 dialogue rounds per worker).
- Historical experience reuse: automatically injects coordinate-matched lessons, bans, empirical
  rules, audited rules, and crowding priors via `ExperienceReuser`.

P0/P1/P2 deterministic primitives implemented here:
1. P0 Execution-Entry Preflight Guard: sequential `NORMAL < 4500` gate before `UNUSED_ALPHA0`,
   fingerprint dedup blocking `COMPLETED_*` / `SUBMITTED` / `PENDING_RECONCILE` / `RESULTS_UNOBSERVED`,
   D1-Only / Decision #3 / Gold-81 validation, and region thread caps (`GLB<=3`, others `<=4`).
2. P0 + P1 + P2 Platform-Day Funnel & Progress Inspector: `America/New_York` alignment,
   NORMAL vs ALPHA0 and FULL vs QUICK separation, alpha_id dedup, `VERIFIED_ZERO_FAIL` vs
   `UNVERIFIED` checks, `last_completed_utc` / `oldest_pending_age_sec` / restart progress,
   and `verified_candidates_per_100_full` unit yield.
3. P1 Target-Aware PPA-First Attribution: counts unique non-exempt ops (`<=8`) and non-exempt
   fields (`<=3`), preserving 403 / raw `/check` / UI `Prod Correlation FAIL` sources separately.
4. P1 Failure-Feedback-to-Origin-Direction & Pivot Budget: structures failure evidence (incl.
   low localSC + high PC) back to the originating research direction, quarantining families after
   2 consecutive same-root-cause batches while excluding `PENDING` / `RESULTS_UNOBSERVED` / platform faults.
5. P2 3-Primary + 1-Backup ("三主一备") Pyramid Manual-Review Roster: selects orthogonal (`<0.68`)
   same-day verified passing candidates by Pyramid priority & Margin DESC, reporting gaps honestly.
6. Antigravity CLI (`agy`) command/prompt builder & self-contained DSH subagent brief compiler.
"""
from __future__ import annotations

import datetime
import json
import shutil
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from wq_research_v2.batch_audit_logger import classify_checks_state
from wq_research_v2.config_loader import REPO_ROOT
from wq_research_v2.experience_reuser import ExperienceReuser
from wq_research_v2.expr_validator import (
    CallNode,
    ExprValidator,
    IdentNode,
    _Parser,
    compute_payload_fingerprint,
    tokenize,
)
from wq_research_v2.ledger_store import LedgerStore
from wq_research_v2.quota_tracker import current_est_platform_date
from wq_research_v2.sim_runner import MAX_THREADS_GLB, MAX_THREADS_OTHER_REGION


TRACK_ID = "alphaforge_agy_dsh_v4"
TRACK_NAME_ZH = "锻造闭环路径 (AlphaForge AGY-DSH v4.0)"
TRACK_LOG_PREFIX = "[TRACK:alphaforge_agy_dsh_v4]"
BASE_TRACK_ID = "baseline_v1"

PPA_EXEMPT_OPERATORS = frozenset({"ts_backfill", "group_backfill"})
PPA_EXEMPT_GROUP_FIELDS = frozenset(
    {"country", "currency", "exchange", "industry", "market", "sector", "subindustry"}
)
TERMINAL_OR_INFLIGHT_FINGERPRINT_STATUSES = frozenset(
    {"COMPLETED_QUICK", "COMPLETED_FULL", "SUBMITTED", "PENDING_RECONCILE", "RESULTS_UNOBSERVED"}
)
NON_STRATEGY_FAILURE_CODES = frozenset(
    {"PENDING", "PENDING_PC_COMPUTING", "RESULTS_UNOBSERVED", "HTTP_429", "HTTP_5XX", "TIMEOUT", "PLATFORM_ERROR", "SYNTAX_ERROR"}
)


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _parse_iso_utc(raw: Optional[str]) -> Optional[datetime.datetime]:
    if not raw:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc)
    except ValueError:
        return None


def resolve_region_thread_cap(region: str, requested_threads: int) -> tuple[int, bool]:
    """Enforce hard concurrency cap: GLB <= 3, all other regions <= 4."""
    reg = (region or "").strip().upper()
    hard_cap = MAX_THREADS_GLB if reg == "GLB" else MAX_THREADS_OTHER_REGION
    req = max(1, int(requested_threads))
    capped = min(req, hard_cap)
    return capped, (req > hard_cap)


# ---------------------------------------------------------------------------
# P0: Execution-Entry Preflight Guard
# ---------------------------------------------------------------------------
@dataclass
class PreflightResult:
    allowed: bool
    queue_type: str
    region: str
    effective_threads: int
    payload_fingerprint: Optional[str]
    block_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    policy_notes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "queue_type": self.queue_type,
            "region": self.region,
            "effective_threads": self.effective_threads,
            "payload_fingerprint": self.payload_fingerprint,
            "block_reasons": self.block_reasons,
            "warnings": self.warnings,
            "policy_notes": self.policy_notes,
        }


def evaluate_dispatch_preflight(
    *,
    region: str,
    queue_type: str,
    normal_completed_today: int,
    alpha0_switch_threshold: int = 4500,
    requested_threads: int = 2,
    expression: Optional[str] = None,
    settings: Optional[Mapping[str, Any]] = None,
    stage: str = "STAGE_3",
    simulation_mode: str = "FULL",
    ledger: Optional[LedgerStore] = None,
    db_path: Optional[Path | str] = None,
    allow_post_429_retry: bool = False,
) -> PreflightResult:
    """Enforce P0 execution-entry rules BEFORE any simulation payload is dispatched.

    Prevents the two real incidents audited in `doc/ALPHAFORGE_WORKFLOW_REVIEW_20261128.md`:
    1. Premature `UNUSED_ALPHA0` dispatch before `normal_completed_today >= 4500`.
    2. Re-dispatching any fingerprint already in COMPLETED/SUBMITTED/PENDING_RECONCILE/RESULTS_UNOBSERVED.
    Also enforces D1-Only, Stage 3-4 FULL lock, Decision #3/Gold-81 AST gates, and region caps.
    """
    reg = (region or "").strip().upper()
    qtype = (queue_type or "NORMAL").strip().upper()
    sim_mode = (simulation_mode or "FULL").strip().upper()
    st_u = (stage or "STAGE_3").strip().upper()

    blocks: list[str] = []
    warnings: list[str] = []
    eff_threads, was_capped = resolve_region_thread_cap(reg, requested_threads)
    if was_capped:
        warnings.append(
            f"Region {reg} requested {requested_threads} threads > hard cap {eff_threads}; clamped to {eff_threads}."
        )

    # 1) Strict sequential quota gate: NORMAL < 4500 MUST NOT dispatch UNUSED_ALPHA0
    if qtype == "UNUSED_ALPHA0" and int(normal_completed_today) < int(alpha0_switch_threshold):
        blocks.append(
            f"PREMATURE_ALPHA0_BLOCKED: normal_completed_today={normal_completed_today} < "
            f"threshold={alpha0_switch_threshold} (must finish NORMAL_ONLY first, no concurrent mix)."
        )

    # 2) Stage 3-4 strictly locked to FULL
    if st_u in ("STAGE_3", "STAGE_4", "STAGE3", "STAGE4") and sim_mode != "FULL":
        blocks.append(f"STAGE34_FULL_LOCKED: {st_u} forbids simulationMode={sim_mode}; must use FULL.")

    # 3) Optional expression + settings AST & fingerprint dedup gate
    fp: Optional[str] = None
    if expression is not None:
        eff_settings = dict(settings or {})
        eff_settings.setdefault("region", reg or "USA")
        eff_settings.setdefault("universe", "TOP3000")
        eff_settings.setdefault("delay", 1)
        eff_settings.setdefault("neutralization", "SUBINDUSTRY")
        eff_settings.setdefault("visualization", False)
        eff_settings["simulationMode"] = sim_mode

        rep = ExprValidator().validate(expression, eff_settings, queue_type=qtype)
        fp = rep.payload_fingerprint or compute_payload_fingerprint(expression, eff_settings)[0]
        if not rep.valid:
            blocks.extend([f"AST_GATE_FAIL: {err}" for err in rep.errors])
        warnings.extend(rep.warnings)

        # Check fingerprint in LedgerStore or read-only SQLite db
        existing_status = _lookup_fingerprint_status(fp, ledger=ledger, db_path=db_path)
        if existing_status in TERMINAL_OR_INFLIGHT_FINGERPRINT_STATUSES:
            blocks.append(
                f"FINGERPRINT_ALREADY_RECORDED: fp={fp[:16]}... has status={existing_status} "
                "(reconcile-once / immutable ledger rule forbids re-dispatch)."
            )

    policy_notes = {
        "track_id": TRACK_ID,
        "alpha0_switch_threshold": int(alpha0_switch_threshold),
        "normal_completed_today": int(normal_completed_today),
        "quota_mode": "ALPHA0_EXEMPT_ONLY" if int(normal_completed_today) >= int(alpha0_switch_threshold) else "NORMAL_ONLY",
        "allow_post_429_retry": bool(allow_post_429_retry),
        "auto_submit_allowed": False,
    }
    if allow_post_429_retry:
        warnings.append(
            "allow_post_429_retry=True enabled: verify 429 occurred BEFORE server creation (no Location header) before retrying."
        )

    return PreflightResult(
        allowed=(len(blocks) == 0),
        queue_type=qtype,
        region=reg,
        effective_threads=eff_threads,
        payload_fingerprint=fp,
        block_reasons=blocks,
        warnings=warnings,
        policy_notes=policy_notes,
    )


def _lookup_fingerprint_status(
    payload_fingerprint: str,
    *,
    ledger: Optional[LedgerStore] = None,
    db_path: Optional[Path | str] = None,
) -> Optional[str]:
    if ledger is not None:
        if ledger.has_completed_fingerprint(payload_fingerprint):
            with ledger._lock:  # noqa: SLF001 - read-only lookup
                row = ledger._conn.execute(  # noqa: SLF001
                    "SELECT status FROM sim_tasks WHERE payload_fingerprint=? ORDER BY completed_at_utc DESC LIMIT 1",
                    (payload_fingerprint,),
                ).fetchone()
                return str(row["status"]) if row else "COMPLETED_FULL"
        return None
    if db_path is not None and Path(db_path).exists():
        conn = sqlite3.connect(f"file:{Path(db_path)}?mode=ro", uri=True)
        try:
            row = conn.execute(
                "SELECT status FROM sim_tasks WHERE payload_fingerprint=? LIMIT 1",
                (payload_fingerprint,),
            ).fetchone()
            return str(row[0]) if row else None
        finally:
            conn.close()
    return None


# ---------------------------------------------------------------------------
# P0 + P1 + P2: Platform-Day Aligned Funnel, Progress & Unit-Yield Inspector
# ---------------------------------------------------------------------------
def build_platform_day_funnel(
    db_path: Path | str,
    *,
    est_platform_date: Optional[str] = None,
    restart_at_utc: Optional[str] = None,
    now_utc: Optional[datetime.datetime] = None,
) -> dict[str, Any]:
    """Build America/New_York platform-day aligned funnel with zero double-counting.

    Implements AlphaForge P0 (funnel accounting), P1 (progress age / stall visibility),
    and P2 (unit yield per 100 completed FULL).
    """
    p = Path(db_path)
    day = est_platform_date or current_est_platform_date()
    now_dt = now_utc or _utc_now()
    restart_dt = _parse_iso_utc(restart_at_utc)

    if not p.exists():
        return {
            "track_id": TRACK_ID,
            "est_platform_date": day,
            "db_found": False,
            "error": f"SQLite ledger not found: {p}",
        }

    conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        rows = conn.execute(
            """
            SELECT task_id, batch_id, queue_type, region, universe, dataset_id, simulation_mode,
                   status, alpha_id, sharpe, fitness, margin, checks_json, submitted_at_utc,
                   completed_at_utc, est_platform_date
            FROM sim_tasks
            WHERE est_platform_date = ?
            """,
            (day,),
        ).fetchall()

        latest_rl = None
        if "ratelimit_events" in tables:
            rl_row = conn.execute(
                """
                SELECT endpoint, http_status, limit_val, remaining_val, reset_val, observed_at_utc
                FROM ratelimit_events
                WHERE est_platform_date = ? AND endpoint LIKE '%/simulations%' AND limit_val IS NOT NULL
                ORDER BY observed_at_utc DESC
                LIMIT 1
                """,
                (day,),
            ).fetchone()
            if rl_row is not None:
                latest_rl = dict(rl_row)

        pc_pass_alphas: set[str] = set()
        sc_pass_alphas: set[str] = set()
        if "sc_evaluations" in tables:
            for r in conn.execute("SELECT alpha_id, sc_state FROM sc_evaluations"):
                if r["sc_state"] == "SC_READY_PASS":
                    sc_pass_alphas.add(str(r["alpha_id"]))
        if "pc_poll_queue" in tables:
            for r in conn.execute("SELECT alpha_id, status FROM pc_poll_queue"):
                if r["status"] == "PC_READY_PASS":
                    pc_pass_alphas.add(str(r["alpha_id"]))
    finally:
        conn.close()

    by_queue: dict[str, dict[str, int]] = {}
    status_counts: dict[str, int] = {}
    unique_completed_alphas: set[str] = set()
    verified_zero_fail_alphas: set[str] = set()
    unverified_full_alphas: set[str] = set()
    final_passed_alphas: set[str] = set()

    last_completed_dt: Optional[datetime.datetime] = None
    oldest_pending_dt: Optional[datetime.datetime] = None
    first_after_restart_dt: Optional[datetime.datetime] = None

    completed_full_total = 0
    completed_quick_total = 0

    for r in rows:
        qt = str(r["queue_type"] or "NORMAL").upper()
        st = str(r["status"] or "UNKNOWN").upper()
        mode = str(r["simulation_mode"] or "").upper()
        aid = str(r["alpha_id"] or "").strip()

        status_counts[st] = status_counts.get(st, 0) + 1
        q_bucket = by_queue.setdefault(
            qt,
            {
                "completed_full": 0,
                "completed_quick": 0,
                "queued": 0,
                "in_flight": 0,
                "pending_reconcile": 0,
                "results_unobserved": 0,
                "dedup_skipped": 0,
                "other": 0,
            },
        )

        if st == "COMPLETED_FULL":
            q_bucket["completed_full"] += 1
            completed_full_total += 1
        elif st == "COMPLETED_QUICK":
            q_bucket["completed_quick"] += 1
            completed_quick_total += 1
        elif st == "QUEUED":
            q_bucket["queued"] += 1
        elif st == "SUBMITTED":
            q_bucket["in_flight"] += 1
        elif st == "PENDING_RECONCILE":
            q_bucket["pending_reconcile"] += 1
        elif st == "RESULTS_UNOBSERVED":
            q_bucket["results_unobserved"] += 1
        elif st == "DEDUP_SKIPPED":
            q_bucket["dedup_skipped"] += 1
        else:
            q_bucket["other"] += 1

        if st in ("COMPLETED_FULL", "COMPLETED_QUICK"):
            comp_dt = _parse_iso_utc(r["completed_at_utc"])
            if comp_dt is not None:
                if last_completed_dt is None or comp_dt > last_completed_dt:
                    last_completed_dt = comp_dt
                if restart_dt is not None and comp_dt >= restart_dt:
                    if first_after_restart_dt is None or comp_dt < first_after_restart_dt:
                        first_after_restart_dt = comp_dt
            if aid:
                unique_completed_alphas.add(aid)
                if st == "COMPLETED_FULL" or mode == "FULL":
                    chk_state, _ = classify_checks_state(r["checks_json"])
                    if chk_state == "VERIFIED_ZERO_FAIL":
                        verified_zero_fail_alphas.add(aid)
                        if aid in sc_pass_alphas and aid in pc_pass_alphas:
                            final_passed_alphas.add(aid)
                    elif chk_state == "UNVERIFIED":
                        unverified_full_alphas.add(aid)
        elif st in ("QUEUED", "SUBMITTED", "PENDING_RECONCILE"):
            sub_dt = _parse_iso_utc(r["submitted_at_utc"])
            if sub_dt is not None and (oldest_pending_dt is None or sub_dt < oldest_pending_dt):
                oldest_pending_dt = sub_dt

    oldest_pending_age_sec = (
        round((now_dt - oldest_pending_dt).total_seconds(), 1) if oldest_pending_dt is not None else None
    )
    first_completion_after_restart_sec = (
        round((first_after_restart_dt - restart_dt).total_seconds(), 1)
        if (restart_dt is not None and first_after_restart_dt is not None)
        else None
    )
    verified_per_100_full = (
        round((len(verified_zero_fail_alphas) * 100.0) / completed_full_total, 2)
        if completed_full_total > 0
        else None
    )
    final_per_100_full = (
        round((len(final_passed_alphas) * 100.0) / completed_full_total, 2)
        if completed_full_total > 0
        else None
    )

    return {
        "track_id": TRACK_ID,
        "est_platform_date": day,
        "db_found": True,
        "total_task_rows": len(rows),
        "status_counts": status_counts,
        "by_queue": by_queue,
        "completed_full": completed_full_total,
        "completed_quick": completed_quick_total,
        "unique_completed_alphas": len(unique_completed_alphas),
        "verified_zero_fail_full_alphas": len(verified_zero_fail_alphas),
        "unverified_full_alphas": len(unverified_full_alphas),
        "verified_final_sc_pc_pass_alphas": len(final_passed_alphas),
        "platform_os_confirmed": "READ_PLATFORM_API_REQUIRED",
        "latest_simulations_ratelimit": latest_rl or "UNOBSERVED_TODAY",
        "progress_metrics": {
            "last_completed_utc": last_completed_dt.isoformat() if last_completed_dt else None,
            "oldest_pending_age_sec": oldest_pending_age_sec,
            "first_completion_after_restart_sec": first_completion_after_restart_sec,
        },
        "unit_yield": {
            "verified_zero_fail_per_100_full": verified_per_100_full,
            "final_pass_per_100_full": final_per_100_full,
        },
    }


# ---------------------------------------------------------------------------
# P1: Target-Aware PPA-First Attribution
# ---------------------------------------------------------------------------
def _collect_ast_ops_and_fields(expression: str) -> tuple[list[str], set[str], set[str]]:
    """Return (non_exempt_op_calls, unique_non_exempt_ops, unique_non_exempt_fields)."""
    ast_root = _Parser(tokenize(expression)).parse()
    op_calls: list[str] = []
    unique_ops: set[str] = set()
    unique_fields: set[str] = set()

    def _walk(node: Any) -> None:
        if isinstance(node, CallNode):
            nm = node.name.lower()
            if nm not in PPA_EXEMPT_OPERATORS:
                op_calls.append(nm)
                unique_ops.add(nm)
            for arg in node.args:
                _walk(arg)
            for kw in node.kwargs.values():
                _walk(kw)
        elif isinstance(node, IdentNode):
            nm = node.name.lower()
            if nm not in PPA_EXEMPT_GROUP_FIELDS and nm not in ("true", "false"):
                unique_fields.add(node.name)
        elif hasattr(node, "left") and hasattr(node, "right"):
            _walk(node.left)
            _walk(node.right)
        elif hasattr(node, "operand"):
            _walk(node.operand)

    _walk(ast_root)
    return op_calls, unique_ops, unique_fields


def attribute_ppa_first_routing(
    expression: str,
    checks: Optional[list[dict[str, Any]]] = None,
    *,
    target_track: str = "RA",
    http_status: Optional[int] = None,
    ui_error_hint: Optional[str] = None,
) -> dict[str, Any]:
    """Attribute PPA-first platform check routing without confusing PPA fallback with RA PC failure."""
    op_calls, unique_ops, unique_fields = _collect_ast_ops_and_fields(expression)
    ppa_eligible_structure = (len(unique_ops) <= 8) and (len(unique_fields) <= 3)

    raw_checks = checks or []
    check_state, state_names = classify_checks_state(json.dumps(raw_checks) if raw_checks else None)
    failed_names = [
        str(c.get("name") or "UNKNOWN")
        for c in raw_checks
        if isinstance(c, dict) and str(c.get("result") or "").upper() == "FAIL"
    ]
    has_ppa_check = any(
        isinstance(c, dict) and "POWER_POOL" in str(c.get("name") or "").upper() for c in raw_checks
    )
    has_ppac_fail = any(
        isinstance(c, dict)
        and str(c.get("name") or "").upper() == "POWER_POOL_CORRELATION"
        and str(c.get("result") or "").upper() == "FAIL"
        for c in raw_checks
    )
    has_pc_fail = any(
        isinstance(c, dict)
        and str(c.get("name") or "").upper() == "PROD_CORRELATION"
        and str(c.get("result") or "").upper() == "FAIL"
        for c in raw_checks
    )

    attribution = "NORMAL_RA_ROUTING"
    advice = "按常规 RA 完整门槛与真实数值 PC 判定。"

    if http_status == 403:
        attribution = "PLATFORM_HTTP_403_BLOCKED"
        advice = "保留原始 HTTP 403 来源（可能涉及当期 Theme/PPA/描述或账户配额限制），切勿误归因为表达式 PC 失败。"
    elif check_state == "UNVERIFIED":
        attribution = "UNVERIFIED_OR_PENDING_CHECKS"
        advice = "原始 checks 为空或含 PENDING/ERROR，保持待判，不归因为通过或失败。"
    elif ppa_eligible_structure and (has_ppac_fail or (ui_error_hint and "prod correlation" in ui_error_hint.lower() and not has_pc_fail)):
        attribution = "PPA_FIRST_FALLBACK_TRAP"
        advice = (
            "表达式满足 PPA 结构（唯一算子<=8 且非豁免字段<=3），系统先跑 PPA 检查；"
            "若 PPAC>=0.50 回退 RA 又未过，UI 常仅显示 Prod Correlation FAIL 假象，必须对照原始 checks 逐项核实。"
        )
    elif ppa_eligible_structure and target_track.upper() == "RA":
        attribution = "PPA_ELIGIBLE_RA_TARGET"
        advice = "表达式结构触发平台 PPA-First 路由；RA 线只要完整 RA 硬检与 SC/PC 全过仍可正常提交（自动 Hybrid），但若需规避 PPA 路由可核对算子/字段数。"
    elif target_track.upper() == "PPA" and not ppa_eligible_structure:
        attribution = "PPA_STRUCTURE_EXCEEDED"
        advice = f"目标为 PPA，但结构超限（unique_ops={len(unique_ops)}/8, unique_fields={len(unique_fields)}/3）。"

    return {
        "target_track": target_track.upper(),
        "ppa_eligible_structure": ppa_eligible_structure,
        "unique_non_exempt_ops": len(unique_ops),
        "total_non_exempt_op_calls": len(op_calls),
        "unique_non_exempt_fields": len(unique_fields),
        "non_exempt_ops_list": sorted(unique_ops),
        "non_exempt_fields_list": sorted(unique_fields),
        "raw_check_state": check_state,
        "raw_failed_checks": failed_names,
        "raw_unverified_checks": state_names if check_state == "UNVERIFIED" else [],
        "has_power_pool_check": has_ppa_check,
        "http_status": http_status,
        "ui_error_hint": ui_error_hint,
        "attribution": attribution,
        "advice": advice,
    }


# ---------------------------------------------------------------------------
# P1: Failure Feedback Packet & Pivot Budget State Machine
# ---------------------------------------------------------------------------
def build_failure_feedback_packet(
    *,
    direction_id: str,
    parent_alpha_id: str,
    region: str,
    universe: str,
    dataset_id: str,
    primary_failure: str,
    numeric_evidence: Mapping[str, Any],
    tried_variables: list[str],
    next_falsifiable_hypothesis: str,
    consecutive_same_failure_batches: int,
    pivot_budget_batches: int = 2,
    blocked_sibling_family: Optional[str] = None,
    evidence_source: str = "BRAIN_API_READONLY",
    pc_state: str = "UNKNOWN",
    neutralization: str = "",
    operators: Optional[list[str]] = None,
    reuser: Optional[ExperienceReuser] = None,
) -> dict[str, Any]:
    """Construct an AlphaForge P1 Failure Feedback Packet + Pivot Budget verdict.

    Key rule from `doc/ALPHAFORGE_WORKFLOW_REVIEW_20261128.md`:
    - Platform faults / PENDING / RESULTS_UNOBSERVED are EXCLUDED from strategy failure pivot budget.
    - When `consecutive_same_failure_batches >= pivot_budget_batches` on a strategy failure,
      quarantine the sibling family and pivot to an orthogonal dataset/direction.
    - Automatically injects matched historical experience (`EFF` / `INEFF` / `IMP` / crowding priors).
    """
    pf_u = (primary_failure or "UNKNOWN").strip().upper()
    is_platform_or_pending = pf_u in NON_STRATEGY_FAILURE_CODES

    if is_platform_or_pending:
        pivot_decision = "EXCLUDE_FROM_FAILURE_BUDGET_HOLD"
        effective_failures = 0
        next_action = "待判或平台故障不计入策略失败次数；按只对账一次规则处理，勿盲重发。"
    elif int(consecutive_same_failure_batches) >= int(pivot_budget_batches):
        pivot_decision = "QUARANTINE_FAMILY_AND_PIVOT"
        effective_failures = int(consecutive_same_failure_batches)
        next_action = (
            f"连续 {effective_failures} 批卡在同一瓶颈 `{pf_u}`（已达换向预算 {pivot_budget_batches} 批），"
            "立即封存同族候选，写入 OPTIMIZATION_LEDGER.json [无效]，切换至正交数据集或下一金字塔空位！"
        )
    else:
        pivot_decision = "CONTINUE_SINGLE_AXIS_FIX"
        effective_failures = int(consecutive_same_failure_batches)
        remaining = int(pivot_budget_batches) - effective_failures
        next_action = (
            f"剩余换向预算 {remaining} 批：将本反馈包传回原研究方向/DSH 子代理，"
            "屏蔽同簇重复变体，仅允许提出 1 条可证伪的单轴修复假设。"
        )

    exp_reuser = reuser or ExperienceReuser()
    exp_packet = exp_reuser.retrieve(
        region=region,
        universe=universe,
        dataset_id=dataset_id,
        neutralization=neutralization,
        failure_code=pf_u,
        operators=operators or [],
        top_eff=3,
        top_ineff=3,
        top_imp=2,
        top_audited=2,
    )
    crowding = exp_reuser.score_direction_crowding_prior(
        region=region,
        dataset_id=dataset_id,
        neutralization=neutralization,
    )

    return {
        "schema_version": "alphaforge_v4_failure_feedback_v1",
        "track_id": TRACK_ID,
        "direction_id": direction_id,
        "parent_alpha_id": parent_alpha_id,
        "coordinates": {
            "region": region.upper(),
            "universe": universe.upper(),
            "dataset_id": dataset_id,
            "neutralization": neutralization.upper() if neutralization else "UNSPECIFIED",
        },
        "evidence_source": evidence_source,
        "primary_failure": pf_u,
        "pc_state": pc_state.upper(),
        "numeric_evidence": dict(numeric_evidence),
        "tried_variables": list(tried_variables),
        "blocked_sibling_family": blocked_sibling_family or f"{region.upper()}/{dataset_id}/{parent_alpha_id}",
        "next_falsifiable_hypothesis": next_falsifiable_hypothesis,
        "pivot_budget": {
            "consecutive_same_failure_batches": effective_failures,
            "budget_limit": int(pivot_budget_batches),
            "excluded_as_pending_or_platform_fault": is_platform_or_pending,
            "decision": pivot_decision,
            "next_action": next_action,
        },
        "crowding_prior": crowding,
        "reused_experience_card": exp_packet.render_compact_markdown(max_bytes=2600),
    }


# ---------------------------------------------------------------------------
# P2: 3-Primary + 1-Backup ("三主一备") Pyramid Manual-Review Roster
# ---------------------------------------------------------------------------
def select_three_plus_one_roster(
    candidates: list[dict[str, Any]],
    *,
    pairwise_corr_fn: Optional[Callable[[dict[str, Any], dict[str, Any]], Optional[float]]] = None,
    max_pair_corr: float = 0.68,
    primary_count: int = 3,
    backup_count: int = 1,
) -> dict[str, Any]:
    """Curate a 3-Primary + 1-Backup Pyramid manual-review roster (NEVER an auto-submit quota).

    Strictly filters to candidates with verified 0-FAIL, numeric SC < 0.65, numeric PC < 0.70,
    sorts by Pyramid priority (empty/high-multiplier) -> Margin DESC -> Sharpe DESC -> Fitness DESC,
    enforces intra-pool pairwise orthogonality (< 0.68), and reserves the backup slot for a distinct family.
    """
    eligible: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for c in candidates:
        aid = str(c.get("alpha_id") or "unknown")
        reasons: list[str] = []
        if not bool(c.get("zero_fail_verified", False)):
            reasons.append("NOT_VERIFIED_ZERO_FAIL")
        sc = c.get("sc")
        pc = c.get("pc")
        if not isinstance(sc, (int, float)) or float(sc) >= 0.65:
            reasons.append(f"SC_INVALID_OR_GE_065({sc})")
        if not isinstance(pc, (int, float)) or float(pc) >= 0.70:
            reasons.append(f"PC_INVALID_OR_GE_070({pc})")
        if reasons:
            rejected.append({"alpha_id": aid, "reasons": reasons})
        else:
            eligible.append(dict(c))

    def _sort_key(item: dict[str, Any]) -> tuple[float, float, float, float, float]:
        # Higher pyramid_priority_score (e.g. empty slot=2, multiplier=1.5) -> higher Margin -> Sharpe -> Fitness
        pyr_empty = 1.0 if item.get("pyramid_slot_empty") else 0.0
        pyr_mult = float(item.get("pyramid_multiplier") or 1.0)
        margin_bp = float(item.get("margin_bp") or 0.0)
        sharpe = float(item.get("sharpe") or 0.0)
        fitness = float(item.get("fitness") or 0.0)
        return (pyr_empty, pyr_mult, margin_bp, sharpe, fitness)

    eligible.sort(key=_sort_key, reverse=True)

    def _is_orthogonal(cand: dict[str, Any], pool: list[dict[str, Any]]) -> tuple[bool, Optional[str]]:
        c_fam = str(cand.get("family_id") or cand.get("dataset_id") or "").lower()
        for existing in pool:
            if pairwise_corr_fn is not None:
                corr = pairwise_corr_fn(cand, existing)
                if corr is not None and abs(float(corr)) >= max_pair_corr:
                    return False, f"PAIRWISE_CORR_GE_{max_pair_corr}({existing.get('alpha_id')}:{corr:.3f})"
            elif c_fam and c_fam == str(existing.get("family_id") or existing.get("dataset_id") or "").lower():
                # Without PnL pairwise function, avoid stacking identical family in same roster slot
                return False, f"SAME_FAMILY_NO_PNL_PROOF({existing.get('alpha_id')}:{c_fam})"
        return True, None

    primaries: list[dict[str, Any]] = []
    backups: list[dict[str, Any]] = []
    used_families: set[str] = set()
    used_ids: set[str] = set()

    for cand in eligible:
        if len(primaries) >= primary_count:
            break
        ok, reason = _is_orthogonal(cand, primaries)
        if ok:
            primaries.append(cand)
            used_ids.add(str(cand.get("alpha_id")))
            fam = str(cand.get("family_id") or cand.get("dataset_id") or "").lower()
            if fam:
                used_families.add(fam)
        else:
            rejected.append({"alpha_id": str(cand.get("alpha_id")), "reasons": [reason or "ORTHOGONALITY_FAIL"]})

    for cand in eligible:
        if len(backups) >= backup_count:
            break
        aid = str(cand.get("alpha_id"))
        if aid in used_ids:
            continue
        fam = str(cand.get("family_id") or cand.get("dataset_id") or "").lower()
        if fam and fam in used_families:
            continue
        ok, reason = _is_orthogonal(cand, primaries + backups)
        if ok:
            backups.append(cand)
            used_ids.add(aid)
            if fam:
                used_families.add(fam)
        else:
            rejected.append({"alpha_id": aid, "reasons": [reason or "BACKUP_ORTHOGONALITY_FAIL"]})

    return {
        "roster_policy": "MANUAL_REVIEW_ONLY_NOT_SUBMIT_QUOTA",
        "auto_submit_allowed": False,
        "target_primary": primary_count,
        "target_backup": backup_count,
        "actual_primary": len(primaries),
        "actual_backup": len(backups),
        "primary_shortfall": max(0, primary_count - len(primaries)),
        "backup_shortfall": max(0, backup_count - len(backups)),
        "primaries": primaries,
        "backups": backups,
        "rejected": rejected,
    }


# ---------------------------------------------------------------------------
# Antigravity CLI (`agy`) Main Controller & DSH (`dsh-crew`) Subagent Builders
# ---------------------------------------------------------------------------
def locate_agy_executable() -> Optional[str]:
    """Locate Antigravity CLI (`agy` / `agy.exe`) across PATH and standard user install paths."""
    found = shutil.which("agy") or shutil.which("agy.exe")
    if found:
        return found
    candidates = [
        Path.home() / ".gemini" / "bin" / "agy.exe",
        Path.home() / ".gemini" / "bin" / "agy",
        Path.home() / ".local" / "bin" / "agy",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None


def build_startup_handoff() -> dict[str, Any]:
    """Project the current direction and latest cases without loading full logs into the prompt."""
    config = json.loads((REPO_ROOT / "goal/run_config.json").read_text(encoding="utf-8-sig"))
    state = json.loads((REPO_ROOT / "docs/agents/CORE_STATE.json").read_text(encoding="utf-8-sig"))
    ledger = json.loads((REPO_ROOT / "docs/agents/OPTIMIZATION_LEDGER.json").read_text(encoding="utf-8-sig"))
    inspection = state["codex_latest_inspection"]
    return {
        "default_track_id": config["default_track_id"],
        "as_of": inspection["observed_at"],
        "planned_followup": inspection["followup_window"]["batch_scope"],
        "closed_wave": [
            {key: batch[key] for key in ("campaign", "completed", "hard_fail", "met_condition")}
            for batch in inspection["closed_wave"]
        ],
        "latest_cases": {
            kind: [{key: case[key] for key in ("case_id", "verdict")} for case in ledger[kind][-2:]]
            for kind in ("effective_cases", "ineffective_cases")
        },
    }


def build_dsh_subagent_brief(
    *,
    task_goal: str,
    region: str,
    universe: str,
    dataset_id: str,
    readonly_evidence: list[str],
    acceptance_criteria: list[str],
    failure_feedback: Optional[dict[str, Any]] = None,
    failure_code: str = "",
    neutralization: str = "",
    operators: Optional[list[str]] = None,
    allowed_new_file: Optional[str] = None,
    reuser: Optional[ExperienceReuser] = None,
) -> str:
    """Compile a self-contained DSH flash subagent brief with injected historical experience.

    Matches `docs/agents/SUBAGENT_BRIEF_TEMPLATE.md` + `dsh-playbook` + AlphaForge P1 feedback loop.
    """
    exp_reuser = reuser or ExperienceReuser()
    if failure_feedback and failure_feedback.get("reused_experience_card"):
        exp_card = str(failure_feedback["reused_experience_card"])
    else:
        packet = exp_reuser.retrieve(
            region=region,
            universe=universe,
            dataset_id=dataset_id,
            neutralization=neutralization,
            failure_code=failure_code,
            operators=operators or [],
            top_eff=3,
            top_ineff=3,
            top_imp=2,
            top_audited=2,
        )
        exp_card = packet.render_compact_markdown(max_bytes=2400)

    ev_block = "\n".join(f"- {p}" for p in readonly_evidence) if readonly_evidence else "- 见任务指定路径"
    acc_block = "\n".join(f"- {a}" for a in acceptance_criteria) if acceptance_criteria else "- 给出可复核证据位置与检查命令输出"
    file_rule = (
        f"仅允许新建此指定文件：`{allowed_new_file}`；严禁覆盖、追加、重命名或删除任何现有文件。"
        if allowed_new_file
        else "默认只读，不创建、修改、覆盖或删除任何文件；所有结论直接文本回传主 Agent。"
    )

    fb_section = ""
    if failure_feedback:
        pb = failure_feedback.get("pivot_budget") or {}
        fb_section = (
            "\n【上轮失败反馈与换向约束】\n"
            f"- 方向/母版：{failure_feedback.get('direction_id')} / `{failure_feedback.get('parent_alpha_id')}`\n"
            f"- 主失败项：`{failure_feedback.get('primary_failure')}`（PC状态=`{failure_feedback.get('pc_state')}`）\n"
            f"- 数值证据：{json.dumps(failure_feedback.get('numeric_evidence') or {}, ensure_ascii=False)}\n"
            f"- 已试变量：{', '.join(failure_feedback.get('tried_variables') or []) or '无'}\n"
            f"- 屏蔽同簇家族：`{failure_feedback.get('blocked_sibling_family')}`（严禁再生成同簇重复变体）\n"
            f"- 换向预算判定：`{pb.get('decision')}` — {pb.get('next_action')}\n"
            f"- 本轮唯一可证伪假设：{failure_feedback.get('next_falsifiable_hypothesis')}\n"
        )

    return (
        f"【路线】{TRACK_NAME_ZH} ({TRACK_ID}) · DSH 子代理任务包\n"
        f"【任务】{task_goal}\n"
        f"【工作区】{REPO_ROOT}\n"
        f"【研究坐标】Region={region.upper()} | Universe={universe.upper()} | Dataset={dataset_id} | Delay=1 (D1-Only)\n"
        f"【只读证据】\n{ev_block}\n"
        f"【验收】\n{acc_block}\n"
        f"{fb_section}\n"
        f"{exp_card}\n\n"
        "【回报】直接返回结论、证据位置、验收输出、单轴可证伪假设和未验证项，最多 30 行。"
        "结论标 [V] 已验证、[R] 有报告未复核、[C] 条件成立或 [U] 未验证。\n"
        f"【文件】{file_rule}\n"
        "【边界】严禁递归调用 DSH/子代理；严禁 commit/push/发回测/写平台/调用 submit/读 Password/config.yaml；"
        "严禁触碰 reference/、legacy_core/Core/runtime_data/ 与 COMPLETED_FULL；"
        "严格遵守 D1-Only、永久禁用 +/*/add/multiply/trade_when、双支仅用 min(rank(A), rank(B))。"
    )


def build_agy_main_prompt(
    *,
    region: str = "USA",
    universe: str = "TOP3000",
    dataset_id: str = "",
    goal: str = "执行 Route ④ 锻造闭环巡检、失败归因与单轴推进",
    failure_code: str = "",
    reuser: Optional[ExperienceReuser] = None,
) -> str:
    """Build compact (< 6 KB) Antigravity CLI (`agy`) main-controller boot prompt for Route ④."""
    exp_reuser = reuser or ExperienceReuser()
    packet = exp_reuser.retrieve(
        region=region,
        universe=universe,
        dataset_id=dataset_id,
        failure_code=failure_code,
        top_eff=3,
        top_ineff=3,
        top_imp=2,
        top_audited=2,
    )
    exp_card = packet.render_compact_markdown(max_bytes=2400)

    return (
        f"你是 WorldQuant BRAIN 路线 ④「{TRACK_NAME_ZH}」(`{TRACK_ID}`) 的 Antigravity CLI (`agy`) 主控 Agent。\n"
        f"本轮目标：{goal}（坐标：{region.upper()}/{universe.upper()}/{dataset_id or '按当前高优空位'}）。\n\n"
        "### 一、精简启动\n"
        "1. 应用 `AGENTS.md`；运行 `python -m wq_research_v2 forge handoff`，仅按 case_id 读取需要验真的原始条目。"
        "不展开完整状态、经验台账、运行日志或旧对话；历史经验卡随本提示附上。\n"
        "2. 严格遵守所有红线：D1-Only、禁 `+/*/add/multiply/trade_when`、零自动 `/submit`、"
        "全过线自动 `PATCH` 并提示（Margin 优先）、`GLB<=3`/其他区`<=4`、只对账 1 次、不覆盖 `COMPLETED_FULL`。\n\n"
        "### 二、执行入口硬门禁（P0）与 DSH 子代理编排\n"
        "1. **先做 P0 预检与平台日漏斗对账**：运行 `python -m wq_research_v2 forge preflight` 与 "
        "`python -m wq_research_v2 forge funnel`，确认 `NORMAL < 4500` 前绝不混发 `UNUSED_ALPHA0`，"
        "已终结/未观测指纹绝不重发。\n"
        "2. **DSH 子代理派单（必须先 probe）**：通过 `dsh-crew` MCP 先调 `dsh_worker_config` 确认 "
        "`mode=hub, enabled=true, escalate_on_failure=false, flash=dsh-opencode-go/deepseek-v4.1-flash`，"
        "再调 `dsh_worker_probe(tier=flash, provider=dsh-opencode-go, model=deepseek-v4.1-flash)`；"
        "探测通过后用 `python -m wq_research_v2 forge dsh-brief` 生成带历史经验与失败反馈的自包含简报，"
        "调用 `dsh_run_worker` / `dsh_spawn_worker`（最多同时 2 组只读研究子代理，每子代理最多 4 轮，保留会话）。\n"
        "3. **失败传回原方向 + 2 批换向预算（P1）**：若同一方向连续 2 批卡在同一策略失败项（排除 PENDING/未观测/平台故障），"
        "立即封存同族候选并换向；遇结构符合 `ops<=8 && fields<=3` 时显式核查 PPA-First 归因。\n"
        "4. **主 Agent 独立验真与收口**：主 Agent 独立复核 DSH 证据、执行 Stage-4 本地 SC/正交/远程 PC 与三主一备人工复核清单（P2），"
        "写回 `[有效]/[无效]` 至 `OPTIMIZATION_LEDGER.json` 并追加战报至 `docs/alphaforge_v4/alphaforge_v4_log.md`（前缀 `[TRACK:alphaforge_agy_dsh_v4]`）。\n\n"
        f"{exp_card}\n"
    )


def build_agy_cli_command(
    prompt: str,
    *,
    agy_bin: Optional[str] = None,
    interactive: bool = False,
    mode: str = "accept-edits",
    effort: str = "high",
    model: Optional[str] = None,
    output_format: str = "text",
    print_timeout: Optional[str] = None,
    log_file: Optional[Path | str] = None,
) -> list[str]:
    """Build verified Antigravity CLI (`agy` v1.5+) invocation argv without guessing flags."""
    exe = agy_bin or locate_agy_executable() or "agy"
    cmd = [exe]
    if mode:
        cmd.extend(["--mode", mode])
    if effort:
        cmd.extend(["--effort", effort])
    if model:
        cmd.extend(["--model", model])
    if log_file:
        cmd.extend(["--log-file", str(log_file)])
    if interactive:
        cmd.extend(["--prompt-interactive", prompt])
    else:
        if output_format:
            cmd.extend(["--output-format", output_format])
        if print_timeout:
            cmd.extend(["--print-timeout", print_timeout])
        cmd.extend(["--print", prompt])
    return cmd
