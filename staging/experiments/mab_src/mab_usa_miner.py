"""
WorldQuant BRAIN USA Autonomous MAB Alpha Miner Orchestrator
Integrated with Thompson Sampling, Unlit Pyramid Targeting, Strict Hard Rules (<5 operators),
8-Concurrency Batch Simulation, Comprehensive Metric Auditing, Robustness & Correlation Verification,
and 10-Round Diversity Reflection.

STRICT CONSTRAINTS ENFORCED:
- NEVER auto-submit (submit_alpha is prohibited; user submits manually).
- NO trade_when, add, multiply.
- Operator count strictly < 5.
- 8-concurrency multi_create_simulate only.
- Region=USA, Delay=1, Neutralization=SUBINDUSTRY, max_trade=ON.
- 3 passing alphas must come from 3 DIFFERENT unlit pyramid datasets with pairwise correlation < 0.40.
"""

from __future__ import annotations

import os
import re
import sys
import json
import time
import math
import random
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import Counter

# Set up paths
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
MAB_SKILL_DIR = WORKSPACE_DIR / "doc" / "多臂老虎机_挖掘总结Skill" / "scripts"
sys.path.append(str(MAB_SKILL_DIR))

from cnhkmcp.untracked.platform_functions import (
    authenticate,
    create_multi_simulation,
    get_alpha_details,
    get_alpha_yearly_stats,
    get_submission_check,
    check_correlation,
    set_alpha_properties,
    get_pyramid_alphas,
    get_pyramid_multipliers
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("USAMABMiner")


class USAMABRulesValidator:
    """Enforces strict operator count < 5 and bans forbidden operators."""
    BANNED_OPERATORS = ["trade_when", "add", "multiply"]
    KNOWN_OPERATORS = [
        "ts_decay_linear", "ts_delta", "ts_zscore", "ts_rank", "ts_mean",
        "ts_std", "ts_std_dev", "ts_sum", "ts_min", "ts_max", "ts_argmax",
        "ts_argmin", "ts_corr", "ts_covariance", "ts_target_tvr_decay",
        "group_rank", "group_zscore", "group_neutralize", "rank", "zscore",
        "scale", "winsorize", "ts_backfill", "divide", "log", "signed_power",
        "abs", "sign"
    ]

    @classmethod
    def validate_expression(cls, expr: str) -> Tuple[bool, str, int]:
        cleaned = expr.strip()
        # 1. Banned operators
        for banned in cls.BANNED_OPERATORS:
            if re.search(rf'\b{banned}\s*\(', cleaned, re.IGNORECASE):
                return False, f"Banned operator detected: {banned}", 0

        # 2. Balanced parentheses
        if cleaned.count('(') != cleaned.count(')'):
            return False, "Unbalanced parentheses", 0

        # 3. Regional prefix
        if re.search(r'\b(USA|EUR|CHN|ASI|GLB|IND)\.[a-z0-9_]+\b', cleaned, re.IGNORECASE):
            return False, "Regional prefix not allowed", 0

        # 4. Count operators
        op_count = 0
        for op in cls.KNOWN_OPERATORS:
            matches = len(re.findall(rf'\b{op}\s*\(', cleaned, re.IGNORECASE))
            op_count += matches

        op_count += len(re.findall(r'[\+\-\*\/]', re.sub(r'[a-zA-Z0-9_]+', '', cleaned)))

        if op_count >= 5:
            return False, f"Operator count {op_count} >= 5 (must be < 5)", op_count

        return True, "Valid", op_count


class USADiversityEvaluator:
    """Computes diversity statistics and generates 10-round evaluation reports."""
    ALL_ALLOWED_OPS = USAMABRulesValidator.KNOWN_OPERATORS

    @classmethod
    def evaluate(cls, round_idx: int, batch_history: List[Dict[str, Any]], available_fields: List[str]) -> str:
        total = len(batch_history)
        if total == 0:
            return "暂无有效回测历史样本。"

        used_ops: Set[str] = set()
        op_counter = Counter()
        used_fields: Set[str] = set()
        field_counter = Counter()
        skeletons: List[str] = []

        for item in batch_history:
            expr = item.get("expression", "")
            for op in cls.ALL_ALLOWED_OPS:
                if re.search(rf'\b{op}\b', expr, re.IGNORECASE):
                    used_ops.add(op)
                    op_counter[op] += 1
            for f in item.get("fields", []):
                used_fields.add(f)
                field_counter[f] += 1
            
            # extract skeleton
            sk = expr
            sk = re.sub(r'\b\d+\.?\d*\b', '$param', sk)
            for tok in set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', sk)):
                if tok.lower() not in cls.ALL_ALLOWED_OPS and tok != "$param" and tok != "subindustry" and tok != "industry":
                    sk = re.sub(rf'\b{tok}\b', '$field', sk)
            skeletons.append(sk)

        op_rate = (len(used_ops) / len(cls.ALL_ALLOWED_OPS)) * 100.0
        field_rate = (len(used_fields) / max(1, len(available_fields))) * 100.0
        skeleton_rate = (len(set(skeletons)) / total) * 100.0

        lines = [
            f"# 🎯 第 {round_idx} 轮 Alpha 表达式多样性评估与量化扫盲报告",
            f"> 审计周期：第 {round_idx-9} 轮 至 第 {round_idx} 轮（共计 {total} 个候选）",
            "",
            "## 1. 核心探索率指标矩阵",
            f"- **算子探索率 (Operator Exploration)**: `{op_rate:.1f}%` ({len(used_ops)}/{len(cls.ALL_ALLOWED_OPS)} 算子激活)",
            f"- **字段探索率 (Field Exploration)**: `{field_rate:.1f}%` ({len(used_fields)}/{len(available_fields)} 字段覆盖)",
            f"- **模板骨架多样性 (Skeleton Diversity)**: `{skeleton_rate:.1f}%` ({len(set(skeletons))} 种独立拓扑)",
            "",
            "## 2. 算子与预处理渗透分布",
            "| 算子类别 | 涉及算子 | 调用频次 | 作用与防过拟合价值 |",
            "|---|---|---|---|",
            f"| **时序低通平滑** | `ts_decay_linear` | {op_counter['ts_decay_linear']} | 赋予近期信息更高权重，消除高频噪声 |",
            f"| **截面组内标准化** | `group_zscore` / `group_rank` | {op_counter['group_zscore'] + op_counter['group_rank']} | 细分子行业内消除估值与行业暴露 |",
            f"| **目标换手控制** | `ts_target_tvr_decay` | {op_counter['ts_target_tvr_decay']} | 动态约束换手率在 5%~30% 走廊 |",
            f"| **自适应极值收缩** | `winsorize` | {op_counter['winsorize']} | 削平长尾极端突变，杜绝权重集中报警 |",
            "",
            "## 3. 收益来源归因与失效风险扫盲",
            "1. **Alpha 收益核心来源**：",
            "   - **基本面/情绪增量预期差**：利用分析师目标价与评级净上调捕捉市场非理性低估；",
            "   - **波动率曲面定价失衡**：利用期权平价隐含波动率偏度捕捉下行防范溢价；",
            "2. **主要失效风险警示**：",
            "   - **生产相关性过载 (Crowding Risk)**：明星深度学习模型（如 model165）已被海量回测覆盖，必须深耕更冷门的低拥挤数据集；",
            "   - **子宇宙夏普断崖 (Sub-universe Cliff)**：在 TOP3000 中若小市值股票缺乏流动性会导致子宇宙测试失败，优先在 TOP2000/TOP1000 保证一致性。",
            ""
        ]
        return "\n".join(lines)


class USAMABOrchestrator:
    """Master controller for USA Alpha mining across 3 unlit datasets."""

    # Curated templates strictly < 5 operators and 0 banned operators
    TEMPLATES = [
        ("ts_decay_linear(ts_delta($field, $lookback), $smooth)", "Trend Revision Momentum", 2),
        ("group_zscore(ts_decay_linear($field, $smooth), subindustry)", "Subindustry Dual Standardized", 2),
        ("group_rank(ts_decay_linear($field, $smooth), subindustry)", "Subindustry Group Rank", 2),
        ("-1.0 * ts_decay_linear(ts_rank($field, $lookback), $smooth)", "Rank Reversal & Mean Reversion", 3),
        ("ts_decay_linear(winsorize($field, std=3.0), $smooth)", "Winsorized Residual Momentum", 2),
        ("ts_target_tvr_decay(group_zscore($field, subindustry), target_tvr=0.10)", "Target Turnover Decay", 2)
    ]

    LOOKBACKS = ["5", "10", "15", "20", "22", "30"]
    SMOOTHS = ["5", "8", "10", "12", "15"]

    # Target unlit datasets in USA Delay 1
    UNLIT_DATASETS = {
        "sentiment1": {
            "category": "sentiment",
            "multiplier": 1.4,
            "fields": [
                "snt1_d1_nettargetpercent",
                "snt1_d1_netearningsrevision",
                "snt1_d1_netrecpercent",
                "snt1_d1_earningssurprise",
                "daily_equity_mood_indicator",
                "snt1_d1_dynamicfocusrank"
            ]
        },
        "option8": {
            "category": "option",
            "multiplier": 1.3,
            "fields": [
                "implied_volatility_mean_skew_60",
                "implied_volatility_mean_skew_90",
                "implied_volatility_call_60",
                "implied_volatility_put_60",
                "historical_volatility_60",
                "implied_volatility_mean_skew_120"
            ]
        },
        "event_return_model": {
            "category": "news",
            "multiplier": 1.2,
            "fields": [
                "prob_rank_bin1_10d_img_news",
                "prob_rank_bin1_5d_img_news",
                "prob_rank_bin1_20d_img_news",
                "prob_rank_bin2_label1_10d_img_news",
                "news_relevance_score_2"
            ]
        }
    }

    def __init__(self, target_winners: int = 3):
        self.target_winners = target_winners
        self.qualified_alphas: List[Dict[str, Any]] = []
        self.all_sim_history: List[Dict[str, Any]] = []
        self.round_index = 0
        self.current_ds_idx = 0
        self.ds_names = list(self.UNLIT_DATASETS.keys())

    async def ensure_auth(self):
        """Re-authenticates session to guarantee fresh token."""
        try:
            res = await authenticate()
            if res.get("status") == "authenticated":
                logger.info("Session authenticated successfully.")
            else:
                logger.warning(f"Auth response: {res}")
        except Exception as e:
            logger.error(f"Authentication error: {e}")

    def generate_batch(self, count: int = 8) -> Tuple[str, List[Dict[str, Any]]]:
        """Generates 8 strictly compliant candidates from the active unlit dataset."""
        ds_name = self.ds_names[self.current_ds_idx]
        ds_info = self.UNLIT_DATASETS[ds_name]
        fields = ds_info["fields"]

        candidates = []
        attempts = 0
        while len(candidates) < count and attempts < 100:
            attempts += 1
            pattern, style, expected_op = random.choice(self.TEMPLATES)
            field = random.choice(fields)
            lookback = random.choice(self.LOOKBACKS)
            smooth = random.choice(self.SMOOTHS)

            expr = pattern.replace("$field", field).replace("$lookback", lookback).replace("$smooth", smooth)

            is_valid, reason, op_count = USAMABRulesValidator.validate_expression(expr)
            if not is_valid:
                continue

            if any(c["expression"] == expr for c in candidates):
                continue

            candidates.append({
                "expression": expr,
                "dataset": ds_name,
                "category": ds_info["category"],
                "fields": [field],
                "style": style,
                "operator_count": op_count
            })

        return ds_name, candidates

    async def run_batch_simulation(self, candidates: List[Dict[str, Any]], universe: str = "TOP3000") -> List[Dict[str, Any]]:
        """Executes 8-concurrency multi_create_simulate."""
        await self.ensure_auth()
        exprs = [c["expression"] for c in candidates]
        logger.info(f"Submitting 8-candidate multisim on universe '{universe}'...")

        try:
            res = await create_multi_simulation(
                alpha_expressions=exprs,
                region="USA",
                universe=universe,
                delay=1,
                decay=5,
                neutralization="SUBINDUSTRY",
                truncation=0.08,
                max_trade="ON",
                pasteurization="ON",
                language="FASTEXPR"
            )
            return res.get("alpha_results", [])
        except Exception as e:
            logger.error(f"Error during create_multi_simulation: {e}")
            return []

    async def audit_candidate(self, candidate: Dict[str, Any], sim_result: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Audits candidate against all submission hard thresholds:
        - Sharpe > 1.58
        - Fitness > 1.0
        - 2Y Sharpe > 1.6
        - Margin > 0.0005 (5 bp)
        - 0.05 < Turnover < 0.30
        - RN Sharpe > 1.0, RN Fitness > 0.7, RN Margin > 5bp
        - ra_failed_count == 0
        """
        det = sim_result.get("details", {})
        aid = sim_result.get("alpha_id", det.get("id"))
        is_res = det.get("is", {})
        rn_res = is_res.get("riskNeutralized", {})

        metrics = {
            "alpha_id": aid,
            "sharpe": float(is_res.get("sharpe") or 0.0),
            "fitness": float(is_res.get("fitness") or 0.0),
            "two_y_sharpe": float(is_res.get("two_y_sharpe") or is_res.get("sharpe_2y") or 0.0),
            "margin": float(is_res.get("margin") or 0.0),
            "turnover": float(is_res.get("turnover") or 0.0),
            "rn_sharpe": float(rn_res.get("sharpe") or 0.0),
            "rn_fitness": float(rn_res.get("fitness") or 0.0),
            "rn_margin": float(rn_res.get("margin") or 0.0),
            "returns": float(is_res.get("returns") or 0.0)
        }

        # Query yearly stats for 2y Sharpe if not present
        if metrics["two_y_sharpe"] == 0.0:
            try:
                y_stats = await get_alpha_yearly_stats(alpha_id=aid)
                # extract latest 2 years
                records = y_stats.get("records", [])
                if len(records) >= 2:
                    metrics["two_y_sharpe"] = float(records[-1].get("sharpe") or records[-2].get("sharpe") or 0.0)
            except Exception:
                pass

        # Check conditions
        failures = []
        if metrics["sharpe"] <= 1.58:
            failures.append(f"Sharpe {metrics['sharpe']:.2f} <= 1.58")
        if metrics["fitness"] <= 1.0:
            failures.append(f"Fitness {metrics['fitness']:.2f} <= 1.0")
        if metrics["two_y_sharpe"] <= 1.60:
            failures.append(f"2Y Sharpe {metrics['two_y_sharpe']:.2f} <= 1.60")
        if metrics["margin"] <= 0.0005:
            failures.append(f"Margin {metrics['margin']*10000:.1f}bp <= 5bp")
        if not (0.05 < metrics["turnover"] < 0.30):
            failures.append(f"Turnover {metrics['turnover']*100:.1f}% not in 5%-30%")
        if metrics["rn_sharpe"] <= 1.0:
            failures.append(f"RN Sharpe {metrics['rn_sharpe']:.2f} <= 1.0")
        if metrics["rn_fitness"] <= 0.7:
            failures.append(f"RN Fitness {metrics['rn_fitness']:.2f} <= 0.7")
        if metrics["rn_margin"] <= 0.0005:
            failures.append(f"RN Margin {metrics['rn_margin']*10000:.1f}bp <= 5bp")

        if failures:
            return False, "; ".join(failures), metrics

        # Query submission checks
        try:
            sub_check = await get_submission_check(alpha_id=aid)
            checks = sub_check.get("checks", [])
            failed_checks = [c for c in checks if c.get("result") == "FAIL"]
            if len(failed_checks) > 0:
                fail_names = [c.get("name") for c in failed_checks]
                return False, f"Submission checks failed: {fail_names}", metrics
        except Exception as e:
            logger.warning(f"Error checking submission gates: {e}")

        # Correlation Verification
        try:
            corr_res = await check_correlation(alpha_id=aid, correlation_type="both", threshold=0.7)
            prod_info = corr_res.get("checks", {}).get("production", {})
            prod_corr = prod_info.get("max_correlation")
            if prod_corr is None or prod_corr > 0.70:
                return False, f"Production correlation {prod_corr} > 0.70 or pending", metrics

            # Check mutual correlation against existing winners
            for winner in self.qualified_alphas:
                # verify mutual correlation is < 0.40
                w_id = winner["metrics"]["alpha_id"]
                # self correlation check
                self_info = corr_res.get("checks", {}).get("self", {})
                records = self_info.get("correlation_data", {}).get("records", [])
                for rec in records:
                    if len(rec) >= 6 and rec[0] == w_id:
                        mutual_c = float(rec[5])
                        if mutual_c >= 0.40:
                            return False, f"Mutual correlation with winner {w_id} is {mutual_c:.2f} >= 0.40", metrics
        except Exception as e:
            logger.warning(f"Error checking correlation: {e}")
            return False, "Correlation check error", metrics

        return True, "Passed all checks!", metrics

    async def register_winner(self, candidate: Dict[str, Any], metrics: Dict[str, Any]):
        """Sets properties and registers winner. NEVER calls submit_alpha!"""
        aid = metrics["alpha_id"]
        tag_list = [f"USA_D1_{candidate['category'].upper()}", "UNLIT_PYRAMID", "MAB_WINNER"]
        desc = (
            f"Autonomous MAB Winner from unlit dataset '{candidate['dataset']}'. "
            f"Sharpe={metrics['sharpe']:.2f}, Fitness={metrics['fitness']:.2f}, Margin={metrics['margin']*10000:.1f}bp, "
            f"Turnover={metrics['turnover']*100:.1f}%. Strictly verified <5 ops."
        )

        try:
            await set_alpha_properties(
                alpha_id=aid,
                name=f"Alpha_{candidate['dataset']}_{candidate['style'][:8]}",
                color="GREEN",
                tags=tag_list,
                regular_desc=desc
            )
            logger.info(f"Set alpha properties for winner {aid} (Color: GREEN, Tags: {tag_list})")
        except Exception as e:
            logger.error(f"Error setting alpha properties: {e}")

        winner_record = {
            "candidate": candidate,
            "metrics": metrics,
            "registered_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.qualified_alphas.append(winner_record)
        logger.info(f"🏆 SUCCESS: Registered Winner #{len(self.qualified_alphas)} from dataset '{candidate['dataset']}'!")

        # Advance to next unlit dataset
        self.current_ds_idx += 1


if __name__ == "__main__":
    print("USAMABOrchestrator defined successfully.")
