# Field Card · P4 `CHN / TOP2000U / D1` 全场最高倍率空白塔（`1.9× / 1.8×`，D1-Only）

> [!IMPORTANT]
> **范围硬锁**：严格锁定 **`CHN / TOP2000U / Delay = 1 (D1)`**。所有元数据于 **`2026-11-25`** 经 `cnhkmcp` 只读实盘核验。
> **战略价值**：`CHN` 为常驻 Gold 区域，当前账号 **全部 12 个 D1 金字塔均为空白（`alphas = 0`）**，其中 `other` 享全场最高倍率 **`1.9×`**，`analyst` / `fundamental` / `macro` 享 **`1.8×`**！且本次在 `other496`（`1.9×`）与 `analyst45`（`1.8×`）核验出 **`74` 个高质量纯数值 `Alphas = 0` 免额度字段**（`cov = 80%–100%`），在 **`2026-12-06` 冻结到期前可零额度成本深度试探**！
> **CHN 严苛门槛警告**：`Sharpe ≥ 2.08`、`Fitness ≥ 1.0`、`Returns ≥ 8%`、`Robust Universe ≥ 40%`、经验 **`Margin ≥ 20bp`**、`Weight < 10%`。严禁低质量放量，必须以高信噪比财报结构比率与分析师收益信号打穿 `Sharpe ≥ 2.08` 与 `Margin ≥ 20bp`！

---

## 1. 卡片头与区域坐标总览

| 字段 | 核验值 |
| --- | --- |
| `card_id` | `FLD-P4-CHN-TOP2000U-D1` |
| `region` | `CHN`（常驻 Gold） |
| `universe` | `TOP2000U` |
| `delay` | `1`（硬断言 `settings.delay == 1`） |
| `verified_date` | `2026-11-25` |
| `freeze_expiry` | `2026-12-06`（`yjwedz7` 免额度窗口） |
| `pyramid_categories & multipliers` | `other` (**`1.9×`**, `0 OS`) · `analyst` (**`1.8×`**, `0 OS`) |
| `d1_thresholds` | **`Sharpe ≥ 2.08`** · `Fitness ≥ 1.0` · **`Returns ≥ 8%`** · **`Robust Universe ≥ 40%`** · 经验 **`Margin ≥ 20bp`** · `1% < TVR < 70%` · `Weight < 10%`；单数据集 ATOM 跳过 IS Ladder（核 `LOW_2Y_SHARPE` 实盘要求） |
| `sc_local_baseline` | `NO_PEERS_IN_REGION`（CHN 当前 0 条 OS；多候选间启用两两 SC 矩阵） |

---

## 2. 数据集 `other496` · `other` 塔（**`1.9×`**，0 OS）—— 33 个 `Alphas=0` 财报 MATRIX 宝库

> **⚠️ 重大名称误导纠偏（实盘核实！）**：`other496` 在 `get_datasets` 中显示名称为 *"Intraday FX rates"*，但经 `get_datafields` 逐字段实核，其底层 **100% 是中国上市公司 ARD（As-Reported Data）资产负债表与利润表 `MATRIX` 财务字段**！
> - **核心价值**：① 挂在 **`other` 塔享全场最高 `1.9×` 倍率**，却拥有纯正基本面低换手特性（**天然极易满足 CHN `Margin ≥ 20bp` 与 `Returns ≥ 8%`**！）；② 去重核验 `63/91` 字段已找到 **`33` 个 `Alphas = 0` MATRIX**（其中 **`21` 个 `cov = 81%–100%` 且 `dateCoverage = 1.0`**，年报 `a_ard_*` 与季报 `q_ard_*` 齐备！）。

### 2.1 `other496` · `Alphas = 0` 免额度核心队列（`FREE`，精选 21 个高覆盖 `cov ≥ 81%` MATRIX）

> **财务量纲铁律**：全部字段均为原始财务金额，**严禁直接对绝对金额做横截面 `rank(x)`（否则退化为纯市值因子）**！在 `Alphas = 0` 免费队列中，可用**同集免额度资产/负债分母做结构比率**（如 `流动资产 / 非流动资产`、`应收账款 / 流动资产`、`应付账款 / 流动负债`）或**自身同比/环比增速**（`ts_delta(ts_backfill(x, 126), 252) / abs(ts_delay(ts_backfill(x, 126), 252))`），全程保持 100% `Alphas = 0` + ATOM！

| 频率 | `field_id` | `type` | `is_fake_single_vector` | `coverage` | `date_coverage` (`≥5yr`) | `alpha_count` | 经济含义与比率构造思路 |
| :---: | --- | :---: | :---: | :---: | :---: | :---: | --- |
| **季报 (Q)** | `oth496_q_ard_accts_receivable_trade` | `MATRIX` | `false` | **`100.00%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | 季度应收账款（贸易）；**高应收/低回款往往预警盈利质量恶化**，可比 `oth496_ard_total_cur_assets_282`（`aCnt=0`）构造应收占比 |
| **季报 (Q)** | `oth496_q_ard_other_current_assets` | `MATRIX` | `false` | **`100.00%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | 季度其他流动资产；做流动资产结构纯度指标 |
| **季报 (Q)** | `oth496_q_ard_total_noncurrent_assets` | `MATRIX` | `false` | **`100.00%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | **核心规模分母（Q）**：季度非流动资产合计；可与 `oth496_ard_total_cur_assets_282` 构造轻重资产结构比（流动/非流动） |
| **季报 (Q)** | `oth496_q_ard_tot_noncurrent_liabilities` | `MATRIX` | `false` | **`100.00%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | 季度非流动负债合计；比 `oth496_q_ard_total_noncurrent_assets` 构造**长期杠杆率（全免额度！）** |
| **季报 (Q)** | `oth496_q_ard_other_noncurrent_asset_267` | `MATRIX` | `false` | **`97.60%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | 季度其他非流动资产 |
| **季报/综合** | `oth496_ard_total_cur_assets_282` | `MATRIX` | `false` | **`100.00%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | **核心规模分母**：流动资产合计；与 `oth496_ff_liabs_curr_nugget` 构造**全免额度流动比率！** |
| **季报/综合** | `oth496_ff_liabs_curr_nugget` | `MATRIX` | `false` | **`100.00%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | **核心负债分母**：流动负债合计（financial fundamental nugget）；与 `oth496_ard_total_cur_assets_282` 构成黄金免费偿债比率 |
| **季报/综合** | `oth496_ard_accounts_payable_trade_333` | `MATRIX` | `false` | **`100.00%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | 应付账款（贸易）；比 `oth496_q_ard_accts_receivable_trade` 构造**上下游占款议价力（应付/应收）**！ |
| **季报/综合** | `oth496_ard_other_payables_277` | `MATRIX` | `false` | **`100.00%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | 其他应付款；A 股中异常高企常提示关联占款或资金紧张 |
| **季报/综合** | `oth496_ard_other_receivables_st` | `MATRIX` | `false` | **`100.00%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | 短期其他应收款；A 股经典财报排雷项（高其他应收款往往对应大股东资金占用，先验负向） |
| **季报/综合** | `oth496_ard_prepayment_advance_259` | `MATRIX` | `false` | **`100.00%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | 预付款项；衡量上游备货积极度或议价弱势（需行业内 `group_rank` 辨向） |
| **季报/综合** | `oth496_ard_deferred_inc_tax_asset_lt_343` | `MATRIX` | `false` | **`100.00%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | 长期递延所得税资产；与 `oth496_ard_deferred_income_taxes_liab`（`cov=92.37%`, `aCnt=0`）衡量税会差异 |
| **季报/综合** | `oth496_ard_deferred_income_taxes_liab` | `MATRIX` | `false` | **`92.37%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | 递延所得税负债（经典会计稳健性/激进度代理变量） |
| **年报 (A)** | `oth496_a_ard_accts_receivable_trade` | `MATRIX` | `false` | **`100.00%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | 年度应收账款（与季报版形成远近对比） |
| **年报 (A)** | `oth496_a_ard_other_current_assets` | `MATRIX` | `false` | **`100.00%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | 年度其他流动资产 |
| **年报 (A)** | `oth496_a_ard_total_noncurrent_assets` | `MATRIX` | `false` | **`100.00%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | 年度非流动资产合计 |
| **年报 (A)** | `oth496_a_ard_tot_noncurrent_liabilities` | `MATRIX` | `false` | **`100.00%`** | `1.0` (✅ ≥5yr) | `0` (FREE) | 年度非流动负债合计 |
| **年报 (A)** | `oth496_a_ard_acc_oth_comprehensive_inc` | `MATRIX` | `false` | `83.23%` | `1.0` (✅ ≥5yr) | `0` (FREE) | 累计其他综合收益（另有季报版 `oth496_q_ard_acc_oth_comprehensive_inc` 亦 `aCnt=0`） |
| **年报 (A)** | `oth496_ardr_additional_paid_in_capital_266` | `MATRIX` | `false` | `82.43%` | `1.0` (✅ ≥5yr) | `0` (FREE) | 资本公积（反映历史融资溢价与转增股本潜力） |
| **年报 (A)** | `oth496_a_ard_notes_payable_st` | `MATRIX` | `false` | `81.17%` | `1.0` (✅ ≥5yr) | `0` (FREE) | 短期应付票据（衡量供应链信用票据融资能力） |

*(注：另有 12 个 `other496` `Alphas=0` 字段覆盖率在 `27.4%–59.5%`，如 `oth496_a2_ardr_inventory` `59.5%`、`oth496_05000_net_profit_incl_min_int_inc_value` `27.8%`；覆盖 `<50%` 的 `05000_*` 利润表子项慎用于 `TOP2000U` 主池，防 `Robust ≥ 40%` 或 Sub-Universe 覆盖不足！)*

### 2.2 `other496` · `Alphas > 0` 普通队列核心底座（`NORMAL`，`cov = 100%`, `dCov = 1.0`）
- `oth496_ard_tot_assets_342`（总资产，`aCnt=14`）、`oth496_ard_tot_liabilities`（总负债，`aCnt=1`）、`oth496_ard_total_shareholders_equity_324`（股东权益，`aCnt=3`）、`oth496_ard_cash_and_equivalents_327`（现金及等价物，`aCnt=15`）、`oth496_ard_inventory`（存货，`aCnt=1`）、`oth496_ardr_retained_earn_acc_deficit_329`（未分配利润，`aCnt=2`）、`oth496_pedv`（折旧，`aCnt=1`）。
- **队列纪律**：若将免额度字段与上述 `aCnt ≥ 1` 底座字段组合，整条将计入 NORMAL 普通队列；因此建议 **12-06 前优先用 §2.1 内部纯 `Alphas=0` 比率跑免费探针**！

---

## 3. 数据集 `analyst45` · `analyst` 塔（**`1.8×`**，0 OS）—— 清洗后 41 个 `Alphas=0` 全覆盖 VECTOR

- **数据集元数据**：*Analyst Trade Ideas*（机构交易推荐想法绩效跟踪数据），总计 `60` 字段，`cov = 100%`，`alphaCount = 7`，`valueScore = 6.0`，上线 `2025-10-01`。
- **核验统计**：首 50 字段全为 **`VECTOR`**（每只股票可被多位分析师同时提交交易想法 → `is_fake_single_vector = false`，可分别检验 `vec_avg`/`vec_max`/`vec_min`/`vec_count`），`cov = 100%`，`dateCoverage = 0.9507`（✅ ≥5yr）。
- **免额度清洗结果**：首 50 中实测 **`44` 个 `Alphas = 0`**，**显式剔除 `3` 个货币代码字符串/分类字段后，保留 `41` 个纯数值 `Alphas = 0` VECTOR 字段！**

### 3.1 🚫 `analyst45` 强制剔除陷阱清单
- **Alphas=0 货币代码陷阱（3 个）**：`investment_currency_code_2`、`reference_index_currency_2`、`security_trading_currency_4`（货币标识代码，严禁参与数值运算）。
- **Alphas>0 废弃空字段陷阱（1 个）**：`adjusted_bias_return`（官方描述明确标示 **`Non-functional field; not in use`**，严禁触碰！）。
- **价格/本金量纲陷阱**：`most_recent_security_price_2`、`period_initial_price`、`period_final_price`、`position_exit_price`、`initial_price_including_fees`、`present_investment_amount`、`starting_investment_amount_2` 等均为绝对价格或投资金额，**严禁直接横截面裸排**，必须用相对比例或 `ts_rank`/`ts_returns` 消量纲！

### 3.2 `analyst45` · 清洗后高优先 `Alphas = 0` 免额度队列（`FREE`，精选 16/41 无量纲绩效与仓位信号）

| 子族 | `field_id` | `type` | `coverage` | `date_coverage` | `alpha_count` | 经济含义与优化提示 |
| --- | --- | :---: | :---: | :---: | :---: | --- |
| **风险调整绩效（首选）** | `risk_adjusted_performance_alpha` | `VECTOR` | **`100%`** | `0.9507` (✅) | `0` (FREE) | 交易想法相对市场基准的超额 Alpha；天然无量纲，首选 `vec_avg`（共识超额）与 `vec_max`（最强多头想法） |
| **风险调整绩效（首选）** | `risk_adjusted_return_treynor` | `VECTOR` | **`100%`** | `0.9507` (✅) | `0` (FREE) | 特雷诺比率（单位系统性风险超额收益）；与 `risk_adjusted_performance_alpha` 或 `net_exposure_value` 天然配对！ |
| **多空净暴露（首选）** | `net_exposure_value` | `VECTOR` | **`100%`** | `0.9507` (✅) | `0` (FREE) | **极强方向信号**：多头与空头交易想法的分数总价值之差（直接度量机构推荐净多空倾向！） |
| **超额与相对收益** | `relative_index_return_value_2` | `VECTOR` | **`100%`** | `0.9507` (✅) | `0` (FREE) | 交易想法收益与基准指数收益之差（相对超额收益百分比） |
| **超额与相对收益** | `mean_daily_relative_index_return_pct` | `VECTOR` | **`100%`** | `0.9507` (✅) | `0` (FREE) | 日均指数相对收益率（%） |
| **超额与相对收益** | `aggregate_return_percentage` | `VECTOR` | **`100%`** | `0.9507` (✅) | `0` (FREE) | 交易想法存续期总收益率（占平均投资额 %） |
| **超额与相对收益** | `aggregate_return_excluding_fx` | `VECTOR` | **`100%`** | `0.9507` (✅) | `0` (FREE) | 剔除汇率影响后的总收益率（%） |
| **超额与相对收益** | `mean_daily_return_pct` | `VECTOR` | **`100%`** | `0.9507` (✅) | `0` (FREE) | 存续期日均收益率（%） |
| **已实现/未实现收益** | `aggregate_realized_unrealized_return` | `VECTOR` | **`100%`** | `0.9507` (✅) | `0` (FREE) | 已实现 + 未实现总收益 |
| **已实现/未实现收益** | `realized_return_value` | `VECTOR` | **`100%`** | `0.9507` (✅) | `0` (FREE) | 想法已实现收益（反映落袋获利了结压力，需验正负方向） |
| **已实现/未实现收益** | `riskless_investment_rate_2` | `VECTOR` | **`100%`** | `0.9507` (✅) | `0` (FREE) | 开放想法的未实现浮盈/浮亏（注意字段名误导，描述为 `The unrealised return on an open idea`！） |
| **短期边际变动** | `realized_return_today` / `relative_return_percentage_today` | `VECTOR` | **`100%`** | `0.9507` (✅) | `0` (FREE) | 昨日收盘至今已实现收益增量（高频易高 TVR，须配 `ts_mean`/`ts_decay_linear` 平滑防破 `Margin ≥ 20bp`） |
| **短期边际变动** | `net_total_return_since_close_pct` / `price_change_percentage_today` | `VECTOR` | **`100%`** | `0.9507` (✅) | `0` (FREE) | 个股日收益率（%）；**陷阱**：近乎等价 PV1 `returns`，在 CHN D1 易高 PC 且易高换手，仅用于与想法绩效做回归去共性或中长窗反转 |
| **拥挤度与持仓周期** | `grouped_idea_quantity` | `VECTOR` | **`100%`** | `0.9507` (✅) | `0` (FREE) | 分组内的想法数量（分析师关注度/拥挤度代理） |
| **拥挤度与持仓周期** | `average_idea_age_period` | `VECTOR` | **`100%`** | `0.9507` (✅) | `0` (FREE) | 想法平均存续天数（**新推荐 vs 陈旧持仓**区分指标：年轻想法往往动量更足！） |

### 3.3 `analyst45` · `Alphas > 0` 普通队列参考（剔除废弃字段后 5 个）
- `expected_exit_price_4`（`aCnt=1`，作者设定的目标退出价，与 `last_available_closing_price` `aCnt=1` 可构造目标隐含上涨空间）、`open_position_value_2`（`aCnt=1`）、`benchmark_index_return_pct`（`aCnt=1`）、`absolute_price_change_today_2`（`aCnt=1`）。

---

## 4. 补充核验的 CHN `other`（`1.9×`）辅助数据集与陷阱预警
- **`other715`（Snapshot Grouping Data，MATRIX，18 字段，5 个 `Alphas=0`，`cov=88%–100%`, `dCov=0.9507`）**：
  - 全部为中国本土行业分类整数代码（中信 CITICS 1–3 级、申万 SWN 1–3 级、万得 Wind 1–4 级、国证 CNI、中证 SECN），其中 `oth715_wind_2l`（`cov=100%`）、`oth715_swn_1l`（`99%`）、`oth715_cni_1l`（`94.4%`）、`oth715_secn_1l/2l`（`88.2%`）为 **`Alphas=0`**。
  - **用途与陷阱**：严禁当作连续数值！可配合 `densify(oth715_wind_2l)` 或作本土化行业中性化对照（注意验证 `type=MATRIX` 是否可直接传入 `group_*` 算子或须先 `bucket` 离散化）；且 `oth715_cni_inindcode`（`dCov=0.3521 < 5yr`）严禁使用！
- **`news_sentiment_enriched`（Chinese News Sentiment Enrichment，VECTOR，7 字段，`cov=88.7%`, `dCov=0.8275`）**：
  - **陷阱捕获**：6 个 `Alphas=0` 字段全为 **codebook 主题/时段分类编码**（`primary/secondary/tertiary_article_theme`、`actionable_time_window`、`article_release_time_span`、`is_theme_assignment_valid`），**不可做数值排序**；唯一真实中文情绪数值为 `news_emotional_tone`（`aCnt=3`，NORMAL 队列），可作 CHN 正常队列低拥挤补充。
- **`other592`（Chinese Equity Relation Data，VECTOR，7 字段）**：全部为内部实体 ID 矢量（`*_relatedii`），**严禁做 `vec_avg`**，最多仅 `vec_count` 统计关联方数量。

---

## 5. CHN 战区攻坚纪律（冲破 `Sharpe ≥ 2.08` + `Margin ≥ 20bp`）
1. **第一优先（低换手天然过 Margin 20bp）**：用 `other496` 纯 `Alphas=0` 财务结构比率（如 `oth496_ard_total_cur_assets_282 / oth496_ff_liabs_curr_nugget`、`oth496_ard_accounts_payable_trade_333 / oth496_q_ard_accts_receivable_trade`、`oth496_q_ard_tot_noncurrent_liabilities / oth496_q_ard_total_noncurrent_assets`）配低频同比变化 + 表达式级 `min(rank(A), rank(B))` 冲击 `other (1.9×)` 空白塔！
2. **第二优先（全覆盖低拥挤机构推荐）**：用 `analyst45` 的 `net_exposure_value` × `risk_adjusted_performance_alpha` × `average_idea_age_period`（全 `Alphas=0`）攻克 `analyst (1.8×)` 空白塔，配合 `ts_mean`/`ts_decay_linear` 控换手保 `Margin ≥ 20bp`！
3. **快速止损**：CHN 门槛极高，Stage-0 探针（24 条）若 `Sharpe < 0.8` 或 `Margin < 10bp` 无改善路径，果断标记 `FAST_DEMOTED`，绝不死磕浪费 12-06 前的 `DEU`/`ASI` 黄金窗口。
