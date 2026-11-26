"""Read-only streaming merger from legacy_core/Core/runtime_data into wq_v2_ledger.db + D1 candidate screener.

Design guarantees:
- STRICTLY READ-ONLY on legacy_core/Core/runtime_data (SQLite ?mode=ro, plain file read).
- STRICTLY D1-Only (delay == 1 enforced in Python and SQL CHECK constraint).
- Streaming JSONL ingestion (low memory, safe for 512MB RAM cap).
- Isolated tables (legacy_alphas, legacy_datasets, legacy_merge_runs) in wq_v2_ledger.db:
  never touches sim_tasks or COMPLETED_FULL rows.
- Decision #3 compliance check (+, *, add, multiply, trade_when) + trap checks
  (lambda_max > 1, ts_decay_linear > 252) using expr_validator.tokenize.
"""
from __future__ import annotations

import datetime
import json
import math
import re
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Iterable, Optional

from wq_research_v2.config_loader import (
    LEDGER_DB_PATH,
    LEGACY_RUNTIME_DATA_DIR,
    SC_CACHE_DB_PATH,
    load_d1_thresholds,
)
from wq_research_v2.expr_validator import tokenize

LEGACY_SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 15000;

CREATE TABLE IF NOT EXISTS legacy_alphas (
    alpha_id            TEXT PRIMARY KEY,
    source_origin       TEXT NOT NULL,
    region              TEXT NOT NULL,
    universe            TEXT,
    delay               INTEGER NOT NULL CHECK (delay = 1),
    dataset_id          TEXT,
    category            TEXT,
    expression          TEXT NOT NULL,
    neutralization      TEXT,
    decay               INTEGER,
    truncation          REAL,
    settings_json       TEXT,
    sharpe              REAL,
    fitness             REAL,
    turnover            REAL,
    margin              REAL,
    sharpe_2y           REAL,
    legacy_sc           REAL,
    hard_pass           INTEGER NOT NULL DEFAULT 0,
    is_already_os       INTEGER NOT NULL DEFAULT 0,
    decision3_compliant INTEGER NOT NULL DEFAULT 1,
    violation_tags_json TEXT NOT NULL DEFAULT '[]',
    opt_tier            TEXT NOT NULL,
    opt_action_hint     TEXT,
    template_id         TEXT,
    source_alpha_id     TEXT,
    legacy_status       TEXT,
    created_at_legacy   TEXT,
    merged_at_utc       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_legacy_region_tier ON legacy_alphas(region, opt_tier, is_already_os, sharpe DESC);
CREATE INDEX IF NOT EXISTS idx_legacy_dataset ON legacy_alphas(region, dataset_id, sharpe DESC);
CREATE INDEX IF NOT EXISTS idx_legacy_compliant ON legacy_alphas(decision3_compliant, opt_tier, sharpe DESC);

CREATE TABLE IF NOT EXISTS legacy_datasets (
    region             TEXT NOT NULL,
    universe           TEXT NOT NULL,
    dataset_id         TEXT NOT NULL,
    delay              INTEGER NOT NULL CHECK (delay = 1),
    name               TEXT,
    category_id        TEXT,
    subcategory_id     TEXT,
    coverage           REAL,
    date_coverage      REAL,
    value_score        REAL,
    user_count         INTEGER,
    alpha_count        INTEGER,
    field_count        INTEGER,
    pyramid_multiplier REAL,
    date_updated       TEXT,
    merged_at_utc      TEXT NOT NULL,
    PRIMARY KEY (region, universe, dataset_id)
);
CREATE INDEX IF NOT EXISTS idx_legacy_ds_region ON legacy_datasets(region, pyramid_multiplier DESC, coverage DESC);

CREATE TABLE IF NOT EXISTS legacy_merge_runs (
    run_id                  TEXT PRIMARY KEY,
    started_at_utc          TEXT NOT NULL,
    completed_at_utc        TEXT NOT NULL,
    files_scanned_json      TEXT NOT NULL,
    rows_scanned            INTEGER NOT NULL,
    d1_unique_alphas_merged INTEGER NOT NULL,
    datasets_merged         INTEGER NOT NULL,
    tier_counts_json        TEXT NOT NULL,
    notes                   TEXT
);
"""

_LAMBDA_MAX_RE = re.compile(r"lambda_max\s*=\s*([0-9]+(?:\.[0-9]+)?)")
_TS_DECAY_RE = re.compile(r"ts_decay_linear\s*\([^()]+,\s*([0-9]+(?:\.[0-9]+)?)\s*\)")


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _safe_float(val: Any) -> Optional[float]:
    if val is None or isinstance(val, bool):
        return None
    try:
        f = float(val)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _safe_int(val: Any) -> Optional[int]:
    if val is None or isinstance(val, bool):
        return None
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return None


def ensure_legacy_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(LEGACY_SCHEMA_SQL)
    conn.commit()


def classify_expression_compliance(expr: str) -> tuple[bool, list[str]]:
    """Fast static check for Decision #3 forbidden ops and known D1 parameter traps."""
    violations: list[str] = []
    if not expr or not isinstance(expr, str):
        return False, ["EMPTY_EXPRESSION"]

    try:
        tokens = tokenize(expr)
    except Exception:
        tokens = []

    if tokens:
        for i, tok in enumerate(tokens):
            if tok.kind == "IDENT" and i + 1 < len(tokens) and tokens[i + 1].kind == "LPAREN":
                low = tok.value.lower()
                if low == "add":
                    violations.append("FORBIDDEN_ADD")
                elif low == "multiply":
                    violations.append("FORBIDDEN_MULTIPLY")
                elif low == "trade_when":
                    violations.append("FORBIDDEN_TRADE_WHEN")
            elif tok.kind == "OP" and tok.value in ("+", "*"):
                prev_tok = tokens[i - 1] if i > 0 else None
                is_unary_plus = tok.value == "+" and (
                    prev_tok is None or prev_tok.kind in ("LPAREN", "COMMA", "OP", "EQ")
                )
                if not is_unary_plus:
                    violations.append("FORBIDDEN_ADD" if tok.value == "+" else "FORBIDDEN_MULTIPLY")
    else:
        low_expr = expr.lower()
        if "trade_when(" in low_expr:
            violations.append("FORBIDDEN_TRADE_WHEN")
        if "add(" in low_expr:
            violations.append("FORBIDDEN_ADD")
        if "multiply(" in low_expr:
            violations.append("FORBIDDEN_MULTIPLY")

    for m in _LAMBDA_MAX_RE.finditer(expr):
        if float(m.group(1)) > 1.0:
            violations.append("TRAP_LAMBDA_MAX_GT_1")
            break
    for m in _TS_DECAY_RE.finditer(expr):
        if float(m.group(1)) > 252.0:
            violations.append("TRAP_TS_DECAY_GT_252")
            break

    dedup = sorted(set(violations))
    d3_ok = not any(v.startswith("FORBIDDEN_") for v in dedup)
    return d3_ok, dedup


def classify_optimization_tier(
    *,
    region: str,
    sharpe: Optional[float],
    fitness: Optional[float],
    turnover: Optional[float],
    margin: Optional[float],
    sharpe_2y: Optional[float],
    legacy_sc: Optional[float],
    is_already_os: bool,
    decision3_compliant: bool,
    violations: list[str],
    thresholds: Optional[dict[str, Any]] = None,
) -> tuple[str, str]:
    """Assign actionable optimization tier and concrete next-step hint."""
    if is_already_os:
        return "ALREADY_OS", "Already submitted to OS pool"

    if sharpe is None or sharpe < 1.20:
        return "LOW_PRIORITY", "Sharpe < 1.20 or missing"

    if legacy_sc is not None and legacy_sc >= 0.70:
        return "LOW_PRIORITY", f"Legacy SC={legacy_sc:.3f} >= 0.70 (high self-corr)"

    th = thresholds or load_d1_thresholds()
    reg_u = (region or "").upper()
    sh_min = 2.08 if reg_u == "CHN" else float(th["regular_d1"]["non_chn"]["sharpe_gt"])
    margin_floor = float(th.get("regional_margin_floor_decimal", {}).get(reg_u, 0.0010))

    gaps: list[str] = []
    if sharpe < sh_min:
        gaps.append(f"SHARPE<{sh_min:.2f}")
    if fitness is not None and fitness < 1.0:
        gaps.append("FITNESS<1.0(raise decay/truncation)")
    if turnover is not None and (turnover <= 0.01 or turnover >= 0.70):
        gaps.append(f"TO={turnover:.3f}(out of 0.01-0.70)")
    if margin is not None and margin < margin_floor:
        gaps.append(f"MARGIN<{margin_floor*10000:.1f}bp(smooth/decay)")
    if sharpe_2y is not None and sharpe_2y < 1.58:
        gaps.append("2Y_SHARPE<1.58(group_rank/ts_decay_linear)")
    if legacy_sc is not None and legacy_sc >= 0.65:
        gaps.append(f"SC={legacy_sc:.3f}(0.65-0.70 tight)")
    if "TRAP_LAMBDA_MAX_GT_1" in violations:
        gaps.append("FIX_LAMBDA_MAX<=1")
    if "TRAP_TS_DECAY_GT_252" in violations:
        gaps.append("FIX_TS_DECAY<=252")

    if not decision3_compliant:
        if sharpe >= 1.50 and (fitness is None or fitness >= 0.90) and (legacy_sc is None or legacy_sc < 0.68):
            return "TIER_B_REFACTOR_OP", "REFACTOR_DECISION3(min(rank,rank)): " + ("; ".join(gaps) if gaps else "metrics strong")
        return "TIER_C_EXPLORE_SEED", "Seed only (needs Decision #3 refactor)"

    if (
        sharpe >= sh_min
        and (fitness is None or fitness >= 1.0)
        and (turnover is None or 0.01 < turnover < 0.70)
        and (margin is None or margin >= margin_floor)
        and (sharpe_2y is None or sharpe_2y >= 1.58)
        and (legacy_sc is None or legacy_sc < 0.65)
        and not any(v.startswith("TRAP_") for v in violations)
    ):
        return "TIER_S_READY_CHECK", "READY_CHECK_SC_PC: re-verify live SC/PC/checks (zero-sim or 1-sim)"

    if sharpe >= 1.40 and (fitness is None or fitness >= 0.80) and (legacy_sc is None or legacy_sc < 0.68):
        return "TIER_A_PARAM_TUNE", "PARAM_TUNE: " + ("; ".join(gaps) if gaps else "verify missing metrics")

    return "TIER_C_EXPLORE_SEED", "SEED: " + ("; ".join(gaps) if gaps else "stage-2/3 exploration")


def load_os_alpha_ids(sc_cache_db: Path = SC_CACHE_DB_PATH) -> set[str]:
    """Read submitted OS alpha IDs from local SC cache (read-only)."""
    if not sc_cache_db.exists():
        return set()
    con = sqlite3.connect(f"file:{sc_cache_db.as_posix()}?mode=ro", uri=True)
    try:
        rows = con.execute("SELECT alpha_id FROM os_alphas").fetchall()
        return {str(r[0]) for r in rows if r and r[0]}
    except sqlite3.Error:
        return set()
    finally:
        con.close()


def merge_legacy_catalog_datasets(
    target_conn: sqlite3.Connection,
    catalog_db: Path = LEGACY_RUNTIME_DATA_DIR / "catalog.db",
) -> int:
    """Copy D1 dataset metadata from legacy catalog.db (strictly read-only) into legacy_datasets."""
    if not catalog_db.exists():
        return 0
    ensure_legacy_schema(target_conn)
    src = sqlite3.connect(f"file:{catalog_db.as_posix()}?mode=ro", uri=True)
    now = _utc_now()
    merged = 0
    try:
        tables = [
            r[0]
            for r in src.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'datasets_%'"
            ).fetchall()
        ]
        batch: list[tuple[Any, ...]] = []
        for tbl in tables:
            cols = {r[1] for r in src.execute(f'PRAGMA table_info("{tbl}")').fetchall()}
            if "id" not in cols or "region" not in cols:
                continue
            for row in src.execute(
                f'SELECT id, name, region, delay, universe, category_id, subcategory_id, '
                f'coverage, dateCoverage, valueScore, userCount, alphaCount, fieldCount, '
                f'pyramidMultiplier, dateUpdated FROM "{tbl}"'
            ):
                delay = _safe_int(row[3])
                if delay != 1:
                    continue
                reg = str(row[2] or "").upper()
                uni = str(row[4] or "").upper()
                ds_id = str(row[0] or "").strip()
                if not reg or not uni or not ds_id:
                    continue
                batch.append((
                    reg, uni, ds_id, 1,
                    row[1], row[5], row[6],
                    _safe_float(row[7]), _safe_float(row[8]), _safe_float(row[9]),
                    _safe_int(row[10]), _safe_int(row[11]), _safe_int(row[12]),
                    _safe_float(row[13]), row[14], now,
                ))
        if batch:
            target_conn.executemany(
                """
                INSERT INTO legacy_datasets (
                    region, universe, dataset_id, delay, name, category_id, subcategory_id,
                    coverage, date_coverage, value_score, user_count, alpha_count, field_count,
                    pyramid_multiplier, date_updated, merged_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(region, universe, dataset_id) DO UPDATE SET
                    name=COALESCE(excluded.name, legacy_datasets.name),
                    category_id=COALESCE(excluded.category_id, legacy_datasets.category_id),
                    subcategory_id=COALESCE(excluded.subcategory_id, legacy_datasets.subcategory_id),
                    coverage=COALESCE(excluded.coverage, legacy_datasets.coverage),
                    date_coverage=COALESCE(excluded.date_coverage, legacy_datasets.date_coverage),
                    value_score=COALESCE(excluded.value_score, legacy_datasets.value_score),
                    user_count=COALESCE(excluded.user_count, legacy_datasets.user_count),
                    alpha_count=COALESCE(excluded.alpha_count, legacy_datasets.alpha_count),
                    field_count=COALESCE(excluded.field_count, legacy_datasets.field_count),
                    pyramid_multiplier=COALESCE(excluded.pyramid_multiplier, legacy_datasets.pyramid_multiplier),
                    date_updated=COALESCE(excluded.date_updated, legacy_datasets.date_updated),
                    merged_at_utc=excluded.merged_at_utc
                """,
                batch,
            )
            target_conn.commit()
            merged = len(batch)
    finally:
        src.close()
    return merged


def _extract_record_from_jsonl_obj(obj: dict[str, Any], source_origin: str) -> Optional[dict[str, Any]]:
    """Normalize either a template_usage event or a hill_climbing_source SOURCE_STATUS event."""
    if source_origin == "hill_climbing_source":
        if obj.get("event") != "SOURCE_STATUS":
            return None
        rec = obj.get("record")
        if not isinstance(rec, dict):
            return None
        aid = rec.get("alpha_id") or obj.get("alpha_id")
        expr = rec.get("expression")
        delay = _safe_int(rec.get("delay"))
        if not aid or not expr or delay != 1:
            return None
        settings = rec.get("settings") if isinstance(rec.get("settings"), dict) else {}
        reg = (rec.get("region") or settings.get("region") or "").upper()
        if not reg:
            return None
        uni = (rec.get("universe") or settings.get("universe") or "").upper() or None
        cats = rec.get("pyramid_categories")
        cat = str(cats[0]) if isinstance(cats, list) and cats else None
        return {
            "alpha_id": str(aid),
            "source_origin": source_origin,
            "region": reg,
            "universe": uni,
            "delay": 1,
            "dataset_id": None,
            "category": cat,
            "expression": str(expr).strip(),
            "neutralization": settings.get("neutralization"),
            "decay": _safe_int(settings.get("decay")),
            "truncation": _safe_float(settings.get("truncation")),
            "settings_json": json.dumps(settings, ensure_ascii=False) if settings else None,
            "sharpe": _safe_float(rec.get("sharpe")),
            "fitness": _safe_float(rec.get("fitness")),
            "turnover": _safe_float(rec.get("turnover")),
            "margin": _safe_float(rec.get("margin")),
            "sharpe_2y": _safe_float(rec.get("sharpe_2y")),
            "legacy_sc": _safe_float(rec.get("sc_value")),
            "hard_pass": 0,
            "template_id": None,
            "source_alpha_id": None,
            "legacy_status": rec.get("status"),
            "created_at_legacy": rec.get("date_created") or rec.get("updated_at") or obj.get("time"),
        }

    # template_usage events*.jsonl
    aid = obj.get("alpha_id")
    expr = obj.get("expression")
    delay = _safe_int(obj.get("delay"))
    if not aid or not expr or delay != 1:
        return None
    reg = str(obj.get("region") or "").upper()
    if not reg:
        return None
    uni = str(obj.get("universe") or "").upper() or None
    settings_dict = {
        "region": reg,
        "universe": uni,
        "delay": 1,
        "neutralization": obj.get("neutralization"),
        "decay": _safe_int(obj.get("decay")),
    }
    return {
        "alpha_id": str(aid),
        "source_origin": source_origin,
        "region": reg,
        "universe": uni,
        "delay": 1,
        "dataset_id": obj.get("dataset_id"),
        "category": obj.get("category"),
        "expression": str(expr).strip(),
        "neutralization": obj.get("neutralization"),
        "decay": _safe_int(obj.get("decay")),
        "truncation": None,
        "settings_json": json.dumps(settings_dict, ensure_ascii=False),
        "sharpe": _safe_float(obj.get("sharpe")),
        "fitness": _safe_float(obj.get("fitness")),
        "turnover": _safe_float(obj.get("turnover")),
        "margin": _safe_float(obj.get("margin")),
        "sharpe_2y": _safe_float(obj.get("sharpe_2y")),
        "legacy_sc": _safe_float(obj.get("sc")),
        "hard_pass": 1 if obj.get("hard_pass") else 0,
        "template_id": obj.get("template_id"),
        "source_alpha_id": obj.get("source_alpha_id"),
        "legacy_status": obj.get("status"),
        "created_at_legacy": obj.get("timestamp"),
    }


def _coalesce_record(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge two records for the same alpha_id, preferring non-null metrics and richer template metadata."""
    merged = dict(existing)
    for k, v in incoming.items():
        if v is None or v == "":
            continue
        if k == "hard_pass":
            merged[k] = max(int(merged.get(k) or 0), int(v))
        elif k == "source_origin":
            # Prefer template_usage origin over hill_climbing_source when both exist (richer metadata)
            if merged.get(k) == "hill_climbing_source" and v != "hill_climbing_source":
                merged[k] = v
        elif merged.get(k) is None or merged.get(k) == "":
            merged[k] = v
        elif k in ("legacy_sc", "legacy_status", "created_at_legacy"):
            # Keep latest non-null SC / status
            merged[k] = v
    return merged


def default_legacy_jsonl_sources(runtime_dir: Path = LEGACY_RUNTIME_DATA_DIR) -> list[tuple[str, Path]]:
    return [
        ("hill_climbing_source", runtime_dir / "hill_climbing_source" / "events.jsonl"),
        ("template_usage_v1", runtime_dir / "template_usage" / "events.jsonl"),
        ("template_usage_v2", runtime_dir / "template_usage" / "events_v2.jsonl"),
        ("template_usage_v3", runtime_dir / "template_usage" / "events_v3.jsonl"),
        ("template_usage_v4", runtime_dir / "template_usage" / "events_v4.jsonl"),
    ]


def merge_all_legacy_to_v2(
    *,
    target_db: Path = LEDGER_DB_PATH,
    runtime_dir: Path = LEGACY_RUNTIME_DATA_DIR,
    sc_cache_db: Path = SC_CACHE_DB_PATH,
    jsonl_sources: Optional[list[tuple[str, Path]]] = None,
    include_catalog_datasets: bool = True,
) -> dict[str, Any]:
    """Stream-merge all legacy D1 alpha records & datasets into wq_v2_ledger.db."""
    started_at = _utc_now()
    run_id = f"legacy_merge_{uuid.uuid4().hex[:10]}"
    thresholds = load_d1_thresholds()
    os_ids = load_os_alpha_ids(sc_cache_db)

    sources = jsonl_sources if jsonl_sources is not None else default_legacy_jsonl_sources(runtime_dir)
    files_scanned: list[str] = []
    rows_scanned = 0
    by_alpha: dict[str, dict[str, Any]] = {}

    for origin, path in sources:
        if not path.exists():
            continue
        files_scanned.append(str(path))
        with path.open("r", encoding="utf-8", errors="replace") as fp:
            for line in fp:
                rows_scanned += 1
                if '"alpha_id"' not in line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                rec = _extract_record_from_jsonl_obj(obj, origin)
                if rec is None:
                    continue
                aid = rec["alpha_id"]
                if aid in by_alpha:
                    by_alpha[aid] = _coalesce_record(by_alpha[aid], rec)
                else:
                    by_alpha[aid] = rec

    target_db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_db))
    try:
        ensure_legacy_schema(conn)
        datasets_merged = (
            merge_legacy_catalog_datasets(conn, runtime_dir / "catalog.db")
            if include_catalog_datasets
            else 0
        )

        now = _utc_now()
        tier_counts: dict[str, int] = {}
        rows_to_upsert: list[tuple[Any, ...]] = []
        for aid, rec in by_alpha.items():
            d3_ok, violations = classify_expression_compliance(rec["expression"])
            is_os = aid in os_ids
            tier, hint = classify_optimization_tier(
                region=rec["region"],
                sharpe=rec["sharpe"],
                fitness=rec["fitness"],
                turnover=rec["turnover"],
                margin=rec["margin"],
                sharpe_2y=rec["sharpe_2y"],
                legacy_sc=rec["legacy_sc"],
                is_already_os=is_os,
                decision3_compliant=d3_ok,
                violations=violations,
                thresholds=thresholds,
            )
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            rows_to_upsert.append((
                aid, rec["source_origin"], rec["region"], rec["universe"], 1,
                rec["dataset_id"], rec["category"], rec["expression"],
                rec["neutralization"], rec["decay"], rec["truncation"], rec["settings_json"],
                rec["sharpe"], rec["fitness"], rec["turnover"], rec["margin"],
                rec["sharpe_2y"], rec["legacy_sc"], int(rec["hard_pass"] or 0),
                1 if is_os else 0, 1 if d3_ok else 0, json.dumps(violations),
                tier, hint, rec["template_id"], rec["source_alpha_id"],
                rec["legacy_status"], rec["created_at_legacy"], now,
            ))

        upsert_sql = """
            INSERT INTO legacy_alphas (
                alpha_id, source_origin, region, universe, delay,
                dataset_id, category, expression, neutralization, decay, truncation, settings_json,
                sharpe, fitness, turnover, margin, sharpe_2y, legacy_sc, hard_pass,
                is_already_os, decision3_compliant, violation_tags_json,
                opt_tier, opt_action_hint, template_id, source_alpha_id,
                legacy_status, created_at_legacy, merged_at_utc
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(alpha_id) DO UPDATE SET
                source_origin=excluded.source_origin,
                region=excluded.region,
                universe=COALESCE(excluded.universe, legacy_alphas.universe),
                dataset_id=COALESCE(excluded.dataset_id, legacy_alphas.dataset_id),
                category=COALESCE(excluded.category, legacy_alphas.category),
                expression=excluded.expression,
                neutralization=COALESCE(excluded.neutralization, legacy_alphas.neutralization),
                decay=COALESCE(excluded.decay, legacy_alphas.decay),
                truncation=COALESCE(excluded.truncation, legacy_alphas.truncation),
                settings_json=COALESCE(excluded.settings_json, legacy_alphas.settings_json),
                sharpe=COALESCE(excluded.sharpe, legacy_alphas.sharpe),
                fitness=COALESCE(excluded.fitness, legacy_alphas.fitness),
                turnover=COALESCE(excluded.turnover, legacy_alphas.turnover),
                margin=COALESCE(excluded.margin, legacy_alphas.margin),
                sharpe_2y=COALESCE(excluded.sharpe_2y, legacy_alphas.sharpe_2y),
                legacy_sc=COALESCE(excluded.legacy_sc, legacy_alphas.legacy_sc),
                hard_pass=MAX(legacy_alphas.hard_pass, excluded.hard_pass),
                is_already_os=excluded.is_already_os,
                decision3_compliant=excluded.decision3_compliant,
                violation_tags_json=excluded.violation_tags_json,
                opt_tier=excluded.opt_tier,
                opt_action_hint=excluded.opt_action_hint,
                template_id=COALESCE(excluded.template_id, legacy_alphas.template_id),
                source_alpha_id=COALESCE(excluded.source_alpha_id, legacy_alphas.source_alpha_id),
                legacy_status=COALESCE(excluded.legacy_status, legacy_alphas.legacy_status),
                created_at_legacy=COALESCE(excluded.created_at_legacy, legacy_alphas.created_at_legacy),
                merged_at_utc=excluded.merged_at_utc
        """
        for idx in range(0, len(rows_to_upsert), 1000):
            conn.executemany(upsert_sql, rows_to_upsert[idx : idx + 1000])
        completed_at = _utc_now()
        conn.execute(
            """
            INSERT INTO legacy_merge_runs (
                run_id, started_at_utc, completed_at_utc, files_scanned_json,
                rows_scanned, d1_unique_alphas_merged, datasets_merged, tier_counts_json, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, started_at, completed_at, json.dumps(files_scanned, ensure_ascii=False),
                rows_scanned, len(rows_to_upsert), datasets_merged,
                json.dumps(tier_counts, ensure_ascii=False),
                "Read-only streaming merge from legacy_core/Core/runtime_data (D1-Only)",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "run_id": run_id,
        "files_scanned": len(files_scanned),
        "rows_scanned": rows_scanned,
        "d1_unique_alphas_merged": len(rows_to_upsert),
        "datasets_merged": datasets_merged,
        "tier_counts": tier_counts,
        "target_db": str(target_db),
    }


def query_legacy_candidates(
    *,
    target_db: Path = LEDGER_DB_PATH,
    regions: Optional[Iterable[str]] = None,
    tiers: Optional[Iterable[str]] = None,
    min_sharpe: float = 1.40,
    max_sc: Optional[float] = 0.68,
    only_compliant: bool = False,
    exclude_os: bool = True,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Query top optimizable historical D1 alphas from wq_v2_ledger.db."""
    conn = sqlite3.connect(f"file:{target_db.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        clauses = ["delay = 1", "sharpe >= ?"]
        params: list[Any] = [min_sharpe]
        if exclude_os:
            clauses.append("is_already_os = 0")
        if only_compliant:
            clauses.append("decision3_compliant = 1")
        if max_sc is not None:
            clauses.append("(legacy_sc IS NULL OR legacy_sc <= ?)")
            params.append(max_sc)
        if regions:
            reg_list = [r.strip().upper() for r in regions if r.strip()]
            if reg_list:
                clauses.append(f"region IN ({','.join('?' for _ in reg_list)})")
                params.extend(reg_list)
        if tiers:
            tier_list = [t.strip() for t in tiers if t.strip()]
            if tier_list:
                clauses.append(f"opt_tier IN ({','.join('?' for _ in tier_list)})")
                params.extend(tier_list)
        sql = f"""
            SELECT alpha_id, region, universe, dataset_id, category, opt_tier,
                   sharpe, fitness, turnover, margin, sharpe_2y, legacy_sc,
                   decision3_compliant, violation_tags_json, opt_action_hint,
                   neutralization, decay, expression, source_origin, created_at_legacy
            FROM legacy_alphas
            WHERE {' AND '.join(clauses)}
            ORDER BY
                CASE opt_tier
                    WHEN 'TIER_S_READY_CHECK' THEN 1
                    WHEN 'TIER_A_PARAM_TUNE' THEN 2
                    WHEN 'TIER_B_REFACTOR_OP' THEN 3
                    ELSE 4
                END ASC,
                COALESCE(margin, 0) DESC,
                sharpe DESC
            LIMIT ?
        """
        params.append(limit)
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def summarize_legacy_pool(target_db: Path = LEDGER_DB_PATH) -> dict[str, Any]:
    """Return Region × Tier counts of merged historical D1 alphas."""
    conn = sqlite3.connect(f"file:{target_db.as_posix()}?mode=ro", uri=True)
    try:
        total = conn.execute("SELECT COUNT(*) FROM legacy_alphas").fetchone()[0]
        ds_total = conn.execute("SELECT COUNT(*) FROM legacy_datasets").fetchone()[0]
        by_reg_tier = conn.execute(
            """
            SELECT region, opt_tier, COUNT(*) AS cnt
            FROM legacy_alphas
            GROUP BY region, opt_tier
            ORDER BY region, cnt DESC
            """
        ).fetchall()
        breakdown: dict[str, dict[str, int]] = {}
        for reg, tier, cnt in by_reg_tier:
            breakdown.setdefault(str(reg), {})[str(tier)] = int(cnt)
        return {
            "total_legacy_d1_alphas": int(total),
            "total_legacy_d1_datasets": int(ds_total),
            "by_region_tier": breakdown,
        }
    finally:
        conn.close()
