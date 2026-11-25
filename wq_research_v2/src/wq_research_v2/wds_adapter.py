"""Thin adapter reusing legacy_core/Core/tools/webdata_quality and scripts/tools/webdata_unexploited_analytics.

Enforces D1-Only (delay=1) on WebDataScope-1.0.6/data, computes the 4 Huazi Ge Gap metrics:
1. OS/IS Sharpe gap vs region mean (+ SWEET_SPOT detection)
2. Production rate gap: osis_count / info_count
3. Neutralization crowding gap (Top-3 non-monopoly high-Sharpe neutralizations, n>=20)
4. 20-bin distribution drift (L1) + AbsRatio(0~1) + NON_DATA_DELAY1 blank-category filter
"""
from __future__ import annotations

import importlib.util
import json
import sys
import zlib
from pathlib import Path
from typing import Any, Optional

import msgpack

from wq_research_v2.config_loader import LEGACY_CORE_DIR, REPO_ROOT, WDS_DATA_DIR

WDS_QUALITY_DIR = LEGACY_CORE_DIR / "tools" / "webdata_quality"
UNEXPLOITED_ANALYTICS_PATH = REPO_ROOT / "scripts" / "tools" / "webdata_unexploited_analytics.py"


def _load_module(name: str, path: Path) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {name} from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _ensure_wds_quality_path() -> None:
    s = str(WDS_QUALITY_DIR)
    if s not in sys.path:
        sys.path.insert(0, s)


def load_wds_bin(path: Path) -> Any:
    return msgpack.unpackb(zlib.decompress(path.read_bytes()), raw=False, strict_map_key=False)


def build_d1_wds_ledger(
    source_dir: Path = WDS_DATA_DIR,
    regions: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Reuse legacy webdata_quality.build_ledger() strictly locked to delay=1."""
    _ensure_wds_quality_path()
    wq_mod = _load_module("_wds_quality_mod", WDS_QUALITY_DIR / "webdata_quality.py")
    reg_set = {r.upper() for r in regions} if regions else None
    filters = {
        "regions": reg_set,
        "delays": {1},
        "universes": None,
        "categories": None,
        "dataset_grades": None,
        "field_tiers": None,
        "neutralizations": None,
        "count_min": None,
        "count_max": None,
        "sharpe_min": None,
        "fitness_min": None,
        "dataset": None,
    }
    rules = wq_mod.load_rules(str(WDS_QUALITY_DIR / "tier_rules.json"))
    try:
        with wq_mod.resolve_source(str(source_dir), WDS_QUALITY_DIR) as source:
            return wq_mod.build_ledger(source, rules, filters)
    except ValueError as exc:
        if "没有匹配的 Region/Delay" in str(exc):
            return {"exact_fields": [], "datasets": [], "coordinates": []}
        raise


def load_osis_d1_map(source_dir: Path = WDS_DATA_DIR) -> dict[str, dict[str, Any]]:
    """Load oth/osis_data.bin strictly keeping *_1 (D1) shards."""
    osis_path = Path(source_dir) / "oth" / "osis_data.bin"
    if not osis_path.exists():
        return {}
    raw = load_wds_bin(osis_path)
    if not isinstance(raw, dict):
        return {}
    return {k: v for k, v in raw.items() if str(k).endswith("_1")}


def load_info_d1_map(source_dir: Path = WDS_DATA_DIR) -> dict[str, dict[str, Any]]:
    """Load oth/info_data.bin strictly keeping *_1 (D1) shards."""
    info_path = Path(source_dir) / "oth" / "info_data.bin"
    if not info_path.exists():
        return {}
    raw = load_wds_bin(info_path)
    if not isinstance(raw, dict):
        return {}
    return {k: v for k, v in raw.items() if str(k).endswith("_1")}


def check_d1_category_validity(region: str, category: str) -> tuple[bool, str]:
    """Reuse scripts/tools/webdata_unexploited_analytics.py NON_DATA_DELAY1 matrix."""
    if UNEXPLOITED_ANALYTICS_PATH.exists():
        mod = _load_module("_wds_unexploited_mod", UNEXPLOITED_ANALYTICS_PATH)
        ok, reason = mod.check_category_validity(region.upper(), category.lower(), delay=1)
        return bool(ok), str(reason)
    return True, "OK"


def compute_distribution_drift(field_payload: dict[str, Any]) -> dict[str, Any]:
    """Compute 20-bin L1 drift and AbsRatio(0~1) from a single .bin field entry."""
    abs01 = field_payload.get("absValueBetween1and0ratio") or []
    valid_abs = [float(x) for x in abs01 if isinstance(x, (int, float))]
    abs01_mean = round(sum(valid_abs) / len(valid_abs), 4) if valid_abs else None

    drift_info: dict[str, Any] = {
        "distribution_drift": None,
        "regime_shift_risk": "UNKNOWN",
        "zero_inflation_ratio": None,
        "abs01_ratio": abs01_mean,
    }
    if UNEXPLOITED_ANALYTICS_PATH.exists():
        mod = _load_module("_wds_unexploited_mod", UNEXPLOITED_ANALYTICS_PATH)
        yd = field_payload.get("yearly_distribution")
        if yd:
            res = mod.analyze_field_yearly_distribution(yd)
            if isinstance(res, dict):
                drift_info["distribution_drift"] = res.get("distribution_drift")
                drift_info["regime_shift_risk"] = res.get("regime_shift_risk", "UNKNOWN")
                drift_info["zero_inflation_ratio"] = res.get("zero_inflation_ratio")
    return drift_info


def extract_top_neutralizations(
    neut_map: dict[str, Any],
    *,
    min_count: int = 20,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Find top non-monopoly neutralizations with highest Sharpe and n >= min_count."""
    if not isinstance(neut_map, dict):
        return []
    total = sum(int((v or {}).get("count", 0)) for v in neut_map.values() if isinstance(v, dict))
    candidates = []
    for name, stats in neut_map.items():
        if not isinstance(stats, dict):
            continue
        cnt = int(stats.get("count", 0))
        sh = stats.get("sharpe_ratio")
        if cnt >= min_count and isinstance(sh, (int, float)):
            share = (cnt / total) if total > 0 else 0.0
            candidates.append({
                "neutralization": str(name).upper(),
                "count": cnt,
                "share": round(share, 4),
                "sharpe_ratio": round(float(sh), 4),
                "fitness_ratio": round(float(stats.get("fitness_ratio") or 0.0), 4),
            })
    candidates.sort(key=lambda x: (-x["sharpe_ratio"], x["share"]))
    return candidates[:top_k]


def compute_region_d1_gaps(
    region: str,
    *,
    source_dir: Path = WDS_DATA_DIR,
) -> dict[str, Any]:
    """Compute Huazi Ge's 4 gap metrics for all datasets in a D1 region shard.

    Explicitly marks GBR/DEU (absent in WebDataScope-1.0.6/data) with
    WEBDATA_SKIP_REASON = REGION_NOT_IN_SNAPSHOT.
    """
    reg = region.upper()
    shard_key = f"{reg}_1"
    info_map = load_info_d1_map(source_dir)
    osis_map = load_osis_d1_map(source_dir)

    if shard_key not in info_map:
        return {
            "region": reg,
            "delay": 1,
            "status": "REGION_NOT_IN_SNAPSHOT",
            "skip_reason": "REGION_NOT_IN_SNAPSHOT",
            "fallback_prior_region": "EUR" if reg in ("GBR", "DEU") else None,
            "datasets": [],
        }

    shard = info_map[shard_key]
    isos = shard.get("isos") or {}
    mean_stats = isos.get("mean") or {}
    mean_sh = float(mean_stats.get("sharpe_ratio") or 0.0)
    mean_fit = float(mean_stats.get("fitness_ratio") or 0.0)
    ds_isos = isos.get("dataset") or {}
    ds_neut = (shard.get("neutralization") or {}).get("dataset") or {}
    osis_ds = ((osis_map.get(shard_key) or {}).get("dataset")) or {}

    rows = []
    for ds_id, st in ds_isos.items():
        if not isinstance(st, dict):
            continue
        cnt = int(st.get("count") or 0)
        sh = float(st.get("sharpe_ratio") or 0.0)
        fit = float(st.get("fitness_ratio") or 0.0)
        osis_entry = osis_ds.get(ds_id) or {}
        osis_cnt = int(osis_entry.get("count") or 0) if isinstance(osis_entry, dict) else 0
        prod_rate = round(osis_cnt / cnt, 4) if cnt > 0 else 0.0
        sh_gap = round(sh - mean_sh, 4)
        is_sweet = (100 <= cnt <= 3000) and (sh >= 1.1 * mean_sh)
        is_blue_ocean = (sh_gap > 0) and (prod_rate < 0.10) and (cnt >= 50)
        grade = "RED" if sh < 0 else ("GREEN" if sh > mean_sh else "YELLOW")

        rows.append({
            "dataset_id": ds_id,
            "region": reg,
            "delay": 1,
            "dataset_grade": grade,
            "info_count": cnt,
            "osis_count": osis_cnt,
            "production_rate": prod_rate,
            "sharpe_ratio": round(sh, 4),
            "fitness_ratio": round(fit, 4),
            "sharpe_gap_vs_mean": sh_gap,
            "is_sweet_spot": is_sweet,
            "is_blue_ocean": is_blue_ocean,
            "recommended_neutralizations": extract_top_neutralizations(ds_neut.get(ds_id) or {}),
        })

    rows.sort(
        key=lambda r: (
            not r["is_blue_ocean"],
            not r["is_sweet_spot"],
            -r["sharpe_gap_vs_mean"],
            r["production_rate"],
        )
    )
    return {
        "region": reg,
        "delay": 1,
        "status": "OK",
        "window": [shard.get("sub_beg_time"), shard.get("sub_end_time")],
        "region_mean_sharpe": round(mean_sh, 4),
        "region_mean_fitness": round(mean_fit, 4),
        "dataset_count": len(rows),
        "datasets": rows,
    }
