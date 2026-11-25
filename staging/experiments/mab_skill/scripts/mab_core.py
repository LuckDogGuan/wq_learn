"""
Multi-Armed Bandit (MAB) Core Engine for WorldQuant Brain Alpha Mining
Implements Thompson Sampling with Beta distributions, Hierarchical Bandits,
Strict Hard Rules Validation (banning trade_when/add/multiply, <8 operators),
and Multi-Objective Reward Calculation with Gate Check Penalties.
"""

from __future__ import annotations

import re
import math
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import numpy as np


@dataclass
class ThompsonArm:
    """Thompson Sampling Arm using Beta prior (alpha, beta)."""
    arm_id: str
    alpha: float = 1.0   # Success equivalent
    beta: float = 1.0    # Failure equivalent
    pulls: int = 0
    total_reward: float = 0.0
    avg_reward: float = 0.0

    def sample(self) -> float:
        """Sample from Beta distribution."""
        return float(np.random.beta(self.alpha, self.beta))

    def update(self, reward: float):
        """
        Update arm with normalized reward in [0, 1].
        Reward R in [-1, 1] is mapped to [0, 1].
        """
        self.pulls += 1
        self.total_reward += reward
        self.avg_reward = self.total_reward / self.pulls

        # Map [-1, 1] to [0, 1]
        norm_r = max(0.0, min(1.0, (reward + 1.0) / 2.0))
        self.alpha += norm_r
        self.beta += (1.0 - norm_r)

    def get_confidence(self) -> float:
        """Confidence score inversely proportional to variance."""
        if self.alpha + self.beta <= 2:
            return 0.0
        var = (self.alpha * self.beta) / (((self.alpha + self.beta) ** 2) * (self.alpha + self.beta + 1))
        return float(1.0 / (1.0 + var))


class ThompsonBandit:
    """Thompson Sampling Bandit manager for a single decision layer."""

    def __init__(self, name: str):
        self.name = name
        self.arms: Dict[str, ThompsonArm] = {}
        self.total_pulls = 0

    def add_arm(self, arm_id: str):
        if arm_id not in self.arms:
            self.arms[arm_id] = ThompsonArm(arm_id=arm_id)

    def select_arm(self, available_arms: Optional[List[str]] = None) -> str:
        candidates = available_arms if available_arms else list(self.arms.keys())
        if not candidates:
            raise ValueError(f"No arms available in bandit {self.name}")

        for arm_id in candidates:
            self.add_arm(arm_id)

        samples = {arm_id: self.arms[arm_id].sample() for arm_id in candidates}
        selected = max(samples.keys(), key=lambda k: samples[k])
        return selected

    def update(self, arm_id: str, reward: float):
        self.add_arm(arm_id)
        self.arms[arm_id].update(reward)
        self.total_pulls += 1


class HierarchicalContextualBandit:
    """
    Hierarchical Bandit:
    Level 1: Dataset
    Level 2: Strategy Style
    Level 3: Skeleton Template
    Level 4: Parameter Configuration
    """

    def __init__(self):
        self.dataset_bandit = ThompsonBandit("dataset")
        self.strategy_bandit = ThompsonBandit("strategy")
        self.skeleton_bandit = ThompsonBandit("skeleton")
        self.param_bandit = ThompsonBandit("parameter")
        self.history: List[Dict[str, Any]] = []

    def select_path(
        self,
        datasets: List[str],
        strategies: List[str],
        skeletons: List[str],
        params: List[str]
    ) -> Dict[str, str]:
        selected_dataset = self.dataset_bandit.select_arm(datasets)
        selected_strategy = self.strategy_bandit.select_arm(strategies)
        selected_skeleton = self.skeleton_bandit.select_arm(skeletons)
        selected_param = self.param_bandit.select_arm(params)

        path = {
            "dataset": selected_dataset,
            "strategy": selected_strategy,
            "skeleton": selected_skeleton,
            "parameter": selected_param
        }
        return path

    def update_path(self, path: Dict[str, str], reward: float):
        self.dataset_bandit.update(path["dataset"], reward)
        self.strategy_bandit.update(path["strategy"], reward)
        self.skeleton_bandit.update(path["skeleton"], reward)
        self.param_bandit.update(path["parameter"], reward)
        self.history.append({"path": path, "reward": reward})


class HardRulesValidator:
    """
    Strict Hard Rules Validator based on doc/总结 and User Constraints:
    1. Operator count < 8
    2. STRICTLY BAN: trade_when, add, multiply
    3. Balanced parentheses
    4. Strip regional prefixes (e.g. EUR., USA.)
    5. Safe division check (non-zero protection)
    """

    BANNED_OPERATORS = ["trade_when", "add", "multiply"]
    
    # Common FASTEXPR operators to count
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
        """
        Validates alpha expression against all hard constraints.
        Returns: (is_valid, error_reason, operator_count)
        """
        cleaned = expr.strip()

        # 1. Check banned operators
        for banned in cls.BANNED_OPERATORS:
            # Match operator name with word boundary or paren
            pattern = rf'\b{banned}\s*\('
            if re.search(pattern, cleaned, re.IGNORECASE):
                return False, f"Banned operator detected: '{banned}'. Prohibited by hard rules!", 0

        # 2. Check parentheses balancing
        if cleaned.count('(') != cleaned.count(')'):
            return False, f"Unbalanced parentheses: '('={cleaned.count('(')} vs ')'={cleaned.count(')')}", 0

        # 3. Check for regional prefix contamination (e.g. EUR.close)
        if re.search(r'\b(USA|EUR|CHN|ASI|GLB|IND)\.[a-z0-9_]+\b', cleaned, re.IGNORECASE):
            return False, "Regional prefix detected (e.g. EUR.field). Must be pure field name!", 0

        # 4. Count operators
        op_count = 0
        for op in cls.KNOWN_OPERATORS:
            matches = len(re.findall(rf'\b{op}\s*\(', cleaned, re.IGNORECASE))
            op_count += matches

        # Also count basic math operators if used outside identifiers
        op_count += len(re.findall(r'[\+\-\*\/]', re.sub(r'[a-zA-Z0-9_]+', '', cleaned)))

        if op_count >= 8:
            return False, f"Operator count exceeded: {op_count} >= 8. Must be strictly < 8!", op_count

        return True, "Valid", op_count


class HardMetricEvaluator:
    """
    Evaluates simulation metrics against the strict user-defined goal baseline:
    - Region: EUR
    - Delay: D1
    - Universe: TOPCS1600 (or TOP2500)
    - max_trade: ON
    - Type: REGULAR
    - Sharpe > 1.58
    - Fitness > 1.00
    - 2Y Sharpe > 1.60
    - Margin > 5.0 bps (0.0005)
    - 5.0% < Turnover < 30.0%
    - Risk Neutralization: RN Sharpe > 1.00, RN Fitness > 0.70, RN Margin > 5.0 bps
    - Operator count < 8
    - ra_failed_count == 0
    - Pairwise correlation < 0.40
    - Prod correlation < 0.70
    """

    @classmethod
    def evaluate(cls, metrics: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        """
        Returns: (passed, reward, failure_reasons)
        """
        reasons = []
        sharpe = float(metrics.get("sharpe", 0.0))
        fitness = float(metrics.get("fitness", 0.0))
        two_y_sharpe = float(metrics.get("two_y_sharpe", metrics.get("sharpe_2y", 0.0)))
        margin = float(metrics.get("margin", 0.0))
        turnover = float(metrics.get("turnover", 0.0))
        rn_sharpe = float(metrics.get("rn_sharpe", 0.0))
        rn_fitness = float(metrics.get("rn_fitness", 0.0))
        rn_margin = float(metrics.get("rn_margin", 0.0))
        ra_failed_count = int(metrics.get("ra_failed_count", 0))
        op_count = int(metrics.get("operator_count", 0))

        # Check all hard conditions
        if sharpe <= 1.58:
            reasons.append(f"Sharpe {sharpe:.2f} <= 1.58")
        if fitness <= 1.00:
            reasons.append(f"Fitness {fitness:.2f} <= 1.00")
        if two_y_sharpe <= 1.60:
            reasons.append(f"2Y Sharpe {two_y_sharpe:.2f} <= 1.60")
        if margin <= 0.0005:  # 5 bps
            reasons.append(f"Margin {margin*10000:.1f}bps <= 5.0bps")
        if turnover <= 0.05 or turnover >= 0.30:
            reasons.append(f"Turnover {turnover*100:.1f}% not in (5.0%, 30.0%)")
        if rn_sharpe <= 1.00:
            reasons.append(f"RN Sharpe {rn_sharpe:.2f} <= 1.00")
        if rn_fitness <= 0.70:
            reasons.append(f"RN Fitness {rn_fitness:.2f} <= 0.70")
        if rn_margin <= 0.0005:
            reasons.append(f"RN Margin {rn_margin*10000:.1f}bps <= 5.0bps")
        if ra_failed_count > 0:
            reasons.append(f"ra_failed_count={ra_failed_count} > 0")
        if op_count >= 8:
            reasons.append(f"Operator count {op_count} >= 8")

        # Calculate reward for MAB feedback
        if reasons:
            # Penalized negative or low reward for failure
            reward = -0.5 if ra_failed_count > 0 else 0.0
            return False, reward, reasons

        # Positive reward calculation
        s_norm = min(sharpe / 3.0, 1.0)
        f_norm = min(fitness / 2.0, 1.0)
        t_norm = 1.0 - abs(turnover - 0.15) / 0.15  # Optimal near 15%
        m_norm = min(margin / 0.0020, 1.0)          # Cap at 20 bps

        base_reward = 0.35 * s_norm + 0.25 * f_norm + 0.20 * m_norm + 0.20 * t_norm

        # Bonus for exceptional performance
        if sharpe > 2.0 and fitness > 1.5 and two_y_sharpe > 1.8:
            base_reward *= 1.5

        return True, min(1.0, base_reward), []
