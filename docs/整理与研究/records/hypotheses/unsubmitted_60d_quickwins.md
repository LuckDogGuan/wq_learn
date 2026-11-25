# 近 60 天未提交 D1 Alpha 池全量速赢扫描报告（`2026-09-26` 至 `2026-11-25`）

> [!IMPORTANT]
> **范围硬锁**：严格遵循 **D1-Only（`Delay = 1` 唯一合法，严禁 `Delay = 0`）** 与 **只读安全边界**（全程仅调用 `get_user_alphas`、`get_alpha_details`、`get_pyramid_alphas`、`get_pyramid_multipliers`，零回测、零改属性、零自动提交）。
> **Margin 口径校准**：BRAIN API 返回 `margin` 为小数（`0.01 = 100bp`），全文已统一精确换算为 `bp`（`= margin × 10000`）。

---

## 1. 60 天池精确统计总览与门禁口径纠偏

### 1.1 精确总盘子与按月切分（两组独立切片交叉验证零误差）

| 时间窗口 (UTC) | 未提交 IS Alpha 精确总数 | 说明与扫描深度 |
| --- | :-: | --- |
| **`2026-09`（09-26 至 09-30）** | **96** | **100% 全量扫描**（96/96） |
| **`2026-10`（10-01 至 10-31）** | **11,987** | 细分验证：`10/01–10/03` **776**（已扫 top 300 覆盖全部 `Fitness ≥ 0.44`）· `10/03–10/10` **0** · `10/10–10/18` **8,537** · `10/18–10/26` **2,645** · `10/26–10/31` **29**（全扫） |
| **`2026-11`（11-01 至 11-25）** | **4,274** | 细分验证：`11/01–11/10` **35**（全扫）· `11/10–11/25` **4,239**（近 30 天 `10/26–11/25` 共 `4,303` 条，已按 `-is.fitness` 扫完 `offset=0..999` 覆盖 **100% `Fitness ≥ 1.06`**！） |
| **60 天合计（09-26 至 11-25）** | **16,357** | 两组独立切片校验：`872 + 0 + 8,537 + 2,645 + 64 + 4,239 = 16,357` ≡ `96 + 4,313 + 7,674 + 4,274 = 16,357` |

- **深度抽样池规模**：跨 31 路时间切片 × (`-is.sharpe` / `-is.fitness`) 拉取去重，共深度扫描 **2,651 条唯一未提交 Alpha**；**`Delay = 1` 占比 100.0%（2,651 / 2,651，检出 `Delay = 0` 为 0 条）**。
- **表达式+全参数去重**：按 `(regular.code, region, universe, neutralization, decay, truncation, maxTrade)` 去重后得 **2,454 条独立候选**。

### 1.2 深度扫描池 `Month × Region × Universe` 明细（共 2,651 条唯一 D1 Alpha）

| 月份 | Region | Universe | 扫描样本数 | 月份 | Region | Universe | 扫描样本数 |
| --- | --- | --- | :-: | --- | --- | --- | :-: |
| `2026-09` | `CHN` | `TOP2000U` | 16 | `2026-10` | `GLB` | `MINVOL10M` | 15 |
| `2026-09` | `EUR` | `TOP2500` | 64 | `2026-10` | `GLB` | `MINVOL1M` | 8 |
| `2026-09` | `GBR` | `TOP700` | 8 | `2026-10` | `GLB` | `TOPDIV3000` | 7 |
| `2026-09` | `USA` | `TOP3000` | 8 | `2026-10` | `USA` | `TOP1000` | 49 |
| `2026-10` | `ASI` | `MINVOL10M` | 8 | `2026-10` | `USA` | `TOP2000` | 89 |
| `2026-10` | `ASI` | `MINVOL1M` | 4 | `2026-10` | `USA` | `TOP3000` | 71 |
| `2026-10` | `ASI` | `TOP500` | 3 | `2026-11` | `CHN` | `TOP2000U` | 22 |
| `2026-10` | `CHN` | `TOP2000U` | 161 | `2026-11` | `EUR` | `TOP2500` | 349 |
| `2026-10` | `EUR` | `TOP1200` | 12 | `2026-11` | `EUR` | `TOPCS1600` | 32 |
| `2026-10` | `EUR` | `TOP2500` | 166 | `2026-11` | `GBR` | `TOP700` | 511 |
| `2026-10` | `EUR` | `TOP800` | 6 | `2026-11` | `USA` | `TOP1000` | 19 |
| `2026-10` | `EUR` | `TOPCS1600` | 91 | `2026-11` | `USA` | `TOP2000` | 51 |
| `2026-10` | `GBR` | `TOP700` | 815 | `2026-11` | `USA` | `TOP3000` | 66 |

### 1.3 关键发现：Power Pool `WARNING` 阻断纠偏 + 金字塔缺口对照

1. **严格纠偏（拦截“伪零 FAIL”陷阱）**：实盘 `is.checks` 揭示，当表达式满足 Power Pool 形态（算子 ≤8 且字段 ≤3）时，BRAIN 会把 Regular Alpha 必过项（`LOW_2Y_SHARPE`、`LOW_SHARPE`、`LOW_FITNESS`、`CONCENTRATED_WEIGHT`、`HIGH_TURNOVER`）显示为 **`WARNING` 而非 `FAIL`**！本报告**严格将上述全部数值类 `WARNING` 判为 RA 阻断项（归入 Tier-B）**，仅将相关性 `PENDING` 及非阻断项（`CLUSTER_TEST`、`MATCHES_*`、`HT_*`、`UNITS`）豁免。
2. **三档分层最终计数（基于 2,454 条去重 D1 候选）**：
   - **Tier-A（`GATE3_TIER1_PASS`，0 阻断 FAIL/WARN/ERR）**：**185 条去重**（剔除 7 条与已有 92 条 OS 完全同式的重复后，净剩 **178 条 / 36 个独立家族**），进一步按历史 `name/tags` 精准拆分为：
     - **Tier-A1（清白无高相关标）**：**74 条**（含 **37 条已标 `Useful` 且 SC<0.70 & PC<0.70 的现成准提交金矿** + **37 条全新待查远程 PC 候选**）！
     - **Tier-A2（临界 PC `[0.70, 0.76]` 且低 SC）**：**18 条**（单步保序降 PC 即过关！含 `GBR/D1/ANALYST` `PC=0.705`！）
     - **Tier-A3（高 PC `>0.76` 或 `SC_IS_HIGHT`）**：**86 条**（覆盖 `USA/OPTION`、`USA/OTHER`、`EUR/MODEL`、`EUR/INSTITUTIONS` 四大空白塔，适合结构化降 PC）。
   - **Tier-B（`ONE_FIX_AWAY`，仅差 1 个阻断项且 `Sharpe ≥ 1.35`）**：**859 条去重 / 86 个独立家族**（含 `CHN/D1/OTHER` `1.9×` 空白塔 18 条、`ASI/D1` 3 条、`EUR/D1/MODEL` 371 条、`USA/D1/OPTION` 84 条、`GBR/D1/RISK` 2 条等）。
   - **Tier-C（`GATE1_SIGNAL_SEEDS`，`0.8 < Sharpe < 1.35`）**：**140 条去重 / 55 个独立家族**（含 `GBR/D1/INSIDERS` `1.4×` 空白塔、`EUR/D1/INSTITUTIONS`、`USA/D1/MODEL`、`ASI/D1` 干净种子）。
3. **对照 3 个“2→3”速赢塔与高倍率空白塔实盘摸底**：
   - **`GBR/D1/OTHER`（当前 OS=2，差 1 条点亮 `1.6×`！）**：**直接爆仓速赢！** 池中现存 37 条 `Useful`（`eur_director_signal_value_2` / `eur_signal_value_1` / `eur_aggregated_value_2` / `eur_2-eur_3`）+ **7 条 11-24 全新独立集 `tm_15_*`（SC=0.14–0.18）**，**零新回测即可同时冲刺 `GBR/D1/OTHER` 2→3 及多条正交提交！**
   - **`GBR/D1/IMBALANCE`（空白 `0→1`，`1.0×`）**：9 条 11-24 全新低 SC（0.16–0.19）Tier-A1 现成候选，RN/IC 俱佳！
   - **`USA/D1/PV`（空白 `0→1`，`1.1×`）**：4 条未查 SC/PC 的 Tier-A1（需留意 `type=RA_CHILD` 提交流程）。
   - **60 天池确证空缺（必须由下阶段新实验补齐）**：**`GLB/D1/fundamental`（2→3）**、**`GLB/D1/analyst`（2→3）**、**`DEU/D1/*`（6 个 `1.8×` 空白塔）** 在近 60 天未提交池中均为 **0 条** Tier-A/B 存货（`GLB/MINVOL1M` 6 条 Tier-A 经核对为已有 OS `9qXaz2Qq` 等的重复表达，已自动剔除）。

---

## 2. Tier-A（`GATE3_TIER1_PASS`）— 立即可进本地 SC + 远程 PC 终检

> **现役 `GBR/D1/OTHER` 已有 2 条 OS 对照**：`1YWNm9eM`（`eur_director_signal_value_1`）与 `mLgkbx5p`（`eur_aggregated_value_1`）。因此下方 `eur_director_signal_value_2`、`eur_signal_value_1`、`eur_aggregated_value_2`、`eur_signal_value_2 - eur_signal_value_3` 均对现有 OS 低 SC；但**同族多条之间存在候选池内部互相关**，务必先跑候选池两两 SC 矩阵（每组只先提 1 条，防“交一个挂一批”），再叠加上完全不同数据集的 `tm_15_*`（`KPVlkqwE`）实现多条正交落地！

### 2.1 Tier-A1：清白无高相关标核心精表（Top 14 独立家族，直接推进 **92 → 100**）

| 优先级 | Alpha ID | 创建日 | Region / Uni | 命中金字塔 (现有OS / 倍率) | 核心设置 (Neut / Dec / Tr) | Sharpe | Fit | TO | Margin (bp) | 2Y / SubUni | RN / IC Sh | Ops & 分类 | 历史 SC/PC 标与状态 | 完整表达式与终检注意点 |
| :-: | --- | --- | --- | --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | --- | --- | --- |
| **P0-1** | **`mL6vGEzE`** | `10-12` | `GBR/TOP700` | **`GBR/D1/OTHER`** (**2→3**, `1.6×`) | `MARKET` / `5` / `0.08` | **2.76** | **2.17** | 34.3% | **12.4** | `1.67` / `1.44` (`≥1.31`) | **1.78** / `0.80` | 3 op · `ATOM+CLU` | **`SC 0.470 PC 0.638`** [`Useful`] | `ts_rank(max(rank(eur_director_signal_value_2), 0.8), 66)`（*注：PC/SC 已过线；留意 IC Sh=0.80 偏弱，GBR 不强制 IC*） |
| **P0-2** | **`KPVlkqwE`** | `11-24` | `GBR/TOP700` | **`GBR/D1/OTHER`** (**2→3**, `1.6×`) | `SUBINDUSTRY` / `6` / `0.04` | **2.22** | 1.26 | 36.0% | 6.5 | `1.63` / **`1.85`** (`≥1.05`) | **2.13** / `0.90` | **2 op** · `ATOM+CLU` | **`SC 0.184`** [未查 PC] | `signed_power(zscore(tm_15_r1_r5_r10_rh_glb_d1_r5_q1), 2)`（**完全独立于 `eur_*` 的新集！RN Sh=2.13 极强，可与 P0-1 正交双收**） |
| **P0-3** | **`bl8LnbA6`** | `10-19` | `GBR/TOP700` | **`GBR/D1/OTHER`** (**2→3**, `1.6×`) | `CROWDING` / `0` / `0.01` | 1.65 | 1.08 | **15.8%** | 8.6 | **`2.33`** / `1.15` (`≥0.78`) | — / `0.74` (**2Y IC=`2.08`!**) | 7 op · `ATOM+CLU` | **`SC 0.172 PC 0.538`** [`Useful`] | `ts_decay_linear(ts_decay_linear(group_zscore(scale(scale(ts_mean(eur_signal_value_2 - eur_signal_value_3, 22))), industry), 10), 5)`（**SC/PC 极低、差值结构、2Y Test IC=2.08！** 冗余 `scale(scale(...))` 若重跑可简） |
| **P0-4** | **`2rG8ZR8Z`** | `11-24` | `GBR/TOP700` | **`GBR/D1/IMBALANCE`** (**空白 0→1**, `1.0×`) | `SUBINDUSTRY` / `4` / `0.04` | **1.96** | **1.40** | **16.6%** | **10.3** | `1.75` / **`1.58`** (`≥0.93`) | **1.83 / 1.54** | 3 op · `ATOM` | **`SC 0.187`** [未查 PC] | `rank(ts_zscore(ts_backfill(imb5_score, 21), 252))`（**点亮全新空白塔！RN=1.83 & IC=1.54 双稳健**；同族备选 `XgNmlLm5` Sh=1.94/2Y=1.84） |
| **P0-5** | **`omomd71E`** | `10-13` | `GBR/TOP700` | **`GBR/D1/OTHER`** (**2→3**, `1.6×`) | `MARKET` / `5` / `0.08` | **2.57** | **1.89** | 40.9% | 10.8 | **`2.09`** / `1.52` (`≥1.22`) | **1.77** (2Y RN `2.38`) / `0.60` | 3 op · `ATOM+CLU` | **`SC 0.434 PC 0.607`** [`Useful`] | `ts_rank(max(rank(eur_signal_value_1), 0.8), 22)`（与 P0-1 互查本地 SC；2Y 表现强于 `mL6vGEzE`） |
| **P0-6** | **`xAbJ6grw`** | `10-12` | `GBR/TOP700` | **`GBR/D1/OTHER`** (**2→3**, `1.6×`) | `MARKET` / `0` / `0.08` | **2.76** | **1.88** | 56.6% | 9.3 | **`2.29`** / `1.43` (`≥1.31`) | **2.03** / `0.47` | 4 op · `ATOM+CLU` | **`SC 0.448 PC 0.625`** [`Useful`] | `ts_decay_linear(ts_quantile(max(rank(eur_aggregated_value_2), 0.8), 60), 2)`（备选低相关变体：`omWx3me6` `SC 0.353 PC 0.549`、`2rm3M5R8` `SC 0.323 PC 0.531`、`kqgz1q5k` `SC 0.192 PC 0.511`） |
| **P0-7** | **`leKO8qPA`** | `10-01` | `USA/TOP3000` | **`USA/D1/PV`** (**空白 0→1**, `1.1×`) | `STATISTICAL` / `25` / `0.08` | **2.73** | **1.57** | 38.8% | 6.6 (`≥5bp`) | `1.59` / `1.60` (`≥1.18`) | — / **`2.14`** | **2 op** · `ATOM+CLU` | [未查 SC/PC] | `-1 * rank(pv47_for_statssimple_only_spret)`（**重要核查**：`type=RA_CHILD` 须验证 UI 可否直提，若否用 `-rank(pv47_for_statssimple_only_spret)` 独立重跑即可同时去掉 `*`） |
| **P0-8** | **`6XKVp8kP`** | `10-01` | `USA/TOP2000` | **`USA/D1/PV`** (**空白 0→1**, `1.1×`) | `STATISTICAL` / `17` / `0.08` | **2.62** | 1.33 | 45.5% | 5.2 | `1.85` / **`1.89`** (`≥1.39`) | — / **`2.28`** | **2 op** · `ATOM+CLU` | [未查 SC/PC] | `-1 * rank(pv47_for_statssimple_only_spret)`（同上 `RA_CHILD`，2Y 更稳于 TOP3000 版；另 `omW5q512` D=22 Sh=2.50） |
| **P1-1** | **`1YGknEYQ`** | `11-24` | `GBR/TOP700` | `GBR/D1/MODEL` (饱和 23, `1.5×`) | `SUBINDUSTRY` / `4` / `0.04` | **2.38** | **2.29** | **14.4%** | **18.4** | `1.79` / `1.19` (`≥1.13`) | 1.41 / **1.74** | 3 op · `ATOM+CLU` | **`SC 0.514`** [未查 PC] | `reverse(rank(ts_rank(mdl177_rvm_tw_ep_alt, 126)))`（虽塔已饱和，但直接贡献 **92→100** 且 IC/Margin 顶级） |
| **P1-2** | **`e71knEaN`** | `11-24` | `GBR/TOP700` | `GBR/D1/MODEL` (饱和 23, `1.5×`) | `SUBINDUSTRY` / `2` / `0.04` | **2.28** | **1.77** | 20.6% | 12.1 | `1.81` / `1.18` (`≥1.08`) | **1.65 / 1.62** | 4 op · `ATOM+CLU` | **`SC 0.567`** [未查 PC] | `tail(vector_neut(ts_zscore(mdl38_rel_val_global_rk, 126), rank(star_val_buyback_yield)), lower=-0.75, upper=0.75, newval=0)`（同族备选 `GrQ1n9mZ` Sh=2.30、`6XGmRNGL` Sh=2.37） |
| **P1-3** | **`0mGOAaW8`** | `11-24` | `GBR/TOP700` | `GBR/D1/MODEL` (饱和 23, `1.5×`) | `SUBINDUSTRY` / `1` / `0.04` | **2.60** | 1.46 | 42.9% | 6.3 | **`2.35`** / **`1.63`** (`≥1.23`) | **1.60 / 2.06** | 5 op · `ATOM+CLU` | **`SC 0.458`** [未查 PC] | `reverse(tail(vector_neut(ts_zscore(mdl177_rvm_rvm_eur_composite_alt, 63), rank(mdl177_pmm_indrelrtn4w_alt)), lower=-1.0, upper=1.0, newval=0))`（备选低换手版 `wpNKJgpQ` TO=12.5% M=15bp 2Y=2.29、`MPgMKR6z` TO=8.7% M=21bp） |
| **P1-4** | **`LL8VlGQ1`** | `11-24` | `GBR/TOP700` | **`GBR/D1/OTHER`** (**2→3**, `1.6×`) | `SUBINDUSTRY` / `6` / `0.04` | 2.09 | 1.22 | 32.6% | 6.8 | `1.64` / **`1.80`** (`≥0.99`) | — | **2 op** · `ATOM+CLU` | **`SC 0.153`** [未查 PC] | `signed_power(zscore(tm_15_r1_r5_r10_rh_glb_d1_r10_q1), 2)`（`r10_q1` 支线，另有正交化版 `zqAKOQPK` `SC 0.173`、`blxGvVWm` `SC 0.179`） |
| **P1-5** | **`j287pqwO`** | `10-12` | `GBR/TOP700` | **`GBR/D1/OTHER`** (**2→3**, `1.6×`) | `MARKET` / `5` / `0.08` | **2.71** | **2.03** | 41.1% | 11.3 | `1.65` / `1.58` (`≥1.29`) | **1.78** (2Y RN `2.12`) / `0.99` | 3 op · `ATOM+CLU` | **`SC 0.423 PC 0.593`** [`Useful`] | `ts_rank(max(rank(eur_director_signal_value_2), 0.8), 22)`（比 `mL6vGEzE` PC 更低 `0.045` 且 IC 更高 `0.99`，两者二选一优胜） |
| **P2-1** | **`786bZAR5`** | `10-01` | `EUR/TOP2500` | `EUR/D1/PV` (已有 8, `1.1×`) | `STATISTICAL` / `25` / `0.08` | **3.29** | **1.55** | 41.1% | `4.5` *(偏低)* | `1.89` / `2.06` (`≥1.71`) | — / **`1.76`** | **2 op** · `ATOM+CLU` | [未查 SC/PC] | `-1 * rank(pv47_for_statssimple_only_spret)`（`RA_CHILD`；注意 EUR 经验 Margin 底线 `≥10bp`，当前 `4.5bp` 仅作备选） |

### 2.2 Tier-A2：临界 PC `[0.70, 0.76]`（全 IS 检查已 PASS + 低 SC，单步保序降 PC 即过关）

| Alpha ID | Region / Uni | 金字塔 (OS / 倍率) | Sharpe / Fit / 2Y | 原记录 SC / PC | 完整表达式 | 单变量降 PC 精准动作（无 `add`/`multiply`/`trade_when`） |
| --- | --- | --- | :-: | :-: | --- | --- |
| **`LL8VRmX6`** | `GBR/TOP700` | `GBR/D1/ANALYST` (3, **`1.6×`**) | `1.92 / 1.23 / 1.64` (**RN=2.07!**) | `SC 0.279` / **`PC 0.705`** *(仅超 0.005!)* | `signed_power(ts_zscore(ts_backfill(anl69_best_eeps_nxt_yr, 20), 84), 2)` | **单轴微调幂次** `signed_power(..., p)` 测 `p ∈ {1.5, 2.5, 0.5}`，或外层改 `group_rank(..., bucket(rank(cap), range='0,1,0.2'))`（同类还有 `LL8VRml6` `PC 0.720`、`E5mOK8b9` `PC 0.721`） |
| **`0mjmJqm8`** | `GBR/TOP700` | **`GBR/D1/OTHER`** (2→3, `1.6×`) | `2.59 / 2.02 / 2.03` | `SC 0.548` / **`PC 0.702`** *(仅超 0.002!)* | `ts_rank(max(rank(eur_signal_value_1), 0.8), 120)` | 已有同族 `O0J03O0Y`（w=66, `PC 0.692`）与 `omomd71E`（w=22, `PC 0.607`）过线，直接用前两者即可零回测替代 |
| **`zqAK5rXO`** | `GBR/TOP700` | `GBR/D1/MODEL` (23, `1.5×`) | `1.92 / 1.17 / 1.86` | `SC 0.476` / `PC 0.744` | `reverse(group_zscore(ts_rank(mdl177_rvm_rvm_eur_composite_alt, 126), subindustry))` | 单轴外层加 `signed_power(..., 2)` 或将 `subindustry` 换 `bucket(rank(mdl177_rvm_roe_alt), range='0,1,0.2')` 降 PC |
| **`N1ep1PqL`** | `GBR/TOP700` | **`GBR/D1/OTHER`** (2→3, `1.6×`) | `2.28 / 1.43 / 2.34` | `SC 0.684` / `PC 0.753` | `power(group_neutralize(max(rank(eur_aggregated_value_1 - eur_aggregated_value_3), 0.5), subindustry), 0.5)` | 单轴改用 `signed_power(..., 1.5)` 或切换 `neutralization = CROWDING`（参考 `bl8LnbA6` 在 `CROWDING` 下 PC 降至 `0.538`） |

### 2.3 Tier-A3：已全过 IS 门槛但被 `PC_IS_HIGHT` 拦截的 4 大高价值空白塔母本（供结构化降 PC）

| 空白塔 (现有OS / 倍率) | 代表 Alpha ID | 关键指标 (Sh / Fit / M / 2Y / RN) | 历史 SC / PC | 完整表达式 | 结构化降 PC 破局路径（严守无 `add`/`multiply`/`trade_when`） |
| --- | --- | --- | :-: | --- | --- |
| **`USA/D1/OPTION`** (`0→1`, `1.3×`) | **`e76lkM1z`** *(同族 9 条)* | `2.15 / 2.62 / 31.3bp / 2.88` (**RN=2.02!**) | `SC 0.372` / `PC 0.865` | `ts_delay(ts_decay_linear(implied_volatility_call_60 - implied_volatility_put_60, 66), 5)` | **高质量底核！** 用 `min(rank(expr_A), rank(expr_B))` 与同数据集期限结构斜率（如 `iv_call_60 - iv_call_180`）或偏度变化率 `ts_delta(...)` 组合，保持 `ATOM` 属性同时打散 PC |
| **`USA/D1/OTHER`** (`0→1`, `1.4×`) | **`P0Mak9Xx`** *(同族 6 条)* | `2.08 / 1.49 / 11.3bp / 2.56` | `SC 0.388` / `PC 0.902` | `ts_delay(ts_decay_linear(signed_power(subtract(group_rank(oth566_l2r20_label, subindustry), 0.5), 1.0), 22), 1)` | 单轴改 `signed_power(..., 2.0)` + 同集字段 `vector_neut` 或 `ts_delta` 去水平趋势降 PC |
| **`EUR/D1/MODEL`** (`0→1`, `1.3×`) | **`mL6RK55x`** / **`RR6QxQKe`** | `2.02 / 1.34 / 65.7bp / 1.88` (`RN=1.38`) | `SC 0.319` / `PC_HIGH` | `group_rank(earnings_quality_raw_score, subindustry)` *(仅 1 op!)* | 原始静态排名过于拥挤；单轴改为 `ts_zscore(..., 252)` 捕捉质量边际改善，或同集 `vector_neut(..., rank(accruals_component_raw_score))` |
| **`EUR/D1/INSTITUTIONS`** (`0→1`, `1.1×`) | **`N1Vvgwzo`** *(同族 3 条)* | `1.67 / 1.02 / 12.1bp / 2.12` | `SC 0.079` / `PC_HIGH` | `signed_power(group_zscore(-ts_quantile(vec_avg(holder_account_total),630), subindustry), 2)` | 与同数据集 `herfindahl_index_holdings` 构造 `min(rank(-ts_quantile(vec_avg(holder_account_total),630)), rank(ts_quantile(vec_avg(herfindahl_index_holdings),630)))`（筹码集中双确认，仍为 ATOM） |

---

## 3. Tier-B（`ONE_FIX_AWAY` — 距 RA 仅差 1 个单变量修复轴）

> **铁律**：以下全部单变量修复方案**严格禁止 `add (+)`、`multiply (*)`、`trade_when`**，优先保持 `SINGLE_DATA_SET (ATOM)` 豁免 IS Ladder，双信号融合一律使用表达式级 **`min(rank(expr_A), rank(expr_B))`** 或同集 `vector_neut`。

| # | Alpha ID | Region / Uni | 金字塔 (现有OS / 倍率) | 核心指标 (Sh / Fit / TO / M) | 唯一阻断项 (实测 vs 门槛) | 当前完整表达式 & 设置 | 精确单变量修复动作（ATLAS 分层） |
| :-: | --- | --- | --- | --- | --- | --- | --- |
| **B1** | **`RRePqKxz`** | `CHN/TOP2000U` | **`CHN/D1/OTHER`** (**空白 0→1**, **`1.9×`** 全场最高!) | `2.31 / 2.31 / 10.3% / 24.2bp` | `FAIL: LOW_2Y_SHARPE` (`1.53 < 2.07`) | `group_zscore(group_neutralize(group_neutralize(rank(group_neutralize(group_rank(ts_target_tvr_decay(group_rank(-vec_sum(aggregate_search_interest_score), sector), target_tvr=0.08), industry), subindustry)), subindustry), subindustry), industry)` (`SUBINDUSTRY`, D=0) | **[L3 算子消融 + 换伪 VECTOR 聚合]** ① 先按 `ZH87224 #51` 拆掉外层 6 层冗余嵌套 `group_neutralize/zscore`（10 op→3 op）并检验 `vec_sum` vs `vec_avg`（防 `JX14975 #100` 伪 VECTOR 漂移）；② 再单轴测 `target_tvr ∈ {0.12, 0.16}` 避免过度平滑杀掉近 2 年弹性（同类 `j2aoAAnZ` `mobile_search_engagement_score` 2Y=1.41 同法修复） |
| **B2** | **`2rmzwv5x`** | `ASI/MINVOL1M` | **`ASI/D1/OTHER+PV`** (**空白 0→1 + 活跃 Theme!**) | `1.96 / 1.00 / 12.0% / 5.4bp` *(偏低)* | `FAIL: LOW_ASI_JPN_SHARPE` (`0.80 < 1.00`) | `rank(group_neutralize(scale(ts_backfill(oth335_combined_all_region_hedge,12)/ts_std_dev(vwap,126)),sector))` (`STATISTICAL`, D=5, `maxTrade=ON`) | **[L4 嵌套分组救区域]** 将内层 `sector` 单轴替换为 `group_cartesian_product(country, sector)`（按 `SZ83096 #47` 强制日本子市场内部对齐）；同时观察 `Margin` 能否推近 ASI 15bp 底线 |
| **B3** | **`O08PGzNq`** | `ASI/MINVOL10M` | **`ASI/D1/PV`** (空白 0→1, `1.0×`) | `2.80 / 1.20 / 57.5% / 3.6bp` | `FAIL: LOW_2Y_SHARPE` (`1.06 < 1.58`) | `-1 * rank(pv47_for_statssimple_only_spret)` (`STATISTICAL`, D=5, `maxTrade=ON`) | **[L2 短窗时序 + 改写法去 `*`]** 先改写为 `-rank(pv47_for_statssimple_only_spret)`，单轴测试外层 `ts_mean(..., 3)` 或小步提高平台 `decay ∈ {8, 12}`（压低 57.5% 高换手并改善 2Y；注：ASI 需同步关注 Margin 偏低风险） |
| **B4** | **`wpZ0v7op`** | `EUR/TOP2500` | **`EUR/D1/MODEL`** (**空白 0→1**, `1.3×`) | **`3.47 / 3.01`** / `11.1%` / `17.1bp` | `WARN: LOW_2Y_SHARPE` (`1.49 < 1.58`, **仅差 0.09!**) | `ts_target_tvr_decay(group_neutralize(zscore(vec_avg(aggregated_model_score)), subindustry), target_tvr=0.08)` (`FAST`, D=0) | **[L3 放松过度平滑]** `target_tvr=0.08` 压制了近 2 年响应，单轴放宽 `target_tvr ∈ {0.12, 0.15}` 或切换中性化 `FAST → REVERSION_AND_MOMENTUM`（2Y 仅差 0.09，一步即破 1.58！） |
| **B5** | **`e7aQxnPz`** | `EUR/TOP2500` | **`EUR/D1/MODEL`** (**空白 0→1**, `1.3×`) | **`3.35 / 2.96`** / `5.5%` / **`35.8bp`** | `FAIL: LOW_SUB_UNIVERSE_SHARPE` (`1.29 < 1.74`) | `group_neutralize(zscore(quantile(value_momentum_sector_percentile)), industry)` (`FAST`, D=3, `maxTrade=ON`) | **[L4 嵌套分组救 Sub-Universe]** 将 `industry` 单轴替换为 `group_cartesian_product(country, industry)` 或 `bucket(rank(cap), range='0,1,0.2')`（压低大中小盘偏差，提升子池 Sharpe；同族 `j2aYOMp9` Sh=3.26 亦同法） |
| **B6** | **`0mPGZYoK`** | `EUR/TOP2500` | **`EUR/D1/MODEL`** (**空白 0→1**, `1.3×`) | `2.39 / 2.12 / 12.6% / 15.7bp` | `WARN: CONCENTRATED_WEIGHT` | `ts_decay_linear(ts_quantile(global_relative_valuation_rank_main, 66), 8)` (`SUBINDUSTRY`, D=0, `Tr=0.08`) | **[L3 尾部压缩 / 截断]** 单轴将设置 `truncation` 从 `0.08 → 0.04`（或开启 `maxPosition=ON`），或外层套 `rank(...)` 消除极值权重集中（0 损收益即过权重检查） |
| **B7** | **`j28qaZ2Z`** | `EUR/TOPCS1600` | **`EUR/D1/MODEL`** (**空白 0→1**, `1.3×`) | `1.91 / 1.95 / 10.4% / 25.1bp` | `WARN: LOW_2Y_SHARPE` (`1.54 < 1.58`, **仅差 0.04!**) | `signed_power(scale(mdl110_score), 2.0)` (`INDUSTRY`, D=4, `Tr=0.05`) | **[L3 幂次微调 / 减 Decay]** 单轴测 `signed_power(..., 1.5)` 或 `decay: 4 → 2` 抬升 2Y 仅需 +0.05 即可全通 |
| **B8** | **`O08EbYMR`** | `EUR/TOP2500` | **`EUR/D1/INSTITUTIONS`** (**空白 0→1**, `1.1×`) | `1.68 / 0.99 / 7.0% / 12.4bp` | `WARN: LOW_FITNESS` (`0.99 < 1.00`, **仅差 0.01!**) | `signed_power(group_zscore(-ts_quantile(vec_avg(holder_account_total),882), subindustry), 1.5)` (`REVERSION_AND_MOMENTUM`, D=0) | **[L3 幂次单轴]** 改 `1.5 → 2.0` 已在 Tier-A3 生成 `vR23eqGr`（Fit=1.01），若为避高 PC 可单轴改为 `tail(..., lower=-0.5, upper=0.5, newval=0)` 同步提 Fit 并降 PC |
| **B9** | **`xAvLg6aw`** | `USA/TOP3000` | **`USA/D1/OPTION`** (**空白 0→1**, `1.3×`) | **`2.19 / 2.67`** / `11.9%` / **`31.2bp`** | `FAIL: LOW_SUB_UNIVERSE_SHARPE` (`0.88 < 0.95`, **仅差 0.07!**) | `ts_decay_linear(implied_volatility_call_60 - implied_volatility_put_60, 66)` (`SUBINDUSTRY`, D=5, `maxTrade=ON`) | **[L4 市值分桶中性化 + 同步降 PC]** 外层单轴套 `group_neutralize(..., bucket(rank(cap), range='0,1,0.2'))` 或与 `ts_delta(implied_volatility_call_60 - implied_volatility_put_60, 22)` 做 `min(rank(A), rank(B))`（既救 SubUni 又解 `e76lkM1z` 的 PC=0.865；同类 `P05YgYXW` `TOP2000` 差 `0.03` 亦同） |
| **B10** | **`qM7w7d3E`** | `USA/TOP3000` | **`USA/D1/OTHER`** (**空白 0→1**, `1.4×`) | `1.54 / 1.07 / 6.2% / 19.3bp` | `WARN: LOW_SHARPE` (`1.54 < 1.58`, **仅差 0.04!**) | `ts_mean(signed_power(subtract(group_rank(oth566_l2r5res_label, subindustry), 0.5), 1.5), 120)` (`REVERSION_AND_MOMENTUM`, D=10) | **[L2 窗口单轴缩短]** 120 日均值叠加 `decay=10` 过慢，单轴改 `120 → 66` 或 `decay: 10 → 4` 即可越过 `1.58` 且观察 PC |
| **B11** | **`A1x2WQme`** | `USA/TOP3000` | **`USA/D1/MODEL`** (**空白 0→1**, `1.3×`) | `1.71 / 1.16 / 7.0% / 16.7bp` | `WARN: LOW_2Y_SHARPE` (`1.36 < 1.58`) | `group_neutralize(rank(rank(ts_decay_linear(group_rank(ts_zscore(mdl26_ep_yield_smartestimate_fy1, 252), subindustry), 5))), subindustry)` (`SUBINDUSTRY`, D=0, `Tr=0.01`) | **[L3 算子精简 + 窗口]** 拆冗余 `rank(rank(...))` 与重复 `subindustry`，单轴测试 `ts_zscore` 窗口 `252 → 126` 提升近 2 年敏感度 |
| **B12** | **`rKd3dd1a`** | `GBR/TOP700` | **`GBR/D1/RISK`** (**空白 0→1**, `1.2×`) | `1.67 / 1.43 / 12.3% / 14.9bp` | `FAIL: LOW_SUB_UNIVERSE_SHARPE` (`0.51 < 0.79`) | `group_rank(quantile(-ts_av_diff(alternative_market_cap_usd, 60)), subindustry)` (`MARKET`, D=5, `Tr=0.0`) | **[L4 中性化轴]** `Tr=0.0` 且 `MARKET` 导致子池偏斜；先单轴设 `truncation=0.04`，再单轴换 `neutralization = SUBINDUSTRY` |
| **B13** | **`RRAMOeQz`** | `GBR/TOP700` | **`GBR/D1/OTHER`** (**2→3**, `1.6×`) | **`2.97 / 2.54`** / `32.9%` / `14.6bp` | `FAIL: LOW_SUB_UNIVERSE_SHARPE` (`1.31 < 1.41`) | `ts_rank(max(rank(eur_top_director_signal_value_2), 0.5), 120)` (`MARKET`, D=5) | **[L3 阈值轴]** 将 `0.5` 单轴改为 `0.8` 或外层加 `group_neutralize(..., industry)`（参考 `mL6vGEzE` 同源已全通） |
| **B14** | **`mLYLvpLW`** | `GBR/TOP700` | **`GBR/D1/OTHER`** (**2→3**, `1.6×`) | `2.58 / 2.05 / 31.8% / 12.6bp` | `WARN: CONCENTRATED_WEIGHT` (`0.10 ≥ 0.10`, 压线!) | `ts_rank(max(rank(eur_signal_value_1), 0.8), 252)` (`MARKET`, D=5, `Tr=0.08`) | **[L3 截断轴]** 仅把设置 `truncation` 从 `0.08 → 0.04` 一步即解除 `0.10` 压线权重警告 |
| **B15** | **`ZYmpX92d`** | `GBR/TOP700` | **`GBR/D1/OTHER`** (**2→3**, `1.6×`) | `1.57 / 1.07 / 14.1% / 9.2bp` | `WARN: LOW_SHARPE` (`1.57 < 1.58`, **仅差 0.01!**) | `ts_decay_linear(group_zscore(winsorize(scale(ts_mean(eur_signal_value_2 - eur_signal_value_3, 22))), industry), 120)` (`CROWDING`, D=0, `Tr=0.01`) | **[L2 衰减窗单轴]** 外层 `120` 偏长，单轴缩短为 `60` 或 `22`（参考 `bl8LnbA6` 已升至 `1.65` 且 `PC=0.538`） |

---

## 4. Tier-C（`GATE1_SIGNAL_SEEDS` — `0.8 < Sharpe < 1.35` 非饱和/空白塔精选种子）

以下精选种子**避开饱和塔（`GBR/MODEL`、`EUR/FUNDAMENTAL`）**，聚焦**空白 D1 金字塔**，可直接进入第二关单变量打磨，或作为 **`min(rank(expr_A), rank(expr_B))`** 表达式级双强组合的天然配对素材：

| 种子 ID | Region / Uni | 目标空白金字塔 (倍率) | Sh / Fit / TO / M | Ops | 完整种子表达式（基线设置） | 第二关单变量强化 / `min(rank, rank)` 配对方向 |
| --- | --- | --- | :-: | :-: | --- | --- |
| **`blaK0a6K`** | `GBR/TOP700` | **`GBR/D1/INSIDERS`** (`0→1`, **`1.4×`**) | **`1.33 / 1.15`** / `15.1%` / `14.9bp` | 4 | `-1 * (scale(ts_backfill(scale(top_directional_significant_value_4), 22)))` (`MARKET`, D=0) | **距 1.58 最近空白塔种子！** 去掉 `*` 与重复 `scale`，单轴测 `-rank(ts_zscore(ts_backfill(top_directional_significant_value_4, 22), 126))`；或与同集 `qM7w2qEv`（`top_significant_value_3`, Sh=1.32）构造 `min(rank(A), rank(B))` 保持 `INSIDERS` ATOM！ |
| **`qM7w2qEv`** | `GBR/TOP700` | **`GBR/D1/INSIDERS`** (`0→1`, **`1.4×`**) | **`1.32 / 1.09`** / `17.1%` / `13.6bp` | 4 | `-1 * (scale(ts_backfill(scale(top_significant_value_3), 15)))` (`MARKET`, D=20) | 与 `blaK0a6K` 组成同集双强 `min(rank(-ts_backfill(top_directional_significant_value_4, 22)), rank(-ts_backfill(top_significant_value_3, 15)))` |
| **`LL5dwJ22`** | `USA/TOP1000` | **`USA/D1/MODEL`** (`0→1`, `1.3×`) | `1.25 / 1.12 / 26.0% / 16.1bp` | 2 | `-ts_zscore(revenue_stability_score, 20)` (`SUBINDUSTRY`, D=6) | 迁移至 `TOP3000` + 单轴拉长 `ts_zscore` 窗口 `{63, 126}`，或与下方 `MP0LapEL` 做同领域 `min(rank(A), rank(B))` |
| **`MP0LapEL`** | `USA/TOP1000` | **`USA/D1/MODEL`** (`0→1`, `1.3×`) | `1.24 / 1.08 / 8.7% / 21.9bp` | 2 | `rank(ts_zscore(downside_risk_score_value, 20))` (`SUBINDUSTRY`, D=6) | 迁移至 `TOP3000` + 测窗口 `{63, 126}`；低换手高 Margin 优质底核 |
| **`LLN0veX6`** | `USA/TOP3000` | **`USA/D1/OTHER`** (`0→1`, `1.4×`) | `1.31 / 0.91 / 12.8% / 9.6bp` | 3 | `zscore(group_rank(ts_delta(probability_label4_5quantile_5day_ohlcv_2, 252), industry))` (`SUBINDUSTRY`, D=6) | 单轴测 `ts_zscore(..., 126)` 替代 `ts_delta(..., 252)` 提 Sharpe；或与 `oth566` 构成互补研究池 |
| **`88PdKod7`** | `EUR/TOP2500` | **`EUR/D1/INSTITUTIONS`** (`0→1`, `1.1×`) | `1.27 / 0.59 / 6.2% / 8.8bp` | 3 | `group_zscore(ts_quantile(vec_avg(herfindahl_index_holdings),630), subindustry)` (`RAM`, D=0) | **天然配对 `N1Vvgwzo`（`holder_account_total`）！** 同数据集 `min(rank(A), rank(B))` 既保 ATOM 又破 `N1Vvgwzo` 的高 PC |
| **`LLZAljAL`** | `EUR/TOP2500` | **`EUR/D1/INSTITUTIONS`** (`0→1`, `1.1×`) | `1.29 / 0.61 / 9.1% / 6.2bp` | 4 | `group_zscore(-ts_quantile(vec_avg(top_weighted_account_number),630), subindustry)` (`RAM`, D=0) | 同属机构持股集中度独立字段，可替代/配对 `holder_account_total` 降 PC |
| **`QPKko7Xg`** | `EUR/TOPCS1600` | **`EUR/D1/MODEL`** (`0→1`, `1.3×`) | `1.28 / 0.80 / 1.7% / 59.8bp` | 1 | `rank(accruals_component_raw_score)` (`SUBINDUSTRY`, D=3) | 仅 1 算子、59.8bp 高 Margin，单轴加 `ts_zscore(..., 252)` 或与 `earnings_quality_raw_score` 配对 `min(rank(A), rank(B))` |
| **`3qVrgbQQ`** | `EUR/TOP800` | `EUR/D1/RISK` (OS=1, `1.0×`) | `0.91 / 0.87 / 3.6% / 63.0bp` | 3 | `-ts_mean(vec_avg(lending_fee_bid_rate),21)` (`COUNTRY`, D=3) | 融券费率高 Margin 种子（63bp），单轴改 `ts_rank(..., 252)` + 嵌套 `group_rank(..., subindustry)` 测 `TOP2500` |
| **`6XKVrldL`** | `ASI/TOP500` | **`ASI/D1/MODEL+SENTIMENT`** (空白 + 活跃 Theme) | `1.13 / 0.62 / 12.8% / 6.0bp` | 6 | `ts_target_tvr_decay(max(rank(ts_zscore(mdl26_ep_yield_smartestimate_fy1, 40)), rank(vec_sum(snl27_relpopularity1))), ...)` (`STATISTICAL`, D=10) | **切回 `ASI/MINVOL1M` + `maxTrade=ON`**，拆解为两个独立单集种子分别验 `PPA+ATOM`（免配额，仅需 Sharpe ≥ 1.0 且 `Robust ≥ 90%`！） |

---

## 5. `92 → 100` 零回测 / 极低回测速赢冲刺执行顺序（供下阶段 Orchestrator 直接接管）

1. **第一波 · 零回测直接终检（最快贡献 **+3 至 +5 条 OS**，同步点亮 2–3 个塔）**：
   - **目标 1（点亮 `GBR/D1/OTHER` 2→3，`1.6×`）**：先跑候选池两两本地 SC，从 `eur_*` 族（`mL6vGEzE` / `j287pqwO` / `omomd71E` / `xAbJ6grw`）择 1 条最优 + **`bl8LnbA6`**（差值结构，SC=0.172, PC=0.538, 2Y IC=2.08）+ **`KPVlkqwE`**（全新独立集 `tm_15_*`, SC=0.184, RN=2.13，跑 1 次远程 PC），预计可正交落地 **2–3 条**！
   - **目标 2（点亮 `GBR/D1/IMBALANCE` 空白塔 0→1）**：对 **`2rG8ZR8Z`**（`SC=0.187`, RN=1.83, IC=1.54）发起远程 PC 终检。
   - **目标 3（冲刺 `92→100` 纯数量补充）**：对 **`1YGknEYQ`**（Sh=2.38, Fit=2.29, IC=1.74）与 **`0mGOAaW8`**（Sh=2.60, IC=2.06, 2Y=2.35）发起远程 PC 终检；并核验 **`leKO8qPA`**（`USA/D1/PV` 空白塔，`RA_CHILD` 性质）可否直提或以 `-rank(pv47_for_statssimple_only_spret)` 1 次复现后终检。
2. **第二波 · 1–3 次单变量微调即过关（目标再收 **+3 至 +4 条**，突破 **100 条 SuperAlpha 门槛**！）**：
   - **`LL8VRmX6`**（`GBR/D1/ANALYST` `1.6×`，`PC=0.705` 仅超 `0.005`）：1 批 3 条 `signed_power` 幂次/分桶微调降 PC。
   - **`wpZ0v7op`**（`EUR/D1/MODEL` 空白塔，`2Y=1.49` 仅差 `0.09`）+ **`0mPGZYoK`**（`EUR/D1/MODEL`，`Tr: 0.08→0.04` 救权重）+ **`j28qaZ2Z`**（`2Y=1.54` 仅差 `0.04`）。
   - **`RRePqKxz`**（`CHN/D1/OTHER` **`1.9×`** 空白塔）：算子消融 10→3 op + `vec_avg` + 放宽 `target_tvr` 冲刺 `2Y ≥ 2.07`。
   - **`blaK0a6K` + `qM7w2qEv`**（`GBR/D1/INSIDERS` `1.4×` 空白塔）：`min(rank(A), rank(B))` 1 批出击。
3. **第三波 · 衔接 12-06 免额度主线（补齐 60 天池确证空缺）**：
   - 本次扫描已证实 **`GLB/D1/fundamental` (2→3)**、**`GLB/D1/analyst` (2→3)**、**`DEU/D1/*` (6 空白 `1.8×` 塔)** 及 **`ASI/D1` Theme 10 推荐集** 在近 60 天池无现成 Tier-A 存货，下阶段新建实验预算直接精准投向上述高倍率空白赛道。
