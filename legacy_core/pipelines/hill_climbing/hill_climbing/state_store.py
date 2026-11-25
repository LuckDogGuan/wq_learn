"""SQLite persistence for continuous hill-climbing state.

The optimizer still works with a dict-like snapshot, while mutations are tracked so
ordinary checkpoints only upsert changed candidates instead of rewriting the full
legacy JSON document.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path


SCHEMA_VERSION = 6


def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sqlite_path_for(path):
    path = Path(path)
    if path.suffix.lower() in {".sqlite", ".sqlite3", ".db"}:
        return path
    return path.with_name("source_state_v6.sqlite3")


class TrackedRecord(dict):
    def __init__(self, alpha_id, value, dirty):
        self._alpha_id = str(alpha_id)
        self._dirty = dirty
        self._tracking = False
        super().__init__(value or {})
        self._tracking = True

    def _mark(self):
        if self._tracking:
            self._dirty.add(self._alpha_id)

    def __setitem__(self, key, value):
        if self.get(key, object()) != value:
            super().__setitem__(key, value)
            self._mark()

    def __delitem__(self, key):
        super().__delitem__(key)
        self._mark()

    def update(self, *args, **kwargs):
        incoming = dict(*args, **kwargs)
        if any(self.get(key, object()) != value for key, value in incoming.items()):
            super().update(incoming)
            self._mark()

    def pop(self, key, *default):
        if key in self:
            value = super().pop(key)
            self._mark()
            return value
        if default:
            return default[0]
        raise KeyError(key)

    def setdefault(self, key, default=None):
        if key not in self:
            super().__setitem__(key, default)
            self._mark()
        return self[key]


class TrackedCandidates(dict):
    def __init__(self, values, dirty, deleted):
        self._dirty = dirty
        self._deleted = deleted
        super().__init__()
        for alpha_id, value in (values or {}).items():
            super().__setitem__(str(alpha_id), TrackedRecord(alpha_id, value, dirty))

    def __setitem__(self, alpha_id, value):
        alpha_id = str(alpha_id)
        wrapped = value if isinstance(value, TrackedRecord) else TrackedRecord(
            alpha_id, value, self._dirty
        )
        super().__setitem__(alpha_id, wrapped)
        self._deleted.discard(alpha_id)
        self._dirty.add(alpha_id)

    def __delitem__(self, alpha_id):
        alpha_id = str(alpha_id)
        super().__delitem__(alpha_id)
        self._dirty.discard(alpha_id)
        self._deleted.add(alpha_id)

    def setdefault(self, alpha_id, default=None):
        alpha_id = str(alpha_id)
        if alpha_id not in self:
            self[alpha_id] = default or {"alpha_id": alpha_id}
        return self[alpha_id]


class SourceState(dict):
    """Dict-compatible state with candidate-level dirty tracking."""

    def __init__(self, values, store):
        self._store = store
        self._dirty_candidates = set()
        self._deleted_candidates = set()
        self._metadata_dirty = False
        self._tracking = False
        payload = dict(values or {})
        candidates = payload.pop("candidates", {})
        super().__init__(payload)
        super().__setitem__(
            "candidates",
            TrackedCandidates(candidates, self._dirty_candidates, self._deleted_candidates),
        )
        self._tracking = True

    def __setitem__(self, key, value):
        if key == "candidates" and not isinstance(value, TrackedCandidates):
            value = TrackedCandidates(
                value, self._dirty_candidates, self._deleted_candidates
            )
        if self.get(key, object()) != value:
            super().__setitem__(key, value)
            if self._tracking and key != "candidates":
                self._metadata_dirty = True

    def update(self, *args, **kwargs):
        for key, value in dict(*args, **kwargs).items():
            self[key] = value

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]

    def mark_clean(self):
        self._dirty_candidates.clear()
        self._deleted_candidates.clear()
        self._metadata_dirty = False


class SourceStateStore:
    def __init__(self, path):
        self.path = sqlite_path_for(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(str(self.path), timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA busy_timeout=30000")
        return connection

    def _initialize(self):
        with closing(self._connect()) as connection, connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS candidates (
                    alpha_id TEXT PRIMARY KEY,
                    status TEXT,
                    retry_after TEXT,
                    hill_stage INTEGER NOT NULL DEFAULT 1,
                    pool_status TEXT,
                    candidate_pool_fingerprint TEXT,
                    blocked_candidate_pool_fingerprint TEXT,
                    selected_at TEXT,
                    select_count INTEGER NOT NULL DEFAULT 0,
                    no_new_candidate_count INTEGER NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_candidates_queue
                    ON candidates(status, retry_after, hill_stage, pool_status);
                CREATE INDEX IF NOT EXISTS idx_candidates_fingerprint
                    ON candidates(candidate_pool_fingerprint,
                                  blocked_candidate_pool_fingerprint);
                CREATE TABLE IF NOT EXISTS batches (
                    batch_fingerprint TEXT PRIMARY KEY,
                    source_alpha_id TEXT,
                    stage INTEGER,
                    status TEXT NOT NULL,
                    retry_after TEXT,
                    location TEXT,
                    post_attempts INTEGER NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_batches_due
                    ON batches(status, retry_after, updated_at);
                CREATE TABLE IF NOT EXISTS events (
                    event_key TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            connection.execute(
                "INSERT OR REPLACE INTO metadata(key, value_json) VALUES(?, ?)",
                ("schema_version", json.dumps(SCHEMA_VERSION)),
            )

    def _has_candidates(self):
        with closing(self._connect()) as connection, connection:
            return bool(connection.execute("SELECT 1 FROM candidates LIMIT 1").fetchone())

    def migrate_legacy_json(self, legacy_path):
        legacy_path = Path(legacy_path)
        if not legacy_path.exists() or self._has_candidates():
            return False
        try:
            payload = json.loads(legacy_path.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError):
            return False
        if not isinstance(payload, dict) or not isinstance(payload.get("candidates"), dict):
            return False
        state = SourceState(payload, self)
        state._dirty_candidates.update(state["candidates"])
        state._metadata_dirty = True
        self.save(state)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT OR REPLACE INTO metadata(key, value_json) VALUES(?, ?)",
                ("legacy_json_migrated_from", json.dumps(str(legacy_path))),
            )
        return True

    def load(self, default_state, legacy_path=None):
        if legacy_path is not None:
            self.migrate_legacy_json(legacy_path)
        with closing(self._connect()) as connection, connection:
            metadata = {
                row["key"]: json.loads(row["value_json"])
                for row in connection.execute("SELECT key, value_json FROM metadata")
                if row["key"] not in {"schema_version", "legacy_json_migrated_from"}
            }
            candidates = {
                row["alpha_id"]: json.loads(row["payload_json"])
                for row in connection.execute("SELECT alpha_id, payload_json FROM candidates")
            }
        state = SourceState({**default_state, **metadata, "candidates": candidates}, self)
        state.mark_clean()
        return state

    def save(self, state):
        if not isinstance(state, SourceState):
            state = SourceState(state, self)
            state._dirty_candidates.update(state.get("candidates", {}))
            state._metadata_dirty = True
        now = _now()
        with closing(self._connect()) as connection, connection:
            for alpha_id in state._deleted_candidates:
                connection.execute("DELETE FROM candidates WHERE alpha_id=?", (alpha_id,))
            for alpha_id in state._dirty_candidates:
                record = dict(state.get("candidates", {}).get(alpha_id) or {})
                if not record:
                    continue
                connection.execute(
                    """
                    INSERT INTO candidates(
                        alpha_id, status, retry_after, hill_stage, pool_status,
                        candidate_pool_fingerprint, blocked_candidate_pool_fingerprint,
                        selected_at, select_count, no_new_candidate_count,
                        payload_json, updated_at
                    ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(alpha_id) DO UPDATE SET
                        status=excluded.status,
                        retry_after=excluded.retry_after,
                        hill_stage=excluded.hill_stage,
                        pool_status=excluded.pool_status,
                        candidate_pool_fingerprint=excluded.candidate_pool_fingerprint,
                        blocked_candidate_pool_fingerprint=excluded.blocked_candidate_pool_fingerprint,
                        selected_at=excluded.selected_at,
                        select_count=excluded.select_count,
                        no_new_candidate_count=excluded.no_new_candidate_count,
                        payload_json=excluded.payload_json,
                        updated_at=excluded.updated_at
                    """,
                    (
                        alpha_id, record.get("status"), record.get("retry_after"),
                        int(record.get("hill_stage") or 1), record.get("pool_status"),
                        record.get("candidate_pool_fingerprint"),
                        record.get("blocked_candidate_pool_fingerprint"),
                        record.get("selected_at"), int(record.get("select_count") or 0),
                        int(record.get("no_new_candidate_count") or 0),
                        json.dumps(record, ensure_ascii=False, default=str), now,
                    ),
                )
            if state._metadata_dirty:
                for key, value in state.items():
                    if key == "candidates":
                        continue
                    connection.execute(
                        "INSERT OR REPLACE INTO metadata(key, value_json) VALUES(?, ?)",
                        (key, json.dumps(value, ensure_ascii=False, default=str)),
                    )
        state.mark_clean()
        return state

    def atomic_claim(self, alpha_id, allowed_statuses, selected_at=None):
        selected_at = selected_at or _now()
        placeholders = ",".join("?" for _ in allowed_statuses)
        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                f"""
                UPDATE candidates
                   SET status='OPTIMIZING', selected_at=?,
                       select_count=select_count + 1, updated_at=?
                 WHERE alpha_id=? AND status IN ({placeholders})
                """,
                (selected_at, selected_at, str(alpha_id), *tuple(allowed_statuses)),
            )
            if cursor.rowcount != 1:
                return None
            row = connection.execute(
                "SELECT payload_json FROM candidates WHERE alpha_id=?", (str(alpha_id),)
            ).fetchone()
            record = json.loads(row["payload_json"])
            record.update({
                "status": "OPTIMIZING",
                "selected_at": selected_at,
                "select_count": int(record.get("select_count") or 0) + 1,
            })
            connection.execute(
                "UPDATE candidates SET payload_json=? WHERE alpha_id=?",
                (json.dumps(record, ensure_ascii=False, default=str), str(alpha_id)),
            )
            return record

    def save_batch(self, fingerprint, payload):
        payload = dict(payload or {})
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                INSERT INTO batches(
                    batch_fingerprint, source_alpha_id, stage, status, retry_after,
                    location, post_attempts, payload_json, updated_at
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(batch_fingerprint) DO UPDATE SET
                    source_alpha_id=excluded.source_alpha_id,
                    stage=excluded.stage,
                    status=excluded.status,
                    retry_after=excluded.retry_after,
                    location=excluded.location,
                    post_attempts=excluded.post_attempts,
                    payload_json=excluded.payload_json,
                    updated_at=excluded.updated_at
                """,
                (
                    str(fingerprint), payload.get("source_alpha_id"),
                    int(payload.get("stage") or 1), payload.get("status") or "PENDING",
                    payload.get("retry_after"), payload.get("location"),
                    int(payload.get("post_attempts") or 0),
                    json.dumps(payload, ensure_ascii=False, default=str), _now(),
                ),
            )

    def due_batch(self, now=None):
        now = now or _now()
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                """
                SELECT batch_fingerprint, payload_json FROM batches
                 WHERE source_alpha_id IS NOT NULL AND (
                       (status='PENDING_RATE_LIMIT' AND (retry_after IS NULL OR retry_after<=?))
                    OR status='SUBMITTED'
                 )
                 ORDER BY CASE status WHEN 'PENDING_RATE_LIMIT' THEN 0 ELSE 1 END,
                          COALESCE(retry_after, updated_at), updated_at
                 LIMIT 1
                """,
                (now,),
            ).fetchone()
        if not row:
            return None
        try:
            payload = json.loads(row["payload_json"])
            payload.setdefault("batch_fingerprint", row["batch_fingerprint"])
            return payload
        except (TypeError, ValueError):
            return None

    def due_batch_source(self, now=None):
        payload = self.due_batch(now=now)
        return payload.get("source_alpha_id") if isinstance(payload, dict) else None

    def append_event(self, event_key, event_type, payload):
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO events(event_key, event_type, payload_json, created_at) "
                "VALUES(?, ?, ?, ?)",
                (
                    str(event_key), str(event_type),
                    json.dumps(payload, ensure_ascii=False, default=str), _now(),
                ),
            )
        return cursor.rowcount == 1

    def operational_counts(self):
        """Return compact, deduplicated scheduler counters for the periodic report."""
        with closing(self._connect()) as connection, connection:
            candidates = connection.execute(
                """
                SELECT COUNT(*) AS unique_sources,
                       COALESCE(SUM(select_count), 0) AS source_selections,
                       COALESCE(SUM(CASE WHEN select_count > 1 THEN select_count - 1 ELSE 0 END), 0)
                           AS repeat_source_selections,
                       COALESCE(SUM(CASE WHEN no_new_candidate_count >= 2 THEN 1 ELSE 0 END), 0)
                           AS no_new_candidate_sources
                  FROM candidates
                """
            ).fetchone()
            batches = connection.execute(
                """
                SELECT COUNT(*) AS unique_batches,
                       COALESCE(SUM(post_attempts), 0) AS batch_post_attempts,
                       COALESCE(SUM(CASE WHEN status='RESULTS_UNOBSERVED' THEN 1 ELSE 0 END), 0)
                           AS read_only_unobserved,
                       COALESCE(SUM(CASE WHEN status='BLOCKED_INCOMPLETE_BATCH' THEN 1 ELSE 0 END), 0)
                           AS incomplete_batches
                  FROM batches
                """
            ).fetchone()
        return {**dict(candidates), **dict(batches)}


__all__ = [
    "SCHEMA_VERSION", "SourceState", "SourceStateStore", "sqlite_path_for",
]
