

import pandas as pd
import logging

def categorize_factors(fields_df: pd.DataFrame):
    """
    对因子进行科学分类与评估，并在不同维度上提供平衡的推荐。
    (从原先的在线拉取，彻底重构为纯粹的数据帧运算，速度可达毫秒级)
    
    返回一个字典，包含以下类型的数据帧 (DataFrame):
    - 'Unexplored' (未探索/蓝海): alphaCount == 0 且覆盖率合格。高风险高回报。
    - 'Emerging' (萌芽/早期): 0 < alphaCount < 50。已有初步验证，尚未过度开发。
    - 'SweetSpot' (黄金甜点区): 50 <= alphaCount <= 300。核心推荐！数学表达强，且容易避开 PROD 相关性墙。
    - 'Crowded' (拥挤/红海): alphaCount > 300。虽然容易做出 Alpha，但在提交时极易因为 PROD Correlation > 0.7 被拒。
    - 'Garbage' (劣质): 覆盖率极低 (< 0.15)，极难跑出稳定的中长周期 Sharpe。
    """
    if fields_df.empty:
        return {}
        
    df = fields_df.copy()
    
    # 确保字段是数值类型
    for col in ['coverage', 'alphaCount', 'userCount']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    has_cov = 'coverage' in df.columns
    has_alpha = 'alphaCount' in df.columns
    
    categories = {
        'Unexplored': pd.DataFrame(),
        'Emerging': pd.DataFrame(),
        'SweetSpot': pd.DataFrame(),
        'Crowded': pd.DataFrame(),
        'Garbage': pd.DataFrame()
    }
    
    if not (has_cov and has_alpha):
        return categories
        
    # 1. 垃圾因子: 覆盖率极低
    mask_garbage = df['coverage'] < 0.15
    categories['Garbage'] = df[mask_garbage].copy()
    
    df_valid = df[~mask_garbage].copy()
    
    # 2. 未被探索的潜力因子: alphaCount == 0
    mask_unexplored = df_valid['alphaCount'] == 0
    categories['Unexplored'] = df_valid[mask_unexplored].sort_values(by='coverage', ascending=False)
    
    # 3. 极度拥挤因子: alphaCount > 300
    mask_crowded = df_valid['alphaCount'] > 300
    categories['Crowded'] = df_valid[mask_crowded].sort_values(by='alphaCount', ascending=False)
    
    # 4. 黄金甜点因子: 50 <= alphaCount <= 300
    mask_sweet = (df_valid['alphaCount'] >= 50) & (df_valid['alphaCount'] <= 300)
    categories['SweetSpot'] = df_valid[mask_sweet].sort_values(by=['alphaCount', 'coverage'], ascending=[False, False])
    
    # 5. 早期萌芽因子: 0 < alphaCount < 50
    mask_emerging = (df_valid['alphaCount'] > 0) & (df_valid['alphaCount'] < 50)
    categories['Emerging'] = df_valid[mask_emerging].sort_values(by=['alphaCount', 'coverage'], ascending=[False, False])
    
    return categories
