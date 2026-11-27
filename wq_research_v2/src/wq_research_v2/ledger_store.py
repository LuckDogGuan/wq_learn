"""SQLite WAL Checkpoint ledger for crash-resilient multi-sim, quota, SC/PC, blacklist, and EST daily reporting."""
from __future__ import annotations

import datetime
import json
import math
import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional

from wq_research_v2.config_loader import LEDGER_DB_PATH
from wq_research_v2.quota_tracker import current_est_platform_date

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 15000;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS experiment_batches (
    batch_id            TEXT PRIMARY KEY,
    hypothesis_id       TEXT,
    queue_type          TEXT NOT NULL CHECK (queue_type IN ('NORMAL', 'UNUSED_ALPHA0')),
    source_side         TEXT NOT NULL CHECK (source_side IN ('ADMIN_ORIGINAL', 'TOP100_2026Q4', 'MIXED_4_4')),
    region              TEXT NOT NULL,
    universe            TEXT NOT NULL,
    delay               INTEGER NOT NULL CHECK (delay = 1),
    simulation_mode     TEXT NOT NULL CHECK (simulation_mode IN ('QUICK', 'FULL')),
    slots_required      INTEGER NOT NULL CHECK (slots_required IN (1, 2)),
    progress_url        TEXT,
    status              TEXT NOT NULL,
    created_at_utc      TEXT NOT NULL,
    updated_at_utc      TEXT NOT NULL,
    est_platform_date   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sim_tasks (
    task_id                  TEXT PRIMARY KEY,
    batch_id                 TEXT NOT NULL REFERENCES experiment_batches(batch_id),
    payload_fingerprint      TEXT NOT NULL,
    canonical_dedup_key      TEXT NOT NULL,
    parent_baseline_alpha_id TEXT,
    parent_quick_task_id     TEXT,
    parent_family_id         TEXT,
    single_changed_axis      TEXT,
    atlas_layer              TEXT,
    template_id              TEXT,
    source_side              TEXT NOT NULL CHECK (source_side IN ('ADMIN_ORIGINAL', 'TOP100_2026Q4')),
    author_id                TEXT,
    canonical_post_id        TEXT,
    queue_type               TEXT NOT NULL CHECK (queue_type IN ('NORMAL', 'UNUSED_ALPHA0')),
    region                   TEXT NOT NULL,
    universe                 TEXT NOT NULL,
    delay                    INTEGER NOT NULL CHECK (delay = 1),
    dataset_id               TEXT,
    primary_field_id         TEXT,
    simulation_mode          TEXT NOT NULL CHECK (simulation_mode IN ('QUICK', 'FULL')),
    expression               TEXT NOT NULL,
    settings_json            TEXT NOT NULL,
    status                   TEXT NOT NULL CHECK (status IN (
        'QUEUED','SUBMITTED','COMPLETED_QUICK','COMPLETED_FULL',
        'PENDING_RECONCILE','RESULTS_UNOBSERVED','SYNTAX_ERROR',
        'RATE_LIMITED_429','FAILED_TECH','DEDUP_SKIPPED','BLACKLIST_SKIPPED'
    )),
    alpha_id                 TEXT,
    sharpe                   REAL,
    fitness                  REAL,
    turnover                 REAL,
    margin                   REAL,
    returns                  REAL,
    sharpe_2y                REAL,
    rn_sharpe                REAL,
    rn_fitness               REAL,
    active_years             INTEGER,
    max_flat_streak_days     INTEGER,
    checks_json              TEXT,
    gate_status              TEXT,
    reconcile_attempts       INTEGER NOT NULL DEFAULT 0 CHECK (reconcile_attempts <= 1),
    error_reason             TEXT,
    submitted_at_utc         TEXT,
    completed_at_utc         TEXT,
    est_platform_date        TEXT
);
CREATE INDEX IF NOT EXISTS idx_sim_fp ON sim_tasks(payload_fingerprint, status);
CREATE INDEX IF NOT EXISTS idx_sim_est_mode ON sim_tasks(est_platform_date, simulation_mode, status);
CREATE INDEX IF NOT EXISTS idx_sim_scope ON sim_tasks(region, universe, delay, dataset_id, primary_field_id, template_id);
CREATE INDEX IF NOT EXISTS idx_sim_alpha_id ON sim_tasks(alpha_id);

CREATE TABLE IF NOT EXISTS ratelimit_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    observed_at_utc     TEXT NOT NULL,
    est_platform_date   TEXT NOT NULL,
    endpoint            TEXT NOT NULL,
    http_status         INTEGER,
    limit_val           INTEGER,
    remaining_val       INTEGER,
    reset_val           REAL,
    retry_after_val     REAL,
    wait_applied_sec    REAL DEFAULT 0.0,
    raw_headers_json    TEXT
);
CREATE INDEX IF NOT EXISTS idx_rl_est ON ratelimit_events(est_platform_date, http_status);

CREATE TABLE IF NOT EXISTS field_profiles (
    region                   TEXT NOT NULL,
    universe                 TEXT NOT NULL,
    delay                    INTEGER NOT NULL CHECK (delay = 1),
    dataset_id               TEXT NOT NULL,
    field_id                 TEXT NOT NULL,
    field_type               TEXT NOT NULL,
    wds_dataset_grade        TEXT,
    wds_field_tier           TEXT,
    wds_coverage_recent_mean REAL,
    wds_coverage_recent_min  REAL,
    wds_history_slots        INTEGER,
    wds_risk_flags_json      TEXT,
    live_alpha_count         INTEGER,
    live_user_count          INTEGER,
    live_coverage            REAL,
    live_date_coverage       REAL,
    is_alpha0_free           INTEGER NOT NULL DEFAULT 0,
    freeze_expiry            TEXT,
    is_fake_single_vector    INTEGER NOT NULL DEFAULT 0,
    strictly_positive        INTEGER NOT NULL DEFAULT 0,
    pyramid_category         TEXT,
    pyramid_multiplier       REAL,
    verified_at_utc          TEXT NOT NULL,
    PRIMARY KEY (region, universe, delay, dataset_id, field_id)
);

CREATE TABLE IF NOT EXISTS sc_evaluations (
    eval_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    alpha_id            TEXT NOT NULL,
    region              TEXT NOT NULL,
    pool_mode           TEXT NOT NULL CHECK (pool_mode IN ('REGULAR_ALL', 'REGULAR_NO_PPA', 'PPAC_ONLY')),
    sc_state            TEXT NOT NULL CHECK (sc_state IN (
        'SC_READY_PASS','SC_READY_HIGH','NO_PEERS_IN_REGION','CACHE_STALE','PENDING_NO_OVERLAP'
    )),
    max_corr            REAL,
    max_peer_id         TEXT,
    max_peer_sharpe     REAL,
    peer_count          INTEGER NOT NULL,
    overlap_days        INTEGER,
    cache_os_count      INTEGER NOT NULL,
    cache_synced_at_utc TEXT NOT NULL,
    evaluated_at_utc    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sc_alpha ON sc_evaluations(alpha_id, pool_mode);

CREATE TABLE IF NOT EXISTS pc_poll_queue (
    alpha_id           TEXT PRIMARY KEY,
    region             TEXT NOT NULL,
    status             TEXT NOT NULL CHECK (status IN (
        'PENDING_PC_COMPUTING','PC_READY_PASS','PC_READY_HIGH','PC_RATE_LIMITED_429','PC_ERROR'
    )),
    pc_max             REAL,
    pc_min             REAL,
    rescue_hint        TEXT,
    check_status       TEXT,
    check_payload_json TEXT,
    attempts           INTEGER NOT NULL DEFAULT 0,
    next_poll_at_utc   TEXT,
    last_http_status   INTEGER,
    last_error         TEXT,
    updated_at_utc     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS blacklist_records (
    record_id                 TEXT PRIMARY KEY,
    level                     TEXT NOT NULL CHECK (level IN ('FAST_DEMOTED','SCOPE_BLACKLISTED','NEEDS_REVIEW')),
    status                    TEXT NOT NULL CHECK (status IN ('ACTIVE','RESTORED')),
    target_type               TEXT NOT NULL CHECK (target_type IN ('FIELD','METHOD','PARAM_COMBO')),
    region                    TEXT NOT NULL,
    universe                  TEXT NOT NULL,
    delay                     INTEGER NOT NULL CHECK (delay = 1),
    dataset_id                TEXT,
    field_id                  TEXT,
    method_id                 TEXT,
    param_axis                TEXT,
    valid_sample_count        INTEGER NOT NULL,
    positive_control_alpha_id TEXT NOT NULL,
    evidence_alpha_ids_json   TEXT NOT NULL,
    failed_check_dist_json    TEXT NOT NULL,
    why_unusable              TEXT NOT NULL,
    dissent_and_rescue_json   TEXT NOT NULL,
    restored_reason           TEXT,
    created_at_utc            TEXT NOT NULL,
    updated_at_utc            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_volume_snapshots (
    est_platform_date          TEXT PRIMARY KEY,
    submitted_count            INTEGER NOT NULL DEFAULT 0,
    quick_screened_count       INTEGER NOT NULL DEFAULT 0,
    full_valid_completed_count INTEGER NOT NULL DEFAULT 0,
    dedup_skipped_count        INTEGER NOT NULL DEFAULT 0,
    tech_fail_count            INTEGER NOT NULL DEFAULT 0,
    unobserved_count           INTEGER NOT NULL DEFAULT 0,
    normal_completed           INTEGER NOT NULL DEFAULT 0,
    alpha0_completed           INTEGER NOT NULL DEFAULT 0,
    admin_completed            INTEGER NOT NULL DEFAULT 0,
    top100_completed           INTEGER NOT NULL DEFAULT 0,
    gate1_count                INTEGER NOT NULL DEFAULT 0,
    tier1_pass_count           INTEGER NOT NULL DEFAULT 0,
    tier2_manual_review_count  INTEGER NOT NULL DEFAULT 0,
    min_ratelimit_remaining    INTEGER,
    observed_ratelimit_limit   INTEGER,
    updated_at_utc             TEXT NOT NULL
);
"""


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _is_finite(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool) and math.isfinite(val)


class LedgerStore:
    """Thread-safe SQLite WAL persistence for wq_research_v2."""

    def __init__(self, db_path: Path = LEDGER_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(SCHEMA_SQL)
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def create_batch(
        self,
        batch_id: str,
        *,
        hypothesis_id: Optional[str],
        queue_type: str,
        source_side: str,
        region: str,
        universe: str,
        delay: int,
        simulation_mode: str,
        slots_required: int,
        status: str = "QUEUED",
        est_platform_date: Optional[str] = None,
    ) -> None:
        if delay != 1:
            raise ValueError(f"D1-Only violation: delay={delay}")
        now = _utc_now()
        est_day = est_platform_date or current_est_platform_date()
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO experiment_batches (
                    batch_id, hypothesis_id, queue_type, source_side, region, universe,
                    delay, simulation_mode, slots_required, status, created_at_utc, updated_at_utc, est_platform_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id, hypothesis_id, queue_type, source_side, region.upper(), universe.upper(),
                    delay, simulation_mode.upper(), slots_required, status, now, now, est_day,
                ),
            )
            self._conn.commit()

    def update_batch_progress(self, batch_id: str, status: str, progress_url: Optional[str] = None) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE experiment_batches SET status=?, progress_url=COALESCE(?, progress_url), updated_at_utc=? WHERE batch_id=?",
                (status, progress_url, _utc_now(), batch_id),
            )
            self._conn.commit()

    def has_completed_fingerprint(self, payload_fingerprint: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM sim_tasks WHERE payload_fingerprint=? AND status IN ('COMPLETED_QUICK','COMPLETED_FULL','SUBMITTED','PENDING_RECONCILE','RESULTS_UNOBSERVED') LIMIT 1",
                (payload_fingerprint,),
            ).fetchone()
            return row is not None

    def get_task_status(self, task_id: str) -> Optional[str]:
        with self._lock:
            row = self._conn.execute(
                "SELECT status FROM sim_tasks WHERE task_id=? LIMIT 1",
                (task_id,),
            ).fetchone()
            return str(row["status"]) if row is not None else None

    def upsert_sim_task(self, task: dict[str, Any]) -> None:
        if task.get("delay", 1) != 1:
            raise ValueError("D1-Only violation in sim_tasks")
        incoming_status = str(task.get("status") or "")
        task_id = str(task.get("task_id") or "")
        # Immutable guard: NEVER let QUEUED/DEDUP_SKIPPED/SYNTAX_ERROR/BLACKLIST_SKIPPED/SUBMITTED
        # overwrite an already completed or reconciled-unobserved simulation row on daemon restart / loop!
        if task_id and incoming_status not in ("COMPLETED_FULL", "COMPLETED_QUICK"):
            existing_status = self.get_task_status(task_id)
            if existing_status in ("COMPLETED_FULL", "COMPLETED_QUICK", "RESULTS_UNOBSERVED"):
                return
        cols = [
            "task_id", "batch_id", "payload_fingerprint", "canonical_dedup_key",
            "parent_baseline_alpha_id", "parent_quick_task_id", "parent_family_id",
            "single_changed_axis", "atlas_layer", "template_id", "source_side",
            "author_id", "canonical_post_id", "queue_type", "region", "universe",
            "delay", "dataset_id", "primary_field_id", "simulation_mode",
            "expression", "settings_json", "status", "alpha_id", "sharpe",
            "fitness", "turnover", "margin", "returns", "sharpe_2y",
            "rn_sharpe", "rn_fitness", "active_years", "max_flat_streak_days",
            "checks_json", "gate_status", "reconcile_attempts", "error_reason",
            "submitted_at_utc", "completed_at_utc", "est_platform_date",
        ]
        vals = [task.get(c) for c in cols]
        if vals[cols.index("reconcile_attempts")] is None:
            vals[cols.index("reconcile_attempts")] = 0
        placeholders = ",".join("?" for _ in cols)
        with self._lock:
            self._conn.execute(
                f"INSERT OR REPLACE INTO sim_tasks ({','.join(cols)}) VALUES ({placeholders})",
                vals,
            )
            self._conn.commit()

    def mark_task_completed(
        self,
        task_id: str,
        *,
        simulation_mode: str,
        alpha_id: str,
        sharpe: Optional[float],
        fitness: Optional[float],
        turnover: Optional[float],
        margin: Optional[float],
        returns: Optional[float] = None,
        sharpe_2y: Optional[float] = None,
        rn_sharpe: Optional[float] = None,
        rn_fitness: Optional[float] = None,
        active_years: Optional[int] = None,
        max_flat_streak_days: Optional[int] = None,
        checks_json: Optional[str] = None,
        gate_status: Optional[str] = None,
        completed_at_utc: Optional[str] = None,
        est_platform_date: Optional[str] = None,
    ) -> None:
        status = "COMPLETED_FULL" if simulation_mode.upper() == "FULL" else "COMPLETED_QUICK"
        comp_ts = completed_at_utc or _utc_now()
        est_day = est_platform_date or current_est_platform_date()
        with self._lock:
            self._conn.execute(
                """
                UPDATE sim_tasks
                SET status=?, alpha_id=?, sharpe=?, fitness=?, turnover=?, margin=?,
                    returns=?, sharpe_2y=?, rn_sharpe=?, rn_fitness=?,
                    active_years=?, max_flat_streak_days=?, checks_json=?, gate_status=?,
                    completed_at_utc=?, est_platform_date=?
                WHERE task_id=?
                """,
                (
                    status, alpha_id, sharpe, fitness, turnover, margin,
                    returns, sharpe_2y, rn_sharpe, rn_fitness,
                    active_years, max_flat_streak_days, checks_json, gate_status,
                    comp_ts, est_day, task_id,
                ),
            )
            self._conn.commit()

    def mark_task_pending_reconcile(self, task_id: str, reason: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE sim_tasks SET status='PENDING_RECONCILE', error_reason=? WHERE task_id=?",
                (reason, task_id),
            )
            self._conn.commit()

    def mark_reconcile_failed_unobserved(self, task_id: str, reason: str) -> None:
        """Enforce reconcile-once-never-resend: attempts <= 1, terminal RESULTS_UNOBSERVED."""
        with self._lock:
            self._conn.execute(
                "UPDATE sim_tasks SET status='RESULTS_UNOBSERVED', reconcile_attempts=1, error_reason=? WHERE task_id=?",
                (reason, task_id),
            )
            self._conn.commit()

    def get_resumable_tasks(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM sim_tasks WHERE status IN ('QUEUED', 'SUBMITTED', 'PENDING_RECONCILE') ORDER BY batch_id, task_id"
            ).fetchall()
            return [dict(r) for r in rows]

    def record_ratelimit_event(
        self,
        *,
        observed_at_utc: str,
        est_platform_date: str,
        endpoint: str,
        http_status: int,
        limit_val: Optional[int],
        remaining_val: Optional[int],
        reset_val: Optional[float],
        retry_after_val: Optional[float],
        wait_applied_sec: float,
        raw_headers_json: str,
    ) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO ratelimit_events (
                    observed_at_utc, est_platform_date, endpoint, http_status,
                    limit_val, remaining_val, reset_val, retry_after_val, wait_applied_sec, raw_headers_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observed_at_utc, est_platform_date, endpoint, http_status,
                    limit_val, remaining_val, reset_val, retry_after_val, wait_applied_sec, raw_headers_json,
                ),
            )
            self._conn.commit()

    def compute_daily_summary(self, est_platform_date: str) -> dict[str, Any]:
        """Compute strict EST platform-day metrics separating Quick Screened vs Full Valid Completed."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM sim_tasks WHERE est_platform_date=?",
                (est_platform_date,),
            ).fetchall()
            rl_row = self._conn.execute(
                "SELECT MIN(remaining_val) AS min_rem, MAX(limit_val) AS max_lim FROM ratelimit_events WHERE est_platform_date=?",
                (est_platform_date,),
            ).fetchone()

        full_valid_keys: set[str] = set()
        quick_keys: set[str] = set()
        submitted = dedup_skipped = tech_fail = unobserved = 0
        normal_comp = alpha0_comp = admin_comp = top100_comp = 0
        gate1 = tier1 = tier2 = 0

        for r in rows:
            st = r["status"]
            if st in ("SUBMITTED", "COMPLETED_QUICK", "COMPLETED_FULL", "PENDING_RECONCILE", "RESULTS_UNOBSERVED"):
                submitted += 1
            if st == "DEDUP_SKIPPED":
                dedup_skipped += 1
            elif st in ("SYNTAX_ERROR", "RATE_LIMITED_429", "FAILED_TECH"):
                tech_fail += 1
            elif st == "RESULTS_UNOBSERVED":
                unobserved += 1
            elif st == "COMPLETED_QUICK":
                if r["canonical_dedup_key"] not in quick_keys:
                    quick_keys.add(r["canonical_dedup_key"])
                    if r["queue_type"] == "UNUSED_ALPHA0":
                        alpha0_comp += 1
                    else:
                        normal_comp += 1
            elif st == "COMPLETED_FULL":
                has_all_four = (
                    bool(r["alpha_id"])
                    and _is_finite(r["sharpe"])
                    and _is_finite(r["fitness"])
                    and _is_finite(r["turnover"])
                    and _is_finite(r["margin"])
                )
                if has_all_four and r["canonical_dedup_key"] not in full_valid_keys:
                    full_valid_keys.add(r["canonical_dedup_key"])
                    if r["queue_type"] == "UNUSED_ALPHA0":
                        alpha0_comp += 1
                    else:
                        normal_comp += 1
                    if r["source_side"] == "ADMIN_ORIGINAL":
                        admin_comp += 1
                    else:
                        top100_comp += 1
                    gs = r["gate_status"] or ""
                    if gs in ("GATE1_POOL_SH08", "GATE2_IMPROVING", "GATE3_TIER1_PASS", "GATE4_CANDIDATE_FOR_MANUAL_REVIEW"):
                        gate1 += 1
                    if gs in ("GATE3_TIER1_PASS", "GATE4_CANDIDATE_FOR_MANUAL_REVIEW"):
                        tier1 += 1
                    if gs == "GATE4_CANDIDATE_FOR_MANUAL_REVIEW":
                        tier2 += 1

        total_source = admin_comp + top100_comp
        admin_ratio = (admin_comp / total_source) if total_source > 0 else 0.5
        ratio_drift_alert = total_source >= 8 and abs(admin_ratio - 0.5) > 0.10

        summary = {
            "est_platform_date": est_platform_date,
            "submitted_count": submitted,
            "quick_screened_count": len(quick_keys),
            "full_valid_completed_count": len(full_valid_keys),
            "dedup_skipped_count": dedup_skipped,
            "tech_fail_count": tech_fail,
            "unobserved_count": unobserved,
            "normal_completed": normal_comp,
            "alpha0_completed": alpha0_comp,
            "admin_completed": admin_comp,
            "top100_completed": top100_comp,
            "admin_source_ratio": round(admin_ratio, 4),
            "ratio_50_50_drift_alert": ratio_drift_alert,
            "gate1_count": gate1,
            "tier1_pass_count": tier1,
            "tier2_manual_review_count": tier2,
            "min_ratelimit_remaining": rl_row["min_rem"] if rl_row else None,
            "observed_ratelimit_limit": rl_row["max_lim"] if rl_row else None,
            "updated_at_utc": _utc_now(),
        }
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO daily_volume_snapshots (
                    est_platform_date, submitted_count, quick_screened_count, full_valid_completed_count,
                    dedup_skipped_count, tech_fail_count, unobserved_count, normal_completed, alpha0_completed,
                    admin_completed, top100_completed, gate1_count, tier1_pass_count, tier2_manual_review_count,
                    min_ratelimit_remaining, observed_ratelimit_limit, updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    summary["est_platform_date"], summary["submitted_count"], summary["quick_screened_count"],
                    summary["full_valid_completed_count"], summary["dedup_skipped_count"], summary["tech_fail_count"],
                    summary["unobserved_count"], summary["normal_completed"], summary["alpha0_completed"],
                    summary["admin_completed"], summary["top100_completed"], summary["gate1_count"],
                    summary["tier1_pass_count"], summary["tier2_manual_review_count"],
                    summary["min_ratelimit_remaining"], summary["observed_ratelimit_limit"], summary["updated_at_utc"],
                ),
            )
            self._conn.commit()
        return summary

    def record_sc_evaluation(self, record: dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO sc_evaluations (
                    alpha_id, region, pool_mode, sc_state, max_corr, max_peer_id, max_peer_sharpe,
                    peer_count, overlap_days, cache_os_count, cache_synced_at_utc, evaluated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["alpha_id"], record["region"].upper(), record["pool_mode"], record["sc_state"],
                    record.get("max_corr"), record.get("max_peer_id"), record.get("max_peer_sharpe"),
                    int(record["peer_count"]), record.get("overlap_days"), int(record["cache_os_count"]),
                    record["cache_synced_at_utc"], record.get("evaluated_at_utc") or _utc_now(),
                ),
            )
            self._conn.commit()

    def upsert_pc_queue(self, entry: dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO pc_poll_queue (
                    alpha_id, region, status, pc_max, pc_min, rescue_hint, check_status,
                    check_payload_json, attempts, next_poll_at_utc, last_http_status, last_error, updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry["alpha_id"], entry["region"].upper(), entry["status"], entry.get("pc_max"),
                    entry.get("pc_min"), entry.get("rescue_hint"), entry.get("check_status"),
                    entry.get("check_payload_json"), int(entry.get("attempts", 0)), entry.get("next_poll_at_utc"),
                    entry.get("last_http_status"), entry.get("last_error"), _utc_now(),
                ),
            )
            self._conn.commit()

    def get_pending_pc_entries(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM pc_poll_queue WHERE status IN ('PENDING_PC_COMPUTING', 'PC_RATE_LIMITED_429')"
            ).fetchall()
            return [dict(r) for r in rows]

    def upsert_field_profile(self, prof: dict[str, Any]) -> None:
        if prof.get("delay", 1) != 1:
            raise ValueError("D1-Only violation in field_profiles")
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO field_profiles (
                    region, universe, delay, dataset_id, field_id, field_type,
                    wds_dataset_grade, wds_field_tier, wds_coverage_recent_mean, wds_coverage_recent_min,
                    wds_history_slots, wds_risk_flags_json, live_alpha_count, live_user_count,
                    live_coverage, live_date_coverage, is_alpha0_free, freeze_expiry,
                    is_fake_single_vector, strictly_positive, pyramid_category, pyramid_multiplier, verified_at_utc
                ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prof["region"].upper(), prof["universe"].upper(), prof["dataset_id"], prof["field_id"],
                    prof["field_type"], prof.get("wds_dataset_grade"), prof.get("wds_field_tier"),
                    prof.get("wds_coverage_recent_mean"), prof.get("wds_coverage_recent_min"),
                    prof.get("wds_history_slots"), json.dumps(prof.get("wds_risk_flags") or []),
                    prof.get("live_alpha_count"), prof.get("live_user_count"), prof.get("live_coverage"),
                    prof.get("live_date_coverage"), int(bool(prof.get("is_alpha0_free", False))),
                    prof.get("freeze_expiry"), int(bool(prof.get("is_fake_single_vector", False))),
                    int(bool(prof.get("strictly_positive", False))), prof.get("pyramid_category"),
                    prof.get("pyramid_multiplier"), prof.get("verified_at_utc") or _utc_now(),
                ),
            )
            self._conn.commit()
