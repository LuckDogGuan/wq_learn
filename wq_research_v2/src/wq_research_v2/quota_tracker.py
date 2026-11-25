"""Real-time BRAIN quota header tracking, EST/EDT platform day clock, and 429 circuit breaker.

Absorbs Share Core's verified (3, 10, 25, 45, 60, 60) backoff ladder and
Retry-After / RateLimit-Reset / X-RateLimit-Reset header priority.
"""
from __future__ import annotations

import datetime
import json
import math
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")
DEFAULT_BACKOFF_SCHEDULE = (3.0, 10.0, 25.0, 45.0, 60.0, 60.0)


def current_est_platform_date(now_utc: Optional[datetime.datetime] = None) -> str:
    """Return YYYY-MM-DD in America/New_York (handles EST/EDT DST automatically).
    Winter EST 00:00 = Beijing 13:00; Summer EDT 00:00 = Beijing 12:00.
    """
    dt = now_utc or datetime.datetime.now(datetime.timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(NY_TZ).strftime("%Y-%m-%d")


def _parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        parsed = float(str(value).strip())
        return parsed if math.isfinite(parsed) else None
    except (TypeError, ValueError):
        return None


def _parse_int(value: Any) -> Optional[int]:
    val = _parse_float(value)
    return int(val) if val is not None else None


@dataclass(frozen=True)
class RateLimitSnapshot:
    observed_at_utc: str
    est_platform_date: str
    endpoint: str
    http_status: int
    limit_val: Optional[int]
    remaining_val: Optional[int]
    reset_val: Optional[float]
    retry_after_val: Optional[float]
    raw_headers: dict[str, str]


def extract_ratelimit_headers(
    endpoint: str,
    http_status: int,
    headers: Mapping[str, Any],
    now_utc: Optional[datetime.datetime] = None,
) -> RateLimitSnapshot:
    dt = now_utc or datetime.datetime.now(datetime.timezone.utc)
    lowered = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    interesting = {
        k: v
        for k, v in lowered.items()
        if "ratelimit" in k or "retry-after" in k or k == "location"
    }

    limit_val = _parse_int(
        lowered.get("x-ratelimit-limit")
        or lowered.get("ratelimit-limit")
        or lowered.get("x-ratelimit-limit-day")
    )
    remaining_val = _parse_int(
        lowered.get("x-ratelimit-remaining")
        or lowered.get("ratelimit-remaining")
        or lowered.get("x-ratelimit-remaining-day")
    )
    reset_val = _parse_float(
        lowered.get("x-ratelimit-reset") or lowered.get("ratelimit-reset")
    )
    retry_after_val = _parse_float(lowered.get("retry-after"))

    return RateLimitSnapshot(
        observed_at_utc=dt.isoformat(),
        est_platform_date=current_est_platform_date(dt),
        endpoint=endpoint,
        http_status=int(http_status),
        limit_val=limit_val,
        remaining_val=remaining_val,
        reset_val=reset_val,
        retry_after_val=retry_after_val,
        raw_headers=interesting,
    )


class QuotaTracker:
    """Thread-safe quota header recorder + shared 429 circuit breaker."""

    def __init__(
        self,
        ledger_store: Any = None,
        *,
        backoff_schedule: tuple[float, ...] = DEFAULT_BACKOFF_SCHEDULE,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._ledger = ledger_store
        self._backoff = backoff_schedule
        self._clock = clock
        self._sleep = sleeper
        self._lock = threading.Lock()
        self._cooldown_until: float = 0.0
        self._consecutive_429: int = 0
        self.last_snapshot: Optional[RateLimitSnapshot] = None

    def compute_wait_seconds(
        self,
        snapshot: RateLimitSnapshot,
        attempt: int = 0,
    ) -> float:
        """Share Core priority: Retry-After > RateLimit-Reset/X-RateLimit-Reset > backoff ladder."""
        ladder_idx = min(max(0, attempt), len(self._backoff) - 1)
        fallback = self._backoff[ladder_idx]

        if snapshot.retry_after_val is not None and snapshot.retry_after_val > 0:
            return min(max(snapshot.retry_after_val, 1.0), 300.0)

        if snapshot.reset_val is not None and snapshot.reset_val > 0:
            # Handle either relative seconds or unix epoch timestamp
            if snapshot.reset_val > 1_000_000_000:
                delta = snapshot.reset_val - time.time()
                if delta > 0:
                    return min(max(delta, 1.0), 300.0)
            else:
                return min(max(snapshot.reset_val, 1.0), 300.0)

        return fallback

    def observe_response(self, endpoint: str, response: Any) -> RateLimitSnapshot:
        snap = extract_ratelimit_headers(
            endpoint=endpoint,
            http_status=getattr(response, "status_code", 0),
            headers=getattr(response, "headers", {}),
        )
        wait_applied = 0.0
        with self._lock:
            self.last_snapshot = snap
            if snap.http_status == 429:
                wait_applied = self.compute_wait_seconds(snap, attempt=self._consecutive_429)
                self._consecutive_429 += 1
                self._cooldown_until = max(self._cooldown_until, self._clock() + wait_applied)
            elif 200 <= snap.http_status < 300:
                self._consecutive_429 = 0
                if snap.remaining_val is not None and snap.remaining_val <= 0:
                    wait_applied = self.compute_wait_seconds(snap, attempt=0)
                    self._cooldown_until = max(self._cooldown_until, self._clock() + wait_applied)

        if self._ledger is not None:
            self._ledger.record_ratelimit_event(
                observed_at_utc=snap.observed_at_utc,
                est_platform_date=snap.est_platform_date,
                endpoint=snap.endpoint,
                http_status=snap.http_status,
                limit_val=snap.limit_val,
                remaining_val=snap.remaining_val,
                reset_val=snap.reset_val,
                retry_after_val=snap.retry_after_val,
                wait_applied_sec=wait_applied,
                raw_headers_json=json.dumps(snap.raw_headers, ensure_ascii=False),
            )
        return snap

    def wait_if_circuit_open(self) -> float:
        with self._lock:
            remaining = self._cooldown_until - self._clock()
        if remaining > 0:
            self._sleep(remaining)
            return remaining
        return 0.0
