"""Asynchronous non-blocking remote PC & read-only Alpha Pre-Submission Check state machine.

Reuses classification discipline from legacy_core/Core/api/submission.py & scripts/tools/corr_map.py:
- HTTP 200 empty body -> PENDING_PC_COMPUTING (NEVER treated as PC=0 or pass!)
- Empty checks list -> PENDING (NEVER treated as all_passed=true!)
- PC in [0.70, 0.75] -> flags RESCUE_CANDIDATE_SIGNED_POWER (SZ83096 #47)
- ZERO /alphas/{id}/submit code paths anywhere in this module.
"""
from __future__ import annotations

import datetime
import json
import math
from dataclasses import dataclass
from typing import Any, Optional

from wq_research_v2.ledger_store import LedgerStore

BACKOFF_SCHEDULE_SEC = (15, 30, 60, 120, 180)
MAX_POLL_ATTEMPTS = 12


@dataclass
class PCPollResult:
    alpha_id: str
    region: str
    status: str  # PENDING_PC_COMPUTING | PC_READY_PASS | PC_READY_HIGH | PC_RATE_LIMITED_429 | PC_ERROR
    pc_max: Optional[float]
    pc_min: Optional[float]
    rescue_hint: Optional[str]
    check_status: Optional[str]  # PASS | PENDING | ERROR
    check_failures: list[str]
    http_status: Optional[int]
    error: Optional[str]
    pc_buckets: Optional[list[dict[str, Any]]] = None
    alphas_ge_070: Optional[int] = None
    alphas_in_070_080: Optional[int] = None
    alphas_ge_080: Optional[int] = None
    alphas_in_060_070: Optional[int] = None
    pc_table_decision: Optional[str] = None


def parse_pc_histogram_records(
    payload: dict[str, Any],
    *,
    pc_hard_lt: float = 0.70,
    near_pc_max: float = 0.78,
    sparse_count_max: int = 10,
    max_ge_080_count: int = 2,
    prior_pc_opt_rounds: int = 0,
    max_pc_opt_rounds: int = 3,
) -> dict[str, Any]:
    """Parse GET /alphas/{alphaId}/correlations/prod histogram table (`records`: [min, max, alphas]).

    Implements the relaxed quantitative PC range-table rule (allows 1 extra optimization round):
    - If pc_max < 0.70 -> `PC_PASS_STRICT` (true low-PC pass).
    - Note: Even if official /check grants +10% Sharpe outperformance exemption at PC >= 0.70,
      we advise rarely submitting PC > 0.70 (`PC_HIGH_ADVISE_HOLD`).
    - If range is moderately close (0.70 <= pc_max <= 0.78) AND colliding prod alpha count in >=0.70
      is manageable (<= 10 alphas total in >=0.70 and <= 2 in >=0.80) AND prior_pc_opt_rounds < max_pc_opt_rounds (up to 3 rounds):
      -> `PC_RESCUE_NEAR_SPARSE` (worth 2-3 dedicated PC optimization rounds).
    - If data count in >=0.70 is crowded (> 10), or >=0.80 has > 2 alphas, or pc_max > 0.78, or 3 rounds
      already failed to move PC < 0.70:
      -> `PC_ABANDON_CROWDED_OR_FAR` / `PC_ABANDON_MAX_ROUNDS_REACHED` (stop optimizing, tag & shelve).
    """
    raw_records = payload.get("records")
    schema_props = ((payload.get("schema") or {}).get("properties")) or []
    col_names = [str(p.get("name") or "").lower() for p in schema_props if isinstance(p, dict)]

    buckets: list[dict[str, Any]] = []
    alphas_ge_070 = 0
    alphas_in_070_080 = 0
    alphas_ge_080 = 0
    alphas_in_060_070 = 0

    if isinstance(raw_records, list):
        for row in raw_records:
            b_min: Optional[float] = None
            b_max: Optional[float] = None
            cnt: int = 0
            if isinstance(row, dict):
                b_min = float(row["min"]) if isinstance(row.get("min"), (int, float)) else None
                b_max = float(row["max"]) if isinstance(row.get("max"), (int, float)) else None
                cnt = int(row.get("alphas") or 0)
            elif isinstance(row, (list, tuple)) and len(row) >= 3:
                try:
                    if col_names and "min" in col_names and "max" in col_names and "alphas" in col_names:
                        b_min = float(row[col_names.index("min")])
                        b_max = float(row[col_names.index("max")])
                        cnt = int(row[col_names.index("alphas")])
                    else:
                        b_min = float(row[0])
                        b_max = float(row[1])
                        cnt = int(row[2])
                except (TypeError, ValueError):
                    continue
            if b_min is None or b_max is None:
                continue
            buckets.append({"min": round(b_min, 4), "max": round(b_max, 4), "alphas": cnt})
            if cnt > 0:
                if b_max > 0.70 + 1e-6 and b_min >= 0.70 - 1e-6:
                    alphas_ge_070 += cnt
                    if b_max <= 0.80 + 1e-6:
                        alphas_in_070_080 += cnt
                    else:
                        alphas_ge_080 += cnt
                elif b_max > 0.60 + 1e-6 and b_min >= 0.60 - 1e-6:
                    alphas_in_060_070 += cnt

    pc_max_raw = payload.get("max")
    pc_val = float(pc_max_raw) if isinstance(pc_max_raw, (int, float)) and math.isfinite(float(pc_max_raw)) else None

    if pc_val is None:
        decision = "PENDING_PC_COMPUTING"
    elif pc_val < pc_hard_lt:
        decision = "PC_PASS_STRICT"
    elif prior_pc_opt_rounds >= max_pc_opt_rounds:
        decision = "PC_ABANDON_MAX_ROUNDS_REACHED"
    elif pc_val <= near_pc_max and alphas_ge_080 <= max_ge_080_count and alphas_ge_070 <= sparse_count_max:
        decision = "PC_RESCUE_NEAR_SPARSE"
    else:
        decision = "PC_ABANDON_CROWDED_OR_FAR"

    return {
        "buckets": buckets,
        "non_empty_buckets": [b for b in buckets if b["alphas"] > 0],
        "alphas_ge_070": alphas_ge_070,
        "alphas_in_070_080": alphas_in_070_080,
        "alphas_ge_080": alphas_ge_080,
        "alphas_in_060_070": alphas_in_060_070,
        "decision": decision,
    }


def classify_readonly_check_payload(status_code: int, body_text: str) -> tuple[str, list[str], str]:
    """Classify GET /alphas/{id}/check strictly preventing empty-check false PASS."""
    if status_code == 429:
        return "PENDING", [], "HTTP 429 rate limited"
    if status_code < 200 or status_code >= 300:
        return "ERROR" if 400 <= status_code < 500 else "PENDING", [], f"HTTP {status_code}"
    if not (body_text or "").strip():
        return "PENDING", [], "Empty 200 check body"
    try:
        data = json.loads(body_text)
    except ValueError:
        return "PENDING", [], "Invalid JSON in check response"

    checks = data.get("checks")
    if checks is None and isinstance(data.get("is"), dict):
        checks = data["is"].get("checks")
    if not isinstance(checks, list) or not checks:
        return "PENDING", [], "Empty checks list (never treat as pass)"

    fails = [
        f"{c.get('name', 'UNKNOWN')}={c.get('value')}"
        for c in checks
        if isinstance(c, dict) and c.get("result") == "FAIL"
    ]
    if fails:
        return "ERROR", fails, f"FAIL: {', '.join(fails)}"
    if any(not isinstance(c, dict) or c.get("result") not in ("PASS", "WARNING") for c in checks):
        return "PENDING", [], "Checks still pending"
    return "PASS", [], "All checks PASS/WARNING"


class PCPoller:
    """Read-only poller for /correlations/prod and /alphas/{id}/check."""

    def __init__(self, client: Any, ledger: Optional[LedgerStore] = None, *, pc_hard_lt: float = 0.70) -> None:
        self.client = client
        self.ledger = ledger
        self.pc_hard_lt = float(pc_hard_lt)

    def poll_once(self, alpha_id: str, region: str, *, include_check: bool = True, attempts: int = 0) -> PCPollResult:
        """Perform a single non-blocking read-only PC + check probe."""
        try:
            resp = self.client.get(f"/alphas/{alpha_id}/correlations/prod", timeout=30)
        except Exception as exc:
            res = PCPollResult(alpha_id, region.upper(), "PC_ERROR", None, None, None, None, [], None, str(exc))
            self._persist(res, attempts + 1, None)
            return res

        code = resp.status_code
        body = (resp.text or "").strip()

        if code == 429:
            res = PCPollResult(alpha_id, region.upper(), "PC_RATE_LIMITED_429", None, None, None, None, [], code, "HTTP 429")
            self._persist(res, attempts + 1, None)
            return res

        if code == 200 and not body:
            res = PCPollResult(
                alpha_id, region.upper(), "PENDING_PC_COMPUTING", None, None, None, None, [], code,
                "HTTP 200 empty body (async compute pending)",
            )
            self._persist(res, attempts + 1, None)
            return res

        if code != 200:
            res = PCPollResult(alpha_id, region.upper(), "PC_ERROR", None, None, None, None, [], code, f"HTTP {code}")
            self._persist(res, attempts + 1, None)
            return res

        try:
            payload = json.loads(body)
        except ValueError:
            res = PCPollResult(alpha_id, region.upper(), "PENDING_PC_COMPUTING", None, None, None, None, [], code, "Non-JSON body")
            self._persist(res, attempts + 1, None)
            return res

        pc_max = payload.get("max")
        pc_min = payload.get("min")
        if not isinstance(pc_max, (int, float)) or not math.isfinite(float(pc_max)):
            res = PCPollResult(
                alpha_id, region.upper(), "PENDING_PC_COMPUTING", None, None, None, None, [], code,
                "Missing numeric max in /correlations/prod",
            )
            self._persist(res, attempts + 1, None)
            return res

        pc_val = float(pc_max)
        pc_min_val = float(pc_min) if isinstance(pc_min, (int, float)) and math.isfinite(float(pc_min)) else None

        check_status = None
        check_failures: list[str] = []
        check_raw = None
        if include_check:
            try:
                cresp = self.client.get(f"/alphas/{alpha_id}/check", timeout=30)
                check_status, check_failures, _ = classify_readonly_check_payload(cresp.status_code, cresp.text or "")
                check_raw = cresp.text if (cresp.text or "").strip() else None
            except Exception:
                check_status = "PENDING"

        hist = parse_pc_histogram_records(payload, pc_hard_lt=self.pc_hard_lt)
        rescue_hint = None
        if pc_val < self.pc_hard_lt:
            status = "PC_READY_PASS"
        else:
            status = "PC_READY_HIGH"
            if hist["decision"] == "PC_RESCUE_NEAR_SPARSE":
                rescue_hint = "RESCUE_CANDIDATE_SIGNED_POWER"
            else:
                rescue_hint = hist["decision"]

        res = PCPollResult(
            alpha_id=alpha_id,
            region=region.upper(),
            status=status,
            pc_max=round(pc_val, 4),
            pc_min=round(pc_min_val, 4) if pc_min_val is not None else None,
            rescue_hint=rescue_hint,
            check_status=check_status,
            check_failures=check_failures,
            http_status=code,
            error=None,
            pc_buckets=hist["non_empty_buckets"],
            alphas_ge_070=hist["alphas_ge_070"],
            alphas_in_070_080=hist["alphas_in_070_080"],
            alphas_ge_080=hist["alphas_ge_080"],
            alphas_in_060_070=hist["alphas_in_060_070"],
            pc_table_decision=hist["decision"],
        )
        self._persist(res, attempts + 1, check_raw)
        return res

    def _persist(self, res: PCPollResult, attempts: int, check_raw: Optional[str]) -> None:
        if self.ledger is None:
            return
        idx = min(max(0, attempts - 1), len(BACKOFF_SCHEDULE_SEC) - 1)
        next_ts = (
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=BACKOFF_SCHEDULE_SEC[idx])
        ).isoformat()
        self.ledger.upsert_pc_queue({
            "alpha_id": res.alpha_id,
            "region": res.region,
            "status": res.status,
            "pc_max": res.pc_max,
            "pc_min": res.pc_min,
            "rescue_hint": res.rescue_hint,
            "check_status": res.check_status,
            "check_payload_json": check_raw,
            "attempts": attempts,
            "next_poll_at_utc": next_ts if res.status in ("PENDING_PC_COMPUTING", "PC_RATE_LIMITED_429") else None,
            "last_http_status": res.http_status,
            "last_error": res.error,
        })
