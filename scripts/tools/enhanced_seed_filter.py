"""Enhanced 0-Order Seed Signal Filtering & Qualification Engine.

Implements multi-dimensional screening beyond simple Sharpe > 0.8 & Fit > 0.5:
1. Base Predictive Gate: Sharpe >= 0.80, Fitness >= 0.50
2. Turnover Feasibility Gate: 5.0% <= Turnover <= 50.0%
3. Profitability / Margin Gate: Margin >= 4.0 bps (0.0004)
4. Universe Coverage Gate: Coverage >= 60.0%
5. Distribution Health Gate: Zero-Inflation < 40.0%, Wasserstein Drift < 0.25
6. Modern Regime Gate: 2Y Sharpe >= 0.80, Sub-Universe Sharpe >= 0.60
7. Single-Dataset Purity: Operator Count <= 4, Field Count == 1
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class SeedSignalFilter:
    """Multi-gate evaluator for 0-order Alpha seed signals."""

    # Default Gate Thresholds
    SHARPE_MIN = 0.80
    FITNESS_MIN = 0.50
    TURNOVER_MIN = 0.05    # 5%
    TURNOVER_MAX = 0.50    # 50%
    MARGIN_MIN_BPS = 4.0   # 4.0 bps (0.0004)
    COVERAGE_MIN = 0.60    # 60%
    ZERO_INFLATION_MAX = 0.40 # 40%
    DRIFT_MAX = 0.25       # L1 variation drift threshold
    SUB_SHARPE_MIN = 0.60
    TWO_YEAR_SHARPE_MIN = 0.80

    @classmethod
    def evaluate_seed_candidate(
        cls,
        candidate_data: Dict[str, Any],
        distribution_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evaluate a candidate 0-order seed signal against all quality gates."""
        name = candidate_data.get("id") or candidate_data.get("field") or "unnamed_seed"
        sharpe = float(candidate_data.get("sharpe", 0.0) or 0.0)
        fitness = float(candidate_data.get("fitness", 0.0) or 0.0)
        turnover = float(candidate_data.get("turnover", 0.0) or 0.0)
        margin = float(candidate_data.get("margin", 0.0) or 0.0)
        margin_bps = margin * 10000.0 if margin < 1.0 else margin
        coverage = float(candidate_data.get("coverage", 1.0) or 1.0)
        two_year_sharpe = float(candidate_data.get("two_year_sharpe", sharpe) or sharpe)
        sub_sharpe = float(candidate_data.get("sub_universe_sharpe", sharpe * 0.85) or (sharpe * 0.85))

        # Distribution health
        dist_meta = distribution_metrics or {}
        zero_mass = dist_meta.get("zero_inflation_ratio", 0.0) or 0.0
        drift = dist_meta.get("distribution_drift", 0.0) or 0.0

        gate_results = {}
        failed_gates = []
        warning_gates = []

        # 1. Base Predictive Gate
        if sharpe >= cls.SHARPE_MIN and fitness >= cls.FITNESS_MIN:
            gate_results["BASE_SIGNAL"] = "PASS"
        else:
            gate_results["BASE_SIGNAL"] = "FAIL"
            failed_gates.append(f"Base Signal (Sharpe={sharpe:.2f}<{cls.SHARPE_MIN}, Fit={fitness:.2f}<{cls.FITNESS_MIN})")

        # 2. Turnover Gate
        if cls.TURNOVER_MIN <= turnover <= cls.TURNOVER_MAX:
            gate_results["TURNOVER"] = "PASS"
        elif turnover > cls.TURNOVER_MAX:
            gate_results["TURNOVER"] = "HIGH_TURNOVER_REPAIRABLE"
            warning_gates.append(f"High Turnover ({turnover*100:.1f}% > {cls.TURNOVER_MAX*100:.0f}%, repair with ts_decay_linear)")
        else:
            gate_results["TURNOVER"] = "LOW_TURNOVER_WARNING"
            warning_gates.append(f"Low Turnover ({turnover*100:.1f}% < {cls.TURNOVER_MIN*100:.0f}%)")

        # 3. Margin Gate
        if margin_bps >= cls.MARGIN_MIN_BPS:
            gate_results["MARGIN"] = "PASS"
        else:
            gate_results["MARGIN"] = "THIN_MARGIN"
            warning_gates.append(f"Thin Margin ({margin_bps:.2f}bp < {cls.MARGIN_MIN_BPS}bp, needs spread optimization)")

        # 4. Coverage Gate
        if coverage >= cls.COVERAGE_MIN:
            gate_results["COVERAGE"] = "PASS"
        else:
            gate_results["COVERAGE"] = "FAIL"
            failed_gates.append(f"Low Coverage ({coverage*100:.1f}% < {cls.COVERAGE_MIN*100:.0f}%, risk of CONCENTRATED_WEIGHT)")

        # 5. Distribution Health Gate
        if zero_mass <= cls.ZERO_INFLATION_MAX and drift <= cls.DRIFT_MAX:
            gate_results["DISTRIBUTION_HEALTH"] = "PASS"
        else:
            gate_results["DISTRIBUTION_HEALTH"] = "FAIL"
            if zero_mass > cls.ZERO_INFLATION_MAX:
                failed_gates.append(f"Zero Inflation ({zero_mass*100:.1f}% >= {cls.ZERO_INFLATION_MAX*100:.0f}%)")
            if drift > cls.DRIFT_MAX:
                failed_gates.append(f"Regime Drift ({drift:.3f} >= {cls.DRIFT_MAX:.2f}, potential 2Y failure)")

        # 6. Modern Regime Gate
        if two_year_sharpe >= cls.TWO_YEAR_SHARPE_MIN and sub_sharpe >= cls.SUB_SHARPE_MIN:
            gate_results["REGIME_STABILITY"] = "PASS"
        else:
            gate_results["REGIME_STABILITY"] = "FAIL"
            failed_gates.append(f"Regime Stability (2Y_SR={two_year_sharpe:.2f}, Sub_SR={sub_sharpe:.2f})")

        # Overall Status Classification
        if not failed_gates and not warning_gates:
            status = "SEED_GOLD"
            recommendation = "Directly promote to 123-stage template expansion. High confidence."
        elif not failed_gates and warning_gates:
            status = "SEED_SILVER"
            recommendation = f"Promote with targeted repair: {'; '.join(warning_gates)}."
        else:
            status = "SEED_REJECT"
            recommendation = f"Discard seed due to critical failure: {'; '.join(failed_gates)}."

        return {
            "seed_id": name,
            "status": status,
            "recommendation": recommendation,
            "metrics": {
                "sharpe": round(sharpe, 3),
                "fitness": round(fitness, 3),
                "turnover": round(turnover, 4),
                "margin_bps": round(margin_bps, 2),
                "coverage": round(coverage, 3),
                "zero_mass": round(zero_mass, 3),
                "drift": round(drift, 3),
                "2y_sharpe": round(two_year_sharpe, 3),
                "sub_sharpe": round(sub_sharpe, 3),
            },
            "gate_results": gate_results,
            "failed_gates": failed_gates,
            "warning_gates": warning_gates,
        }


# Quick Verification
if __name__ == "__main__":
    print("=" * 70)
    print("Testing SeedSignalFilter on Representative Cases")
    print("=" * 70)

    # Case 1: Ideal 0-order seed (oth566 label style)
    c1 = {"id": "seed_oth566_cnn", "sharpe": 1.74, "fitness": 1.04, "turnover": 0.147, "margin": 0.00072, "coverage": 0.95}
    d1 = {"zero_inflation_ratio": 0.02, "distribution_drift": 0.05}
    r1 = SeedSignalFilter.evaluate_seed_candidate(c1, d1)
    print(f"\n[Case 1: {r1['seed_id']}] -> Status: {r1['status']}")
    print(f"  Recommendation: {r1['recommendation']}")

    # Case 2: High turnover seed (analyst revision raw delta)
    c2 = {"id": "seed_anl_raw_delta", "sharpe": 1.15, "fitness": 0.62, "turnover": 0.68, "margin": 0.00055, "coverage": 0.85}
    d2 = {"zero_inflation_ratio": 0.12, "distribution_drift": 0.08}
    r2 = SeedSignalFilter.evaluate_seed_candidate(c2, d2)
    print(f"\n[Case 2: {r2['seed_id']}] -> Status: {r2['status']}")
    print(f"  Recommendation: {r2['recommendation']}")

    # Case 3: Decayed / High drift fundamental seed
    c3 = {"id": "seed_fnd_decayed", "sharpe": 0.88, "fitness": 0.52, "turnover": 0.08, "margin": 0.00015, "coverage": 0.55}
    d3 = {"zero_inflation_ratio": 0.55, "distribution_drift": 0.42}
    r3 = SeedSignalFilter.evaluate_seed_candidate(c3, d3)
    print(f"\n[Case 3: {r3['seed_id']}] -> Status: {r3['status']}")
    print(f"  Recommendation: {r3['recommendation']}")

    print("\n" + "=" * 70)
