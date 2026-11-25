import json
import os

export_dir = 'exports'
os.makedirs(export_dir, exist_ok=True)

# 1. 导出插件中性化数据 (Plugin Neutralization Insights)
plugin_data = {
    "field_pattern": "analyst*",
    "insights": [
        {
            "neutralization": "INDUSTRY",
            "usage_percent": 90.04,
            "avg_sharpe": 0.29,
            "note": "大众常用，极度拥挤，易被 PROD 判定高相关"
        },
        {
            "neutralization": "SUBINDUSTRY",
            "usage_percent": 2.38,
            "avg_sharpe": 0.55,
            "note": "强力推荐：极少人使用，夏普翻倍，极大概率通过 PROD 独特性检查"
        }
    ]
}
with open(f'{export_dir}/Plugin_Neutralization_Insights.json', 'w', encoding='utf-8') as f:
    json.dump(plugin_data, f, ensure_ascii=False, indent=4)

# 2. 导出并修改区域推荐范围 (Region Recommendations)
orig_path = r'C:\Users\31186\.gemini\antigravity\brain\b9bf721c-4d79-4a41-a877-5277fdd86c4e\region_recommendations.json'
with open(orig_path, 'r', encoding='utf-8') as f:
    rec_data = json.load(f)

# 融入最新的 WDS 分析洞察
rec_data['GLB']['recommended_datasets'].append("analyst15 (Tier 1 Whitelist)")
rec_data['GLB']['advisor_notes'] += " 【2026最新洞察】分析师预期(analyst15)类因子在 GLB 极具挖掘价值！强烈建议：完全抛弃传统的 INDUSTRY 中性化，改用 SUBINDUSTRY 中性化（经过插件数据验证，夏普率可翻倍且避开拥挤人群）。"

with open(f'{export_dir}/region_recommendations_updated.json', 'w', encoding='utf-8') as f:
    json.dump(rec_data, f, ensure_ascii=False, indent=4)

print("Files created successfully!")
