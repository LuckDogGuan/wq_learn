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

- **2026-11-26 08:40（2 小时定时审计 #5 · 历史双里程碑：单小时狂飙 `648 FULL` + 首条 `USA / TOP3000` `0-FAIL` `19.95bp` `SC_PASS` 冠军 `blxZQePZ` 诞生！）**：
  - **历史级吞吐与零故障**：`EUR:1 + USA:3` 满载机构纯 `MATRIX` 队列后，单小时飙至 **`648 FULL / hr`**（近 2 小时净增 **`+1,048 FULL`**，总完成 **`4,179`**，日完成 **`4,166 / 4,500`**，`0` 次 `HTTP 429`！`USA/model31` 与 `model30` 完成率 **`100%`**，`model28` 免额 `97.5%`！）。
  - **美股首条 `0-FAIL` 正式通过 `/check` 里程碑：`blxZQePZ`（`USA / TOP3000 / model31`, `mdl31_ab1_ass_tvr_prior_qtr`）**：
    - 表达式：`group_rank(ts_decay_linear(ts_backfill(mdl31_ab1_ass_tvr_prior_qtr, 21), 10), subindustry)`（`RAM, d=0, tr=0.04`）
    - 官方 `/check` 实测：**`Sh = 1.58 (PASS), 2Y = 2.34 (PASS), Fit = 1.01 (PASS), Sub-Uni = 0.81/0.68 (PASS), TO = 5.1%, Margin = 19.95bp, 官方 SC = 0.5495 (本地 0.5465, PASS), MATCHES_PYRAMID = PASS`**，仅 `PC = 0.8072` 距 `< 0.70` 仅差 `0.107`！已打 **`SC_PASS`** + 别名 **`SC 0.547 PC 0.807`**！
  - **配套低 PC 辅支全面就位**：`USA / model30` 首波打出 **`58G0pARz`（`star_eps_surprise_prediction_fq1`, `Sh=1.35, SC=0.431, 远程 PC=0.6755 < 0.70!`）**，`USA / model28`（免额）打出 `58G0pRqz`（`Sh=1.29`）。
  - **立即置顶第 1 顺位冲刺 USA 首条 `Useful`**：上线 **`S3-r7-USA-M31-*`**（`blxZQePZ` 叠 `signed_power(1.5/2)` + 跨集双支 `model31 × model30 (PC=0.676)` / `price_signal_dl (2Y=2.89)` / `gm`/`roe` + `vector_neut` + `CROWDING/STATISTICAL/SLOW_AND_FAST/RAM`）+ 追加 `USA_M31_ERQ_V2_NORM`（8 个最新季度 `last_qtr/t4q` 字段）。
- **2026-11-26 09:15（`4,500 FULL/天` 达标里程碑 + `USA / model31` 再连出 `3` 条官方 `/check` `0-FAIL` 冠军，其中 **`QPWkKAMX` 距首条 USA `Useful` 仅差 `0.0055` PC！**）**：
  - **日吞吐里程碑达成**：`EST 2026-11-25` 实际完成 **`4,499+ / 4,500 FULL`**（`0` 次 `HTTP 429`，因含 `Alphas=0` 免额字段，API 仍余 **`1,031 / 5,000`** 实额！）。
  - **3 条新增官方 `/check` 硬检全过（仅 `PC` 未过）均已按规打标 `SC_PASS` + 写别名 `SC 0.xxx PC 0.xxx`（零 `/submit`）**：
    1. **`QPWkKAMX`**（`min(rank(ass_tvr_last_qtr), rank(acc_prior_qtr))`, `RAM d=0 tr=0.04`）：**`Margin = 17.58bp, Sh = 1.72, 2Y = 2.36, Fit = 1.03, Sub-Uni PASS (0.91/0.74), 官方 SC = 0.5423 PASS, 官方 PC = 0.7055`**（距 `< 0.70` 仅 **`0.0055`**！仅靠叠 `acc_prior_qtr` 就在 `d=0` 下单步压降 `-0.1003` PC！）→ 别名 **`SC 0.542 PC 0.706`**；
    2. **`MPgR3wQ6`**（`ass_tvr_last_qtr`, `RAM d=0 tr=0.04`）：**`Margin = 20.09bp, Sh = 1.63, 2Y = 2.17, Fit = 1.04, Sub-Uni PASS (0.81/0.71), 官方 SC = 0.5203 PASS, 官方 PC = 0.8058`** → 别名 **`SC 0.520 PC 0.806`**；
    3. **`qM5r0dxj`**（`vector_neut(group_rank(ass_tvr_prior_qtr), rank(ts_mean(returns, 22)))`, `STATISTICAL d=3 tr=0.06`）：**`Sh = 1.95, 2Y = 2.69, Fit = 1.26, Sub-Uni PASS (1.10/0.84), Margin = 10.21bp, 官方 SC = 0.4569 PASS, 官方 PC = 0.7896`**，且与 `QPWkKAMX` 池内两两相关性仅 **`0.5208 < 0.68`**（天然正交第二簇！）→ 别名 **`SC 0.457 PC 0.790`**。
  - **上线精准收口包 `S3-r8-USA-M31-QPW`（48 FULL）**：直接以 `QPWkKAMX`（`PC=0.7055`）为核心骨架，扫 `decay {2,4,6}` / `tr {0.06,0.08}` / `signed_power(1.5)` / `vector_neut(returns)`（融合 `qM5r0dxj` 正交簇！）/ `hump(0.01)` / `acc_prior_y` / `ass_tvr_prior_y(21.35bp)` 跨 `RAM / CROWDING / STATISTICAL`，一举冲破 `PC < 0.70` 并冲刺 `17–25bp` USA 首条（乃至双条正交）`Useful`！
- **2026-11-26 09:38（`S3-r8-USA-M31-QPW` 单包狂出 `11` 条 `0-FAIL POOL_S`（`22.9%` 命中率！），`78GbojXL` 已压至 `PC = 0.7020`，距首条 USA `Useful` 仅差 `0.0020`！上线王哥 80% 经验 `S3-r9-USA-M31-WG` 精准斩首！）**：
  - **11 条 `0-FAIL + SC < 0.65` 全部完成 `SC_PASS` 打标 + `SC 0.xxx PC 0.xxx` 别名（`HTTP 200 OK`，零 `/submit`）**：
    - **后置 `ts_decay_linear(min(...), 22)` 冠军簇（同时拉升 Sh/2Y/Margin 并降 PC！）**：`2rGzjlNJ`（`20.19bp, Sh=1.75, 2Y=2.56, Fit=1.06, SC 0.541 PC 0.705`）、`ZYX3m7qd`（`19.73bp, Sh=1.75, 2Y=2.55, SC 0.539 PC 0.703`）、**`78GbojXL`（`18.90bp, Sh=1.74, 2Y=2.50, Fit=1.05, SC 0.538 PC 0.702` — 仅差 `0.0020`！）**；
    - **`ass_tvr_prior_y × acc_prior_qtr` 最高 Margin 簇**：`N1Kme7Ro`（**`21.70bp`**, `SC 0.579 PC 0.784`）、`zqA6rkQO`（`21.21bp`, `SC 0.577 PC 0.784`）、`MPgR0788`（`20.52bp`, `SC 0.575 PC 0.784`）；
    - **`QPWkKAMX` 原骨架衰减簇**：`omP5oql6`（`19.37bp, SC 0.546 PC 0.709`）、`xAl81jwb`（`18.88bp, SC 0.545 PC 0.707`）、`GrQAgl60`（`18.16bp, SC 0.544 PC 0.706`）；
    - **正交 `STATISTICAL + vector_neut(returns)` 簇**：`1YGbjW96`（`10.17bp, Sh=1.72, SC 0.437 PC 0.746`）、`Jj3EPPb2`（`8.99bp, Sh=1.78, Fit=1.09, SC 0.444 PC 0.755`）。
  - **关键物理规律 + 80% 王哥 Skill 精准手术（`S3-r9-USA-M31-WG-*`, `32 FULL`）**：
    - `d=6 → d=4 → d=2` 单调降 PC（`0.7047 → 0.7031 → 0.7020`），且后置 `ts_decay_linear(22)` 全面碾压前置 `10d`；
    - 严格按 8:2 原则调用 `worldquant-brain-cyber-game-king`（王哥 Skill）核心降 PC 算子：**`d=0` 外推 + `d44` 长衰减 + L6 `tail(0.25/0.75)` & `tail(0.35/0.65)` 尾部浓缩 + 动态 `bucket(rank(cap), range="0,1,0.1")` & `sector*cap` 分组 + `industry` 分组 + `vector_neut(..., rank(ts_std_dev(returns, 66)))`**，直击 `-0.01 ~ -0.08` PC 降幅，锁定 `19–25bp` USA 首条 `Useful`！
- **2026-11-26 09:53（🏆 历史级里程碑：**首条 `USA / TOP3000` `Useful` 冠军 `e71w5Qrl`（`Margin = 18.58bp`）正式通过官方 `/check` `0-FAIL` 全绿通关！**）**：
  - **王哥 80% Skill `L6 tail(0.25, 0.75, 0.5)` 精准斩首成功**：`S3-r9-USA-M31-WG` 仅用 `30` 次有效回测狂出 **`18` 条 `0-FAIL POOL_S`（`60%` 命中率！）**，其中 **全部 4 条 `tail(lower=0.25, upper=0.75, newval=0.5)` 在 `decay = 0 / 2 / 4` 全扫频区间无一例外全部打穿 `PC < 0.70` 且官方 `/check` `0 FAIL`**（完美符合王哥稳定性扫频铁律！）：
    - **🏆 美股 `Useful` 最高 Margin 冠军：`e71w5Qrl`**（`USA / TOP3000 / model31`, `model 1.3× 0 OS 空白塔`, `RAM d=4 tr=0.08`）：
      - 表达式：`tail(group_rank(ts_decay_linear(min(rank(ts_backfill(mdl31_ab1_ass_tvr_last_qtr, 21)), rank(ts_backfill(mdl31_ab1_acc_prior_qtr, 21))), 22), subindustry), lower=0.25, upper=0.75, newval=0.5)`
      - 官方 `/check` 全绿指标：**`Margin = 18.58bp`**, **`Sharpe = 1.71`**, **`2Y Sharpe = 2.63`**, **`Fitness = 1.07`**, `TO = 5.2%`, `Sub-Uni = PASS (0.84/0.74)`, **`官方 SC = 0.5358 (本地 0.5350)`**, **`官方 PC = 0.6936 (< 0.70!)`**, **`fails = []`**！已打 **`Useful`** 标签 + 别名 **`SC 0.536 PC 0.694`**（严守零 `/submit`）！
    - **3 条全绿同簇备胎（均已通过官方 `/check` `0 FAIL`，因 Margin 低于 `e71w5Qrl` 且相关 `0.999` 归入 `SC_PASS`）**：`KPVdJ7px`（`17.74bp, d=2, SC 0.534 PC 0.692`）、`xAl8rjnW`（`17.12bp, d=0 t04, SC 0.533 PC 0.692`）、`legOAj1x`（`17.12bp, d=0 t06, SC 0.533 PC 0.692`）。
    - **另 14 条 `0-FAIL + SC < 0.65` 高 Margin 候选（最高 `omP5EWYl 21.95bp`）** 均已完成 `SC_PASS` 打标 + `SC 0.xxx PC 0.xxx` 别名落盘。
  - **可复用核心方法论固化**：`tail(group_rank(...), lower=0.25, upper=0.75, newval=0.5)` 同步降 PC **`-0.010`** + 降 SC **`-0.005`** + 提 `2Y Sharpe (+0.08)` 与 `Fitness (+0.02)`，将在美东新一天（`13:00 CST`）直接推广至 `e71w5Qrl (d=6 冲 20bp+)`、正交 `STATISTICAL` 簇（`1YGbjW96` 冲美股第 2 条正交 `Useful`！）及 `EUR` 近门槛 `SC_PASS` 因子！
- **2026-11-26 10:55（2 小时定时审计 #6 · 抓获并永久根治 `Gold-81` 34 个不可用算子误放行 Bug + 热部署 `S3-r10b` 多角度降 PC 实验室！）**：
  - **关键排雷与根因定位**：巡检发现 `S3-r10` 有 `16/20` 批（`128/160` FULL）在 `50–73s` 内全批报错 `RESULTS_UNOBSERVED`，根因是旧 `operators_gold_81.json` 含 `114` 个算子，其中 **34 个在本账号 Gold 级 `REGULAR` 范围不可用**（本次触发：`clamp`、`group_median`、`tanh`、`vector_proj`、`keep`、`s_log_1p`、`arc_tan`），单个坏算子即击穿整批 8-Alpha Multi-Sim！
  - **永久工程修复**：已实时拉取本账号 `GET /operators` 核验确切 `84` 个 `REGULAR` 算子（扣除 Decision #3 禁用 `add`/`multiply`/`trade_when` 后恰为 **81 个真实可用 Gold 算子**），彻底清洗 `wq_research_v2/config/operators_gold_81.json` 并补充 `test_expr_validator.py` 静态拦截回归测试，同时将 `pc_breakout_lab.py` 全量升级为 **`S3-r10b`**（`47/47` 单测 + 40 文件 AST/安全校验全过，已热部署广州开跑，`day_est=4676/4790`，API 余 `865/5000`，`0` 次 `429`）。
  - **全量 `S3-r9` 18 条 `0-FAIL` 二次核账**：确认除冠军 **`e71w5Qrl` (`Useful`, `18.58bp, SC 0.536 PC 0.694`)** 外，其余 `17` 条均已准确落盘 `SC_PASS` + `SC 0.xxx PC 0.xxx` 别名，零漏标、零 `/submit`；`S3-r10-USA-PC-NEST` 已无报错跑完 `32/32`（`N1KmLbEg 2Y=2.82`, `omP5RlmJ 15.51bp`）。
- **2026-11-26 11:46（🏆 里程碑再破！美股第二条正交 `Useful` 冠军 `E5mWLW0J` 官方 `/check` `0-FAIL` 全绿通关，超低 `SC = 0.3443`！）**：
  - **第一性原理 3-Dataset 正交破壁实证（`S3-r10b → S3-r11 → S3-r12`）**：确认 `e71w5Qrl` 与 `RR5QjWYz` 已实盘进入 **95 OS** 后，单集微调全部在 `0.84–0.87` 撞车自身 OS；通过 **`model31 × model30 (SmartEstimate EPS Surprise) × model28 (免额结构性违约距离)` 三集嵌套 + `STATISTICAL` + `tail(vector_neut(..., rank(ts_mean(returns, 22))), -0.25, 0.25, 0)`**，不仅把对全库 `95 OS` 的官方自相关砸低至 **`0.3443`**，还将 Sharpe 一举推升至 **`1.83`**（触发平台高夏普 `+10%` 胜出免杀规则，官方 **`PROD_CORRELATION = 0.7531` 正式判定 `PASS`**！）：
    - **🏆 美股第二条正交 `Useful` 冠军：`E5mWLW0J`**（`STATISTICAL d=6 tr=0.08, delay=1`）：
      - 表达式：`tail(vector_neut(group_rank(ts_decay_linear(min(rank(ts_backfill(mdl31_ab1_ass_tvr_prior_qtr, 21)), min(rank(ts_backfill(star_eps_surprise_prediction_fq1, 21)), rank(ts_backfill(mdl28_sm_structural2_v14_0_0_nd_credit_structural_distance_to_default, 21)))), 22), subindustry), rank(ts_mean(returns, 22))), lower=-0.25, upper=0.25, newval=0)`
      - 官方 `/check` 全绿指标：**`Sharpe = 1.83 PASS`**, **`2Y Sharpe = 2.38/2.02 PASS`**, **`Fitness = 1.11 PASS`**, **`Sub-Uni = 0.97/0.79 PASS`**, `TO = 11.5%`, `Margin = 7.99bp`, **`官方 SC = 0.3443 PASS`**, **`官方 PC = 0.7531 PASS`**, `DATA_DIVERSITY PASS`, `MATCHES_PYRAMID PASS (USA/D1/MODEL 1.3× + PV 1.1×)`, 命中 `AQP202611`！已打 **`Useful`** + 别名 **`SC 0.344 PC 0.753`**（严守零 `/submit`）。
  - **广州服务状态**：已优雅回落 `--daily-target 4500` 休眠（`EST 2026-11-25` 实际完成 **`4,880 FULL`**，API 富余 **`605 / 5,000`**，`0` 次 `429`），静待 `13:00 CST` 美东新一天开启！
- **2026-11-26 12:55（2 小时定时审计 #7 · 补齐 `S3-r12` 3 条同簇 `SC_PASS` 标注 + EST `2026-11-26` 美东新一天顶配队列热装载！）**：
  - **补标完成（零漏标、零 `/submit`）**：为 `S3-r12` 剩余 3 条 `0-FAIL` 候选完成本地 95-OS SC、两两相关与远程串行 PC 校验并全部打标 `SC_PASS` + 写别名：`omP5r7zm`（`7.99bp, Sh=1.83, SC 0.344 PC 0.753`, `corr(E5m)=1.000`）、`A1LZmW6Q`（`7.99bp, Sh=1.66, SC 0.417 PC 0.745`, `corr(E5m)=0.826`）、`VkMj59oA`（`7.49bp, Sh=1.83, SC 0.374 PC 0.757`, `corr(E5m)=0.999`）。
  - **EST `2026-11-26`（`13:00 CST` 起 `4,500 FULL` 新额）双引擎上新**：
    1. **置顶提 Margin 收口包 `S3-r13-USA-E5M-HIGHMGN`（32 FULL）**：直接对 `E5mWLW0J`（`SC=0.344, Sh=1.83, Mgn=7.99bp`）将快 `22d` 收益中性化拉慢至 `66d/126d` + `33d/44d` 后置衰减 + `hump(0.01)` + `ts_target_tvr_decay(target_tvr=0.05)` + `ass_tvr_prior_y`，目标将 Margin 从 `7.99bp` 推升至 **`12–18bp+`**；
    2. **4 个全新实盘核验纯 `MATRIX` 机构蓝海大集（含 24 个 `Alphas=0` 免额字段！）**：`USA / model36`（StarMine SmartRatios, `cov=1.000, aCnt=1..8`）、`USA / model227`（纯基本面财务比率与增速，**8/8 `Alphas=0` 免额**, `cov=0.825–0.979`）、`USA / analyst_revision_horizons`（多周期分析师 EBITDA/营收修正，**8/8 `Alphas=0` 免额**, `cov=1.000, val=5.0`）、`USA / expected_move`（期权隐含波动幅，**8/8 `Alphas=0` 免额**, `cov=0.836–0.942, val=5.0`）。
- **2026-11-26 14:53（2 小时定时审计 #8 · EST `2026-11-26` 首波 656 FULL 复盘 + 止损 `expected_move` + 切入 `model39` 美股估值动量孪生与免额 EPS 扩散度！）**：
  - **首波复盘与控制变量归因（已记入 `OPTIMIZATION_LEDGER.json`）**：
    - `USA / analyst_revision_horizons`（免额）首波即出 `POOL_A` **`A1LMJpeg`（`Sh=1.28, 2Y=1.39`）** 及 `Jj3Zwmem / vRY3g5Y3 (1.21)`；`model227` 出 `21.98bp` 种子（`max=1.05`），`model36` 出 `25.71bp` 种子（`max=0.99`）；
    - `USA / expected_move` 满 `64 FULL` `0` 命中（`max=0.76`），**果断下线止损**；
    - `S3-r13` 归因确认 `pwWrLpaV`（`9.56bp, 2Y=2.63, Sh=1.65, Fit=0.95`）因同时改 3 轴导致 `Fit` 略差 `0.05`；新增严格单轴 **`S3-r14-USA-E5M-1AX`（16 FULL）** 冻结 `ret22` 单步测 `d33/d44/ret33/ret44/tail/tvr08`（严禁 `tail` 外套 `hump`）。
  - **美股双王牌上新**：新增 **`USA / model39`**（StarMine Valuation-Momentum 美股孪生，40 个纯 `MATRIX`，精选 8 个 `aCnt=1..4, cov=0.95–0.97` 低拥挤字段）+ **`USA / analyst_revision_horizons` V2**（8/8 `Alphas=0` 免额：含 EPS 净修正扩散度 `estimate_diffusion_quarterly_eps_30d_short`、分析师修正簇幅度及 52 周高点动量）。
- **2026-11-26 19:03（2 小时定时审计 #9 · 🏆 重大突破：`S3-r14` 严格单轴 `ts_target_tvr_decay(0.08)` 诞生严格 `PC < 0.70` 正交新 `Useful` 冠军 `kq82m3gL` (`10.28bp, SC 0.351 PC 0.699`)！）**：
  - **🏆 新增 `USA / TOP3000` 严格 `< 0.70` PC 正交 `Useful`：`kq82m3gL`**（`S3-r14-USA-E5M-1AX-stat_d6_t08`, `model31 × model30 × model28 FREE`, `STATISTICAL d=6 tr=0.08`）：
    - 在已被降级 `SC_PASS` 的 `E5mWLW0J`（`7.99bp, TO=11.5%, PC=0.7531`）上严格单步叠加 `ts_target_tvr_decay(..., lambda_min=0, lambda_max=0.9, target_tvr=0.08)`，实现 **Margin `7.99bp → 10.28bp` (+2.29bp)**、**TO `11.5% → 8.3%`**、**远程 `PC` 从 `0.7531 → 0.6989` (`[0.7, 1.0]` 碰撞数 `= 0`!)**、**官方 `SC = 0.3509 PASS`**、**`Sh = 1.78 / 2Y = 2.38 / Fit = 1.04 / Sub-Uni = 0.91/0.77 PASS`**，命中 `USA/D1/MODEL 1.3×` + `AQP202611`！已打 **`Useful`** + 别名 **`SC 0.351 PC 0.699`**（同时注明 8 层 `OVER_NESTED_TEMP_PC_FIX` 供人工终审，严守零 `/submit`）。
  - **免额新矿进展**：`USA / analyst_revision_horizons`（`mean_revisioncluster_revision_pct_quarterly_eps_long`）在 `admin_ts_regime`（`ts_rank 252`）下已冲至 **`akRqV77w Sh=1.47, 2Y=1.78, Mgn=7.69bp`** 与 **`RR5nb5oj Sh=1.41, 2Y=2.23, Mgn=8.96bp`**（距 `1.58` 仅一步之遥）。
- **2026-11-26 21:15（2 小时定时审计 #10 · 补齐 `S3-r14` 6 条 `0-FAIL` 姊妹 `SC_PASS` 标注并验证 `kq82m3gL` 平滑反悬崖稳定性 + 清零 `USA SLOW_AND_FAST` 残留并恢复 `USA:2` 调度！）**：
  - **6 条 `S3-r14` `0-FAIL + SC < 0.65` 姊妹全部串行完成 PC 体检、打标 `SC_PASS` + 别名 `SC 0.xxx PC 0.xxx`（零 `/submit`）**：
    - **`3qGZ6peg`**（`d=4`, `9.85bp, Sh=1.78, Fit=1.05, TO=8.8%, SC 0.347 PC 0.712, >=0.70仅1个, pair_vs_kq=0.9988`）：**实证 `d=4 → d=6`（`kq82m3gL 10.28bp, PC=0.6989, >=0.70=0`）呈单调平滑提升、零单点悬崖！**
    - **`E5mXawvm`**（`ret33`, `8.71bp, Sh=1.80, 2Y=2.44, Fit=1.08, SC 0.384 PC 0.720, >=0.70=2`）、`A1LMaw0g`（`d44`, `8.46bp, Sh=1.86, Fit=1.14, SC 0.381 PC 0.756`）、`Jj3ZXp7A`（`d33`, `8.34bp, Sh=1.86, 2Y=2.48, SC 0.374 PC 0.756`）、`WjY6XpeQ`（`tail20`, `8.31bp, Sh=1.82, SC 0.370 PC 0.755`）、`wpNMzRZ5`（`last_qtr`, `7.99bp, Sh=1.83, 2Y=2.52, SC 0.363 PC 0.753`）。
  - **调度与排雷修复**：修复 `daemon_ra_runner.py` 去重前缀饿死 Bug，将 `USA` 重新纳入 **`EUR:2,USA:2,ASI:1,KOR:1`** 4 槽均衡并行（加速迈向 `4,000` 常规额度线，之后自动转入 `USA/board_network`、`USA/chart_cnn_alpha`、`USA/analyst_revision_horizons` 共 `139` 批 `Alphas=0` 免额池！），并彻底清除 `stage23_refiner.py` 中残留的 2 条 `USA SLOW_AND_FAST` 慢配置且补入单测守卫。
- **2026-11-26 23:00（2 小时定时审计 #11 · 🎉 祝贺 `E5mWLW0J` + `Jj88vq2e` 入网达 `97/100 OS`！实时清理 `kq82m3gL` 撞车并补入 3 个空白塔纯 `MATRIX` 新集！）**：
  - **97-OS 实时同步防误交**：用户于 `22:06 CST` 手动提交 `E5mWLW0J`（`USA/TOP3000, Sh=1.83`）与 `Jj88vq2e`（`GBR, Sh=2.03`），账号 OS 跃升至 **`97 / 100`**；本地 `os_pnl_cache.db` 同步至 `97 OS` 后实测 **`kq82m3gL` 自相关升至 `0.9695`（撞车 `E5mWLW0J`）**，已即时剥离过期 `Useful` 改标 **`SC_IS_HIGHT`** + 别名 `SC 0.970 PC 0.699`（同步清理 6 条 `S3-r14` 同簇姊妹为 `SC_IS_HIGHT`）。
  - **补满 `USA:2` 防止常规队列见底（原仅剩 7 批！）**：新增 3 个实盘核验 100% 纯 `MATRIX` 低拥挤空白塔新矿脉：**`USA/multi_source_model`**（`cov=0.980–0.983, aCnt=1..2`）、**`USA/news_sentiment_transfer`**（**`sentiment 1.5× 空白塔`**, `cov=0.947, aCnt=2..6`）、**`USA/ai_news_scores`**（**`other 1.4× 空白塔`**, `val=5.0, cov=1.000, aCnt=1..2`），全速冲过 `4,000` 解锁 139 批 `USA` `Alphas=0` 免额队列！
- **2026-11-27 00:56（2 小时定时审计 #12 · `USA` 近 2h 完成 `440 QUICK` + `ai_news_scores` 空白塔出 `S2` 强苗 + 距 `4,000` 自动切换 `139` 批 `Alphas=0` 仅余 ~45 分钟！）**：
  - **新纯 `MATRIX` 队列初筛成绩单**：
    - **`USA/ai_news_scores`（`other 1.4×, 0 OS` 空白塔）**：`160 QUICK` 产出 **`36` 条 S1 + `5` 条 S2**，头部 `blx3vWbN / O06vov3g / zqAzOzl8`（`Sh=1.27, 2Y=1.79, TO=28.3%`）与 `WjYm9m5Q`（`Sh=1.25, 2Y=1.82`），属典型高换手高 2Y 信号，后续可直接进通用高换手降换手梯队；
    - **`USA/multi_source_model`**：`184 QUICK` 产出 `32` 条 S1（`maxSh=1.17, 11.49bp`）；
    - **`USA/news_sentiment_transfer`**：`48 QUICK` 仅 `0/48`（`max=0.55`），已由守护进程**自动早停降权**，零浪费额度。
  - **Phase-2 自动切换倒计时**：当前 `normal_done = 3,576 / 4,000`（仅差 `424` 条常规回测 ≈ 45 分钟），已确认 `resolve_quota_queue_policy()` 按 `normal_done` 而非总日回数判定，不会被 `day_est=4,202/4,500` 提前打断；满 `4,000` 后将自动切入 `USA` `139` 批免费 `Alphas=0` 队列（含 `analyst_revision_horizons`、`board_network`、`chart_cnn_alpha`）！
- **2026-11-27 02:57（2 小时定时审计 #13 · Phase-2 免额自动切换无缝达成（日总回测冲破 `5,452`！）+ 免额 `USA/chart_cnn_alpha` 首波爆发 `Sh=1.45 / 2Y=2.74` → 立即上线 `S3-r20-USA-CNN-FREE` 零额度 `FULL` 降换手！）**：
  - **Phase-2 无缝切入与黑马爆发**：常规额度满 `4,018 >= 4,000` 后守护进程自动切换 `ALPHA0_EXEMPT_ONLY`，近 2h 免费跑完 **`476`** 条（日官方总回测达 **`5,452`**，`0` 次 `HTTP 429`！）；
    - **`USA/chart_cnn_alpha`（100% `Alphas=0` FREE）首波 128 QUICK 爆出高 2Y 强矿**：**`rK0mNeX8`**（`img30d_return_tercile_confidence0_zackbatch`, `Sh=1.45, 2Y=2.74, TO=51.9%`）、`RR5LemNg`（`Sh=1.36, 2Y=2.72, TO=51.4%`）、`MPgAe0wa`（`Sh=1.33, 2Y=2.48, TO=56.4%`），均属典型超高 2Y + 高换手信号；
    - **`USA/ai_news_scores`（NORMAL）** 进一步抬升至 **`xAla3EOW Sh=1.41, 2Y=2.22, TO=27.5%`**（留待次轮常规降换手）。
  - **立即热部署零额度 Stage-3 + 新免费矿脉**：
    1. **`S3-r20-USA-CNN-FREE`（32 FULL `UNUSED_ALPHA0` FREE）**：在 `rK0mNeX8 / RR5LemNg / MPgAe0wa` 上立即跑通用高换手降换手梯队（`ts_decay_linear 5/10`、`ts_mean 5/10`、`ts_target_tvr_decay 0.15`、`hump 0.01`、底/顶三分位与四分位互补双支，零额度消耗直冲美股免费 `Useful`！）；
    2. **`USA_OPTCHART_FREE`（`option_chart_model`, `model 1.3×`, `val=5.0, cov=0.865–0.954, 8/8 Alphas=0`）**：与 `chart_cnn_alpha` 同源的期权图谱 CNN 预测免费蓝海集！
- **2026-11-27 04:54（2 小时定时审计 #14 · 日官方回测狂破历史新高 `6,588`（`0` 次 `429`！）+ `S3-r20-USA-CNN-FREE` 归因定案 + 换装 `60d/120d` 免额长周期双引擎！）**：
  - **控制变量归因（记入 `INEFF-10`）**：`S3-r20-USA-CNN-FREE`（`32/32 FULL` 零超时完成）证实 `chart_cnn_alpha` 在 `SUBINDUSTRY d=4 + ts_decay5` 下 **`2Y` 飙升至 `2.96`（`wpNV7mxd`）**，但 10Y 全期 Sharpe 从 `1.45` 回落至 `1.20`（`RAM`/`CROWDING` 跌至 `0.92`），适合留作高 2Y 辅支而非单打 RA `1.58`；`USA/option_chart_model` 虽 `maxSh=1.41` 但换手 `89–105%`、`2Y=0.99–1.17`，同样不投入重 Stage-3。
  - **Phase-2 零额度长周期换血**：为 `USA:2` 补入两大实盘核验 `60d/120d` 低换手 `Alphas=0` 纯 `MATRIX` 免费矿脉：**`USA_MULTIFACT_120D_FREE`（`multifactor_return_pred`, `cov=0.983`, 8/8 `Alphas=0`）** 与 **`USA_GLBSEASON_20D_FREE`（`global_seasonal_model`, `cov=0.997`, 8/8 `Alphas=0`）**，保持 4 槽免额全速推进至 `13:00 CST`！
- **2026-11-27 06:53（2 小时定时审计 #15 · 日官方回测狂飙 **`7,740`**（连续 10h 零 `429`！）+ `USA/multifactor_return_pred` 免额首波打出 `Sh=1.59 / 2Y=2.17` → 秒发 `S3-r22-USA-MF120-FREE` + `USA_MF120_V2_FREE` + 双 NLP 空白塔免额集！）**：
  - **`USA/multifactor_return_pred`（100% `Alphas=0` FREE）首波 `208 QUICK` 大丰收**：产出 `46` S1 / `15` S2 / `1` S3 —— **`RR5X05Yj`（`long_term_quantile1_r60_pred`, `Sh=1.59`）**、`QPWeEOXQ`（`1.48, 2Y=1.69`）、`qM5beOvK`（`long_term_quantile5_r60_pred`, `1.44, 2Y=1.99`）、`0mGozr56`（`1.36, 2Y=2.17`），且 `blxp7x2r`（`d10`）将换手从 `41.3%` 砍至 `12.9%` 仍保住 `Sh=1.41`（抗衰减性能极佳！）；
  - **立即热部署免费 Stage-3 + Wave-3 空白塔矿脉**：① **`S3-r22-USA-MF120-FREE`（24 FULL `UNUSED_ALPHA0` FREE）** 融合 `q1_r60 × q5_r60 × seasonal_r120 / regime2_r120` + `d5/d10/tvr15/tail25` 直冲美股免费 `Useful`；② **`USA_MF120_V2_FREE`** 引入 `ASI 2.87` 核弹的美股同源字段 **`short_term_regime2_quantile1_r60_pred`**；③ 新增两大 `other 1.4×` 空白塔免额集 **`USA_FINNEWS_NLP_FREE`**（`cov=1.000`）与 **`USA_MMP_NLP_FREE`**（`cov=0.979–1.000`）！
- **2026-11-27 08:52（2 小时定时审计 #16 · 日官方回测狂破 **`8,548`**（连续 12h 零 `429`！）+ Phase-2 免额全线跑完，无缝切回剩余 `460` 常规额发射 `S3-r23-ASI` + `S3-r20-EUR`！）**：
  - `S3-r22-USA-MF120-FREE`（24/24 `FULL`）：最高 `omP2g7X2`（`tail25`, `Sh=1.33, 2Y=1.74, 5.76bp`）；`USA_MF120_V2_FREE` 出 `mLKOVed9`（`short_term_regime2_quantile1_r60_pred`, `Sh=1.49`）；`USA/finnews_nlp_scores`（`2/104, max=0.81`）与 `USA/mmp_nlp_sentiment`（`1/64, max=0.84`）已自动早停。Phase-2 全部 `4,188` 条免费回测已收官，守护进程即将在 `08:55–10:15 CST` 自动消耗剩余 `460` 常规额度执行 `S3-r23-ASI-MF120-ROBUST` + `S3-r20-EUR-1YG-HIGHMGN`，随后优雅休眠至 `13:00 CST` 美东换日！

### 2026-11-28 00:13 · 常规快筛与中性化对照

- **[V] 新增的 analyst11、model110 各有 4 条 QUICK 达 Sharpe≥1.25。** 已核的 `vRYxL3aw` 为 18.37bp、换手 4.71%，Sharpe 1.31、Fitness 0.77、2Y 1.26。 `E5mYKPPL` 两年 Sharpe 2.11，Sharpe 1.37、Fitness 0.81，集中度 FAIL。直接转 FULL 前仍须筛查硬检短板和同簇重复。
- **[V][C] 两对 analyst11 单改 SUBINDUSTRY→RAM，Fitness 分别从 0.81→0.87、0.77→0.84，Margin 从 13.55→10.29bp、13.03→10.00bp。** `E5mYKPPL`→`mLKJj519` 的 2Y 为 2.11→1.76，两条均有 Sharpe、Fitness、集中度 FAIL。见 EFF-22。现有 NORMAL QUICK 继续筛查这两个方向。
- **[V] `USA_SI6_SMARTHOLD_NORM` 的 64 条 D1 QUICK 已完成并自动早停。** 0/64 达正向 Sharpe 0.80，最高 0.42。
- **2026-11-28 00:22（2 小时定时审计 #24 · 远程 PC 直方图排雷 `USA/analyst11` (`QPWqKVO5` `>=0.70` 碰撞 `7,018` 条，记入 `INEFF-24`) + 下线已完结 3 批 + 换装超低拥挤 `USA/fundamental72` (`aCnt=1..2`) 与满覆盖 `USA/institutions6` (`cov=1.000`) 纯 `MATRIX` 常规新矿脉！）**：
  - `USA_ANL11_PYRAMID_NORM`（`384/384 QUICK` 完成，产出 `86` S1、`4` S2，最高 `E5mYKPPL` `Sh=1.37, 2Y=2.11, 13.55bp, 100-OS SC=0.6332`）经远程 PC 直方图预检，头部 `QPWqKVO5`（`CROWDING Sh=1.20, 2Y=1.75, 16.95bp, 100-OS SC=0.6090`）在生产库 **`>=0.70` 碰撞高达 `7,018` 条（`>=0.80` 达 `198` 条，`PC_ABANDON_CROWDED_OR_FAR`）**，避免盲目投入 Stage-3 `FULL` 浪费额度（记入 `INEFF-24`）；
  - 下线已跑完/早停的 `USA_SI6_SMARTHOLD_NORM`（`0/64`）、`USA_ANL11_PYRAMID_NORM`（`384/384`）、`USA_M110_PYRAMID_NORM`（`384/384`），立即换入实盘核验超低拥挤纯 `MATRIX` 常规新集 **`USA_FND72_PIT_NORM`（`USA/TOP3000/fundamental72` Point-in-Time 财报，**`aCnt=1..2`**, `cov=0.790–0.905, dCov=1.00`）** 与 **`USA_INST6_OWNERSHIP_NORM`（`USA/TOP3000/institutions6` 机构持股，**`cov=1.000`**, `dCov=0.9507`）**，全速推进 `2,920 -> 4,500` 常规额度！
- **2026-11-28 02:21（2 小时定时审计 #25 · `100-OS` 同步确认 `USA/model31` 全簇饱和 (`SC=0.71–0.99`) + 下线早停 `fundamental72` / `institutions6` + 换装 `USA/ai_equity_alpha` (`aCnt=1` 超低拥挤) 与 `USA/ai_factor_transfer` (`cov=1.000`) 纯 `MATRIX` 常规新矿脉！）**：
  - 同步广州 `os_pnl_cache.db` 至 `100/100 OS` 后，实测 `USA/model31` 既有 `0-FAIL` `SC_PASS` 候选（`qM5r0dxj`, `1YGbl1EQ`, `legO522N`, `1YGbjW96`, `Jj3EPPb2`, `78GbojXL`, `2rGzjlNJ`, `N1Kme7Ro`）对已入库 `e71w5Qrl` + `E5mWLW0J` 的 **`100-OS SC` 均升至 `0.7115–0.9876`（`SC_READY_HIGH`）**，确认 `USA/model31`（`ass_tvr / acc`）单集簇已饱和，不再投入 Stage-3 `FULL` 额度（记入 `INEFF-26`）；
  - `USA_FND72_PIT_NORM`（`64/64 QUICK`, `1/64 >= 0.80, max=0.83`）与 `USA_INST6_OWNERSHIP_NORM`（`72/72 QUICK`, `0/72 >= 0.80, max=0.76`）已自动早停下线；立即补入实盘核验高覆盖纯 `MATRIX` 常规新集 **`USA_AIEQ_ALPHA_NORM`（`USA/TOP3000/ai_equity_alpha`, `model 1.3×`, `valScore=3.0`, **`aCnt=1` 超低拥挤**, `cov=0.9113, dCov=0.9507`）** 与 **`USA_AIFACT_TRANSFER_NORM`（`USA/TOP3000/ai_factor_transfer`, `model 1.3×`, `valScore=3.0, cov=1.000, dCov=0.9507`）** 继续冲刺 `3,384 -> 4,500` 常规额度！

- **2026-11-28 03:17 Codex 巡检 [V][U]**。USA/ai_equity_alpha 单支与双支合计完成 88 条 NORMAL QUICK，9 条 Sharpe≥0.80、4 条≥1.25，另 8 条标为在途。`O06kqe1b` 是抽核三条同簇种子中 Margin 最高的代表，Sharpe 1.41、2Y 1.56、Fitness 0.89、Margin 39.70bp、换手 2.49%。按 BRAIN 当前 100 个 OS 与本地缓存逐 ID 核对后，同区 31 个对手中的最大 SC 为 0.6340（对 `kqdKxAX6`，985 日重合）。另两条与代表的四年日收益相关性为 0.9504、0.9690。沿现有队列筛查，FULL 中优先验证 Sharpe、Fitness 和 2Y；该代表的低换手无需再降。
- **[V] 上轮跟进窗口结束**。USA/analyst11 与 USA/model110 各新增 48 条 QUICK，分别 10 与 2 条达到 0.80，均未增加 ≥1.25 候选。当前台账分别累计完成 400、416 条，各 4 条达到 1.25。
- **2026-11-28 04:16（2 小时定时审计 #26 · 重大单轴归因发现：`USA/ai_equity_alpha` 单改 `SUBINDUSTRY -> REVERSION_AND_MOMENTUM` 将 `>=0.70` 生产碰撞从 `439` 条砍至 `2` 条 (`-99.5%`!) → 立即热部署 `S3-r34-USA-AIEQ-LL8-LOWPC-ram_d4_t06` `FULL`！）**：
  - **严格单轴中性化降 PC 实证（记入 `EFF-26`）**：在 `USA/TOP3000/ai_equity_alpha`（`aCnt=1`）上固定 `group_rank(ts_decay_linear(ts_backfill(analyst_sentiment_score_3, 21), 10), subindustry)` 与 `d=0, tr=0.04`，对比 **`O06kqe1b`（`SUBINDUSTRY`: `Sh=1.41, 2Y=1.56, Fit=0.89, 39.70bp, 100-OS SC=0.6340, 远程 PC=0.8355, >=0.70 碰撞=439 条`）** vs **`LL86Rx8e`（`REVERSION_AND_MOMENTUM`: `Sh=1.45, Fit=0.90, TO=6.81%, 14.25bp, 100-OS SC=0.4754 < 0.65, 远程 PC >=0.70 碰撞仅 2 条!`）**，证实 `RAM` 在美股同样能砍掉 `99.5%` 的生产碰撞并把 Sharpe 从 `1.41` 推高至 `1.45`！
  - 立即上线 **`S3-r34-USA-AIEQ-LL8-LOWPC-ram_d4_t06`（8 FULL `NORMAL`, `REVERSION_AND_MOMENTUM d=4, tr=0.06`）**，将 `LL86Rx8e` (`sent3`)、`O06kpr8g` (`sent4`)、`E5mbwl9K` (`sent5`, `SUBINDUSTRY 2Y=1.63`)、王哥 L6 `tail(0.25, 0.75, 0.5)` 与 `sent3 × sent4/5` 双/三支直接升 `FULL` 冲刺美股正交 `Useful`！
