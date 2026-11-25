"""Stage-0 D1 Field Screener combining WebDataScope-1.0.6/data, Huazi Ge 4 gaps,
Admin WL13229/KH94146 recommendations, JX79797/JX14975 blacklists, KZ79256 30% Fundamental cap,
and live Alphas=0 (freeze 2026-12-06) / dateCoverage>=0.60 / fake-VECTOR checks.
"""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from typing import Any, Optional

from wq_research_v2.config_loader import DATA_DIR, WDS_DATA_DIR, load_operators_config
from wq_research_v2.wds_adapter import (
    build_d1_wds_ledger,
    check_d1_category_validity,
    compute_region_d1_gaps,
)

# Verified Admin WL13229/KH94146 & y56zvK7 D1 dataset seed recommendations
ADMIN_D1_RECOMMENDED_SEEDS: dict[str, set[str]] = {
    "GLB": {"analyst4", "analyst10", "analyst11", "analyst14", "analyst15", "fundamental23", "global_seasonal_model", "insider_agg_matrix"},
    "ASI": {"ai_news_scores", "model207", "price_signal_dl", "behavioral_signals", "model307", "mmp_nlp_sentiment", "sentiment7", "fundamental4", "news85", "corporate_news_index"},
    "CHN": {"other496", "analyst45"},
    "DEU": {"model264", "analyst93", "other250", "other455", "fundamental6", "fundamental89", "fundamental93", "fundamental72"},
    "GBR": {"dl_riskfree_returns", "other250", "other455", "other47", "other696"},
    "USA": {"news18", "news54", "socialmedia12", "analyst10", "fundamental23", "pattern_scores", "sentiment33"},
    "EUR": {"analyst10", "fundamental23", "sentiment21"},
}

REGION_MAX_D1_UNIVERSE: dict[str, str] = {
    "USA": "TOP3000",
    "GLB": "TOP3000",
    "EUR": "TOP2500",
    "ASI": "MINVOL1M",
    "CHN": "TOP2000U",
    "DEU": "TOP500",
    "GBR": "TOP700",
    "IND": "TOP500",
    "AMR": "TOP600",
    "HKG": "TOP800",
    "KOR": "TOP600",
}

PYRAMID_GOAL_MAP: dict[str, str] = {
    "GLB": "GLB_2to3",
    "GBR": "GBR_2to3",
    "DEU": "DEU_BLANK_1.8X",
    "ASI": "ASI_BLANK_THEME_DEC20",
    "CHN": "CHN_BLANK_1.9X",
    "EUR": "EUR_EXPANSION",
    "USA": "USA_EXPANSION",
}


def is_fake_single_vector_probe(vec_avg_sharpe: float, vec_max_sharpe: float, tol: float = 0.02) -> bool:
    """JX14975 #100 rule: if vec_avg vs vec_max differ by < 2%, mark as fake single-value VECTOR."""
    denom = max(abs(vec_avg_sharpe), abs(vec_max_sharpe), 1e-6)
    return abs(vec_avg_sharpe - vec_max_sharpe) / denom < tol


class FieldScreener:
    """Stage-0 D1-Only field & dataset ranking pipeline."""

    def __init__(self, wds_data_dir: Path = WDS_DATA_DIR) -> None:
        self.wds_data_dir = Path(wds_data_dir)
        self.ops_cfg = load_operators_config()
        self.global_bl = set(self.ops_cfg["blacklisted_datasets"]["global_jx79797"])
        self.recent_2y_bl = {
            k.upper(): set(v)
            for k, v in self.ops_cfg["blacklisted_datasets"]["recent_2y_missing_jx14975"].items()
        }
        self.known_fake_vec = set(self.ops_cfg["known_fake_vector_datasets"])
        self.trap_patterns = [re.compile(p, re.I) for p in self.ops_cfg["trap_field_patterns"]]

    def is_dataset_blacklisted(self, region: str, dataset_id: str) -> tuple[bool, str]:
        reg = region.upper()
        if dataset_id in self.global_bl:
            return True, "JX79797_GLOBAL_BLACKLIST"
        if dataset_id in self.recent_2y_bl.get(reg, set()):
            return True, f"JX14975_2Y_MISSING_{reg}"
        return False, ""

    def is_trap_field(self, field_id: str) -> bool:
        return any(p.match(field_id) for p in self.trap_patterns)

    def check_fundamental_quota_cap(
        self,
        region_total_os: int,
        region_fundamental_os: int,
    ) -> tuple[bool, str]:
        """KZ79256 (30840996648983): if total OS > 50, keep Fundamental <= 30% (warn at >= 28%)."""
        if region_total_os <= 50:
            return True, "OK_UNDER_50_TOTAL"
        ratio = region_fundamental_os / max(region_total_os, 1)
        if ratio >= 0.28:
            return False, f"KZ79256_FUNDAMENTAL_CAP_WARNING ({ratio:.1%} >= 28%)"
        return True, f"OK ({ratio:.1%})"

    def screen_regions_offline(
        self,
        regions: list[str],
        *,
        top_datasets_per_region: int = 20,
        include_exact_bin_tiers: bool = True,
    ) -> dict[str, Any]:
        """Run complete Stage-0 D1 screening strictly from WebDataScope-1.0.6/data + Admin seeds + blacklists."""
        regs = [r.upper() for r in regions]
        exact_ledger = (
            build_d1_wds_ledger(self.wds_data_dir, regions=regs)
            if include_exact_bin_tiers and self.wds_data_dir.exists()
            else {}
        )
        exact_by_ds: dict[tuple[str, str], dict[str, Any]] = {}
        for item in (exact_ledger.get("exact_fields") or []):
            if not isinstance(item, dict):
                continue
            ds_name = str(item.get("dataset") or item.get("dataset_id") or "")
            fld_name = str(item.get("field") or item.get("field_id") or "")
            key = (str(item.get("region", "")).upper(), ds_name)
            bucket = exact_by_ds.setdefault(key, {"t1_count": 0, "t2_count": 0, "sample_t1_fields": []})
            tier = str(item.get("field_tier", "")).upper()
            if tier == "T1":
                bucket["t1_count"] += 1
                if fld_name and len(bucket["sample_t1_fields"]) < 5:
                    bucket["sample_t1_fields"].append(fld_name)
            elif tier == "T2":
                bucket["t2_count"] += 1

        results: dict[str, Any] = {
            "schema_version": "stage0_d1_queue_v1",
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "delay_locked": 1,
            "alphas_zero_freeze_expiry": "2026-12-06",
            "snapshot_source": str(self.wds_data_dir),
            "regions": {},
            "ranked_datasets": [],
        }

        for reg in regs:
            gap_info = compute_region_d1_gaps(reg, source_dir=self.wds_data_dir)
            admin_seeds = ADMIN_D1_RECOMMENDED_SEEDS.get(reg, set())
            if gap_info["status"] == "REGION_NOT_IN_SNAPSHOT":
                # Emit explicit live-API fallback items for GBR / DEU
                fallback_rows = []
                for ds_id in sorted(admin_seeds):
                    bl, bl_reason = self.is_dataset_blacklisted(reg, ds_id)
                    if bl:
                        continue
                    row = {
                        "priority_tier": "P0",
                        "pyramid_goal": PYRAMID_GOAL_MAP.get(reg, f"{reg}_D1"),
                        "region": reg,
                        "delay": 1,
                        "universe": REGION_MAX_D1_UNIVERSE.get(reg, "TOP500"),
                        "dataset_id": ds_id,
                        "sources_matched": ["ADMIN_OR_LIVE_FIELD_CARD", "LIVE_API_REQUIRED"],
                        "wds_prior": {
                            "status": "REGION_NOT_IN_SNAPSHOT",
                            "fallback_prior_region": gap_info.get("fallback_prior_region"),
                        },
                        "known_fake_vector_dataset": ds_id in self.known_fake_vec,
                    }
                    fallback_rows.append(row)
                    results["ranked_datasets"].append(row)
                results["regions"][reg] = {
                    "status": "REGION_NOT_IN_SNAPSHOT",
                    "note": "Use live cnhkmcp + FLD-P1/P2 cards; EUR_1 only as weak structural prior.",
                    "selected_count": len(fallback_rows),
                    "datasets": fallback_rows,
                }
                continue

            selected = []
            blocked_count = 0
            for ds in gap_info["datasets"]:
                ds_id = ds["dataset_id"]
                bl, _ = self.is_dataset_blacklisted(reg, ds_id)
                if bl:
                    blocked_count += 1
                    continue
                if ds["dataset_grade"] == "RED":
                    continue
                ex = exact_by_ds.get((reg, ds_id), {})
                sources = []
                if ds["is_blue_ocean"]:
                    sources.append("WDS_BLUE_OCEAN_GAP")
                if ds["is_sweet_spot"]:
                    sources.append("WDS_SWEET_SPOT")
                if ds_id in admin_seeds:
                    sources.append("ADMIN_RECOMMENDED_SEED")
                if ex.get("t1_count", 0) > 0:
                    sources.append("WDS_EXACT_BIN_T1")
                if not sources and ds["dataset_grade"] == "GREEN":
                    sources.append("WDS_GREEN_ABOVE_MEAN")
                if not sources:
                    continue

                prio = (
                    "P0"
                    if len(sources) >= 2
                    else (
                        "P1"
                        if (ds["is_blue_ocean"] or ds["is_sweet_spot"] or ds_id in admin_seeds or ex.get("t1_count", 0) > 0)
                        else "P2"
                    )
                )
                row = {
                    "priority_tier": prio,
                    "pyramid_goal": PYRAMID_GOAL_MAP.get(reg, f"{reg}_D1"),
                    "region": reg,
                    "delay": 1,
                    "universe": REGION_MAX_D1_UNIVERSE.get(reg, "TOP3000"),
                    "dataset_id": ds_id,
                    "sources_matched": sources,
                    "wds_prior": {
                        "status": "OK",
                        "dataset_grade": ds["dataset_grade"],
                        "info_count": ds["info_count"],
                        "osis_count": ds["osis_count"],
                        "production_rate": ds["production_rate"],
                        "sharpe_ratio": ds["sharpe_ratio"],
                        "sharpe_gap_vs_mean": ds["sharpe_gap_vs_mean"],
                        "is_sweet_spot": ds["is_sweet_spot"],
                        "is_blue_ocean": ds["is_blue_ocean"],
                        "recommended_neutralizations": ds["recommended_neutralizations"],
                        "exact_bin_t1_count": ex.get("t1_count", 0),
                        "exact_bin_t2_count": ex.get("t2_count", 0),
                        "sample_t1_fields": ex.get("sample_t1_fields", []),
                    },
                    "known_fake_vector_dataset": ds_id in self.known_fake_vec,
                }
                selected.append(row)

            # Also include Admin seeds not seen in Feb-2026 WDS snapshot (e.g., newer datasets like other496/ai_news_scores)
            seen_ds = {r["dataset_id"] for r in selected}
            for ds_id in sorted(admin_seeds - seen_ds):
                bl, _ = self.is_dataset_blacklisted(reg, ds_id)
                if bl:
                    continue
                selected.append({
                    "priority_tier": "P0",
                    "pyramid_goal": PYRAMID_GOAL_MAP.get(reg, f"{reg}_D1"),
                    "region": reg,
                    "delay": 1,
                    "universe": REGION_MAX_D1_UNIVERSE.get(reg, "TOP3000"),
                    "dataset_id": ds_id,
                    "sources_matched": ["ADMIN_RECOMMENDED_SEED", "NEWER_THAN_WDS_SNAPSHOT"],
                    "wds_prior": {"status": "NOT_IN_FEB2026_SNAPSHOT"},
                    "known_fake_vector_dataset": ds_id in self.known_fake_vec,
                })

            prio_order = {"P0": 0, "P1": 1, "P2": 2}
            selected.sort(
                key=lambda r: (
                    prio_order.get(r["priority_tier"], 9),
                    -(r["wds_prior"].get("sharpe_gap_vs_mean") or 0.0),
                    r["wds_prior"].get("production_rate", 1.0),
                )
            )
            top_sel = selected[:top_datasets_per_region]
            results["regions"][reg] = {
                "status": "OK",
                "window": gap_info.get("window"),
                "region_mean_sharpe": gap_info.get("region_mean_sharpe"),
                "region_mean_fitness": gap_info.get("region_mean_fitness"),
                "blacklisted_filtered": blocked_count,
                "selected_count": len(top_sel),
                "datasets": top_sel,
            }
            results["ranked_datasets"].extend(top_sel)

        return results

    def validate_live_field(
        self,
        field_meta: dict[str, Any],
        *,
        min_matrix_date_coverage: float = 0.60,
    ) -> tuple[bool, str]:
        """Apply JX14975 dateCoverage gate & trap field guard to live /datafields metadata."""
        fid = str(field_meta.get("id") or "")
        if self.is_trap_field(fid):
            return False, "TRAP_NON_NUMERIC_FIELD"
        ftype = str(field_meta.get("type") or "").upper()
        dcov = field_meta.get("dateCoverage")
        if ftype == "MATRIX" and isinstance(dcov, (int, float)) and dcov < min_matrix_date_coverage:
            return False, f"LOW_DATE_COVERAGE ({dcov:.2f} < {min_matrix_date_coverage:.2f})"
        return True, "OK"

    def export_queue(self, screened: dict[str, Any], out_path: Optional[Path] = None) -> Path:
        target = out_path or (DATA_DIR / "exports" / "stage0_d1_queue_v1.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(screened, indent=2, ensure_ascii=False), encoding="utf-8")
        return target
