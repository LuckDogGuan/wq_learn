import sys
from pathlib import Path

# 添加 Core ?sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from Core.factor.filter.expression_checker import verify_alpha_expression
from Core.factor.assembly.hu_ge_series import *
from Core.factor.assembly.sixty_days_matrix import *

def test_assemblies():
    print("=== Testing Hu Ge Series ===")
    h_funcs = [
        huge_series_1_cross_sectional_residual("close", "volume"),
        huge_series_2_timeseries_residual_stddev("close", "volume"),
        huge_series_2_timeseries_beta_lagged("close", "volume"),
        huge_series_3_beta_stability("close", "volume"),
        huge_series_4_beta_sharpe("close", "volume"),
        huge_series_4_beta_tstat_newey_west("close", "volume"),
        huge_series_5_time_trend_residual("close")
    ]
    for expr in h_funcs:
        res = verify_alpha_expression(expr)
        status = "[OK]" if res.get("valid") else f"[FAIL] {res.get('errors')}"
        print(f"{status} {expr}")

    print("\n=== Testing Sixty Days Matrix ===")
    s_funcs = [
        unary_0_slope("close"),
        unary_1_growth_rate_acceleration("close"),
        unary_2_growth_rate("close"),
        unary_3_autoregressive_slope("close"),
        unary_4_squared_momentum("close"),
        unary_5_decay_weighted_momentum("close"),
        unary_6_rank_reversal("close"),
        unary_7_log_smoothing("close"),
        unary_8_sign_preserved_power("close"),
        unary_9_differential_cascade("close"),
        binary_0_regression_residual("close", "volume"),
        binary_1_regression_beta("close", "volume"),
        binary_2_regression_residual_stddev("close", "volume"),
        binary_3_raw_regression_beta_short("close", "volume"),
        binary_4_raw_regression_beta_long("close", "volume"),
        binary_5_log_regression_neut("close", "volume"),
        binary_6_vector_neut("close", "volume"),
        ternary_0_joint_neutralization("close", "volume", "returns"),
        ternary_1_layered_regression_residual("close", "volume", "returns"),
        ternary_3_correlation_with_weight("close", "volume", "returns"),
        ternary_4_dynamic_ranking_timing("close", "sector", "returns"),
        ternary_5_triple_interaction("close", "volume", "returns"),
        ternary_6_conditional_switch("close", "volume", "returns")
    ]
    for expr in s_funcs:
        res = verify_alpha_expression(expr)
        status = "[OK]" if res.get("valid") else f"[FAIL] {res.get('errors')}"
        print(f"{status} {expr}")

if __name__ == "__main__":
    test_assemblies()
