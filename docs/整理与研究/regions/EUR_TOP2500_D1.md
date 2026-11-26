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
- **2026-11-25 17:45（30 分钟巡检 #1 · `news_sentiment_dl` 首波偏弱，静待 `price_signal_dl` 波次）**：
  - `EUR / TOP2500 / news_sentiment_dl`（`Alphas=0` 免额，Wave #1 `32` FULL 耗时 `165.0s`）：`0` 条 `|Sh| ≥ 0.80`，最高仅 `+0.42` / 最低 `-0.40`，`avg_mgn = -0.16bp`，信号偏弱。
  - **方向判断**：无需中途打断服务，等待 Pass 2 对 `EUR / price_signal_dl`（`cov=100%` MATRIX，同系列已在 USA 首波打出 `Sh=1.10 / 2Y=1.84 / Mgn=24.9bp`）进行实盘验证；若 `EUR / news_sentiment_dl` 满 48 条仍无起色，守护进程将自动早停该数据集。

- **2026-11-25 20:16（1 小时定时检查 #2 · 重大方向升级至 `model25` 历史冠军矿脉！）**：
  - `EUR / price_signal_dl` 完成 `68` 条，产出 `4` 条 `POOL_B`（最高 `Jj3wRw7j Sh=+0.90`），但单集天花板偏低。
  - **深度诊断与换轨**：对照 [guangzhou_history_postmortem.md](../records/experiments/guangzhou_history_postmortem.md)，EUR 历史产出 `Sh 2.37–3.26, Fit 2.77, Margin 29.8bp` 的真正核心矿脉是 **`model25`**（`model 1.3×`, 本账号 **`0` OS**）配 1 算子直出 `group_zscore(x, industry)`！现已实时核验 `value_momentum_region_percentile`、`operating_efficiency_component_percentile`、`exclusions_component_percentile`、`regional/mid/long/global_momentum_percentile`（`cov=89–100%`, `dCov=1.0`, `aCnt=5–21`），置顶全队列第 1 顺位并升级 `v4` 4 组完全对称模板（含 1 算子 `group_zscore(x, industry)`）。

- **2026-11-25 21:05（大爆发！`EUR / model25` 单波 32 条直出 5 条 `POOL_S`，最高 `Sharpe = +3.16, Fit = +3.24`！）**：
  - **`legq0aml`**：`group_zscore(value_momentum_region_percentile, industry)` → **`Sharpe = +3.16, 2Y = +2.27, Fit = +3.24, Ret = 13.18%, TO = 11.09%, Margin = +23.78bp`** — **仅差 1 项 `LOW_SUB_UNIVERSE_SHARPE (1.29)`**！
  - **`6XG8EML5`**：`group_zscore(ts_mean(value_momentum_region_percentile, 22), subindustry)` → **`Sharpe = +2.66, 2Y = +2.07, Fit = +2.31, TO = 3.13%, Margin = +60.53bp`** — **仅差 1 项 `LOW_SUB_UNIVERSE_SHARPE (1.04)`**！
  - **`np6JW77q`**：`operating_efficiency_component_percentile` → **`Sharpe = +1.85, 2Y = +1.79, Fit = +1.25, TO = 2.80%, Margin = +40.73bp`** — **仅差 1 项 `LOW_SUB_UNIVERSE_SHARPE (0.75)`**！
  - **`kq87KjPK`**：`operating_efficiency_component_percentile` → **`Sharpe = +1.70, 2Y = +1.85, Fit = +1.03, TO = 1.74%, Margin = +52.92bp`** — **仅差 1 项 `LOW_SUB_UNIVERSE_SHARPE (0.64)`**！
  - **立即启动 Stage-3 Sub-Universe 专项解救（[stage23_refiner.py](../../../wq_research_v2/src/wq_research_v2/stage23_refiner.py)）**：采用嵌套分组 `group_cartesian_product(country, industry/subindustry)` + 宇宙切换 `EUR/TOP1200` / `EUR/TOP800` + 小幅参数微调（`decay ∈ {0,2,4,6}`、`truncation ∈ {0.04,0.06,0.08}`、`signed_power 0.5/0.75`）+ `val_mom × op_eff` ATOM 双支，直取 `0 FAIL` 可打 `Useful` 候选！

- **2026-11-25 21:16（`TOP1200` 对比实证 & 切换专注 `EUR + USA` 双方向独占运行）**：
  - Stage-3 首波实测：`EUR / TOP1200 / model25` 将 `value_momentum_region_percentile` Sharpe 从 `3.16` 降至 `1.26`（`vRYq23qw`, `2Y=0.85`），证明**核心超额仍在 `TOP2500` 中大盘+次优盘结构中，不宜直接切小宇宙 `TOP1200`**！
  - **立即精准修正**：停掉 `TOP1200/TOP800`，回归 **`EUR / TOP2500`**，在 `TOP2500` 内直接采用 **单数据集 ATOM 总资产大盘门控/分桶**（`mdl25_bsv421_5v`: `if_else(rank(...)>0.3/0.45, ...)` 与 `bucket(rank(...), range="0.2,1,0.2")`）+ **`adv20` 流动性大盘门控** + 轻参数微调（`decay ∈ {0,2,4,6}`、`truncation ∈ {0.04,0.06,0.08}`），专攻把 `Sub-Universe Sharpe` 从 `1.29` 推过门槛实现 **`0 FAIL` `POOL_S`**！同时广州服务已热切换至 **`--region EUR,USA` 专注 2 方向独占模式**。

- **2026-11-25 22:20（2 小时定时审计 #1 · 0-FAIL 大爆发 + 真实远程 PC 体检救命避坑 & 精准压 PC 升级！）**：
  - **重大战果**：`EUR / TOP2500 / model25` 累计 `224` FULL，产出 **`82` 条 `Sharpe ≥ 1.58`**，其中 **`adv20` / `mdl25_bsv421_5v` 大盘门控一次斩获 `20+` 条 `0-FAIL` `POOL_S` 全绿因子**（全部通过 `LOW_SUB_UNIVERSE_SHARPE` 与 `IS_LADDER_SHARPE 2Y > 2.02`），最高 **`6XG8AOVP`**（`Sh=2.49, 2Y=2.40, Fit=2.38, Mgn=18.60bp`）、**`rK030WX9`**（`Sh=2.25, 2Y=2.29, Mgn=31.44bp`）、**`pwWXv5Kq`**（`Sh=1.95, 2Y=2.20, country*industry, RAM`）、**`WjYqLeGo`**（`Sh=1.63, 2Y=2.28, min(rank(val_mom), rank(op_eff)), RAM`）！
  - **关键 Stage-4 真实体检（本地 92-OS SC + 异步远程 `pc_poller.py`）**：
    - **本地 SC 全部极度安全（`0.23–0.41 << 0.68`）**，与我方现有 18/26 条 EUR OS 零撞车；池内正交剪枝保留 `6XG8AOVP` + `pwWXv5Kq`（两两 `0.6242`）+ `1YG9P5lK`。
    - **但真实远程 Prod Correlation（PC）暴露关键规律（幸亏严禁轻信 `cnhkmcp` 假通过！）**：
      - 普通 `INDUSTRY`/`MARKET` 的 `model25` 因子（`6XG8AOVP`、`rK030WX9`、`xAl6lnMp`、`A1LWQKrW`、`gJrArXVO`）`PC = 0.863–0.947`（StarMine 热门拥挤区）；
      - **但仅凭 `REVERSION_AND_MOMENTUM` + `country*industry`（`pwWXv5Kq`）就把 `PC` 砍降 `-0.153` 至 `0.7948`**；
      - **仅凭 `REVERSION_AND_MOMENTUM` + 双支 `min(rank(val_mom), rank(op_eff))`（`WjYqLeGo`）就把 `PC` 砍降 `-0.166` 至 `0.7815`（距 `< 0.70` 仅差 `0.08`！）**
  - **本轮精准方向修正**：
    1. **下线低天花板 `EUR / price_signal_dl`**（`148` FULL，`0` 条 `≥1.25`，最高 `1.22`、`max_fit=0.36`）；
    2. **上线 `S3-r2-EUR-M25PCA/B` 专项压 PC 组合包**（[stage23_refiner.py](../../../wq_research_v2/src/wq_research_v2/stage23_refiner.py)）：将 `WjYqLeGo` 与 `pwWXv5Kq` 两大已验真降 PC 杠杆叠加 **`STATISTICAL` / `SLOW_AND_FAST` / `CROWDING` / `FAST`** 风险模型中性化 + **`signed_power(..., 2/0.5)`** + **`ts_av_diff(..., 126)`** + **`vector_neut(..., rank(ts_mean(returns, 22)))`** + **跨数据集融合超低拥挤 `EUR / model238`（SmartHoldings，`cov=96.27%`, `aCnt=0..2`！）**，目标把 `PC` 从 `0.7815` 压穿 `< 0.68` 直取可打 `Useful` 的全绿正交因子！
    3. **接入 `EUR_M238_SMARTHOLDINGS_NORM`**（8 个 `aCnt=0..3`、`cov=96.27%` 的 `_d1` 干净 MATRIX 字段，直补 `EUR / model 1.3×, 0 OS` 空白塔）。

- **2026-11-26 00:41（2 小时定时审计 #1 · 重大里程碑：首条 100% 全绿 `Useful` 因子 `RR5QjWYz` 诞生并完成平台打标写别名！）**：
  - **首破 `EUR / D1 / model (1.3×, 0 OS)` 空白金字塔！** 经过 `S3-r3b-EUR-FINA` 精准微调（`CROWDING, d=5, tr=0.08, adv20 > 0.4` + `val_mom × mdl25_8v` 应计项双支 + `country*industry`），一次性跑出 **`8` 条新 `0-FAIL` `POOL_S`**，其中：
    - **`RR5QjWYz`（已打 `Useful` + 别名 `SC 0.259 PC 0.668`）**：**`Sharpe = 1.74, 2Y = 2.28 (>2.02 PASS), Fit = 1.04, Sub-Uni = 0.94/0.90 PASS, TO = 6.3%, Margin = 14.10bp, 本地 SC = 0.259, 远程 PC = 0.668 < 0.70`**！
    - **`np6RxVz3`（已打 `SC_PASS` + 别名 `SC 0.241 PC 0.720`）**：`Sh=2.10, 2Y=2.73, Fit=1.56, Margin=15.10bp, 0 FAIL`（仅 PC 差 `0.02`）；
    - **`3qGrQQ8Q`（已打 `SC_PASS` + 别名 `SC 0.242 PC 0.720`）**：`Sh=2.14, 2Y=2.75, Fit=1.61, Margin=14.20bp, 0 FAIL`；
    - 同批另 5 条 `0-FAIL` 且 `SC = 0.229–0.259`（`WjYQ18WQ`, `kq8rEEAl`, `MPgRMMJ8`, `A1LZjjAw`, `omP588xJ`）已进入异步 PC 排队，下轮巡检继续按 **`Margin` 降序 + 正交 `< 0.68`** 收割！
  - **新集首波战果**：`EUR / TOP2500 / model238`（SmartHoldings）首波已出 **`kq87w6vO`（`Sh=1.50, SC=0.233, PC=0.6349`）**，已从易超时 `STATISTICAL` 切换至高速 `CROWDING/RAM`；新接入 `EUR / TOP2500 / model354`（`cov=100%, aCnt=1..3`）同步进入 `4,500/天` 连续流水线。

- **2026-11-26 02:50（2 小时定时审计 #2 · 串行 PC 体检再斩 5 条 `PC < 0.70` 全绿因子 + `model238` 正交大突破 + 僵尸仿真 `DELETE` 提速上线！）**：
  - **串行 Stage-4 PC/SC/正交审计战果（11/11 全部完成 `SC_PASS` 打标 + `SC 0.xxx PC 0.xxx` 别名，`0` 次 `/submit`）**：
    - 在 11 条新 `0-FAIL + 2Y ≥ 2.24` 候选中，共 **5 条全部打穿 `PC < 0.70`**：`kq8rEEAl`（`13.37bp, Sh=1.78, SC 0.259 PC 0.665`）、**`vRYM8X5d`**（`12.97bp, Sh=1.92, 2Y=2.73, Fit=1.35, SC 0.254 PC 0.662`）、`A1LZjjAw`（`12.89bp, SC 0.251 PC 0.659`）、`omP57YLE`（`12.38bp, Sh=1.95, 2Y=2.74, Fit=1.39, SC 0.252 PC 0.661`）、`ZYX3k2O0`（`12.03bp, Sh=1.82, SC 0.239 PC 0.659`）；另 6 条 `vector_neut` / `sp2` 候选录得 `PC = 0.713–0.767`。
    - **Margin 优先 + 正交 `< 0.68` 关键洞察**：所有含 `value_momentum_region_percentile` 的 11 条候选与现役冠军 **`RR5QjWYz`（`Margin=14.10bp, SC 0.259 PC 0.668`）** 两两相关均达 `0.7069–0.9997`（均 `≥ 0.68`），因此 **`RR5QjWYz` 稳居该簇唯一最高 Margin `Useful` 冠军**，其余 11 条全部落位 `SC_PASS` + 精确 `SC/PC` 别名（`vRYM8X5d` 作为高夏普 `1.92` 备胎登记在案）。
  - **重大正交突破 & 换轨升级**：
    1. **`EUR / model238`（SmartHoldings）直出 `xAl8adOn`（`country_relative_investment_rank_d1`, `Sh=1.58, 2Y=1.95, SC=0.284`）且与 `RR5QjWYz` 两两相关仅 `0.2957`（完全正交！）**，仅缺 `Fitness(0.77)` 与 `Sub-Uni(0.13)` → 已上线 **`S3-r4-EUR-M238-*`** 置顶第 1 顺位直冲第 2 条正交 `Useful`！
    2. **新增纯非 `val_mom` 高 Margin 正交包 `S3-r4-EUR-OPEFF-*`**（主攻 `operating_efficiency_component_percentile` × `exclusions`/`accruals`/`NOA`/`model238`，脱离 `val_mom` 相关性簇，历史 Margin `40–52bp`！）。
    3. **止损弱集 & 接入新蓝海**：淘汰 `EUR / model354`（`40 FULL, 0 命中, max=0.47`），换入实盘核验的 **`EUR / ai_equity_alpha`**（`cov=86.1%, aCnt=0..1`，分析师预测修正 AI 信号）。
    4. **根治吞吐卡顿**：实证抓出 BRAIN 后端卡死在 `progress=0.15/0.90` 长达 44 分钟以上的僵尸仿真占满并发槽并引发 `POST 429` → 已实测官方 `DELETE /simulations/{id}` 返回 `HTTP 200` 清理僵尸成功，并在 `sim_runner.py` 固化 **`stall_timeout_sec=240s` 停滞早退 + 自动 `DELETE` 释槽 + 子查询 429 重试**！

- **2026-11-26 04:42（2 小时定时审计 #3 · 0 次 `429` + `model238` 爆出 `88G9Kk9o` (`Sh=1.76, SC=0.188, PC=0.608, corr=0.205`) + EUR 并发降为 1 槽消杀 `Sim ERROR`！）**：
  - **新增 3 条 `0-FAIL + SC < 0.65` 全完成打标与别名**：`1YGb19Gm`（`13.64bp, Sh=1.74, SC 0.239 PC 0.667`）、`2rGzqY2x`（`12.91bp, Sh=1.77, SC 0.239 PC 0.664`）、`WjYQw5xG`（`11.24bp, Sh=1.61, SC 0.251 PC 0.742`），均因与 `RR5QjWYz`（`14.10bp`）相关性 `0.820–0.979 ≥ 0.68` 归入 `SC_PASS`；**`RR5QjWYz` 稳居唯一最高 Margin `Useful` 冠军**。
  - **头号正交核弹诞生：`EUR / model238` `88G9Kk9o`**：`group_zscore(ts_backfill(regional_change_in_preference_rank_d1, 21), industry)`（`RAM d=0`）直出 **`Sh = 1.76, 2Y = PASS, 本地 SC = 0.1876, 远程 PC = 0.6075, 与 RR5QjWYz 相关性仅 0.2054`**，仅缺 `Fitness(0.60)` 与 `Sub-Uni(0.43)`！
  - **坏批次复盘与精准纠偏**：`S3-r4-EUR-M238` 与 `S3-r4-EUR-OPEFF` 因直接硬切 `adv20 > 0.40/0.45` 导致信号掉至 `0.71/0.83` → 新上线严格单轴 **`S3-r5-EUR-88G-*`**（严禁硬切 `adv20 > 0.40`，在 `RAM` 下采用轻衰减 `d={2,4,6}` + `ts_decay_linear(3/5)` + `hump(0.01)` + 轻门控 `adv20 > 0.20/0.30` 及原池 `TOP1200/TOP800` 对照），直冲第 2 条正交 `Useful`！
  - **工程与数据集换血**：实证 `EUR` 2 并发叠加 `VECTOR` 集 `ai_equity_alpha` 导致 `58%` 后端 `Sim ERROR`/停滞（而 `USA` 零 `Sim ERROR` 且完成率 `88–100%`！）→ 立即淘汰 `EUR/ai_equity_alpha`，引入纯 `MATRIX` 机构大集 **`EUR/model77`**（S&P Capital IQ Alpha Factors, `dCov=1.00`）与 **`EUR/other455`**（`other 1.5×` 最高塔倍率, `cov=97.1%`），并上线 **`--region-caps EUR:1,USA:3`**（EUR 单槽稳健零抖动 + USA 三槽高速满载）+ 修复空体 `HTTP 200` 僵尸漏删边界。

- **2026-11-26 06:40（2 小时定时审计 #4 · `EUR / model77` 首波 48 条直接爆矿！全员天然正交 `RR5QjWYz` + 19–25bp 高 Margin！）**：
  - **重大新矿脉大爆发（`EUR / TOP2500 / model77` S&P Capital IQ Alpha Factors，仅跑 `48` FULL 即出 `2` 条 `POOL_S` + `3` 条 `Sh ≥ 1.65`）**：
    - **`1YGbzOlz`**（`mdl177_qvm_ev_qvaeur_alt`, `RAM d=0`）：**`Sh = 1.80, 2Y = 2.49, Fit = 1.25, TO = 6.2%, Mgn = 19.30bp, SC = 0.345, 与 RR5QjWYz 相关仅 0.583 (< 0.68 正交!), PC = 0.850`** — 仅差 1 项 `Sub-Uni(0.53)` + 压 PC！
    - **`N1KmRLLE`**（`mdl177_qvm_ev_qvaeur_alt m22`, `RAM d=0`）：**`Sh = 1.65, 2Y = 2.45, Fit = 1.01, TO = 3.7%, Mgn = 25.29bp, SC = 0.336, corr(RR5) = 0.540, PC = 0.813`** — 仅差 1 项 `Sub-Uni(0.45)` + 压 PC！
    - **`gJrO9RbK`**（`mdl177_emm_fc_rev3y2_alt` 3M FY2 EPS 修正, `RAM d=0`）：**`Sh = 1.66, Fit = 0.91, SC = 0.149, corr(RR5) = 0.135（几乎零相关!）, 远程 PC = 0.6976（原生态已破 < 0.70!）`**！
  - **`model238` 复盘**：`S3-r5-EUR-88G` 将 `88G9Kk9o` 推至 **`78GbxbA1`（`Sh=1.73, 2Y=2.21, Fit=0.99, SC=0.346, corr=0.250, PC=0.721`）**，但 `TOP1200` 骤降至 `0.43` 证实其纯单集难过 `Sub-Uni`，本轮将其作为正交减 PC 辅支融入 `S3-r6-EUR-M77`！
  - **立即置顶第 1 顺位**：上线 **`S3-r6-EUR-M77-*`**（复刻 `RR5QjWYz` 冠军公式：`country*industry + adv20(0.35/0.40/0.45) + qvm × emm/balshtrank/roe/model238 + signed_power + CROWDING/RAM`），同步追加 `EUR_M77_CAPIQ_V2_NORM`（8 个精选 `qvm/emm/dvm` 字段）并淘汰死集 `EUR / other455`（`24 FULL, max=0.36`）。

- **2026-11-26 08:40（2 小时定时审计 #5 · `EUR / model77` V2 再爆 `Sh=2.05` & `1.95` 正交双星！上线软门控 `S3-r7-EUR-M77V2`）**：
  - **V2 新星连爆**：
    - **`YPlK5WxA`**（`mdl177_qvm_dvm_qvaeur_alt`, `RAM d=0`）：**`Sh = 2.05, 2Y = 2.24, Fit = 1.54, Mgn = 21.81bp, SC = 0.316, corr(RR5QjWYz) = 0.557 (正交!), PC = 0.893`**，仅缺 `Sub-Uni(0.62)` + 压 PC；
    - **`88G93gMv`**（`mdl177_qvm_estrevrank_qmaeur_alt`, `RAM d=0`）：**`Sh = 1.95, 2Y = 1.63, Fit = 1.17, SC = 0.159, corr(RR5) = 0.271 (完全正交!), PC = 0.846`**，仅缺 `Sub-Uni(0.84)`（只差 `0.17`！）；
    - **`78GbZK6v`**（`mdl177_qvm_dvm_qvaeur_alt m22`）：**`Sh = 1.87, 2Y = 2.31, Fit = 1.24, TO = 3.7%, Mgn = 29.39bp`**！
  - **坏批次纠偏**：`S3-r6-EUR-M77` 对 `1.80` 的 `qvm_ev` 用 `adv20 > 0.40` 略重（降至 `1.47`）→ 新上线 **`S3-r7-EUR-M77V2-*`** 改以 `2.05 / 1.95` 更强基座配 **软门控 `adv20 > 0.25/0.30/0.35`** + `dvm × estrev × emm(PC=0.698) × model238` + `country*industry` + `signed_power(2)` 冲刺高 Margin 正交 `Useful`！
- **2026-11-26 09:15（`S3-r7-EUR-M77V2` 复盘 + 上线 `S3-r8-EUR-M77SUB` 精修 `Sub-Universe`）**：
  - `S3-r7-EUR-M77V2` 在 `adv20 > 0.30` 下完整保住了高 Margin 与强 Sharpe：`wpNxbL9x`（`Sh=1.74, 2Y=2.03, Fit=1.25, Mgn=22.88bp`）、`58G0gkRJ`（`Sh=1.70, Mgn=26.07bp`）、`88G9P92o`（`Sh=1.74, Mgn=17.47bp`），但仍仅差 **`LOW_SUB_UNIVERSE_SHARPE(0.53–0.55)`**；
  - 上线 **`S3-r8-EUR-M77SUB-*`**（`32 FULL`）：直接对 `2.05` `dvm` / `1.95` `estrev` / `1.66` `emm(PC=0.698)` 对比测试 **`TOP2500` + `adv20 > 0.45/0.50`** 与 **原生 `TOP1200`**（缩小中小盘稀释效应），直攻 `EUR` 第二条 `20bp+` 正交 `Useful`！
  - **重要反证（`09:34` 实测）**：`S3-r8-EUR-M77SUB-u1200_crd_d4_t08`（原生 `TOP1200`）全部掉至 `Sh <= 0.76`（最高 `GrQAWPMJ Sh=0.76`），证实 `EUR / model77` 超额收益高度集中于 `TOP2500` 中小盘端、不适合直跑 `TOP1200`；后续 `EUR` 应回到 `TOP2500` 搭配更强多因子组合或低拥挤新机构大集。
- **2026-11-26 10:55（2 小时定时审计 #6 · 修复 `S3-r10-EUR` `clamp`/`group_median` 算子报错并重发 `S3-r10b-EUR-PC-M25 / M77` 48 FULL！）**：
  - 根因定位：`S3-r10-EUR-PC-M25-*`（24 FULL）与 `S3-r10-EUR-PC-M77-*`（24 FULL）此前因含本账号不可用的 `clamp` 与 `group_median` 全部 `RESULTS_UNOBSERVED`；
  - 已在 `S3-r10b` 中分别替换为真实可用 Gold-81 算子 `tail(..., lower=0.2, upper=0.8, newval=0.5)` 与 `winsorize(divide(group_neutralize(...), group_std_dev(...)), std=3)`，并在广州热重启开跑，主攻 **`EUR/model25`（非 `val_mom` `OpEff × emm` 正交簇 + L6 `tail`）** 与 **`EUR/model77` 连续流动性倾斜（无硬切悬崖）**，冲刺 `EUR` 第 2 条正交高 Margin `Useful`！
- **2026-11-26 12:55（2 小时定时审计 #7 · EST `2026-11-26` 美东新一天 `EUR` 全新纯 `MATRIX` 机构四连发上新！）**：
  - `S3-r10b/r11` 复盘：`EUR / model77` 连续流动性倾斜打出 `wpNx22Gd`（`22.47bp, Sh=1.62, Fit=1.01`）与 `24.87bp`，但 `Sub-Uni` 仍停在 `0.52`；为跳出 `model25`（`RR5QjWYz` 已入 OS）与 `model77` 中小盘约束，美东新一天（`13:00 CST`）直接为 `EUR:1` 槽位前置 **4 个全新实盘核验纯 `MATRIX` 机构大集（零 `VECTOR` 停滞）**：
    1. **`EUR / model36`**（StarMine SmartRatios 信用风险，`cov=0.764–0.941, aCnt=0..4`）；
    2. **`EUR / model28`**（StarMine 结构性信用风险，`cov=0.911–0.930, aCnt=0..1`）；
    3. **`EUR / predictive_starmine`**（StarMine 预测性分析师修正，**7/7 `Alphas=0` 免额**, `cov=0.756–0.949`）；
    4. **`EUR / model27`**（StarMine 综合信用风险 CCR，`cov=0.779–0.967, aCnt=0..6`）。
- **2026-11-26 14:53（2 小时定时审计 #8 · 果断止损 3 个欧股弱集，全速换装 `model110` 机构多因子 + `model39` + `analyst39` + `shortinterest6`！）**：
  - **快速止损（已记入 `INEFF-05`）**：`EUR / model28`（`0/32, max=0.66`）、`EUR / predictive_starmine`（`0/24, max=0.26`）、`EUR / model27`（`0/24, max=0.73`）全部清出主队列；保留 `EUR / model36`（`4/32, max=0.89, 12.09bp`）观察。
  - **欧股纯 `MATRIX` 机构四王牌置顶**：换入 **`EUR / model110`**（`quality / value / growth / analyst_sentiment / alternative / tree / price_momentum_reversal / score` 8 大机构复合因子，纯 `MATRIX, cov=0.853`）、**`EUR / model39`**（StarMine Valuation-Momentum 纯 `MATRIX`）、**`EUR / analyst39`**（分析师盈利与财务比率 `cov=0.77–0.92`）、**`EUR / shortinterest6`**（SmartHoldings `cov=1.000, aCnt=5..25`），零 `VECTOR` 停滞直冲 `EUR` 正交高 Margin `Useful #2`！
- **2026-11-26 21:05（2 小时定时审计 #10 · 修复多区饿死调度 Bug 恢复 `EUR:2` 满载 + 上线 `S3-r17` 攻打正交低 PC 矿脉 `model238 (PC=0.608)` 与 `shortinterest6`！）**：
  - **`S3-r16-EUR-M110-LOWPC` 复盘（24/24 FULL 零超时）**：`mdl110_value × mdl110_tree` 最高 `P0P93QrM`（`Sh=1.47, 2Y=1.05, Fit=0.70`）与 `zqApRpJX`（`Sh=1.44, 2Y=0.97`）——注意因仅含 2 字段触发平台 **PPA-First** 检查显示 `FAIL=[]`，实为未达 RA `1.58` 且 `2Y` 偏弱，已严守规则不误标。
  - **高 ROI 正交升级 (`S3-r17`, 40 FULL) + `EUR:2` 恢复满载**：修复 `daemon_ra_runner.py` 去重前缀饿死 Bug（`collect_balanced_runnable_window()`），将 `EUR` 升回 **`EUR:2`** 并发并置顶两路低 PC 高 2Y 正交冲刺：
    1. **`S3-r17-EUR-M238-ORTHO`（24 FULL）**：直救仅差 `Fit=0.99` 与 `Sub-Uni` 的超低相关王牌 `78GbxbA1`（`Sh=1.73, 2Y=2.21, corr=0.205 vs RR5QjWYz, PC=0.608 < 0.70!`），叠 `EFF-03` (`adv20 > 0.35/0.40/0.45` + `country*industry` + 后置 `d10/15/22` + `tail25`) 冲刺 `EUR` 第 2 条完全正交 `Useful`；
    2. **`S3-r17-EUR-SI6-PROMO`（16 FULL）**：将 `shortinterest6` 首波 `1YGQzpGR`（`Sh=1.47, 2Y=1.91`）与 `P0PdGrlJ`（`1.37, 2Y=1.84`）配 `adv20` 门控 + `country*industry` + 跨集 `model238` 推向 Stage-3 `1.60+`。
