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

- **2026-11-25 20:16（1 小时定时检查 #2 · 新增 `option_horizon_decomp` 免额期权偏度/期限矿脉！）**：
  - `USA / price_signal_dl` 累计 `128` 条收获 `10` 条 `POOL_B`（最高 `Sh=+1.10, 2Y=+1.99, Mgn=+33.4bp`），单字段天花板暂卡在 `1.10`；需补入更高毛 Alpha 矿脉破 `1.58`！
  - **新增核心矿脉**：经 `cnhkmcp` 实盘核验 **`option_horizon_decomp`**（`option 1.3×`, 本账号 **`0` OS**, `cov=96.7–98.4%`, `dCov=0.9507`）含 **8 个纯 `Alphas=0` 免额 MATRIX**（`put_call_open_interest_ratio_*`、`put_call_volume_ratio_*`、`implied_volatility_*`）+ 4 个免额期限结构价差（借鉴历史 `Sh=2.22, Fit=2.58, Mgn=27bp` 的期权 IV 骨架），已置顶第 2 顺位开跑！

- **2026-11-25 22:20（2 小时定时审计 #1 · `price_signal_dl` 冲破第 2 轮目标 `1.51 / 2Y 2.89 / PC 0.749`！果断止损期权集并换入 `model238`）**：
  - **重大突破**：`USA / TOP3000 / price_signal_dl`（`232` FULL）一举冲破第 2 轮目标（`1.30–1.45+`），连出 **`3` 条 `POOL_A` 强因子**，且 **2Y Sharpe 全面爆表（`2.33–2.89`）**、**远程 `PC` 已迫近可提交黄金解救区（`0.749`！）**：
    - **`xAl6rxYw`**：`group_rank(ts_zscore(ts_mean(ts_backfill(raw_trend_indicator_1, 21), 5), 66), subindustry)`（`RAM, d=0`）→ **`Sh = +1.51, 2Y = +2.89, Fit = 0.69, TO = 25.4%, Mgn = 4.22bp, PC = 0.7490`**（距 `< 0.70` 仅差 `0.049`！）；
    - **`gJrAXo2J`**：`min(rank(raw_volume_indicator_6), rank(raw_trend_indicator_1))` 双支（`RAM, d=0`）→ **`Sh = +1.49, 2Y = +2.65, Fit = 0.74, TO = 19.1%, Mgn = 4.90bp, PC = 0.7576`**；
    - **`xAl6VmEw`**：`min(rank(raw_volume_indicator_6), rank(raw_trend_indicator_4))` 双支（`RAM, d=0`）→ **`Sh = +1.43, 2Y = +2.33, Fit = 0.64, TO = 22.9%, Mgn = 3.99bp`**。
  - **果断止损弱向**：`USA / TOP3000 / option_horizon_decomp` 完成 `64` FULL 仅 `1` 条刚过 `0.80`（`YPlrpXQw Sh=0.84, 2Y=0.07`，命中率 `1.56% < 2%`），立即移出主队列停止浪费算力！
  - **本轮精准方向修正**：
    1. **上线 `S3-r2-USA-PSD-*` 第 3 轮专项冲刺包**（[stage23_refiner.py](../../../wq_research_v2/src/wq_research_v2/stage23_refiner.py)）：在 `xAl6rxYw` / `gJrAXo2J` / `xAl6VmEw` 骨架上将 `ts_mean(..., 5)` 轻度拉长至 `10/15/22` + `decay ∈ {4, 6}` + `hump=0.01`（把换手从 `25%` 压至 `7–12%`，同步拉升 **Fitness `0.74→1.1+`** 与 **Margin `4.9bp→10bp+`**）+ **`if_else(rank(adv20) > 0.35, ...)`** 解救 `Sub-Universe` + **`STATISTICAL` / `SLOW_AND_FAST` / `CROWDING` / `signed_power(..., 2)` / 融合 `model238`**，一举把 `Sh 1.51 → 1.65+` 且 `PC 0.749 → < 0.65`！
    2. **换入高价值超低拥挤新矿脉 `USA / TOP3000 / model238`（SmartHoldings）**：实盘核验 `cov = 96.74%`, `val = 5.0`, 8 个 MATRIX 字段全部仅 `aCnt = 1–3`（`model 1.3×, 0 OS`），天然低 PC 撞车率！

- **2026-11-26 00:35（2 小时定时审计 #1 · 单轴纠偏验证成功 + 3 个新数据集并行验证 + 4,500/天流水线上线）**：
  - **坏批次纠偏实证**：`S3-r2-USA-PSD` 因同时修改窗口+`adv20`硬切+`decay` 导致 `1.51 → 0.77`；切换严格单轴 **`S3-r3b-USA-1AX`** 后立刻恢复 **`Jj3Ej6bO`（`Sh=1.51, 2Y=2.89, sub=PASS:0.82/0.65`）**、**`RR5QRjmj`（`Sh=1.47, 2Y=2.84, sub=PASS`）** 与 **`LL8aLV7L`（`Sh=1.46, 2Y=2.66`）**。
  - **数据集快速止损与新集初筛**：`USA / model238` 满 `48` 条 `0` 命中（`max=0.61`）已自动早停；新换入 **`USA / forward_beta_risk`** 首波即出 **`kq8rxe3k`（`Sh=0.99, Mgn=6.33bp`）**，**`USA / news_sentiment_nlp`** 首波出 **`wpNxpZ3Y`（`Sh=0.89`）**，**`USA / forum_sentiment`** 正在零屏障连续流水线中与 `EUR` 2+2 混跑推进。

- **2026-11-26 02:50（2 小时定时审计 #2 · `price_signal_dl` `POOL_A` 扩至 `10` 条 + 淘汰低天花板舆情集、换入 `model68` DREAM 风险调整动量！）**：
  - **漏斗增量**：`USA / TOP3000` 累计 `664` FULL，一阶段 `83` 条、二阶段 `POOL_A` 从 `2` 条暴增至 **`10` 条**（全部由 `price_signal_dl` 单轴微调贡献：`Jj3Ej6bO 1.51/2Y 2.89`、`akRZk5ow 1.49/2Y 2.65`、`xAl6VmEw 1.43/2Y 2.33`、`blxZle1p 1.42/2Y 2.62`、`9qG1qN3V 1.41/2Y 2.79`、`XgNQgd1b 1.28/2Y 2.62` 等）。
  - **数据集果断换血**：`USA / news_sentiment_nlp`（`80 FULL, max=0.91, 2Y=0.77`）与 `USA / forum_sentiment`（`80 FULL, max=0.86, 2Y=0.94`）天花板明显偏低，本轮下线停止消耗额度；保留 `price_signal_dl` + `forward_beta_risk`（`max=0.99`），并引入实盘核验的 **`USA / model68`（DREAM Risk-Alleviated Momentum Scores，`val=5.0, cov=82.5–86.4%, aCnt=1..12`）** 补强 `USA / model (1.3×, 0 OS)` 空白塔！

- **2026-11-26 04:42（2 小时定时审计 #3 · USA 零 `Sim ERROR` 稳健提速至 `3` 并发槽 + 接入纯 `MATRIX` 免额 `other580` & `val=6.0` `pv_tech_indicators`！）**：
  - **稳定性与换血复盘**：近 2 小时 `USA` 完成 `216` FULL（`880` 累计）且 **0 次 `Sim ERROR`、0 次 `429`**，但 `USA / model68`（`56 FULL, max=0.82, 2Y=0.27`）与 `USA / forward_beta_risk`（`120 FULL, max=0.99, 0≥1.25`）表现偏弱且全队列跑空导致后半段 2 槽闲置。
  - **本轮满槽换血升级（`--region-caps EUR:1,USA:3`）**：淘汰 `model68` 与 `forward_beta_risk`，接入两大实盘核验 **100% 纯 `MATRIX`** 蓝海大集，供 `USA` 3 并发槽高速满载运行：
    1. **`USA / other580`**（Standardized Daily ETF Holdings，**`other 1.4×, 0 OS`**，8 个核心 `MATRIX` 字段**全部 `Alphas=0` 免额**、`cov=90.8%–100%`）；
    2. **`USA / pv_tech_indicators`**（Price Volume Technical Indicators，**`model 1.3×, 0 OS`**，**`val=6.0`**, `cov=100%`, `aCnt=1`）。

- **2026-11-26 06:40（2 小时定时审计 #4 · 吞吐飙升至 `320 FULL/小时`（0 次 `429`）+ 全面切换美股 StarMine 机构三大王牌 `model28/model31/model30`！）**：
  - **近 2 小时吞吐与结果复盘**：`EUR:1 + USA:3` 落地后 `USA` 劲增 **`+320 FULL`（累计 `1,200`）** 且 **0 次 `429`、0 次 `Sim ERROR`**，全库单小时冲破 **`320 FULL/hr`**（日完成已至 **`3,131 / 4,500`**，剩余额度 `2,119 / 5,000`）。
    - `USA / pv_tech_indicators`（`264 FULL`）：出 `11` 条 S1 种子，最高 **`j2VR1R5Q`（`price_reversal_index`, `Sh=1.22, 2Y=2.75, SC=0.439, PC=0.720`）** → 上线 `S2-r6-USA-PVTECH` 降换手精修；
    - `USA / other580`（`48 FULL` 免额）：`0` 命中（`max=0.56`），已自动止损下线。
  - **美股全面换装机构级 StarMine 三大王牌（纯 `MATRIX`，960+ 满仓队列供 3 槽全速狂飙至 4,500/天）**：
    1. **`USA / model28`（StarMine Structural Credit Risk）**：**8 个纯 `MATRIX` 全部 `Alphas=0` 免额**（`cov=96.4–98.8%, dCov=1.00`，含违约距离/资产漂移/违约概率行业分位）；
    2. **`USA / model31`（StarMine Earnings Quality）**：美股版 `model25` 孪生矿脉，精选 8 个低拥挤 `MATRIX`（`cov=89–95%, aCnt=3..9`）；
    3. **`USA / model30`（StarMine SmartEstimate EPS Surprise）**：机构盈利预期差（`MATRIX, dCov=1.00, aCnt=12..41`）。
