import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def plot_histogram(df, column_name, plot_title, bins):
    sns.set(style="whitegrid")
    plt.figure(figsize=(10, 6))
    
    # 过滤出非空数据
    valid_data = df[column_name].dropna()
    if len(valid_data) == 0:
        print(f"⚠️ 列 {column_name} 无有效数据，跳过绘图。")
        return
        
    sns.histplot(valid_data, bins=bins, kde=False, color='skyblue', edgecolor='black')
    
    # 画一条均值线作为参考
    mean_val = valid_data.mean()
    plt.axvline(mean_val, color='red', linestyle='dashed', linewidth=1.5, label=f'Mean: {mean_val:.2f}')
    plt.legend()
    
    plt.title(plot_title, fontsize=16)
    plt.xlabel(column_name, fontsize=14)
    plt.ylabel('Frequency', fontsize=14)
    plt.tight_layout()
    plt.show()

def main():
    print("=" * 60)
    print("📊 数据集质量可视化评估工具 (Dataset Visualization)")
    print("通过绘制 Alpha 关键指标的分布直方图，帮您一眼看穿当前数据集是否有挖掘价值。")
    print("=" * 60)
    
    # 提示输入 CSV 路径
    csv_path = input("请输入包含 Alpha 指标数据的 CSV 文件路径 (例如: data.csv):\n> ").strip()
    
    if not csv_path or not os.path.exists(csv_path):
        print(f"❌ 找不到文件: {csv_path}")
        # 创建演示文件
        print("正在生成 demo_alphas.csv 供您体验测试...")
        demo_data = pd.DataFrame({
            'alpha_id': [f'alpha_{i}' for i in range(100)],
            'sharpe': np.random.normal(0.8, 0.5, 100),      # 模拟正偏的Sharpe
            'turnover': np.random.uniform(0.01, 0.3, 100),  # 模拟低换手
            'fitness': np.random.normal(0.6, 0.3, 100),
            'longCount': np.random.randint(100, 1000, 100),
            'shortCount': np.random.randint(100, 1000, 100)
        })
        demo_data.to_csv("demo_alphas.csv", index=False)
        csv_path = "demo_alphas.csv"
        print(f"✅ 已自动加载 {csv_path}。")
        
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"❌ 读取 CSV 失败: {e}")
        return
        
    required_cols = {'sharpe', 'turnover', 'fitness', 'longCount', 'shortCount'}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"⚠️ 警告: 您的 CSV 中缺少以下列，可能无法绘制部分图表: {missing}")
        
    # 定义常见分箱规则
    sharp_bins = np.arange(-3, 3.1, 0.2).round(2)
    turnover_bins = np.arange(0, 1.05, 0.05).round(2)
    fitness_bins = np.arange(-2, 2.05, 0.1).round(2)
    count_bins = np.arange(0, 3000, 100)

    # 绘制图形
    if 'sharpe' in df.columns:
        print("\n📈 正在绘制 Sharpe 比例分布...")
        print("💡 优秀特征: 分布明显右偏，大量数据集中在 0 以上，甚至有超过 1 的肥尾。")
        plot_histogram(df, 'sharpe', 'Distribution of Sharpe Ratio', bins=sharp_bins)
        
    if 'turnover' in df.columns:
        print("\n📈 正在绘制 Turnover 分布...")
        print("💡 优秀特征: 大部分因子的换手率在 0.2 以下，说明信号稳定。")
        plot_histogram(df, 'turnover', 'Distribution of Turnover', bins=turnover_bins)
        
    if 'fitness' in df.columns:
        print("\n📈 正在绘制 Fitness 分布...")
        plot_histogram(df, 'fitness', 'Distribution of Fitness', bins=fitness_bins)
        
    if 'longCount' in df.columns:
        print("\n📈 正在绘制 Long Count 分布...")
        plot_histogram(df, 'longCount', 'Distribution of Long Count', bins=count_bins)
        
    if 'shortCount' in df.columns:
        print("\n📈 正在绘制 Short Count 分布...")
        plot_histogram(df, 'shortCount', 'Distribution of Short Count', bins=count_bins)
        
    print("\n🎉 绘图完成！如果您发现数据集的 Sharpe 主要集中在左侧负数区域，建议立刻换一个数据集，及时止损。")

if __name__ == "__main__":
    main()
