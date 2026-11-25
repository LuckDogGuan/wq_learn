# 地区独立作战档案：`USA / TOP3000 / D1`（美股市场 · Tier-1 最高 Base 核心池）

> [!IMPORTANT]
> - **战略定位**：`USA` 是 WorldQuant BRAIN **Base Weight（资金容量与基础收益权重）最高的单一核心市场**！
> - **金字塔现状（2026-11-25 实时核验）**：现有 `14` 条 USA OS（其中 `analyst` 占 8 条），而 **`sentiment (1.5×)`、`other (1.4×)`、`model (1.3×)`、`earnings (1.3×)`、`option (1.3×)` 均为 `0` OS 空白塔**！
> - **广州历史避坑教训**：历史上盲扫 `USA / TOP1000` 情绪长衰减 129 次均 Sharpe 仅 `1.303`、产出极差；因此 **USA 绝不跑 `TOP1000` 老旧情绪长衰减**，必须锁定 **`TOP3000`** 宽池 + **高覆盖新上架/低拥挤/免费数据集**！

---

## 1. 美股市场特征与宇宙/规则说明

- **宇宙范围选择**：官方合法 D1 Universes 为 `TOP3000`, `TOP2000`, `TOP1000`, `TOP500`, `TOP200`, `TOPSP500`。
  - **主战宇宙：`TOP3000`** —— 覆盖美股流动性前 3,000 只（含 Russell 3000 主体），大中小盘跨度完整、低拥挤新信号超额空间显著优于极度有效的 `TOP500`/`TOPSP500`；
  - 避坑提示：切忌在 `TOP200`/`TOPSP500` 做常规 Stage-1 普筛（头部大盘定价极有效，易浪费额度）。
- **市场微观结构**：全球定价效率最高、机构与量化资金密度最高；单因子容易撞 PC（生产相关性），因此优先采用 **低拥挤 `Alphas=0` / `aCnt=1-3` 新数据集** + **同集双支 `min(rank(A), rank(B))`** + **`signed_power` / `subindustry` 截面分组** 压低 PC！
- **平台 RA 硬门槛**：`Delay = 1` · `Sharpe > 1.58` · `Fitness > 1.0` · `2Y Sharpe > 1.58` · `1% < TVR < 70%` · `Weight < 10%` · 经验 `Margin ≥ 10bp` · 并发占 **1 槽** · **不支持 `COUNTRY` 中性化**。

---

## 2. 严格分层首轮探针资产（2026-11-25 `cnhkmcp` 实盘核验）

| 梯队 | Dataset ID | 目标塔 (倍率 / 现 OS) | 队列 | 字段类型 & 覆盖率 | 首轮精选清洗字段 |
| :-: | --- | :-: | :-: | --- | --- |
| **P0** | **`price_signal_dl`** | `model` (`1.3×` / **0**) | **`Alphas=0` 免额 + `aCnt=1`** | `MATRIX`, `cov=78.6%–95.6%`, `dCov=0.9507` | 4 个纯免额 `raw_volume_indicator_0/3/5/6` + 低拥挤 `raw_trend_indicator_6`, `raw_volume_indicator_1/2/4` |
| **P0** | **`news_sentiment_dl`** | `other` (`1.4×` / **0**) | **`Alphas=0` 免额** | `VECTOR`, **`cov=100%`**, `dCov=0.9507` | `min_negative_word_sentiment_djnews`, `min_negative_word_sentiment_inferess`, `min_negative_word_sentiment_trna_us`, `negative_word_sentiment_stddev_djnews`, `output_metric_1_djnews`, `output_metric_1_inferess` |
| **P1** | **`other566`** | `other` (`1.4×` / **0**) | `NORMAL` (`aCnt=2–4`) | `MATRIX`, **`cov=100%`**, `dCov=0.95–1.0` | `oth566_l3r20gasfmulti_prob_last_pattern`, `oth566_l5r20gasfculr_prob_pattern`, `five_bucket_return_rank_confidence_l3`, `twenty_bucket_return_rank_confidence_l5`, `oth566_l3r20gasf_prob` |
| **P1** | **`fundamental91`** | `fundamental` (`1.1×`) | **`Alphas=0` 免额** | `VECTOR`, `cov=65.2–65.8%`, `dCov=0.9507` | 财报文本情绪分 `cat8_secondary_sentiment_score0`, `cat7_secondary_sentiment_score0/1`, `fnd91_cat0_sentiment1_0` |

- **中性化轮换序列**：`SUBINDUSTRY` → `REVERSION_AND_MOMENTUM` → `CROWDING`（严禁传 `COUNTRY`）。
- **独立漏斗快照**：`data/exports/usa_ra_funnel_latest.json`。

---

## 3. 实盘运行与 30 分钟滚动复盘日志

- **2026-11-25 17:26（建档完成）**：完成 `USA/TOP3000/D1` 实时免额/低拥挤字段核验，纳入高 Base 多市场轮巡。
- **2026-11-25 17:45（30 分钟巡检 #1 · `price_signal_dl` 首波 32 条即出高质种子！）**：
  - `USA / TOP3000 / price_signal_dl`（`Alphas=0` 免额，Wave #1 `32` FULL 仅耗时 `144.1s`）：
    - **头号高质种子 `N1K03xae`**（`raw_volume_indicator_6` · `group_rank(ts_decay_linear(ts_backfill(raw_volume_indicator_6, 21), 10), subindustry)`）：**`Sharpe = +1.10`、`2Y Sharpe = +1.84`（已远超 1.58！）`、Fit = 0.67、TO = 3.71%、Margin = +24.91bp`**！同时落入最高 Base 市场 `USA` + `model (1.3×, 0 OS)` 空白塔！
    - 同批另出 `RR5MKj6n`（`Sh=-0.92, 2Y=-1.55`，说明 `raw_volume_indicator_6` 经 `ts_zscore(...,66)` **正向**约 `+0.92 / 2Y +1.55`）与 `omP7GbJE`（`raw_volume_indicator_3`, `Sh=+0.70, 2Y=+1.29`）及 `MPgOzEz9`（`-0.79, 2Y=-1.39`）。
  - **方向修正建议**：`price_signal_dl` 的 `raw_volume_indicator_*` 系列在美股呈现清晰**正向 + 高 2Y + 超低换手高 Margin** 特征！待 Pass 1 全市场摸底完毕后，将把 `raw_volume_indicator_0..6` 与 `raw_trend_indicator_0..6` 的正向 `group_rank`/`group_zscore` + 同集双支 `min(rank(vol), rank(trend))` 作为 USA 第一精修主力！

- **2026-11-25 19:16（1 小时定时检查 #1 · `USA / price_signal_dl` 稳居全场头号真 Alpha 矿脉！）**：
  - 累计完成 `64` 条即收获 **`8` 条纯正向 `POOL_B` 种子**（对称验真，非成本假象！）：`xAl6KWkp` (`Sh=+1.10, 2Y=+1.85, Mgn=+26.42bp`)、`N1K03xae` (`Sh=+1.10, 2Y=+1.84, Mgn=+24.91bp`)、`gJrAY2bM` (`Sh=+1.06, 2Y=+1.99, TO=2.66%, Mgn=+33.40bp`!)、`j2VE57mo` (`+0.89`)、`1YG9qMQR` (`+0.87`)、`np6J1r2a` (`+0.87`)、`xAl6KZYw` (`+0.84`)。
  - **加码方向**：已将 `USA` 置顶为全队列第 1 顺位，新增 `USA_PRICEDL_NORMVOL_FREE`（5 个实盘核验 `Alphas=0` `normalized_volume_indicator_1/2/3/5/6`）与 `USA_PRICEDL_TREND_VOL_NORM`（`raw_trend_indicator_0..6` + 跨子族量价双支 `min(rank(vol), rank(trend))`），主冲 `Sharpe > 1.58`！
