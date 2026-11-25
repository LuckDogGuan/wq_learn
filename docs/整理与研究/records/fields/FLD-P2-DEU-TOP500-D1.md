# Field Card · P2 `DEU / TOP500 / D1` 六塔 `1.8×` 全空白主战场（D1-Only）

> [!IMPORTANT]
> **范围硬锁**：严格锁定 **`DEU / TOP500 / Delay = 1 (D1)`**。所有元数据于 **`2026-11-25`** 经 `cnhkmcp` 只读实盘核验。
> **战略价值**：`DEU` 为常驻 Gold 区域，当前账号 **全部 16 个 D1 金字塔均为空白（`alphas = 0`）**，其中 **`model`、`analyst`、`other`、`fundamental`、`news`、`sentiment` 六大类别同时享受 `1.8×` 高倍率**，且执行常规非 CHN 门槛（`Sharpe > 1.58`, `Fitness > 1.0`, `Cluster Test ≥ 1.0`，且本账号 `DEU` 本地 SC 池为空 → `NO_PEERS_IN_REGION`，零自相关历史包袱！）。
> **免额度冻结红线（`yjwedz7`）**：`freeze_expiry = 2026-12-06`。本次在 `DEU/TOP500/D1` 已实盘核验 **189 个 `Alphas = 0` 字段**（含 **102 个 `cov > 0` 净数值/分组可用字段** + **86 个 `fundamental` 免额度字段**，已显式剔除 5 个 `analyst93` 纯 ID 字段）。

---

## 1. 卡片头与区域坐标总览

| 字段 | 核验值 |
| --- | --- |
| `card_id` | `FLD-P2-DEU-TOP500-D1` |
| `region` | `DEU`（常驻 Gold，非临时权限） |
| `universe` | `TOP500` |
| `delay` | `1`（硬断言 `settings.delay == 1`） |
| `verified_date` | `2026-11-25` |
| `freeze_expiry` | `2026-12-06` |
| `pyramid_categories & multipliers` | `model` (`1.8×`, `0 OS`) · `analyst` (`1.8×`, `0 OS`) · `other` (`1.8×`, `0 OS`) · `fundamental` (`1.8×`, `0 OS`) |
| `d1_thresholds` | `Sharpe > 1.58`, `Fitness > 1.0`, `1% < TVR < 70%`, `Weight < 10%`, `Cluster ≥ 1.0`, 经验 `Margin ≥ 10bp`；单数据集 ATOM 跳过 IS Ladder（核 `LOW_2Y_SHARPE` 实盘 `1.58`） |
| `sc_local_baseline` | `NO_PEERS_IN_REGION`（DEU 当前 0 条 OS，但需启用候选池内两两 SC 矩阵防 `JR23144 #12` 互撞！） |

---

## 2. 数据集 `model264` · `model` 塔（`1.8×`，0 OS）—— 全场头号免额度 MATRIX 矿脉

- **数据集元数据**：*Predictive data using Deep Learning models*，总计 `380` 字段，`cov = 99.73%`，`alphaCount = 271`，`valueScore = 5.0`，上线日期 `2026-07-01`。
- **核验统计**：首 50 字段全部为 **`MATRIX`**（`is_fake_single_vector = false`），`cov = 99.58%–99.66%`，`dateCoverage = 1.0`（✅ 远超 ≥5 年要求），其中 **`24` 个 `Alphas = 0`（全部免额度且 99.6%+ 覆盖）**，`26` 个 `Alphas > 0`。

### 2.1 `model264` · `Alphas = 0` 免额度队列（`FREE`，24 个已核实）

> **关键方向语义提示（必读！）**：`model264` 这一批 `mdl264_1l_*` 字段的含义均为 **“未来趋势将下跌（will be fall）的深度学习预测概率”**！因此：
> - **量价/资金流/分析师上修指标下跌概率越高 → 预期看空**，第一关基线先验负向（`reverse(rank(x))`）并同步验证正向（均值回归可能性）；
> - **波动率/特殊项目/负向指标**（如 `rta` ATR、`od` 终止经营、`ips` 特殊项目）下跌概率则可能对应正向质量改善，严禁默认全同号，必须按子域分组设方向！

| 子族 | `field_id` | `type` | `coverage` | `date_coverage` | `alpha_count` | 经济含义（预测未来趋势下跌的概率） |
| --- | --- | :---: | :---: | :---: | :---: | --- |
| **资金流与量价动能** | `mdl264_1l_fmc` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | Chaikin Money Flow（资金流量指标）下跌概率 |
| **资金流与量价动能** | `mdl264_1l_ifm` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | Money Flow Index（资金流量指数）下跌概率 |
| **资金流与量价动能** | `mdl264_1l_lda` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | Accumulation Distribution Line（量价派发线）下跌概率 |
| **资金流与量价动能** | `mdl264_1l_ovp` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | Percentage Volume Oscillator（成交量震荡指标）下跌概率 |
| **价格震荡/动量** | `mdl264_1l_icc` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | Commodity Channel Index（CCI）下跌概率 |
| **价格震荡/动量** | `mdl264_1l_ist` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | True Strength Index（TSI）下跌概率 |
| **价格震荡/动量** | `mdl264_1l_ompd` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | DecisionPoint Price Momentum Oscillator 下跌概率 |
| **价格震荡/动量** | `mdl264_1l_opd` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | Detrended Price Oscillator（DPO）下跌概率 |
| **价格震荡/动量** | `mdl264_1l_opp` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | Percentage Price Oscillator（PPO）下跌概率 |
| **价格震荡/动量** | `mdl264_1l_os` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | Stochastic Oscillator（随机震荡）下跌概率 |
| **波动与财报特殊项** | `mdl264_1l_rta` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | Average True Range（ATR 波动率）下跌概率（波动率收敛信号） |
| **波动与财报特殊项** | `mdl264_1l_ips` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | Special Items（特殊项目）下跌概率 |
| **波动与财报特殊项** | `mdl264_1l_od` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | Discontinued Operations（终止经营）下跌概率 |
| **分析师预期扩散/修正** | `mdl264_1l_m1d_cer_se` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | 1M 评级上调/下调扩散度下跌概率（**强基本面+分析师交叉共振首选**） |
| **分析师预期扩散/修正** | `mdl264_1l_m1r_cer_se` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | 1M 评级修正下跌概率 |
| **分析师预期扩散/修正** | `mdl264_1l_m1d_pt_se` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | 1M 目标价扩散度下跌概率 |
| **分析师预期扩散/修正** | `mdl264_1l_m1d_1yf_spd_se` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | 1M FY1 每股股息（DPS）扩散度下跌概率 |
| **分析师预期扩散/修正** | `mdl264_1l_m1r_mtn_spd_se` | `MATRIX` | `99.66%` | `1.0` (✅) | `0` (FREE) | 1M NTM 每股股息修正下跌概率 |
| **分析师预期扩散/修正** | `mdl264_1l_m1r_mtn_spfc_se` | `MATRIX` | `99.65%` | `1.0` (✅) | `0` (FREE) | 1M NTM 每股现金流（CFPS）修正下跌概率 |
| **分析师预期扩散/修正** | `mdl264_1l_m1d_gtl_se` | `MATRIX` | `99.63%` | `1.0` (✅) | `0` (FREE) | 1M 长期增长预期扩散度下跌概率 |
| **分析师预期扩散/修正** | `mdl264_1l_m1r_gtl_se` | `MATRIX` | `99.63%` | `1.0` (✅) | `0` (FREE) | 1M 长期增长预期修正下跌概率 |
| **分析师预期扩散/修正** | `mdl264_1l_m1d_1yf_van_se` | `MATRIX` | `99.61%` | `1.0` (✅) | `0` (FREE) | 1M FY1 NAV（净资产值）扩散度下跌概率 |
| **分析师预期扩散/修正** | `mdl264_1l_m3d_1yf_van_se` | `MATRIX` | `99.61%` | `1.0` (✅) | `0` (FREE) | 3M FY1 NAV 扩散度下跌概率 |
| **分析师预期扩散/修正** | `mdl264_1l_m1r_1yf_van_se` | `MATRIX` | `99.58%` | `1.0` (✅) | `0` (FREE) | 1M FY1 NAV 修正下跌概率 |

### 2.2 `model264` · `Alphas > 0` 普通参考队列（`NORMAL`，极低拥挤 `aCnt=1–2`）
- `mdl264_1l_ghc_qe_td_tl`（`aCnt=1`：长期负债/权益同比变化下跌概率）
- `mdl264_1l_m1r_1yf_spe_se`（`aCnt=1`：1M FY1 EPS 修正下跌概率）
- `mdl264_1l_m1d_1yf_spfc_se`（`aCnt=1`：1M FY1 CFPS 扩散度下跌概率）
- `mdl264_1l_m3d_cer_se`（`aCnt=1`：3M 评级扩散度下跌概率）
- `mdl264_1l_m1r_mtn_spe_se`（`aCnt=2`：1M NTM EPS 修正下跌概率）

---

## 3. 数据集 `analyst93` · `analyst` 塔（`1.8×`，0 OS）—— 严滤纯 ID 后的 38 个免额度 VECTOR

- **数据集元数据**：*Europe Analyst Estimate Daily Data*，总计 `100` 字段，`cov = 63.73%`，`alphaCount = 222`，`valueScore = 4.0`，上线日期 `2026-07-01`。
- **核验统计**：通过常规拉取 + `profitability` 检索共去重核验 `87/100` 个字段，全为 **`VECTOR`**（多分析师覆盖每只股票 → **真多元素 VECTOR，`is_fake_single_vector = false`**，适合 `vec_avg`/`vec_max`/`vec_min` 语义区分），`dCov = 1.0`（✅ ≥5yr）。
- **免额度清洗结果**：实测 `43` 个 `Alphas = 0` 字段，**显式剔除 `5` 个纯 IBES 分析师编号 ID 陷阱后，保留 `38` 个高纯度数值 `Alphas = 0` VECTOR 字段！**

### 3.1 🚫 `analyst93` 强制剔除清单（纯 ID 陷阱，严禁传入任何表达式！）
- **Alphas=0 中剔除（5 个）**：`anl93_profitabilityprev_analyst_analyst`、`anl93_accuracy_estimator_analyst`、`anl93_consistency_analyst_analyst`、`anl93_correv_analyst_analyst`、`anl93_correv_estimator_analyst`（描述均为 `Integer identifier / Numeric index of the analyst, consistent with IBES`）
- **Alphas>0 中剔除（2 个）**：`anl93_consistency_estimator_analyst`、`anl93_accuracy_analyst_analyst`
- **工程防线**：`expr_validator.py` 对 `anl93_*_analyst` 结尾字段直接硬拦截！

### 3.2 `analyst93` · 清洗后核心 `Alphas = 0` 免额度队列（`FREE`，精选 22/38 高经济价值字段）

| 子类 | `field_id` | `type` | `is_fake_single_vector` | `coverage` | `date_coverage` | `alpha_count` | 经济含义与聚合建议 |
| --- | --- | :---: | :---: | :---: | :---: | :---: | --- |
| **盈利能力（跟单收益）** | `anl93_profitabilityprev_analyst_profitability1_60d` | `VECTOR` | `false` | **`64.59%`** | `1.0` (✅) | `0` (FREE) | 过去 60 日跟踪分析师预测（法 1）的平均日收益；用 `vec_avg`（共识盈利力）或 `vec_max`（明星分析师） |
| **盈利能力（跟单收益）** | `anl93_profitabilityprev_analyst_profitability2_60d` | `VECTOR` | `false` | **`64.59%`** | `1.0` (✅) | `0` (FREE) | 过去 60 日相对预测日收盘价（法 2）平均日收益 |
| **盈利能力（跟单收益）** | `anl93_profitabilityprev_estimator_profitability1` | `VECTOR` | `false` | **`64.59%`** | `1.0` (✅) | `0` (FREE) | 过去全期跟踪机构（estimator）预测法 1 平均日收益（另有 `_60d`, `_120d`, `profitability2_60d` 均 `Alphas=0`） |
| **推荐评级跟单收益** | `anl93_recprofitabilityprev_analyst_profitability1` | `VECTOR` | `false` | `63.58%` | `1.0` (✅) | `0` (FREE) | 跟踪分析师评级变动（法 1）平均日收益（另有 `_20d`, `_60d`, `profitability2_60d` 均 `Alphas=0`） |
| **推荐评级跟单收益** | `anl93_recprofitabilityprev_estimator_profitability1_60d` | `VECTOR` | `false` | `63.58%` | `1.0` (✅) | `0` (FREE) | 跟踪机构评级过去 60 日（法 1）收益（另有 `_20d`, `_120d`, `profitability2_20d` 均 `Alphas=0`） |
| **预测准确率与修正胜率** | `anl93_estimator_accuracy2` | `VECTOR` | `false` | `63.28%` | `1.0` (✅) | `0` (FREE) | 机构按规则 2（到期日精确命中目标价）的预测准确概率；天然 `[0,1]` 无量纲 |
| **预测准确率与修正胜率** | `anl93_estimator_relative_ratio2` | `VECTOR` | `false` | `63.28%` | `1.0` (✅) | `0` (FREE) | 覆盖同股机构中方向修正胜率的 min-max 归一化值；**陷阱**：单分析师覆盖时为 `NaN` |
| **预测准确率与修正胜率** | `anl93_analyst_relative_accuracy1` | `VECTOR` | `false` | `63.28%` | `1.0` (✅) | `0` (FREE) | 覆盖同股分析师的准确率 1 组内排名（另有 `estimator_relative_accuracy3/4`、`analyst_relative_accuracy4` 均 `Alphas=0`） |
| **预测一致性（误差稳定性）** | `anl93_estimator_consistency` | `VECTOR` | `false` | `63.28%` | `1.0` (✅) | `0` (FREE) | 预测误差的负标准差（越大越稳定精准）；**极佳与盈利力组合成 `min(rank(盈利力), rank(一致性))`！** |
| **预测一致性（误差稳定性）** | `anl93_estimator_relative_consistency1` | `VECTOR` | `false` | `63.28%` | `1.0` (✅) | `0` (FREE) | 同股机构一致性排名（另有 `relative_consistency2` min-max 归一化，均 `Alphas=0`） |
| **活跃度与命中次数** | `anl93_estimator_correct_revision_times` | `VECTOR` | `false` | `63.28%` | `1.0` (✅) | `0` (FREE) | 方向预测正确的修正次数；可除以 `anl93_analyst_total_revision_times`（`aCnt=0`）或单用 `vec_sum` |
| **活跃度与命中次数** | `anl93_analyst_correct_forecast_times1` | `VECTOR` | `false` | `63.28%` | `1.0` (✅) | `0` (FREE) | 规则 1 命中目标价次数（另有 `estimator_correct_forecast_times1/2`、`consistency_analyst/estimator_total_forecast_times`、`profitabilityprev_estimator_total_forecast_times`、`recprofitabilityprev_estimator_total_forecast_times` 均 `Alphas=0`） |

### 3.3 `analyst93` · `Alphas > 0` 普通参考队列（`NORMAL`）
- `anl93_profitabilityprev_analyst_profitability1_20d`（`aCnt=1`）、`anl93_profitabilityprev_estimator_profitability2_20d`（`aCnt=1`）、`anl93_analyst_consistency`（`aCnt=1`）、`anl93_profitabilityprev_analyst_profitability2`（`aCnt=34`，可做阳性对照）。

---

## 4. 数据集 `other250` & `other455` · `other` 塔（`1.8×`，0 OS）

### 4.1 `other250`（details data，VECTOR，9 个 `Alphas=0` + 3 个 `Alphas>0`）
- **数据集元数据**：`cov = 61.26%`（高于 GBR 的 `52.06%`！），`dCov = 1.0`（✅ ≥5yr），`alphaCount = 6`，`valueScore = 7.0`，上线 `2026-07-01`，真多元素 VECTOR（`is_fake_single_vector = false`）。
- **`Alphas = 0` 免额度队列（9 个全收录）**：
  1. `sales_position_rank`（品类畅销排名，越低越热销 → 先验负向；`u=1, a=0`）
  2. `oth250_item_review_count`（解析时客户评论数；需求热度）
  3. `total_review_number`（采集时客户评论总数；适合 `ts_delta` 看增速）
  4. `oth250_item_display_price`（站点本币标价；必须做 `ts_returns`/`ts_rank` 去量纲）
  5. `product_listed_price`（USD 标价；同上）
  6. `oth250_price_range_max` / `oth250_price_range_min`（USD 价格带上下限；适合构造价格带比率 `vec_avg(max) / vec_avg(min)`）
  7. `product_price_upper_bound` / `product_price_lower_bound`（USD/本币价格区间上下限）
- **`Alphas > 0` 普通队列（3 个）**：`oth250_item_rating`（`aCnt=1`）、`average_star_score`（`aCnt=2`）、`oth250_rank`（`aCnt=2`）。

### 4.2 `other455`（Relationship enhanced with AI/ML，GROUP + MATRIX，首 50 抽检 **31 个 `Alphas=0` GROUP**）
- **数据集元数据**：`cov = 95.35%`，总计 `1,500` 字段，`alphaCount = 267`，`valueScore = 6.0`，上线 `2026-07-01`。
- **`Alphas = 0` 免额度队列（31 个 GROUP，`cov = 100%`, `dCov = 1.0`）**：
  - 全部为基于 Node2Vec 竞争关系图嵌入（`w1/w2/w3/w4`, `kmeans`/`pca_fact1..3`, `k=5/10/20`）的 D1 滞后聚类分组标签，如：
    - `oth455_competitor_n2v_p10_q200_w1_kmeans_cluster_10` / `_20`
    - `oth455_competitor_n2v_p10_q200_w2_kmeans_cluster_5` / `_20`
    - `oth455_competitor_n2v_p10_q200_w2_pca_fact1_cluster_5` / `_20`
    - `oth455_competitor_n2v_p10_q200_w3_pca_fact1_cluster_10` / `w4_kmeans_cluster_10`
- **`Alphas > 0` 连续值 MATRIX 队列（9 个，`cov = 71.87%`, `dCov = 1.0`, `aCnt = 2`）**：
  - 如 `oth455_competitor_n2v_p10_q200_w2_pca_fact1_value`、`w3_pca_fact2_value`、`w1_pca_fact3_value` 等。
- **使用纪律与陷阱**：
  - `GROUP` 字段**不可单独作为 Alpha 输出**，必须作 `group_rank(signal, grp)` / `group_neutralize(signal, grp)` 的分组参数；
  - 若想拿 `other` 塔单数据集 ATOM + 免额度，需检视 `other455` 其余 1,450 字段是否有 `Alphas=0` 的 `*_value` MATRIX 字段；若用 `other455` GROUP 搭配 `model264` 免额度字段，全式仍享免额度，但归属多数据集（需过 IS Ladder）。

---

## 5. 新发现并核验的 `DEU / TOP500 / D1` · `fundamental` 强数据集（`1.8×`，0 OS）

通过全量扫描 `DEU/TOP500/D1` 全部 10 个 `fundamental` 数据集，**主推 1 个已实测正覆盖的核心财报集 + 2 个 `Alphas=0` 高倍率应计/税务比率集**（组成双梯队）：

### 5.1 实测正覆盖首选：`fundamental6`（Company Fundamental Data for Equity，NORMAL 队列）
- **元数据**：`cov = 49.23%–65.87%`（唯一覆盖率已实测 >49% 的多字段基本面矩阵集！），`196` 字段，全 **`MATRIX`**，`dCov = 1.0`（✅ ≥5yr），`alphaCount = 1,184`，`valueScore = 3.0`。
- **精选高覆盖核心字段（全为 `MATRIX`, `dCov=1.0`, `pm=1.8`）**：

| `field_id` | `coverage` | `alpha_count` | 经济含义与组合建议 |
| --- | :---: | :---: | --- |
| `fnd6_revty` / `fnd6_revtsa` | **`65.87%`** / `65.13%` | `43` / `19` | 总营收（年/半年）；做盈利/现金流分母或营收增速 `ts_delta` |
| `fnd6_cptnewq_atq` | **`65.57%`** | `263` | 季度总资产；标准规模分母（配合 `fnd6_ewq_ibmiiq` 构造 ROA） |
| `fnd6_newq_cheq` | **`65.31%`** | `50` | 季度现金与短期投资；与总资产比值衡量现金缓冲安全垫 |
| `fnd6_ewq_teqq` | **`64.10%`** | `52` | 季度股东权益合计；构造 ROE 与杠杆率 |
| `fnd6_ewq_intanq` | **`63.19%`** | `6` | 季度无形资产合计（低拥挤！构造无形资产占比或有形净资产质量） |
| `fnd6_ewq_ibmiiq` | **`62.31%`** | `105` | 扣非及少数股东前净利润；分子首选 |
| `fnd6_ewq_eqrtq` | **`62.17%`** | `14` | 股权储备合计（低拥挤）；衡量留存盈余积累 |
| `fnd6_dpy` / `fnd6_dpsa` | `61.76%` / `60.13%` | **`1` / `2`** | 折旧与摊销（极低拥挤！与 `fnd6_newq_ppentq` `cov=60.56%, aCnt=6` 构造折旧强度/资本密度） |
| `fnd6_cptnewq_dlttq` / `fnd6_ewq_lltq` | `57.94%` / `54.15%` | `16` / **`4`** | 长期债务 / 长期负债合计；衡量长期偿债与去杠杆趋势 |
| `fnd6_gpsa` / `fnd6_chechy` | `54.51%` / `54.20%` | `7` / `8` | 毛利润 / 现金及等价物增减额；直接测盈利质量与现金创造 |
- **陷阱**：`fnd6_adesinda_curcd`（`cov=100%`, `aCnt=9`）是 **ISO 货币代码**，严禁当作数值信号！

### 5.2 免额度 `Alphas=0` 潜力强集：`fundamental89`（Accrual based Earnings Model）与 `fundamental93`（Earnings Tax Data）
- **为何纳入**：二者均为 `2026-07-01` 新上架的纯 **`MATRIX` 标准化比率集**，`dCov = 1.0`（✅ ≥5yr），且平台已产生 `484` / `46` 条实盘 Alpha（说明实盘有真实覆盖；`coverage = 0.0` 为 2026-07 DEU 新上数据集元数据尚未重算所致，**须在 Stage-0 先跑 4 条探针实测真实持仓覆盖与有效年**）。
- **`fundamental89`（首 50 抽检 29 个 `Alphas=0` MATRIX，全部为现成无量纲应计比率！）**：
  - 流动资产应计/总资产（均值法 2）：`fnd89_asset_43_13`（`aCnt=0`）
  - 流动资产应计/营收：`fnd89_asset_43_31`（`aCnt=0`）
  - 非流动资产应计/总资产：`fnd89_asset_52_11`、`fnd89_asset_53_11`、`fnd89_asset_55_11`、`fnd89_asset_56_11`（均 `aCnt=0`）
  - 非流动资产应计/营收：`fnd89_asset_52_31`、`fnd89_asset_54_31`（均 `aCnt=0`）
  - **经济直觉**：高应计往往伴随低未来收益（Sloan 应计异象），先验负向 `reverse(rank(x))`。
- **`fundamental93`（全量 46 字段中 28 个 `Alphas=0` MATRIX，含税务应计与递延税负债比率）**：
  - 优选：`fnd93_accruals_d1_mean`（LTM 应计比率均值）、`fnd93_accruals_d1_dts`（LTM 应计波动率）、`fnd93_tax_accruals_11` / `_12` / `_22` / `_31`（税务费用 − 实缴现金税 / 分母）、`fnd93_liability_d1_asset_change`（总资产同比变动比）、`fnd93_expense_d1_mean`（均 `Alphas=0`）。
  - **陷阱**：`fnd93_*_length` 仅是 LTM 观测计数，非经济方向信号。
- **补充参考**：`fundamental86`（Stock Reports Plus，7 个 1–10 十分位 MATRIX 综合评分，含 1 个 `Alphas=0`：`fnd86_insider_trading_score`，其余 `fnd86_earnings_score` 等已有 204 条实盘 Alpha）。

---

## 6. DEU 战区 12-06 前免额度优先攻击顺序
1. **第一波（纯 MATRIX，99.6% 覆盖，0 陷阱）**：`model264` 24 个 `Alphas=0`（按资金流 / 价格震荡 / 分析师扩散三大子族各抽 3–4 个跑 Stage-0 + 跨子族 `reverse(min(rank(A), rank(B)))`）→ 攻克 `DEU/D1/model (1.8×)`！
2. **第二波（清洗后 38 个纯数值 VECTOR）**：`analyst93` 盈利力 × 一致性 × 胜率双支组合 → 攻克 `DEU/D1/analyst (1.8×)`！
3. **第三波（双线并行）**：`other250` 9 个 `Alphas=0` VECTOR（`cov=61.3%`）攻 `DEU/D1/other (1.8×)`；`fundamental89`/`93` 先跑 8 条免额度覆盖探针 + `fundamental6` 正覆盖比率组攻 `DEU/D1/fundamental (1.8×)`！
