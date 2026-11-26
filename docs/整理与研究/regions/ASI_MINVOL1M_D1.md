# 地区独立作战档案：`ASI / MINVOL1M / D1`（亚太市场 · 独立 PPA 主题支线）

## 1. 亚太市场特征与 BRAIN 平台规则
- **市场微观结构**：多国混合市场（日本、香港、台湾、韩国、新加坡等），**必须重视 `COUNTRY` 中性化或 `group_cartesian_product(country, sector)`**，以通过日本子市场检查（`LOW_ASI_JPN_SHARPE ≥ 1.0`）。
- **平台硬规则**：必须开启 **`maxTrade = ON`**、满足 **`Robust Universe ≥ 90%`**；活跃 D1 Power Pool Theme（`7MZJV8A`, `11/23–12/20`），10 个官方推荐集均已验真有权限。
- **分离原则（不与 RA 主线混为一谈）**：本档案作为独立 PPA 支线保留，遵循 [d1_4stage_pipeline.json](../workflow/d1_4stage_pipeline.json) 的 `ppa_d1_standalone` 四阶段流程（`Sharpe ≥ 1.0` + `PPAC < 0.50` + 描述 `≥ 100` 字符 + 打独立标签 `PPA_Useful`），待主线 `DEU` RA 稳定放量后再择机单独启用。
- **核心字段卡**：[FLD-P3-ASI-MINVOL1M-D1.md](../records/fields/FLD-P3-ASI-MINVOL1M-D1.md)（注意 `behavioral_signals` 为已知伪 VECTOR，只测 `vec_avg`）。

- **2026-11-25 19:16（1 小时定时检查 #1 · `ASI / price_signal_dl` 单波爆发 5 条纯正向对称种子！）**：
  - 放宽 `600s` 超时后首波 `31/31` 零漏单完成，单波即出 **`5` 条正向 `POOL_B` 种子**（且正反完全对称验真：`6XG87dkJ = +0.98` vs `omP7keVv = -0.98`！）：**`kq8dY5nz` (`Sh=+1.13, 2Y=+1.40, Fit=0.57`)**、`6XG87dkJ` (`+0.98, 2Y=+0.97`)、`vRYq8P8b` (`+0.96`)、`O06YYNOv` (`+0.83`)、**`legd1PAN` (`+0.82, Margin=+15.28bp` 已过 ASI 15bp 安全垫！)**。
  - **加码方向**：提至全队列第 2 顺位，新增 `ASI_PRICEDL_DUAL_LOWTO`（前置 `ts_mean 22` 低换手高 Margin 变体 + `min(rank(vol), rank(trend))` 同集双支，保持 `maxTrade=ON` + `COUNTRY` + RA 与 PPA 严格隔离）。
- **2026-11-26 19:03（2 小时定时审计 #9 · 多域星阵 `ASI / MINVOL1M` 首波 `QUICK` 狂爆 `8` 条 `0-FAIL` 高质种子，`ASI` 现有 OS=0 天然 `SC=0.000`！）**：
  - **`ASI / MINVOL1M / model39`**（`64 QUICK, 0 unobs`，`7` 条 `0-FAIL`）：`akRqpR1v`（**`24.19bp`**, `Sh=1.98, 2Y=1.96, Fit=1.45, Sub-Uni PASS 1.13/0.58`）、`P0Pdk9Gq`（**`21.32bp`**, `Sh=2.10, 2Y=2.21, Fit=1.45, Sub-Uni PASS 1.19/0.62`）、`vRY3QYjr`（`17.66bp, Sh=2.21, Fit=1.91`）、`RR5nGWmg`（`12.65bp, Sh=2.35, Fit=1.87`）；实时核查 **`SC(ASI)=0.000`**，但单字段原始 `model39` `PC = 0.949–0.981`（后续晋级 `FULL` 必配 `country*industry` + `nonlinear_tail_group` / 跨集 `price_signal_dl` 降 PC！）。
  - **`ASI / MINVOL1M / price_signal_dl`（`Alphas=0` 免额）**：`d59AaaMg`（`normalized_volume_indicator_2`, `RAM d=4`）打出 **`Sh=1.74, 2Y=2.56, Fit=1.00, Sub-Uni PASS 1.19/0.51, fails=[], SC=0.000`**，为下一轮转 `FULL` 实盘冲 `ASI` 首条 `Useful` 的头号低拥挤种子！
- **2026-11-26 21:05（2 小时定时审计 #10 · 抓获两大核心排雷真相：`ASI QUICK` 漏检日本子市场陷阱 + `ASI:2` 导致 53% 停滞误杀！已降回 `ASI:1` + `360s` 并上线 `COUNTRY` 专项诊断）**：
  - **关键排雷 1（`QUICK` vs `FULL` 陷阱，记入 `INEFF-09`）**：`S3-r16` 晋级 `FULL` 实证显示，此前 `QUICK` 看似 `0-FAIL` 的 `ASI/model39` 在 `FULL` 下 **`16/16` 全员触发 `LOW_ASI_JPN_SHARPE (-0.19 ~ +0.35 / 1.00)` + `LOW_ROBUST_UNIVERSE_SHARPE (0.75× / 0.90×)` + `LOW_ROBUST_UNIVERSE_RETURNS`**（虽总 Sharpe 达 `QPWXVaPr 1.91 / 16.51bp`, `9qG0rwZo 1.83 / 17.43bp`）；原因一是 `QUICK` 跳过 ASI 专属子检，二是 `S3-r16` 的 `COUNTRY` 中性化批因并发停滞超时未出结果，仅看到了未去国家暴露的 `SUBINDUSTRY`/`RAM`；`behavioral_signals (d=20)` 跌至 `0.59`、`price_signal_dl (cty d=10)` 跌至 `0.63`。
  - **关键排雷 2（`ASI:2` 停滞根治）**：实测 `ASI:2` + `stall_timeout=240s` 在 30 分钟内造成 `64` 条 `progress=0.35` 误杀（健康 `ASI FULL` 耗时 `249–294s`），且去重前缀导致 `EUR/USA` 两槽闲置；已落地 `collect_balanced_runnable_window()` + **`ASI:1` 永久单槽** + **`stall_timeout=360s`**，并上线控制变量诊断包 **`S3-r17-ASI-M39-JPNFIX`（24 FULL：`COUNTRY` 中性化 × 国家内排序 `group_rank(..., country)` / `country*sector` × `d ∈ {0, 5, 15}`）**，实测验证能否把 `LOW_ASI_JPN_SHARPE` 拉过 `1.00`（若仍 `< 0.70` 立即止损换集）。
- **2026-11-26 23:00（2 小时定时审计 #11 · `ASI/model39` 彻底定案止损，换装低拥挤 `ASI/model25` 纯 `MATRIX`！）**：
  - `S3-r17-ASI-M39-JPNFIX`（`COUNTRY d=0/d=5`）与 `S3-r16-cty` 全部 `FULL` 完成，证实即便在 `COUNTRY` 中性化与国家内排序下 `ASI/model39` 仍仅得 `LOW_ASI_JPN_SHARPE = 0.08–0.36 / 1.00`（日本区结构性无信号），已正式移出主队列停止消耗额度；
  - 立即换入实盘核验的 **`ASI / MINVOL1M / model25`**（50/50 纯 `MATRIX`, `cov=0.804–1.000, aCnt=1..2`, `0 OS -> SC=0.000`, `maxTrade=ON`），保持 `ASI:1` 单槽稳健推进。
- **2026-11-27 00:56（2 小时定时审计 #12 · 🚀 `ASI/model25` 首波大爆发 `51.63bp / Sh=1.91 / 2Y=2.62`！立即转 `S3-r19-ASI-M25-FULL` 核验日本子市场！）**：
  - **首波 `QUICK` 战果（`152 QUICK`，`ev_to_ebitda_relative_score`, `aCnt=1`, `0 OS -> SC=0.000!`）**：
    - **`78GVVzjx`**（`group_rank(ts_decay_linear(ts_backfill(ev_to_ebitda_relative_score, 21), 10), subindustry)`, `COUNTRY d=0, maxTrade=ON`）：**`Margin = 51.63bp`**, **`Sh = 1.91`**, **`2Y = 2.62`**, **`Fit = 1.29`**, **`TO = 2.2%`**（`< 8%` 触发 `SKIP_LOW_TURNOVER` 跳过降换手！）；
    - 同字段多变体全面开花：`d59wlY2g`（`SUBINDUSTRY d=0`, `44.47bp, Sh=1.58, 2Y=2.06, Fit=1.32, TO=3.9%`）、`j2VQdVq5`（`62.96bp, Sh=1.47, 2Y=2.40`）、`ZYXLWXJn`（`103.89bp, Sh=1.34, 2Y=2.02`）。
  - **吸取 `INEFF-09` 教训立即转 `FULL` 实测**：严禁把 `ASI QUICK` 的 `FAIL=[]` 当真 `0-FAIL`，已热部署 **`S3-r19-ASI-M25-FULL`（24 FULL：`COUNTRY d=0` / `SUBINDUSTRY d=0` / `CROWDING d=2`, `maxTrade=ON`）**，覆盖单支 `ev_to_ebitda`（`subindustry`/`industry`/`country*industry`/`country`/`tail25`/`sp1.5`）及双/三支 `ev_to_sales`、`forward_10yr_eps_cagr × industry_credit_risk_percentile`，第一时间验明 **`LOW_ASI_JPN_SHARPE`** 与 **`ROBUST_UNIVERSE`** 真实表现！
