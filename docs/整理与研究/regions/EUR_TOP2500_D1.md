# 地区独立作战档案：`EUR / TOP2500 / D1`（泛欧多国市场 · Tier-1 高 Base 首选主力）

> [!IMPORTANT]
> - **战略定位**：`EUR` 是 BRAIN **Tier-1 高 Base Weight 核心市场**之一，且在广州历史 7,894 条回测复盘中 **`EUR / TOP2500` 录得全场最高的平均最优 Sharpe（`2.018`，157 条样本）**！
> - **金字塔现状（2026-11-25 实时核验）**：现有 `26` 条 EUR OS，其中 **`other` 塔倍率最高（`1.5×`）**，而 **`model (1.3×)`、`news (1.4×)`、`sentiment (1.4×)` 均为空白 `0` OS**（`analyst` 仅 `1` OS）！

---

## 1. 欧洲股票市场特征与宇宙/规则说明

- **宇宙范围选择**：官方合法 D1 Universes 为 `TOP2500`, `TOP1200`, `TOP800`, `TOP400`, `TOPCS1600`。
  - **主战宇宙：`TOP2500`** —— 覆盖英/德/法/瑞/荷/北欧等泛欧约 2,500 只高流动性股票，截面宽、容量大、单股集中度风险低；
  - 备选排障宇宙：若遇 `Sub-Universe Sharpe` 不足，可单独在 `TOP1200` / `TOP800` 对照检查大中盘稳定性。
- **市场微观结构**：跨多国、多币种（EUR/GBP/CHF/SEK 等），机构主导，质量/动量/盈利修正与深度新闻情绪信号稳定性极高；**多国池天然支持 `COUNTRY` 中性化**，配 `SUBINDUSTRY` / `REVERSION_AND_MOMENTUM` 消除跨国宏观 beta 非常有效。
- **平台 RA 硬门槛**：`Delay = 1` · `Sharpe > 1.58` · `Fitness > 1.0` · `2Y Sharpe > 1.58` · `1% < TVR < 70%` · `Weight < 10%` · 经验 `Margin ≥ 10bp` · 并发占 **1 槽**。
- **本地 SC 注意事项**：本账号已有 `26` 条 EUR OS，Stage-4 必须用全量同步的 `os_pnl_cache.db` 严查本地 SC `< 0.68`（优先主攻 `0 OS` 的 `model`/`news`/`sentiment` 与新数据集降撞车率）。

---

## 2. 严格分层首轮探针资产（2026-11-25 `cnhkmcp` 实盘核验）

| 梯队 | Dataset ID | 目标塔 (倍率 / 现 OS) | 队列 | 字段类型 & 覆盖率 | 首轮精选清洗字段 |
| :-: | --- | :-: | :-: | --- | --- |
| **P0** | **`news_sentiment_dl`** | `other` (`1.5×` / 4) | **`Alphas=0` 免额** | `VECTOR`, `cov=75.1–77.2%`, `dCov=0.9507` | `min_positive_word_sentiment_inferess`, `negative_word_count_inferess`, `negative_word_sentiment_stddev_inferess`, `positive_word_sentiment_entropy_inferess`, `min_negative_word_sentiment_trna`, `min_positive_word_sentiment_trna` |
| **P0** | **`price_signal_dl`** | `model` (`1.3×` / **0**) | `NORMAL` (`aCnt=1–5`) | `MATRIX`, **`cov=100%`**, `dCov=0.87–0.95` | `raw_trend_indicator_2`, `raw_volume_indicator_2`, `normalized_trend_indicator_6`, `raw_trend_indicator_0`, `raw_volume_indicator_3`, `normalized_trend_indicator_2`, `raw_trend_indicator_1`, `raw_trend_indicator_6` |
| **P1** | **`analyst10`** | `analyst` (`1.3×` / 1) | `NORMAL` (`aCnt=11–16`) | `MATRIX`, `cov=50.2%`, `dCov=1.0` | `anl10_analyst_innovation_tbv_revise_ratio_to_consensus_fy1`, `anl10_analyst_innovation_tbv_revise_ratio_to_close_fy1`, `anl10_analyst_innovation_tbv_innovation_score_fy1` *(严格剔除 `*_det_excflag`/`*_det_indicator`/`*_det_anntime` 等元数据陷阱！)* |

- **中性化轮换序列**：`SUBINDUSTRY` → `COUNTRY` → `REVERSION_AND_MOMENTUM`（前置 `ts_mean(x, 22)` / `ts_decay_linear(x, 10)` 控换手保 `Margin ≥ 10bp`）。
- **独立漏斗快照**：`data/exports/eur_ra_funnel_latest.json`。

---

## 3. 实盘运行与 30 分钟滚动复盘日志

- **2026-11-25 17:26（建档完成）**：完成 `EUR/TOP2500/D1` 实时字段核验与探针队列接入，纳入高 Base 多市场轮巡首位。
