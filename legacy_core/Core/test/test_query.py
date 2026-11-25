import sys
import os
from pathlib import Path
import pandas as pd

# 添加父目录到环境变量，以允许正确的 import
parent_dir = str(Path(__file__).parent.parent)
sys.path.append(parent_dir)

from Core.catalog.catalog_db import CatalogDB
from Core.catalog.factor_utils import analyze_keyword_frequency, filter_by_keywords


def print_factor_details(df: pd.DataFrame, num: int = 2):
    """
    专门用于打印因子详细信息的独立函数。
    将因子的全量字段以易读的字典/JSON格式打印出来。
    """
    if df.empty:
        return
        
    print(f"[INFO] 抽取前 {min(num, len(df))} 个因子的详细信息展示:")
    # 抽取前几行，转为字典列表方便遍历打印
    sample_records = df.head(num).to_dict('records')
    
    for i, record in enumerate(sample_records, 1):
        print(f"  [{i}] 因子 ID: {record.get('id', 'N/A')}")
        print(f"      - Dataset: {record.get('dataset_id', 'N/A')} ({record.get('dataset_name', '')})")
        print(f"      - Region: {record.get('region', 'N/A')} | Universe: {record.get('universe', 'N/A')}")
        print(f"      - Category: {record.get('category_name', 'N/A')} | Subcategory: {record.get('subcategory_name', 'N/A')}")
        print(f"      - Type: {record.get('type', 'N/A')} | Delay: {record.get('delay', 'N/A')}")
        print(f"      - Coverage: {record.get('coverage', 'N/A')}")
        print(f"      - Description: {record.get('description', 'N/A')}")
        print("      " + "-"*40)


def test_flexible_queries():
    db = CatalogDB()
    
    print("--- 场景 1: 完全没有任何条件，查全量 (会查遍所有地区所有表) ---")
    df1 = db.query_factors()
    if not df1.empty:
        print(f"[OK] 查到全库总计 {len(df1)} 个因子。\n")
    
    print("--- 场景 2: 只查特定 Region (中国区) ---")
    df2 = db.query_factors(region='CHN')
    if not df2.empty:
        print(f"[OK] 查到中国区 (CHN) 总计 {len(df2)} 个因子。\n")
    
    print("--- 场景 3: 组合查询 (Region + Universe + Category) ---")
    # 注意: USA区真实存的universe可能是 TOPSP500 等细分板块，我们用真实的 TOPSP500 测试
    df3 = db.query_factors(region='USA', universe='TOPSP500', category='Model')
    if not df3.empty:
        print(f"[OK] 查到 USA区 + TOPSP500股票池 + Model类别 的因子共计 {len(df3)} 个。")
        print_factor_details(df3, num=1)
    print("\n")
    
    print("--- 场景 4: 组合查询 (Region + Category) ---")
    df4 = db.query_factors(region='EUR', category='Analyst')
    if not df4.empty:
        print(f"[OK] 查到 欧洲区 (EUR) + Analyst类别 的因子共计 {len(df4)} 个。")
        print_factor_details(df4, num=1)
    print("\n")
    
    print("--- 场景 5: 精确查询某地区特定数据集 (Region + Dataset ID) ---")
    # 注意: model25 实际在 GBR 英国区，所以我们查 GBR
    df5 = db.query_factors(region='GBR', dataset_id='model25')
    if not df5.empty:
        print(f"[OK] 查到 GBR 区 dataset 为 model25 的因子共计 {len(df5)} 个。")
        print_factor_details(df5, num=2)
    print("\n")
    
    print("--- 场景 6: 精确查询附带模糊匹配 (Region + Dataset ID + Search) ---")
    df6 = db.query_factors(region='USA', dataset_id='fundamental31', search='revenue')
    if not df6.empty:
        print(f"[OK] 查到 USA区 + fundamental31数据集 + 包含 'revenue' 的因子共计 {len(df6)} 个。")
        print_factor_details(df6, num=2)
    print("\n")

    print("--- 场景 7: 大范围模糊匹配 (Region + Search) ---")
    df7 = db.query_factors(region='USA', search='sentiment')
    if not df7.empty:
        print(f"[OK] 查到 USA 区带有 'sentiment' 关键词的因子共计 {len(df7)} 个。")
        # 大范围查到的数据太多，这里就不详细打印了
    print("\n")

    print("--- 场景 8: 智能进阶分析 (词频分析 + 关键词及量化指标过滤) ---")
    # 步骤 1: 查出一个目标大类（比如 USA 的 Model 类别因子）
    df8_base = db.query_factors(region='USA', category='Model')
    print(f"[OK] 步骤 1: 捞取 USA 区所有的 Model 类别因子，共计 {len(df8_base)} 个。")
    
    # 步骤 2: 对捞取到的因子群，进行词根切分和词频统计 (自动揭示高频思路)
    from factor_utils import analyze_keyword_frequency, filter_by_keywords, filter_by_metrics
    
    print("[INFO] 步骤 2: 开始统计高频因子的特征词 (仅显示出现大于 200 次的):")
    analyze_keyword_frequency(df8_base, min_count=200)
    
    # 步骤 3: 关键词提纯 (展示 match_all=False 和 True 的区别)
    target_words = ['forecast', 'yield']
    print(f"\n[INFO] 步骤 3A: 二次过滤 -> 包含 {target_words} 中 【任意一个】 的因子 (match_all=False)...")
    df8_any = filter_by_keywords(df8_base, keywords=target_words, match_all=False)
    print(f"       -> 命中 {len(df8_any)} 个因子。")
    
    print(f"[INFO] 步骤 3B: 二次过滤 -> 必须 【同时包含】 {target_words} 所有词的因子 (match_all=True)...")
    df8_all = filter_by_keywords(df8_base, keywords=target_words, match_all=True)
    print(f"       -> 命中 {len(df8_all)} 个因子。")
    if not df8_all.empty:
        print_factor_details(df8_all, num=1)

    # 步骤 4: 加入量化指标进行极端“蓝海挖掘”过滤
    # 假设我们要在 df8_any 里面，找出 覆盖率 >= 0.2，且 平台提交 Alpha 数量少于 5 个(不拥挤)，且是 2026年 以后出的新字段。
    print("\n[INFO] 步骤 4: 进行量化指标过滤 (寻找高覆盖、未被过度挖掘的新星蓝海字段)...")
    df8_metrics = filter_by_metrics(
        df8_any, 
        min_coverage=0.20, 
        max_alpha_count=5, 
        newer_than_date='2026-01-01'
    )
    print(f"       -> 经过 Coverage >= 20%, AlphaCount <= 5, 日期>=2026 过滤后，剩下 {len(df8_metrics)} 个终极候选。")
    if not df8_metrics.empty:
        print_factor_details(df8_metrics, num=2)

if __name__ == "__main__":
    test_flexible_queries()

