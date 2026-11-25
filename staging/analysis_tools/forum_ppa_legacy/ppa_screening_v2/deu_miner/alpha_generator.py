import pandas as pd
import os
import random
from .config import DATEFIELDS_CSV

# Base templates that use < 6 operators and NO trade_when, add, multiply.
# Inspired by distilled_alpha.md
# Targeted fields identified from previous high-Sharpe candidates
TARGET_FIELDS = [
    'short_term_price_change',
    'positive_score_median_value_5',
    'positive_score_confidence_lower_bound'
]

# Advanced parameter-swept templates for DEU targeting Sharpe > 1.58
# Must keep operator depth < 6 and avoid trade_when, add, multiply.
# Phase 1: Fixed decay=0, subindustry neutralization
def get_swept_templates():
    templates = []
    lookbacks = [5, 10, 20, 60, 120, 240]
    
    # Base indicators with subindustry neutralization
    for d in lookbacks:
        # Time-series rank neutralized
        templates.append(f"group_zscore(ts_rank({{f}}, {d}), subindustry)")
        templates.append(f"group_neutralize(ts_rank({{f}}, {d}), subindustry)")
        
        # Time-series zscore neutralized
        templates.append(f"group_zscore(ts_zscore({{f}}, {d}), subindustry)")
        
        # Delta neutralized
        templates.append(f"group_zscore(ts_delta({{f}}, {d}), subindustry)")
        templates.append(f"-1 * group_zscore(ts_delta({{f}}, {d}), subindustry)")
        
        # Distribution neutralized
        templates.append(f"group_zscore(ts_skewness({{f}}, {d}), subindustry)")
        templates.append(f"group_zscore(ts_kurtosis({{f}}, {d}), subindustry)")
        
        # Combo: ts_rank of ts_zscore neutralized
        templates.append(f"group_zscore(ts_rank(ts_zscore({{f}}, {d}), {d}), subindustry)")
        templates.append(f"-1 * group_zscore(ts_rank(ts_zscore({{f}}, {d}), {d}), subindustry)")

    return templates

def load_datefields_datasets():
    if not os.path.exists(DATEFIELDS_CSV):
        raise FileNotFoundError(f"CSV not found: {DATEFIELDS_CSV}")
    
    df = pd.read_csv(DATEFIELDS_CSV)
    # Group by dataset.id and collect fields (id)
    grouped = df.groupby('dataset.id')['id'].apply(list).to_dict()
    return grouped

import sqlite3
import json

import sqlite3
import json

def generate_expressions(dataset_id, fields, max_fields=2):
    """
    Two-Phase Generation:
    1. Phase 1: Base templates (decay=0, subindustry) - no settings_override.
    2. Phase 2: Sweep decay, neutralization, and region for > 1.2 alphas.
    """
    expressions = []
    
    # Phase 1
    templates_p1 = get_swept_templates()
    for f in TARGET_FIELDS:
        for tpl in templates_p1:
            expr = tpl.format(f=f)
            expressions.append({
                "expression": expr,
                "dataset_id": "targeted_opt",
                "field_id": f,
                "settings": {}
            })
            
    # Phase 2: API Sweeps for > 1.2 alphas
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'deu_miner_state.db')
        if os.path.exists(db_path):
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT expression, metrics, settings FROM expressions WHERE status NOT IN ('PENDING', 'FAIL') AND metrics IS NOT NULL")
                for row in cursor.fetchall():
                    base_expr = row[0]
                    base_settings = json.loads(row[2]) if row[2] else {}
                    
                    if not any(f in base_expr for f in TARGET_FIELDS): continue
                    
                    try:
                        metrics = json.loads(row[1])
                        sharpe = metrics.get('is', {}).get('sharpe', -1)
                        if sharpe > 1.2:
                            # We found a winner! Sweep Decay
                            for decay_val in [0, 5, 20]:
                                if decay_val != base_settings.get('decay', 0):
                                    expressions.append({
                                        "expression": base_expr,
                                        "dataset_id": "targeted_opt",
                                        "field_id": "phase2_decay",
                                        "settings": {"decay": decay_val}
                                    })
                            # Sweep Neutralization
                            for neut in ['INDUSTRY', 'SECTOR', 'MARKET']:
                                if neut != base_settings.get('neutralization', 'SUBINDUSTRY'):
                                    expressions.append({
                                        "expression": base_expr,
                                        "dataset_id": "targeted_opt",
                                        "field_id": "phase2_neut",
                                        "settings": {"neutralization": neut}
                                    })
                            # Sweep Region
                            for reg in ['USA', 'ASI', 'EUR']:
                                if reg != base_settings.get('region', 'DEU'):
                                    expressions.append({
                                        "expression": base_expr,
                                        "dataset_id": "targeted_opt",
                                        "field_id": "phase2_region",
                                        "settings": {"region": reg}
                                    })
                    except Exception:
                        pass
    except Exception as e:
        print("Error Phase 2 sweep generation:", e)
        
    return expressions, TARGET_FIELDS
