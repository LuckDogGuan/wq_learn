"""Portable Local Self-Correlation (SC / PPAC) & N×N Candidate Pairwise Dedup Engine.

Fixes ALL 3 legacy sc_engine.py defects:
1. Never silently returns 0.0 on missing peers, stale cache, or NaN/no-overlap:
   explicitly returns NO_PEERS_IN_REGION / CACHE_STALE / PENDING_NO_OVERLAP with max_corr=None
2. Always excludes peer_id == alpha_id (self-exclusion)
3. Supports explicit pool_mode in {'REGULAR_ALL', 'REGULAR_NO_PPA', 'PPAC_ONLY'}
4. Stores PnL arrays in portable SQLite (zlib + little-endian float64), immune to pandas pickle drift
5. Provides N×N candidate pairwise SC matrix & greedy orthogonal subset selection (JR23144 #12)
"""
from __future__ import annotations

import datetime
import hashlib
import json
import math
import sqlite3
import time
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from wq_research_v2.config_loader import SC_CACHE_DB_PATH

SC_CACHE_SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
CREATE TABLE IF NOT EXISTS os_alphas (
    alpha_id       TEXT PRIMARY KEY,
    region         TEXT NOT NULL,
    universe       TEXT,
    delay          INTEGER,
    stage          TEXT NOT NULL,
    is_ppa         INTEGER NOT NULL DEFAULT 0,
    sharpe         REAL,
    date_submitted TEXT,
    pnl_start_date TEXT,
    pnl_end_date   TEXT,
    row_count      INTEGER NOT NULL,
    synced_at_utc  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pnl_series (
    alpha_id        TEXT PRIMARY KEY,
    kind            TEXT NOT NULL CHECK (kind IN ('OS', 'CANDIDATE')),
    dates_zlib_json BLOB NOT NULL,
    pnls_zlib_f64   BLOB NOT NULL,
    sha256          TEXT NOT NULL,
    updated_at_utc  TEXT NOT NULL
);
"""


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def encode_pnl_series(dates: list[str], pnls: list[float]) -> tuple[bytes, bytes, str]:
    d_bytes = json.dumps(dates, separators=(",", ":")).encode("utf-8")
    arr = np.asarray(pnls, dtype="<f8")
    p_bytes = arr.tobytes()
    digest = hashlib.sha256(d_bytes + p_bytes).hexdigest()
    return zlib.compress(d_bytes, level=6), zlib.compress(p_bytes, level=6), digest


def decode_pnl_series(dates_blob: bytes, pnls_blob: bytes) -> pd.Series:
    dates = json.loads(zlib.decompress(dates_blob).decode("utf-8"))
    arr = np.frombuffer(zlib.decompress(pnls_blob), dtype="<f8")
    return pd.Series(arr, index=pd.Index(dates, name="date"), dtype="float64")


def parse_brain_pnl_payload(payload: dict[str, Any]) -> tuple[list[str], list[float]]:
    """Parse BRAIN /alphas/{id}/recordsets/pnl JSON into (dates, pnl_values)."""
    records = payload.get("records") or []
    schema = (payload.get("schema") or {}).get("properties") or []
    date_idx = 0
    pnl_idx = 1
    for i, prop in enumerate(schema):
        nm = str((prop or {}).get("name", "")).lower()
        if nm == "date":
            date_idx = i
        elif nm == "pnl":
            pnl_idx = i
    dates: list[str] = []
    pnls: list[float] = []
    for row in records:
        if not isinstance(row, (list, tuple)) or len(row) <= max(date_idx, pnl_idx):
            continue
        d = row[date_idx]
        v = row[pnl_idx]
        if d is not None and isinstance(v, (int, float)) and math.isfinite(v):
            dates.append(str(d))
            pnls.append(float(v))
    return dates, pnls


@dataclass
class SCResult:
    alpha_id: str
    region: str
    pool_mode: str
    sc_state: str  # SC_READY_PASS | SC_READY_HIGH | NO_PEERS_IN_REGION | CACHE_STALE | PENDING_NO_OVERLAP
    max_corr: Optional[float]
    max_peer_id: Optional[str]
    max_peer_sharpe: Optional[float]
    peer_count: int
    overlap_days: Optional[int]
    cache_os_count: int
    cache_synced_at_utc: str


class LocalSCEngine:
    """Portable local SC/PPAC & candidate-pool pairwise correlation engine."""

    def __init__(
        self,
        cache_db_path: Path = SC_CACHE_DB_PATH,
        *,
        safe_sc_threshold: float = 0.68,
        hard_sc_threshold: float = 0.70,
        ppac_threshold: float = 0.50,
        min_overlap_days: int = 60,
        recent_years: int = 4,
    ) -> None:
        self.cache_db_path = Path(cache_db_path)
        self.cache_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.safe_sc_threshold = float(safe_sc_threshold)
        self.hard_sc_threshold = float(hard_sc_threshold)
        self.ppac_threshold = float(ppac_threshold)
        self.min_overlap_days = int(min_overlap_days)
        self.recent_years = int(recent_years)
        self._conn = sqlite3.connect(str(self.cache_db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SC_CACHE_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def save_pnl(self, alpha_id: str, dates: list[str], pnls: list[float], kind: str = "CANDIDATE") -> None:
        d_blob, p_blob, digest = encode_pnl_series(dates, pnls)
        self._conn.execute(
            "INSERT OR REPLACE INTO pnl_series (alpha_id, kind, dates_zlib_json, pnls_zlib_f64, sha256, updated_at_utc) VALUES (?, ?, ?, ?, ?, ?)",
            (alpha_id, kind, d_blob, p_blob, digest, _utc_now()),
        )
        self._conn.commit()

    def upsert_os_alpha(
        self,
        *,
        alpha_id: str,
        region: str,
        universe: str,
        delay: int,
        is_ppa: bool,
        sharpe: Optional[float],
        date_submitted: Optional[str],
        dates: list[str],
        pnls: list[float],
        stage: str = "OS",
    ) -> None:
        self.save_pnl(alpha_id, dates, pnls, kind="OS")
        self._conn.execute(
            """
            INSERT OR REPLACE INTO os_alphas (
                alpha_id, region, universe, delay, stage, is_ppa, sharpe,
                date_submitted, pnl_start_date, pnl_end_date, row_count, synced_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alpha_id, region.upper(), universe, int(delay), stage, int(bool(is_ppa)),
                sharpe, date_submitted, dates[0] if dates else None, dates[-1] if dates else None,
                len(dates), _utc_now(),
            ),
        )
        self._conn.commit()

    def get_cached_pnl(self, alpha_id: str) -> Optional[pd.Series]:
        row = self._conn.execute(
            "SELECT dates_zlib_json, pnls_zlib_f64 FROM pnl_series WHERE alpha_id=?",
            (alpha_id,),
        ).fetchone()
        if not row:
            return None
        return decode_pnl_series(row["dates_zlib_json"], row["pnls_zlib_f64"])

    def fetch_and_cache_pnl(self, client: Any, alpha_id: str, kind: str = "CANDIDATE") -> Optional[pd.Series]:
        cached = self.get_cached_pnl(alpha_id)
        if cached is not None and len(cached) >= self.min_overlap_days:
            return cached
        for _ in range(12):
            resp = client.get(f"/alphas/{alpha_id}/recordsets/pnl", timeout=30)
            if resp.status_code == 200 and (resp.text or "").strip():
                dates, pnls = parse_brain_pnl_payload(resp.json())
                if dates:
                    self.save_pnl(alpha_id, dates, pnls, kind=kind)
                    return pd.Series(pnls, index=pd.Index(dates, name="date"), dtype="float64")
                return None
            retry = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
            time.sleep(max(1.0, min(float(retry), 15.0)) if retry else 2.0)
        return None

    def sync_os_alphas(self, client: Any, *, max_pages: int = 20) -> dict[str, Any]:
        """Incrementally sync ALL submitted OS alphas (e.g., all 92+) into portable SQLite cache."""
        existing = {
            r["alpha_id"]
            for r in self._conn.execute("SELECT alpha_id FROM os_alphas").fetchall()
        }
        fetched_total = 0
        newly_synced = 0
        failed_pnl: list[str] = []

        offset = 0
        limit = 100
        for _ in range(max_pages):
            resp = client.get(f"/users/self/alphas?limit={limit}&offset={offset}&stage=OS", timeout=30)
            if resp.status_code != 200:
                break
            data = resp.json()
            results = data.get("results") or []
            if not results:
                break
            fetched_total += len(results)
            for item in results:
                aid = item.get("id")
                if not aid or aid in existing:
                    continue
                settings = item.get("settings") or {}
                cls_ids = {str((c or {}).get("id", "")) for c in (item.get("classifications") or [])}
                is_ppa = any("POWER_POOL" in cid for cid in cls_ids)
                series = self.fetch_and_cache_pnl(client, aid, kind="OS")
                if series is None or len(series) == 0:
                    failed_pnl.append(aid)
                    continue
                self.upsert_os_alpha(
                    alpha_id=aid,
                    region=str(settings.get("region") or "UNKNOWN"),
                    universe=str(settings.get("universe") or ""),
                    delay=int(settings.get("delay", 1)),
                    is_ppa=is_ppa,
                    sharpe=(item.get("is") or {}).get("sharpe"),
                    date_submitted=item.get("dateSubmitted"),
                    dates=list(series.index),
                    pnls=list(series.values),
                )
                existing.add(aid)
                newly_synced += 1
            if len(results) < limit:
                break
            offset += limit

        total_cached = self._conn.execute("SELECT COUNT(*) FROM os_alphas").fetchone()[0]
        return {
            "platform_os_seen": fetched_total,
            "newly_synced": newly_synced,
            "total_cached_os": total_cached,
            "failed_pnl": failed_pnl,
            "synced_at_utc": _utc_now(),
        }

    def _to_daily_returns(self, pnl: pd.Series) -> pd.Series:
        s = pnl.sort_index()
        if self.recent_years > 0 and len(s) > 0:
            try:
                end_dt = pd.to_datetime(s.index[-1])
                cutoff = (end_dt - pd.DateOffset(years=self.recent_years)).strftime("%Y-%m-%d")
                s = s.loc[s.index >= cutoff]
            except Exception:
                pass
        return s.diff().dropna()

    def evaluate_sc(
        self,
        alpha_id: str,
        region: str,
        target_pnl: pd.Series,
        *,
        pool_mode: str = "REGULAR_ALL",
        cache_stale: bool = False,
    ) -> SCResult:
        """Compute local SC/PPAC without EVER returning a false 0.0 on missing data/NaN."""
        reg = region.upper()
        total_os_row = self._conn.execute("SELECT COUNT(*) AS c, MAX(synced_at_utc) AS ts FROM os_alphas").fetchone()
        total_os = int(total_os_row["c"]) if total_os_row else 0
        synced_ts = str(total_os_row["ts"] or "NEVER") if total_os_row else "NEVER"

        if cache_stale or total_os == 0:
            return SCResult(alpha_id, reg, pool_mode, "CACHE_STALE", None, None, None, 0, None, total_os, synced_ts)

        if pool_mode == "REGULAR_ALL":
            rows = self._conn.execute(
                "SELECT alpha_id, sharpe FROM os_alphas WHERE region=? AND alpha_id != ?",
                (reg, alpha_id),
            ).fetchall()
        elif pool_mode == "REGULAR_NO_PPA":
            rows = self._conn.execute(
                "SELECT alpha_id, sharpe FROM os_alphas WHERE region=? AND is_ppa=0 AND alpha_id != ?",
                (reg, alpha_id),
            ).fetchall()
        elif pool_mode == "PPAC_ONLY":
            rows = self._conn.execute(
                "SELECT alpha_id, sharpe FROM os_alphas WHERE region=? AND is_ppa=1 AND alpha_id != ?",
                (reg, alpha_id),
            ).fetchall()
        else:
            raise ValueError(f"Invalid pool_mode: {pool_mode!r}")

        if not rows:
            return SCResult(alpha_id, reg, pool_mode, "NO_PEERS_IN_REGION", None, None, None, 0, None, total_os, synced_ts)

        target_ret = self._to_daily_returns(target_pnl)
        if len(target_ret) < self.min_overlap_days or float(target_ret.std()) == 0.0:
            return SCResult(alpha_id, reg, pool_mode, "PENDING_NO_OVERLAP", None, None, None, len(rows), 0, total_os, synced_ts)

        best_corr: Optional[float] = None
        best_peer: Optional[str] = None
        best_peer_sh: Optional[float] = None
        best_overlap = 0

        for r in rows:
            pid = r["alpha_id"]
            peer_pnl = self.get_cached_pnl(pid)
            if peer_pnl is None:
                continue
            peer_ret = self._to_daily_returns(peer_pnl)
            joined = pd.concat([target_ret.rename("t"), peer_ret.rename("p")], axis=1, join="inner").dropna()
            if len(joined) < self.min_overlap_days:
                continue
            c = joined["t"].corr(joined["p"])
            if pd.isna(c) or not math.isfinite(float(c)):
                continue
            val = float(c)
            if best_corr is None or val > best_corr:
                best_corr = val
                best_peer = pid
                best_peer_sh = r["sharpe"]
                best_overlap = len(joined)

        if best_corr is None:
            return SCResult(alpha_id, reg, pool_mode, "PENDING_NO_OVERLAP", None, None, None, len(rows), 0, total_os, synced_ts)

        cutoff = self.ppac_threshold if pool_mode == "PPAC_ONLY" else self.hard_sc_threshold
        state = "SC_READY_PASS" if best_corr < cutoff else "SC_READY_HIGH"
        return SCResult(
            alpha_id=alpha_id,
            region=reg,
            pool_mode=pool_mode,
            sc_state=state,
            max_corr=round(best_corr, 4),
            max_peer_id=best_peer,
            max_peer_sharpe=best_peer_sh,
            peer_count=len(rows),
            overlap_days=best_overlap,
            cache_os_count=total_os,
            cache_synced_at_utc=synced_ts,
        )

    def compute_pairwise_matrix(
        self,
        pnls_by_id: dict[str, pd.Series],
    ) -> pd.DataFrame:
        """Compute N×N pairwise daily-return Pearson correlation matrix across candidates (JR23144 #12)."""
        ret_map = {aid: self._to_daily_returns(s) for aid, s in pnls_by_id.items() if s is not None and len(s) > 1}
        if not ret_map:
            return pd.DataFrame()
        df = pd.DataFrame(ret_map)
        return df.corr(min_periods=self.min_overlap_days)

    @staticmethod
    def select_orthogonal_subset(
        ranked_ids: list[str],
        corr_matrix: pd.DataFrame,
        *,
        max_pairwise_corr: float = 0.68,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Greedy orthogonal deduplication: preserve top-ranked alphas mutually below max_pairwise_corr."""
        kept: list[str] = []
        pruned: list[dict[str, Any]] = []
        for aid in ranked_ids:
            if aid not in corr_matrix.index:
                kept.append(aid)
                continue
            conflict = None
            for k in kept:
                if k in corr_matrix.columns:
                    val = corr_matrix.loc[aid, k]
                    if pd.notna(val) and float(val) >= max_pairwise_corr:
                        conflict = (k, round(float(val), 4))
                        break
            if conflict is None:
                kept.append(aid)
            else:
                pruned.append({"alpha_id": aid, "blocked_by": conflict[0], "pairwise_corr": conflict[1]})
        return kept, pruned
