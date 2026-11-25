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

        rescue_hint = None
        if pc_val < self.pc_hard_lt:
            status = "PC_READY_PASS"
        else:
            status = "PC_READY_HIGH"
            if self.pc_hard_lt <= pc_val <= 0.75:
                rescue_hint = "RESCUE_CANDIDATE_SIGNED_POWER"

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
