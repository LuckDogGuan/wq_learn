# 地区独立作战档案：`HKG / TOP800 / D1`（香港市场 · `1.7×` 空白高倍率探针）

- **宇宙范围**：合法 D1 为 **`TOP800`（主选）**、 `TOP500`。选 `TOP800` 提供更宽截面降低集中度风险。
- **市场与规则**：单一市场（不支持 `COUNTRY`），常规 D1 门槛（`Sh>1.58, Fit>1.0, 2Y>1.58`, 经验 `M≥10bp`），1 并发槽；账号当前 **`0` OS**（零本地 SC 撞车），`analyst`/`model`/`other` 享 **`1.7×`**，`fundamental`/`news`/`sentiment` 享 `1.6×`。
- **微观结构**：受外资机构流动、中资南下资金与港股新闻事件驱动明显，流动性向中大盘集中，须严控换手率与 `truncation=0.04`。
- **首轮实盘核验探针（2026-11-25 `cnhkmcp`）**：
  - **`news_sentiment_dl`**（`other` **`1.7×`**, **`Alphas=0` 免额**, `VECTOR`, `cov=86.3%`, `dCov=0.9507`）：`min_positive_word_sentiment_inferess`, `positive_word_sentiment_entropy_inferess`, `positive_word_sentiment_stddev_inferess`, `text_complexity_score_inferess`, `sentence_count_inferess`, `avg_words_per_sentence_inferess`。
- **独立漏斗快照**：`data/exports/hkg_ra_funnel_latest.json`。
- **2026-11-25 18:15（巡检 #2）**：`news_sentiment_dl` 首波完成 32 条（24 条入库，已修 `batch_id` 24 字符前缀碰撞），出现 **`RR5Mwj1j`（`min_positive_word_sentiment_inferess`, `Sh=-0.95` → 正向 `+0.95`）** 与 **`2rGMo8LN`（`Sh=+0.64, 2Y=+1.35, Margin=+8.93bp`）**，确有真实信号，继续保留在多市场轮巡中。
