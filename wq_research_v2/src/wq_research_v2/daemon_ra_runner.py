"""Low-memory D1-Only RA Production Runner & Incremental Scanner for Guangzhou server (1.9 GiB RAM).

Strictly enforces:
- RA-Only D1 pipeline (PPA kept completely separate to avoid complexity/confusion)
- Delay = 1 hard lock, Decision #3 (NO add/multiply/trade_when), Gold 81 operator whitelist
- Prioritizes Alphas=0 free-quota datasets (freeze 2026-12-06) across DEU (1.8x), CHN (1.9x/1.8x),
  and high-priority GLB/GBR 2->3 quick-win pyramids
- 8-item Multi-Sim packing, weighted slot concurrency (GLB=2 slots), SQLite WAL checkpoints,
  10m auth refresh + 10s reconnect, zero /submit calls
- Streaming low-memory design: processes batches sequentially/bounded-parallel and commits directly to SQLite
"""
from __future__ import annotations

import argparse
import gc
import itertools
import json
import sys
import time
from pathlib import Path
from typing import Any, Optional

from wq_research_v2.auth_session import BrainAuthSession
from wq_research_v2.blacklist_registry import BlacklistRegistry
from wq_research_v2.ledger_store import LedgerStore
from wq_research_v2.quota_tracker import QuotaTracker, current_est_platform_date
from wq_research_v2.ra_evaluator import D1RAEvaluator
from wq_research_v2.sc_local import LocalSCEngine
from wq_research_v2.sim_runner import SimRunner

# Verified clean D1 RA seed pools (ALL checked against live cnhkmcp Field Cards FLD-P1..P4)
# Strictly MATRIX / verified non-fake VECTOR fields, zero trap IDs, zero blacklisted datasets.
CURATED_RA_D1_CAMPAIGNS: list[dict[str, Any]] = [
    {
        "campaign_id": "DEU_M264_FREE",
        "region": "DEU",
        "universe": "TOP500",
        "dataset_id": "model264",
        "queue_type": "UNUSED_ALPHA0",
        "field_type": "MATRIX",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["INDUSTRY", "REVERSION_AND_MOMENTUM"],
        "fields": [
            "mdl264_1l_fmc", "mdl264_1l_ifm", "mdl264_1l_lda", "mdl264_1l_ovp",
            "mdl264_1l_icc", "mdl264_1l_ist", "mdl264_1l_ompd", "mdl264_1l_opd",
            "mdl264_1l_opp", "mdl264_1l_os", "mdl264_1l_rta", "mdl264_1l_ips",
            "mdl264_1l_od", "mdl264_1l_m1d_cer_se", "mdl264_1l_m1r_cer_se",
            "mdl264_1l_m1d_pt_se", "mdl264_1l_m1d_1yf_spd_se", "mdl264_1l_m1r_mtn_spd_se",
            "mdl264_1l_m1r_mtn_spfc_se", "mdl264_1l_m1d_gtl_se", "mdl264_1l_m1r_gtl_se",
            "mdl264_1l_m1d_1yf_van_se", "mdl264_1l_m3d_1yf_van_se", "mdl264_1l_m1r_1yf_van_se",
        ],
    },
    {
        "campaign_id": "DEU_ANL93_FREE",
        "region": "DEU",
        "universe": "TOP500",
        "dataset_id": "analyst93",
        "queue_type": "UNUSED_ALPHA0",
        "field_type": "VECTOR",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["INDUSTRY", "CROWDING"],
        "fields": [
            "anl93_profitabilityprev_analyst_profitability1_60d",
            "anl93_profitabilityprev_analyst_profitability2_60d",
            "anl93_profitabilityprev_estimator_profitability1",
            "anl93_recprofitabilityprev_analyst_profitability1",
            "anl93_recprofitabilityprev_estimator_profitability1_60d",
            "anl93_estimator_accuracy2",
            "anl93_analyst_relative_accuracy1",
            "anl93_estimator_consistency",
            "anl93_estimator_relative_consistency1",
            "anl93_estimator_correct_revision_times",
            "anl93_analyst_correct_forecast_times1",
        ],
    },
    {
        "campaign_id": "CHN_ANL45_FREE",
        "region": "CHN",
        "universe": "TOP2000U",
        "dataset_id": "analyst45",
        "queue_type": "UNUSED_ALPHA0",
        "field_type": "VECTOR",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["INDUSTRY", "REVERSION_AND_MOMENTUM"],
        "fields": [
            "risk_adjusted_performance_alpha",
            "risk_adjusted_return_treynor",
            "net_exposure_value",
            "relative_index_return_value_2",
            "mean_daily_relative_index_return_pct",
            "aggregate_return_percentage",
            "aggregate_return_excluding_fx",
            "mean_daily_return_pct",
            "aggregate_realized_unrealized_return",
            "realized_return_value",
            "riskless_investment_rate_2",
            "grouped_idea_quantity",
            "average_idea_age_period",
        ],
    },
    {
        "campaign_id": "CHN_OTH496_RATIOS_FREE",
        "region": "CHN",
        "universe": "TOP2000U",
        "dataset_id": "other496",
        "queue_type": "UNUSED_ALPHA0",
        "field_type": "CUSTOM_EXPRS",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["INDUSTRY", "CROWDING"],
        "custom_base_exprs": [
            ("oth496_curr_ratio", "divide(ts_backfill(oth496_ard_total_cur_assets_282, 126), abs(ts_backfill(oth496_ff_liabs_curr_nugget, 126)))"),
            ("oth496_pay_rec_power", "divide(ts_backfill(oth496_ard_accounts_payable_trade_333, 126), abs(ts_backfill(oth496_q_ard_accts_receivable_trade, 126)))"),
            ("oth496_lt_lev", "reverse(divide(ts_backfill(oth496_q_ard_tot_noncurrent_liabilities, 126), abs(ts_backfill(oth496_q_ard_total_noncurrent_assets, 126))))"),
            ("oth496_rec_share", "reverse(divide(ts_backfill(oth496_q_ard_accts_receivable_trade, 126), abs(ts_backfill(oth496_ard_total_cur_assets_282, 126))))"),
            ("oth496_oth_rec_risk", "reverse(divide(ts_backfill(oth496_ard_other_receivables_st, 126), abs(ts_backfill(oth496_ard_total_cur_assets_282, 126))))"),
            ("oth496_oth_pay_risk", "reverse(divide(ts_backfill(oth496_ard_other_payables_277, 126), abs(ts_backfill(oth496_ff_liabs_curr_nugget, 126))))"),
            ("oth496_asset_light", "divide(ts_backfill(oth496_ard_total_cur_assets_282, 126), abs(ts_backfill(oth496_q_ard_total_noncurrent_assets, 126)))"),
            ("oth496_tax_conserv", "divide(ts_backfill(oth496_ard_deferred_inc_tax_asset_lt_343, 126), abs(ts_backfill(oth496_ard_deferred_income_taxes_liab, 126)))"),
        ],
    },
    {
        "campaign_id": "GLB_ANL10_2TO3",
        "region": "GLB",
        "universe": "TOP3000",
        "dataset_id": "analyst10",
        "queue_type": "NORMAL",
        "field_type": "MATRIX",
        "default_neut": "REVERSION_AND_MOMENTUM",
        "alt_neuts": ["FAST", "SUBINDUSTRY"],
        "fields": [
            "anl10_entfy1_pred_surps_v1_6484",
            "anl10_entfy2_pred_surps_v1_6476",
            "anl10_fcffy1_pred_surps_v1_6437",
            "anl10_fcffy2_pred_surps_v1_6420",
            "anl10_grmfq2_pred_surps_v1_6235",
            "anl10_cpsfy2_pred_surps_v1_6286",
        ],
    },
    {
        "campaign_id": "GLB_FND44_2TO3",
        "region": "GLB",
        "universe": "TOP3000",
        "dataset_id": "fundamental44",
        "queue_type": "NORMAL",
        "field_type": "MATRIX",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["REVERSION_AND_MOMENTUM", "COUNTRY"],
        "fields": [
            "fnd44_fscore",
            "fnd44_yoon_wc_accruals",
            "fnd44_probability_restatement",
        ],
    },
    {
        "campaign_id": "DEU_OTH250_FREE",
        "region": "DEU",
        "universe": "TOP500",
        "dataset_id": "other250",
        "queue_type": "UNUSED_ALPHA0",
        "field_type": "VECTOR",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["INDUSTRY", "MARKET"],
        "fields": [
            "sales_position_rank",
            "oth250_item_review_count",
            "total_review_number",
            "oth250_item_display_price",
            "product_listed_price",
        ],
    },
    {
        "campaign_id": "DEU_FND6_RATIOS",
        "region": "DEU",
        "universe": "TOP500",
        "dataset_id": "fundamental6",
        "queue_type": "NORMAL",
        "field_type": "CUSTOM_EXPRS",
        "default_neut": "SUBINDUSTRY",
        "alt_neuts": ["INDUSTRY", "REVERSION_AND_MOMENTUM"],
        "custom_base_exprs": [
            ("fnd6_roa", "divide(ts_backfill(fnd6_ewq_ibmiiq, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"),
            ("fnd6_roe", "divide(ts_backfill(fnd6_ewq_ibmiiq, 126), abs(ts_backfill(fnd6_ewq_teqq, 126)))"),
            ("fnd6_cash_at", "divide(ts_backfill(fnd6_newq_cheq, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"),
            ("fnd6_gp_at", "divide(ts_backfill(fnd6_gpsa, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"),
            ("fnd6_cf_at", "divide(ts_backfill(fnd6_chechy, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"),
            ("fnd6_rev_at", "divide(ts_backfill(fnd6_revty, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"),
            ("fnd6_low_lev", "reverse(divide(ts_backfill(fnd6_ewq_lltq, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126))))"),
            ("fnd6_intan_low", "reverse(divide(ts_backfill(fnd6_ewq_intanq, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126))))"),
            ("fnd6_depr_capex", "divide(ts_backfill(fnd6_dpy, 126), abs(ts_backfill(fnd6_newq_ppentq, 126)))"),
            ("fnd6_eq_res", "divide(ts_backfill(fnd6_ewq_eqrtq, 126), abs(ts_backfill(fnd6_cptnewq_atq, 126)))"),
        ],
    },
]


# 8 clean 5:5 Stage-1/Stage-2 RA templates (4 ADMIN_ORIGINAL : 4 TOP100_2026Q4).
# Updated with live T0 empirical insight: pre-smoothing (ts_mean 22 / ts_decay_linear 10)
# sharply reduces noisy daily-signal turnover (e.g. model264 TO 67%->2.4%, Margin 26bp),
# paired with Guangzhou post-mortem champions (group_zscore/group_rank/group_neutralize by subindustry).
# Strictly ZERO add/multiply/trade_when, ZERO decay > 252, ZERO lambda_max > 1.
STAGE12_TEMPLATES_8: list[dict[str, str]] = [
    {"id": "RA-ADM-01-rank-m22", "side": "ADMIN_ORIGINAL", "author": "WL13229", "fmt": "rank(ts_mean({x}, 22))"},
    {"id": "RA-ADM-02-rev-rank-m22", "side": "ADMIN_ORIGINAL", "author": "WL13229", "fmt": "reverse(rank(ts_mean({x}, 22)))"},
    {"id": "RA-ADM-03-sub-grank-dec10", "side": "ADMIN_ORIGINAL", "author": "WL13229", "fmt": "group_rank(ts_decay_linear({x}, 10), subindustry)"},
    {"id": "RA-ADM-04-rev-sub-grank-z66", "side": "ADMIN_ORIGINAL", "author": "WL13229", "fmt": "reverse(group_rank(ts_zscore(ts_mean({x}, 5), 66), subindustry))"},
    {"id": "RA-TOP-01-sub-gz-m22", "side": "TOP100_2026Q4", "author": "SZ83096", "fmt": "group_zscore(ts_mean({x}, 22), subindustry)"},
    {"id": "RA-TOP-02-rev-sub-gz-m22", "side": "TOP100_2026Q4", "author": "SZ83096", "fmt": "reverse(group_zscore(ts_mean({x}, 22), subindustry))"},
    {"id": "RA-TOP-03-sp-sub-m22", "side": "TOP100_2026Q4", "author": "ZS59763", "fmt": "signed_power(group_zscore(ts_mean({x}, 22), subindustry), 1.5)"},
    {"id": "RA-TOP-04-rev-sub-tsrank66", "side": "TOP100_2026Q4", "author": "LD22811", "fmt": "reverse(group_neutralize(ts_rank(ts_decay_linear({x}, 10), 66), subindustry))"},
]


def _wrap_field(field_id: str, field_type: str, backfill_days: int = 21) -> str:
    if field_type == "VECTOR":
        return f"ts_backfill(vec_avg({field_id}), {backfill_days})"
    return f"ts_backfill({field_id}, {backfill_days})"


def build_ra_campaign_specs(
    *,
    campaigns: Optional[list[dict[str, Any]]] = None,
    include_dual_branch: bool = True,
    include_alt_neut: bool = True,
) -> list[dict[str, Any]]:
    """Build deterministic, 5:5 balanced, Decision-#3 compliant D1 RA specs (8 tasks per batch)."""
    camp_list = campaigns or CURATED_RA_D1_CAMPAIGNS
    specs: list[dict[str, Any]] = []

    for camp in camp_list:
        cid = camp["campaign_id"]
        reg = camp["region"]
        uni = camp["universe"]
        ds = camp["dataset_id"]
        qtype = camp["queue_type"]
        ftype = camp["field_type"]
        neuts = [camp["default_neut"]] + (camp.get("alt_neuts") or [] if include_alt_neut else [])

        if ftype == "CUSTOM_EXPRS":
            base_list = camp.get("custom_base_exprs") or []
            for neut in neuts:
                for name, base_expr in base_list:
                    items = [
                        {
                            "expression": t["fmt"].format(x=base_expr),
                            "template_id": f"{t['id']}_{neut}",
                            "source_side": t["side"],
                            "author_id": t["author"],
                            "dataset_id": ds,
                            "primary_field_id": name,
                        }
                        for t in STAGE12_TEMPLATES_8
                    ]
                    specs.append({
                        "batch_id": f"RA-{cid}-{name}-{neut}",
                        "hypothesis_id": f"HYP-{cid}",
                        "queue_type": qtype,
                        "source_side": "MIXED_4_4",
                        "region": reg,
                        "universe": uni,
                        "dataset_id": ds,
                        "settings": {
                            "region": reg, "universe": uni, "delay": 1,
                            "neutralization": neut, "decay": 0, "truncation": 0.04,
                            "pasteurization": "ON", "unitHandling": "VERIFY", "nanHandling": "ON",
                            "maxTrade": "OFF", "visualization": False,
                        },
                        "items": items,
                    })
            continue

        fields = camp.get("fields") or []
        for neut in neuts:
            for fid in fields:
                wrapped = _wrap_field(fid, ftype)
                items = [
                    {
                        "expression": t["fmt"].format(x=wrapped),
                        "template_id": f"{t['id']}_{neut}",
                        "source_side": t["side"],
                        "author_id": t["author"],
                        "dataset_id": ds,
                        "primary_field_id": fid,
                    }
                    for t in STAGE12_TEMPLATES_8
                ]
                specs.append({
                    "batch_id": f"RA-{cid}-{fid[:24]}-{neut}",
                    "hypothesis_id": f"HYP-{cid}",
                    "queue_type": qtype,
                    "source_side": "MIXED_4_4",
                    "region": reg,
                    "universe": uni,
                    "dataset_id": ds,
                    "settings": {
                        "region": reg, "universe": uni, "delay": 1,
                        "neutralization": neut, "decay": 0, "truncation": 0.04,
                        "pasteurization": "ON", "unitHandling": "VERIFY", "nanHandling": "ON",
                        "maxTrade": "OFF", "visualization": False,
                    },
                    "items": items,
                })

            # Decision #3 canonical dual-branch pairs (same dataset -> keeps ATOM!)
            if include_dual_branch and len(fields) >= 2:
                pair_items = []
                for f1, f2 in list(itertools.combinations(fields[:8], 2))[:8]:
                    w1 = _wrap_field(f1, ftype)
                    w2 = _wrap_field(f2, ftype)
                    expr_a = f"ts_zscore({w1}, 66)"
                    expr_b = f"ts_zscore({w2}, 66)"
                    pair_items.append({
                        "expression": f"reverse(min(rank({expr_a}), rank({expr_b})))",
                        "template_id": f"RA-DUAL-REV-MIN-{neut}",
                        "source_side": "ADMIN_ORIGINAL",
                        "author_id": "WL13229",
                        "dataset_id": ds,
                        "primary_field_id": f1,
                    })
                    pair_items.append({
                        "expression": f"min(rank({expr_a}), rank({expr_b}))",
                        "template_id": f"RA-DUAL-MIN-{neut}",
                        "source_side": "TOP100_2026Q4",
                        "author_id": "SZ83096",
                        "dataset_id": ds,
                        "primary_field_id": f1,
                    })
                for chunk_i in range(0, len(pair_items), 8):
                    sub = pair_items[chunk_i : chunk_i + 8]
                    if len(sub) >= 2:
                        specs.append({
                            "batch_id": f"RA-{cid}-DUAL-{neut}-{chunk_i//8:02d}",
                            "hypothesis_id": f"HYP-{cid}-DUAL",
                            "queue_type": qtype,
                            "source_side": "MIXED_4_4",
                            "region": reg,
                            "universe": uni,
                            "dataset_id": ds,
                            "settings": {
                                "region": reg, "universe": uni, "delay": 1,
                                "neutralization": neut, "decay": 0, "truncation": 0.04,
                                "pasteurization": "ON", "unitHandling": "VERIFY", "nanHandling": "ON",
                                "maxTrade": "OFF", "visualization": False,
                            },
                            "items": sub,
                        })

    return specs


def export_funnel_snapshot(ledger: LedgerStore, region: str) -> Path:
    """Persist non-destructive tiered funnel snapshot so zero good alphas are ever lost."""
    from wq_research_v2.config_loader import DATA_DIR

    reg = region.upper()
    rows = [
        dict(r)
        for r in ledger._conn.execute(
            """
            SELECT task_id, batch_id, dataset_id, primary_field_id, template_id, source_side,
                   alpha_id, expression, sharpe, fitness, turnover, margin, returns, sharpe_2y, status
            FROM sim_tasks
            WHERE region=? AND status IN ('COMPLETED_FULL','COMPLETED_QUICK')
            ORDER BY sharpe DESC
            """,
            (reg,),
        ).fetchall()
    ]
    pools: dict[str, list[dict[str, Any]]] = {
        "POOL_S_SH158_FIT1": [],
        "POOL_A_NEAR_SH135": [],
        "POOL_B_SEED_SH080": [],
        "POOL_FLIP_SH_LT_NEG120": [],
    }
    for r in rows:
        sh = r.get("sharpe")
        fit = r.get("fitness")
        if sh is None:
            continue
        if sh > 1.58 and (fit or 0) > 1.0:
            pools["POOL_S_SH158_FIT1"].append(r)
        elif sh >= 1.35:
            pools["POOL_A_NEAR_SH135"].append(r)
        elif sh > 0.80:
            pools["POOL_B_SEED_SH080"].append(r)
        elif sh < -1.20:
            pools["POOL_FLIP_SH_LT_NEG120"].append(r)

    out_path = DATA_DIR / "exports" / f"{reg.lower()}_ra_funnel_latest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "region": reg,
        "delay": 1,
        "total_completed": len(rows),
        "counts": {k: len(v) for k, v in pools.items()},
        "top_pool_s": pools["POOL_S_SH158_FIT1"][:50],
        "top_pool_a": pools["POOL_A_NEAR_SH135"][:50],
        "top_pool_b": pools["POOL_B_SEED_SH080"][:50],
        "top_pool_flip": pools["POOL_FLIP_SH_LT_NEG120"][:50],
    }
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def run_ra_production_loop(
    *,
    regions: Optional[list[str]] = None,
    max_slots: int = 4,
    batch_size: int = 8,
    simulation_mode: str = "FULL",
    daily_target: int = 2400,
    max_batches: Optional[int] = None,
    sleep_between_batches_sec: float = 2.0,
    only_free_alpha0: bool = False,
) -> dict[str, Any]:
    """Run low-memory D1 RA production simulation loop with wave-level multi-slot concurrency."""
    ledger = LedgerStore()
    quota = QuotaTracker(ledger)
    auth = BrainAuthSession(quota_observer=quota.observe_response)
    bl = BlacklistRegistry(ledger)
    runner = SimRunner(auth, ledger, quota, blacklist_registry=bl, max_slots=max_slots, poll_interval_sec=4.0)
    evaluator = D1RAEvaluator()

    selected_campaigns = CURATED_RA_D1_CAMPAIGNS
    if regions:
        reg_set = {r.strip().upper() for r in regions if r.strip()}
        selected_campaigns = [c for c in CURATED_RA_D1_CAMPAIGNS if c["region"].upper() in reg_set]

    specs = build_ra_campaign_specs(campaigns=selected_campaigns)
    if only_free_alpha0:
        specs = [s for s in specs if s.get("queue_type") == "UNUSED_ALPHA0"]

    # Build alpha0 map for validation
    alpha0_map: dict[str, int] = {}
    for camp in CURATED_RA_D1_CAMPAIGNS:
        if camp["queue_type"] == "UNUSED_ALPHA0":
            for f in camp.get("fields") or []:
                alpha0_map[f] = 0
            for _, expr in camp.get("custom_base_exprs") or []:
                for tok in expr.replace("(", " ").replace(")", " ").replace(",", " ").split():
                    if tok.startswith("oth496_"):
                        alpha0_map[tok] = 0

    auth.authenticate()
    auth.start_background_monitors()
    batches_executed = 0
    total_completed = 0
    gate1_hits = 0
    gate3_hits = 0

    # Group same-region specs into concurrent waves of (max_slots // weight) * batch_size tasks
    print(
        f"[RA-DAEMON] Started D1-Only RA runner | regions={regions or 'ALL'} | specs={len(specs)} | "
        f"slots={max_slots} | mode={simulation_mode} | daily_target={daily_target}",
        flush=True,
    )

    try:
        idx = 0
        while idx < len(specs):
            est_day = current_est_platform_date()
            day_stats = ledger.compute_daily_summary(est_day)
            day_done = int(day_stats.get("full_valid_completed_count", 0)) + int(day_stats.get("quick_screened_count", 0))
            if day_done >= daily_target:
                print(f"[RA-DAEMON] Daily target reached ({day_done}/{daily_target}) on EST {est_day}; sleeping 300s.", flush=True)
                if max_batches is not None:
                    break
                time.sleep(300)
                continue

            if max_batches is not None and batches_executed >= max_batches:
                break

            first = specs[idx]
            reg = first["region"]
            weight = runner.slot_weight_for_region(reg)
            wave_specs_cap = max(1, max_slots // weight)
            wave_tasks: list[dict[str, Any]] = []
            wave_batch_ids: list[str] = []

            while idx < len(specs) and len(wave_batch_ids) < wave_specs_cap and specs[idx]["region"] == reg:
                spec = specs[idx]
                idx += 1
                bid, runnable, _ = runner.prepare_batch_tasks(
                    spec,
                    simulation_mode=simulation_mode,
                    field_alpha_counts=alpha0_map if spec["queue_type"] == "UNUSED_ALPHA0" else None,
                )
                if runnable:
                    wave_tasks.extend(runnable)
                    wave_batch_ids.append(bid)

            if not wave_tasks:
                continue

            wave_id = f"WAVE-{reg}-{batches_executed + 1:04d}"
            t0 = time.monotonic()
            res = runner.run_prepared_tasks(wave_id, wave_tasks, batch_size=batch_size)
            elapsed = round(time.monotonic() - t0, 1)
            for bid in wave_batch_ids:
                ledger.update_batch_progress(bid, "DONE")

            batches_executed += len(wave_batch_ids)
            total_completed += res["completed"]

            placeholders = ",".join("?" for _ in wave_batch_ids)
            rows = ledger._conn.execute(
                f"SELECT task_id, alpha_id, dataset_id, sharpe, fitness, turnover, margin, returns, checks_json FROM sim_tasks WHERE batch_id IN ({placeholders}) AND status IN ('COMPLETED_FULL','COMPLETED_QUICK')",
                tuple(wave_batch_ids),
            ).fetchall()
            for r in rows:
                checks = json.loads(r["checks_json"]) if r["checks_json"] else []
                ev = evaluator.evaluate(
                    str(r["alpha_id"] or r["task_id"]),
                    region=reg,
                    delay=1,
                    sharpe=r["sharpe"],
                    fitness=r["fitness"],
                    turnover=r["turnover"],
                    margin=r["margin"],
                    returns=r["returns"],
                    is_checks=checks,
                )
                if ev.gate_status in ("GATE3_TIER1_PASS", "GATE4_CANDIDATE_FOR_MANUAL_REVIEW"):
                    gate3_hits += 1
                    print(
                        f"  [POOL_S GATE3_PASS!] {reg}/{r['dataset_id']} alpha={r['alpha_id']} "
                        f"Sh={r['sharpe']} Fit={r['fitness']} M={ev.margin_bp}bp",
                        flush=True,
                    )
                elif ev.gate_status in ("GATE2_IMPROVING", "GATE1_POOL_SH08"):
                    gate1_hits += 1
                    print(
                        f"  [POOL_A/B SEED] {reg}/{r['dataset_id']} alpha={r['alpha_id']} "
                        f"Sh={r['sharpe']} Fit={r['fitness']} M={ev.margin_bp}bp",
                        flush=True,
                    )

            export_funnel_snapshot(ledger, reg)
            print(
                f"[RA-DAEMON] {wave_id} ({len(wave_batch_ids)}x{batch_size} in {elapsed}s): "
                f"done={res['completed']} unobs={res['unobserved']} | day_total={day_done + res['completed']}/{daily_target} "
                f"| gate1={gate1_hits} gate3={gate3_hits}",
                flush=True,
            )
            del rows, wave_tasks
            gc.collect()
            time.sleep(sleep_between_batches_sec)

        return {
            "batches_executed": batches_executed,
            "total_completed": total_completed,
            "gate1_hits": gate1_hits,
            "gate3_hits": gate3_hits,
        }
    finally:
        auth.close()
        ledger.close()


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Low-memory D1-Only RA production simulation daemon")
    p.add_argument("--region", default="DEU", help="Comma-separated focus region(s); default DEU (single-region focus)")
    p.add_argument("--slots", type=int, default=4)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--mode", default="FULL", choices=["FULL", "QUICK"])
    p.add_argument("--daily-target", type=int, default=2400)
    p.add_argument("--max-batches", type=int, default=None)
    p.add_argument("--only-free-alpha0", action="store_true")
    p.add_argument("--loop", action="store_true", help="Continuously loop across EST platform days")
    args = p.parse_args(argv)

    reg_list = [r.strip().upper() for r in str(args.region).split(",") if r.strip()]
    while True:
        res = run_ra_production_loop(
            regions=reg_list,
            max_slots=args.slots,
            batch_size=args.batch_size,
            simulation_mode=args.mode,
            daily_target=args.daily_target,
            max_batches=args.max_batches,
            only_free_alpha0=args.only_free_alpha0,
        )
        print("[RA-DAEMON] Pass finished:", json.dumps(res), flush=True)
        if not args.loop or args.max_batches is not None:
            return 0
        time.sleep(300)


if __name__ == "__main__":
    raise SystemExit(main())
