# 地区独立作战档案：`IND / TOP500 / D1`（印度市场 · `1.4×` 新兴成长轻探针）

- **宇宙范围**：合法 D1 仅 **`TOP500`**（印度流动性前 500 只上市股，唯一主池）。
- **市场与规则**：单一市场（不支持 `COUNTRY`），常规 D1 门槛（`Sh>1.58, Fit>1.0, 2Y>1.58`, 经验 `M≥10bp`），1 并发槽；账号当前 **`0` OS**（零本地 SC 撞车），`analyst (1.4×)`、`fundamental/news/other (1.3×)`。
- **微观结构**：高成长新兴市场、大型企业集团（金融/IT/能源）市值权重集中，严守 `truncation=0.04` 防单股权重超 10%；注意筛选数据时必检 **`dateCoverage ≥ 0.80`**（本次实测 `quant_factor_lib` 在 IND 仅 `dCov = 0.3924` 已主动剔除！）。
- **首轮实盘核验探针（2026-11-25 `cnhkmcp`）**：
  - **`ai_news_scores`**（`other` `1.3×`, `MATRIX`, `cov=69.3%`, `dCov=0.9255`, `aCnt=3–5`）：`negative_score_median_value_4`, `negative_score_median_value_5`, `negative_score_minimum_value_4`, `negative_score_maximum_value_2`, `negative_score_minimum_value_2`, `negative_sentiment_upper_estimate_2`。
- **独立漏斗快照**：`data/exports/ind_ra_funnel_latest.json`。
