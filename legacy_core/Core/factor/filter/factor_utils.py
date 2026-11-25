

import pandas as pd
from typing import List, Union, Dict
from collections import Counter

def analyze_keyword_frequency(df: pd.DataFrame, min_count: int = 5) -> Dict[str, int]:
    """
    词频分析器：
    输入筛选好的因子 DataFrame，提取所有因子 ID 并使用 '_' 拆分。
    统计各个词根的出现频率，并展示匹配数量大于 min_count 的词根。
    """
    if df.empty or 'id' not in df.columns:
        print("[INFO] 因子列表为空或不包含 id 列，无法进行词频分析。")
        return {}

    # 提取所有因子的 ID
    factor_ids = df['id'].dropna().tolist()
    
    # 拆分并打散成单词列表
    all_words = []
    for fid in factor_ids:
        # 按下划线拆分，并过滤掉空字符串
        words = [w for w in fid.split('_') if w]
        all_words.extend(words)
        
    # 统计词频
    word_counts = Counter(all_words)
    
    # 筛选大于 min_count 的词
    filtered_counts = {word: count for word, count in word_counts.items() if count > min_count}
    
    # 按词频从高到低排序
    sorted_counts = dict(sorted(filtered_counts.items(), key=lambda item: item[1], reverse=True))
    
    if not sorted_counts:
        print(f"[INFO] 没有找到匹配数量大于 {min_count} 的词根。")
        return {}
        
    print(f"\n[INFO] 因子词频分析结果 (展示出现 > {min_count} 次的词根):")
    for word, count in sorted_counts.items():
        print(f"  - {word:<20} : {count} 个")
        
    return sorted_counts

def filter_by_keywords(df: pd.DataFrame, keywords: Union[str, List[str]], match_all: bool = False) -> pd.DataFrame:
    """
    关键词过滤器：
    输入筛选好的因子 DataFrame 和 匹配字段(一个或多个)。
    返回包含这些字段的因子列表。
    - match_all=True: 因子名必须包含所有传入的 keyword
    - match_all=False: 因子名包含任意一个 keyword 即可
    """
    if df.empty or 'id' not in df.columns:
        return pd.DataFrame()
        
    if isinstance(keywords, str):
        keywords = [keywords]
        
    if not keywords:
        return df
        
    # 确保小写匹配，提升鲁棒性
    keywords = [k.lower() for k in keywords]
    
    def check_match(factor_id):
        if not isinstance(factor_id, str):
            return False
        fid_lower = factor_id.lower()
        if match_all:
            return all(k in fid_lower for k in keywords)
        else:
            return any(k in fid_lower for k in keywords)
            
    # 使用布尔索引过滤
    mask = df['id'].apply(check_match)
    return df[mask].copy()

def filter_by_metrics(df: pd.DataFrame, 
                      min_coverage: float = None, 
                      min_date_coverage: float = None,
                      max_alpha_count: int = None, 
                      min_alpha_count: int = None,
                      newer_than_date: str = None,
                      min_value_score: float = None) -> pd.DataFrame:
    """
    量化指标高级过滤器：
    - min_coverage: 最低覆盖率，例如 0.2 (20%)，过滤掉覆盖率太低容易导致换手率不合格的废弃字段。
    - min_date_coverage: 最低时间覆盖率，例如 0.6，过滤长期断档的数据字段。
    - max_alpha_count: 过滤掉过度拥挤的字段 (防止 PROD 相关性太高)。
    - min_alpha_count: 过滤掉太难挖或者毫无头绪的死坑字段。
    - newer_than_date: 'YYYY-MM-DD' 格式，只保留在这之后新上的字段（低相关性蓝海）。
    - min_value_score: 最低 Value Score，例如 6.0，寻找包含高预测力的高级数据集字段。
    """
    if df.empty:
        return df

    mask = pd.Series(True, index=df.index)

    if min_coverage is not None and 'coverage' in df.columns:
        cov = pd.to_numeric(df['coverage'], errors='coerce').fillna(0)
        mask = mask & (cov >= min_coverage)

    if min_date_coverage is not None and 'dateCoverage' in df.columns:
        date_cov = pd.to_numeric(df['dateCoverage'], errors='coerce').fillna(0)
        mask = mask & (date_cov >= min_date_coverage)

    if max_alpha_count is not None and 'alphaCount' in df.columns:
        ac = pd.to_numeric(df['alphaCount'], errors='coerce').fillna(0)
        mask = mask & (ac <= max_alpha_count)
        
    if min_alpha_count is not None and 'alphaCount' in df.columns:
        ac = pd.to_numeric(df['alphaCount'], errors='coerce').fillna(0)
        mask = mask & (ac >= min_alpha_count)

    if newer_than_date is not None and 'dateCreated' in df.columns:
        dc = pd.to_datetime(df['dateCreated'], errors='coerce')
        target_date = pd.to_datetime(newer_than_date)
        mask = mask & (dc >= target_date)
        
    if min_value_score is not None and 'valueScore' in df.columns:
        vs = pd.to_numeric(df['valueScore'], errors='coerce').fillna(0)
        mask = mask & (vs >= min_value_score)

    return df[mask].copy()
