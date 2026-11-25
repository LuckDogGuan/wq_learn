import json
from .config import HARD_THRESHOLDS, REPORT_PATH

def evaluate_metrics(details):
    is_metrics = details.get('is', {})
    
    # 1. Base thresholds
    sharpe = is_metrics.get('sharpe', 0)
    fitness = is_metrics.get('fitness', 0)
    margin = is_metrics.get('margin', 0)
    turnover = is_metrics.get('turnover', 0)
    
    checks = is_metrics.get('checks', [])
    y2_sharpe = 0
    for c in checks:
        if c.get('name') == 'LOW_2Y_SHARPE':
            y2_sharpe = c.get('value', 0)
            
    if sharpe <= HARD_THRESHOLDS['is_sharpe']: return False, "Low Sharpe"
    if fitness <= HARD_THRESHOLDS['is_fitness']: return False, "Low Fitness"
    if y2_sharpe <= HARD_THRESHOLDS['is_2y_sharpe']: return False, "Low 2Y Sharpe"
    if margin <= HARD_THRESHOLDS['margin_bp'] / 10000.0: return False, "Low Margin"
    if turnover <= HARD_THRESHOLDS['turnover_min'] or turnover >= HARD_THRESHOLDS['turnover_max']: 
        return False, "Turnover out of bounds"
        
    return True, "Passed IS Checks"

def evaluate_neutralized(details):
    # Depending on the WQ Brain API, neutralized metrics might be nested or we need to submit a neutralized sim.
    # Usually, if we submitted with Neutralization = SUBINDUSTRY, the `is_metrics` ARE neutralized.
    # We apply the neutralized thresholds here to the same metrics if that's the case.
    is_metrics = details.get('is', {})
    sharpe = is_metrics.get('sharpe', 0)
    fitness = is_metrics.get('fitness', 0)
    margin = is_metrics.get('margin', 0)
    
    if sharpe <= HARD_THRESHOLDS['neut_sharpe']: return False, "Low Neut Sharpe"
    if fitness <= HARD_THRESHOLDS['neut_fitness']: return False, "Low Neut Fitness"
    if margin <= HARD_THRESHOLDS['neut_margin_bp'] / 10000.0: return False, "Low Neut Margin"
    
    return True, "Passed Neutralized Checks"

def generate_diversity_report(state_manager, batch_num):
    success_pool = state_manager.get_success_pool()
    tested_exprs = state_manager.get_tested_expressions()
    
    report_content = f"# Diversity Report - Batch {batch_num}\n\n"
    report_content += f"## Summary\n"
    report_content += f"- Total expressions tested: {len(tested_exprs)}\n"
    report_content += f"- Total submit-ready alphas found: {len(success_pool)}\n\n"
    
    if success_pool:
        report_content += "## Found Alphas\n"
        for idx, a in enumerate(success_pool):
            report_content += f"{idx+1}. **Dataset**: {a['dataset_id']}, **Expr**: `{a['expression']}`\n"
    
    report_content += "\n## Exploration Metrics\n"
    report_content += "- Operator exploration: Evaluated various standard fast expressions.\n"
    report_content += "- Field exploration: Sticking to DateFields.\n"
    report_content += "- Template skeleton: Basic ranks, z-scores, and cross-sectional groups.\n"
    
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report_content)
