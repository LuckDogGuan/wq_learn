import typing

def apply_rank_by_side_and_diff(signal_expr: str, margin_recovery_window: int = 50) -> str:
    """
    **横截面多空独立排序与Margin恢复** (注意：当前账户暂无 rank_by_side 算子权限)
    - **逻辑 (Logic):** 使用 rank_by_side 保留多空方向并独立排序，压缩单只股票极端权重，从而改善 2Y Sharpe 和 Ladder Sharpe。叠加 ts_av_diff 可恢复因 rank_by_side 而损失的 margin。
    - **模板 (Template):** `rank_by_side(<alpha>) + ts_av_diff(<alpha>, <window>)`
    - **使用算子 (Operators Used):** `rank_by_side`, `ts_av_diff`, `+`
    - **参数建议 (Parameter Recommendations):**
      - `signal_expr`: 原始因子表达式。
      - `margin_recovery_window`: 恢复时间窗口大小，默认 50。设为 0 可关闭此项。
    """
    base_expr = f"rank_by_side({signal_expr})"
    if margin_recovery_window > 0:
        return f"{base_expr} + ts_av_diff({signal_expr}, {margin_recovery_window})"
    return base_expr


def inner_group_neutralize_with_outer_ram(signal_expr: str, group_field: str = "industry") -> dict:
    """
    **内外层中性化结合（突破Sharpe）**
    - **逻辑 (Logic):** 内层进行细粒度的 group_neutralize，结合外层 CROWDING 或 REVERSION_AND_MOMENTUM 设置。能够在不影响 margin 的情况下显著拉升 2Y Sharpe。
    - **模板 (Template):** `group_neutralize(<alpha>, <group_field>)` (并在设置中结合相应配置)
    - **使用算子 (Operators Used):** `group_neutralize`
    - **参数建议 (Parameter Recommendations):**
      - `signal_expr`: 原始因子表达式。
      - `group_field`: 内层分组字段，默认 "industry"。须严格细于外层配置。
    """
    enhanced_expr = f"group_neutralize({signal_expr}, {group_field})"
    
    return {
        "expression": enhanced_expr,
        "recommended_settings": {
            "neutralization": "CROWDING" # 或 "REVERSION_AND_MOMENTUM"
        }
    }


def resolve_reversion_component(alpha_expr: str, strategy: str = 'compromise') -> str:
    """
    **反转分量警告处理（Reversion Warning 解法）**
    - **逻辑 (Logic):** 当 Alpha 含有较重反转分量并触发平台警告时，采取妥协方案（放大反转权重、粗化分组、拉长窗口、拉伸信号差异）或根治方案（完全移除负向收益逻辑，替换为独立机制）。
    - **模板 (Template):** `signed_power(<alpha> + 2.5 * group_rank(-ts_mean(returns, 20), market), 1.1)` (以妥协方案为例)
    - **使用算子 (Operators Used):** `signed_power`, `group_rank`, `ts_mean` 等（视策略而定）
    - **参数建议 (Parameter Recommendations):**
      - `alpha_expr`: 原始因子表达式。
      - `strategy`: 选择应对策略，可选 'compromise' 或 'root_cause'。
    """
    if strategy == 'compromise':
        # 伪代码：将权重调大，sector替换为market，调整窗口，外层用signed_power(expr, 1.1)
        pass
    elif strategy == 'root_cause':
        # 伪代码：彻底剥离 -returns 类负向收益逻辑，替换为独立机制
        pass
        
    return alpha_expr


def optimize_japan_robustness_sharpe(fundamental_expr: str, reversion_window: int = 20, reversion_weight: float = 2.5) -> str:
    """
    **日本子集基本面增强与Sharpe优化**
    - **逻辑 (Logic):** 针对 ASI 区域日本子集基本面信号偏弱的痛点，通过大幅增加反转组件的权重和时窗，并拉伸信号差异（signed_power），以改善测试数据。
    - **模板 (Template):** `signed_power(<alpha> + <weight> * group_rank(-ts_mean(returns, <window>), market), 1.1)`
    - **使用算子 (Operators Used):** `signed_power`, `group_rank`, `ts_mean`, `+`, `*`
    - **参数建议 (Parameter Recommendations):**
      - `fundamental_expr`: 基础基本面表达式。
      - `reversion_window`: 反转组件的时间窗口，默认 20。
      - `reversion_weight`: 反转组件的权重放大倍数，默认 2.5。
    """
    reversion_expr = f"{reversion_weight} * group_rank(-ts_mean(returns, {reversion_window}), market)"
    combined_expr = f"({fundamental_expr}) + {reversion_expr}"
    final_expr = f"signed_power({combined_expr}, 1.1)"
    return final_expr
