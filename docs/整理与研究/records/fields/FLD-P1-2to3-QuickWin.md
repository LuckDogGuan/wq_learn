# Field Card · P1 2→3 准达标金字塔速赢区（D1-Only）

> [!IMPORTANT]
> **范围硬锁**：本字段卡严格锁定 **`Delay = 1 (D1)`**（不做 D0）。所有字段元数据于 **`2026-11-25`** 经 `cnhkmcp`（只读 `get_datasets` / `get_datafields` / `get_pyramid_multipliers` / `get_pyramid_alphas`）实盘核验。
> **核心战术目标**：账号当前有 **3 个 D1 金字塔均已持有 2 条 OS Alpha，各自仅差 1 条即可点亮 ≥3 达标金字塔**（立刻拉升 Genius 达标塔数并贡献 **92→100 SuperAlpha** 进度）：
> 1. `GLB / D1 / fundamental`（当前 **2 条**，倍率 **`1.4×`**，注意 GLB 占 **2 并发槽**）
> 2. `GLB / D1 / analyst`（当前 **2 条**，倍率 **`1.4×`**，注意 GLB 占 **2 并发槽**）
> 3. `GBR / D1 / other`（当前 **2 条**，倍率 **`1.6×`**，常规 1 并发槽）
> **免额度冻结红线（`yjwedz7`）**：`freeze_expiry = 2026-12-06`。表达式中**全部**经济字段必须均为 `Alphas = 0`（仅可搭用 9 个 PV1 辅助字段：`currency, country, exchange, sector, industry, subindustry, market, split, adjfactor`）方可免计普通日额度（5,000/日）；混入任意 1 个 `Alphas > 0` 字段即归入 **NORMAL 普通队列**。

---

## 1. 卡片头与区域坐标总览

| 字段 | 核验值 |
| --- | --- |
| `card_id` | `FLD-P1-2to3-QuickWin` |
| `verified_date` | `2026-11-25` |
| `freeze_expiry` | `2026-12-06`（`yjwedz7` `Alphas=0` 免额度冻结期） |
| `delay` | `1`（硬断言 `settings.delay == 1`） |
| `target_pyramids` | ① `GLB / TOP3000 (或 TOPDIV3000) / D1 / fundamental`（`1.4×`，现有 `2/3`）<br>② `GLB / TOP3000 (或 TOPDIV3000) / D1 / analyst`（`1.4×`，现有 `2/3`）<br>③ `GBR / TOP700 / D1 / other`（`1.6×`，现有 `2/3`） |
| `d1_thresholds` | 常规非 CHN D1：`Sharpe > 1.58`, `Fitness > 1.0`, `1% < TVR < 70%`, `Weight < 10%`, 经验 Margin 底线 `GLB ≥ 9bp` / `GBR ≥ 10bp`（单数据集 ATOM 跳过 IS Ladder，核 `LOW_2Y_SHARPE` 实盘 `1.58`） |
| `y56zvK7_custom_recs` | `fundamental23`（GLB）、`analyst10`（GLB）、`other696`（GBR）已全部实盘核验（注：`other696` 在 `GLB/TOP3000/D1` 返回 0 字段，仅存于 `GBR/TOP700/D1` 等区域） |

### 1.1 `GLB/TOP3000/D1` vs `GLB/TOPDIV3000/D1` 选池核验结论
- 两者共享相同的 138 个数据集与基础覆盖率，但 **`GLB/TOP3000/D1` 拥挤度显著低于 `GLB/TOPDIV3000/D1`**（例如 `analyst10`：`791` vs `2,225` alphas；`fundamental23`：`2,951` vs `3,525` alphas；`fundamental44`：`523` vs `1,416` alphas）。
- **结论**：P1 速赢优先主攻 **`GLB / TOP3000 / D1`**（低 PC 风险、更高单字段低拥挤度）；仅当 `TOP3000` 出现 Sub-Universe 瓶颈或穷尽单轴优化后，再按 `SZ83096 #47` 纪律切至 `TOPDIV3000` 对照。

---

## 2. 战区 A：`GLB / TOP3000 / D1` · `fundamental`（`1.4×`，当前 `2/3`）

### 2.1 数据集核验摘要
| `dataset_id` | 名称 | 数据集覆盖率 | 字段总数 | 数据集 `alphaCount` | 定位与推荐理由 |
| --- | --- | :---: | :---: | :---: | --- |
| **`fundamental23`** | Fundamental Point in Time Data（`y56zvK7` 定制推荐） | `67.97%` | 1,748 | 2,951 | **主攻 Normal 队列（ATOM）**：2025-11-01 刚上线一批 `cov=92%–96%`, `dCov=1.0`, `aCnt=1–4` 的超低拥挤 PIT 财务比率/资产负债字段，且含稀疏 `Alphas=0` 字段 |
| **`fundamental44`** | Accounting Quality Models | **`81.91%`** | 12 | 523 | **高覆盖低复杂度备选**：全 12 个 MATRIX 财务舞弊/应计质量模型分（`cov=84.76%`, `dCov=0.9507`），单字段极易出清晰经济逻辑 |
| **`fundamental72`** | Comprehensive Fundamental Data | `57.20%` | 896 | 683 | **次选**：含 2026-03-01 新增 `aCnt=1` MATRIX 资产/股息字段（注意剔除 `*_fiscal_year_period` 辅助矢量字段） |
| **`fundamental22`** | Environmental and Social Governance Data | `61.34%` | 6 | 63 | **低拥挤 ESG 备选**：6 个 VECTOR 字段（`aCnt=1–44`），需先验是否单值伪 VECTOR |

### 2.2 队列一：`Alphas = 0` 免额度队列（`FREE`，冻结至 `2026-12-06`）
> 实测说明：`GLB/TOP3000/D1` 的 `fundamental` 头部成熟数据集几乎均有用户触达，本次抽检 145 个 `fundamental23` 字段仅命中 1 个 `Alphas=0` 且属特定行业（医疗床位利用率），**不建议在 GLB/fundamental 强凑免额度队列**，应以 `fundamental23` / `fundamental44` 低拥挤 Normal 队列速拿 1 条为主。

| `field_id` | `dataset_id` | `type` | `is_fake_single_vector` | `coverage` | `date_coverage` (`≥5yr`) | `alpha_count` | 经济含义与已知陷阱 |
| --- | --- | :---: | :---: | :---: | :---: | :---: | --- |
| `fnd23_intfvalld1_pghm` | `fundamental23` | `MATRIX` | `false` | `44.95%` | `None` (⚠️ 须 Stage-0 核实 `≥5yr`) | `0` (FREE) | 许可床位利用率（%）；**陷阱**：仅医疗/养老子行业有效，全市场覆盖低、易厂字型，仅作免额度探索记录 |

### 2.3 队列二：`Alphas > 0` 普通高优队列（`NORMAL`，优先速赢 1 条点亮 `2→3`）

| `field_id` | `dataset_id` | `type` | `is_fake_single_vector` | `coverage` | `date_coverage` (`≥5yr`) | `alpha_count` | 经济含义与已知陷阱 |
| --- | --- | :---: | :---: | :---: | :---: | :---: | --- |
| `fnd23_intfvm_sedv` | `fundamental23` | `MATRIX` | `false` | **`96.09%`** | `1.0000` (✅ ≥5yr) | `1` | 稀释标准化 EPS（2025-11 新建，超低拥挤）；与 `fnd23_intfvm_swds` 配套；注意财务披露低频，配 `ts_backfill(x, 66..126)` |
| `fnd23_icsm_m_sedv` | `fundamental23` | `MATRIX` | `false` | **`92.23%`** | `1.0000` (✅ ≥5yr) | `1` | 季度稀释标准化 EPS（PIT 季频）；适合做同比/环比改善 `ts_delta` 或与规模比率构造 |
| `fnd23_icsm_m_caiv` | `fundamental23` | `MATRIX` | `false` | **`92.13%`** | `1.0000` (✅ ≥5yr) | `1` | 季度归属普通股标准化净利润；金额字段严禁裸排，须先用同集资产 `assets_total_2` 做 `profit_to_size` 规模化 |
| `fnd23_intfvalld1_mpns` | `fundamental23` | `MATRIX` | `false` | **`100.00%`** | `None` (⚠️ 2022 老字段，Stage-0 核实有效年) | `2` | 净利率（扣非净利润 / 总营收）；现成无量纲比率，可直接进 `rank` / `group_rank` / `ts_delta` |
| `fnd23_intfvalld1_mtps` | `fundamental23` | `MATRIX` | `false` | **`100.00%`** | `None` (⚠️ 同上) | `3` | 税前利润率（Pretax Margin）；与 `mpns` 可验证盈利质量与税负变化 |
| `fnd23_intfvalld1_rucs` | `fundamental23` | `MATRIX` | `false` | **`92.05%`** | `None` (⚠️ 同上) | `1` | 流动比率（流动资产 / 流动负债）；短期偿债能力比率，金融股可能缺失或失真 |
| `fnd23_intfvalld1_kcqs` | `fundamental23` | `MATRIX` | `false` | **`92.05%`** | `None` (⚠️ 同上) | `3` | 速动比率；与 `rucs` 共同检验存货压力与流动性风险 |
| `annual_net_income_value` | `fundamental23` | `MATRIX` | `false` | **`92.82%`** | `1.0000` (✅ ≥5yr) | `1` | 年度净利润（2025-11 新建）；必须除以 `assets_total_2`（`cov=96.03%`, `aCnt=16`）消除市值规模偏差 |
| `annual_statement_of_cash_flows` | `fundamental23` | `MATRIX` | `false` | **`92.79%`** | `1.0000` (✅ ≥5yr) | `2` | 年度现金流；适合同集构造现金流质量比率（现金流 / 总资产） |
| `bank_borrowings_total` | `fundamental23` | `MATRIX` | `false` | **`96.07%`** | `1.0000` (✅ ≥5yr) | `4` | 银行借款总额；配 `assets_total_2` 构造银行负债率（低杠杆溢价） |
| `fnd44_fscore` | `fundamental44` | `MATRIX` | `false` | **`84.76%`** | `0.9507` (✅ ≥5yr) | `29` | 会计错报风险综合模型分（越高风险越大，先验负向 `reverse(rank(x))`） |
| `fnd44_yoon_wc_accruals` | `fundamental44` | `MATRIX` | `false` | **`84.76%`** | `0.9507` (✅ ≥5yr) | `24` | Yoon 模型营运资本应计项（经典应计异象：高应计低未来收益，先验负向） |
| `fnd44_probability_restatement` | `fundamental44` | `MATRIX` | `false` | **`84.76%`** | `0.9507` (✅ ≥5yr) | `35` | ML 预测财务重述概率（高重述风险往往对应负超额收益） |
| `fnd72_a_bs_net_fix_asset` | `fundamental72` | `MATRIX` | `false` | `84.50%` | `1.0000` (✅ ≥5yr) | `1` | 固定资产净值（2026-03 新建）；配合 `dividends_paid_cashflow_2`（`cov=83.95%`, `aCnt=1`）构建资本开支与分红纪律 |

**已知陷阱与避坑清单（GLB/fundamental）**：
- `fnd72_*_fiscal_year_period` 属于财年编号元数据矢量，**严禁当作经济信号**。
- `fundamental23` 原始金额字段（如 `annual_net_income_value`、`bank_borrowings_total`）严禁直接裸排，必须用同集 `assets_total_2` 或 `fnd23_intfvm_eltq` 标准化，避免变成市值因子。
- GLB 占 **2 并发槽**，Stage-0 探针务必精简在 8–16 条内快速验出信号方向。

---

## 3. 战区 B：`GLB / TOP3000 / D1` · `analyst`（`1.4×`，当前 `2/3`）

### 3.1 数据集核验摘要
| `dataset_id` | 名称 | 数据集覆盖率 | 字段总数 | 数据集 `alphaCount` | 定位与推荐理由 |
| --- | --- | :---: | :---: | :---: | --- |
| **`analyst10`** | Performance-Weighted Analyst Estimates（`y56zvK7` 定制推荐） | **`95.03%`** | 174 | 791 | **主攻 Normal 队列（ATOM）**：近乎全覆盖（`100%` 字段覆盖、`dCov=1.0`），核心为基于 SmartEstimate 的预测盈余/现金流/毛利率意外（`pred_surps_v1/v2`），`aCnt=1–2` 极低拥挤！ |
| **`analyst_consensus`** | Standardized Analyst Consensus Forecasts | `72.22%` | 1,607 | 376 | **免额度 + 低拥挤双修**：2026-03-01 新建，实测含 **5 个 `Alphas=0` VECTOR**（`cov=57%–58.5%`, `dCov=1.0`）及大量 `aCnt=1` EPS/DPS/BVPS 字段 |
| **`analyst_factor_signals`** | Global Analyst Factor Signals | `60.46%` | 328 | 236 | **现成修正/偏度 MATRIX 备选**：EBITDA 一致预期 3M 变动、修正幅度与分布偏度（`cov=79%–82%`, `dCov=1.0`, `aCnt=1–6`） |

### 3.2 队列一：`Alphas = 0` 免额度队列（`FREE`，冻结至 `2026-12-06`）

| `field_id` | `dataset_id` | `type` | `is_fake_single_vector` | `coverage` | `date_coverage` (`≥5yr`) | `alpha_count` | 经济含义与已知陷阱 |
| --- | --- | :---: | :---: | :---: | :---: | :---: | --- |
| `actual_eps_reported_value_fxadj_quarterly16` | `analyst_consensus` | `VECTOR` | `TBD_STAGE0`（大概率多期事件矢量，先测 `vec_avg` 与 `vec_max` 对比） | `58.53%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 汇率/拆股调整后季度实际报告 EPS；需注意向量内多期数值口径，适合做 `ts_delta(ts_backfill(vec_avg(x), 66), 66)` |
| `actual_eps_reported_value_quarterly16` | `analyst_consensus` | `VECTOR` | `TBD_STAGE0` | `58.53%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 未调整季度实际 EPS（GLB 多币种市场存在汇兑量纲偏差，优先用 `fxadj` 版本或时序增长率） |
| `actual_ebit_value_fxadj_quarterly16_tribes` | `analyst_consensus` | `VECTOR` | `TBD_STAGE0` | `57.11%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 汇率调整后季度实际 EBIT；绝对金额型，须做时序变化率或 `ts_zscore` 消量纲 |
| `actual_fcf_value_fxadj_quarterly16` | `analyst_consensus` | `VECTOR` | `TBD_STAGE0` | `24.62%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 汇率调整季度 FCF；覆盖偏低（24.6%），易在 Sub-Universe 失守，仅作免额度辅助探测 |
| `actual_fcf_value_fxadj_quarterly16_tribes` | `analyst_consensus` | `VECTOR` | `TBD_STAGE0` | `24.62%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 按事件线对齐的季度实际 FCF；覆盖偏低（24.6%），同上 |

### 3.3 队列二：`Alphas > 0` 普通高优队列（`NORMAL`，`y56zvK7` `analyst10` 核心速赢）

| `field_id` | `dataset_id` | `type` | `is_fake_single_vector` | `coverage` | `date_coverage` (`≥5yr`) | `alpha_count` | 经济含义与已知陷阱 |
| --- | --- | :---: | :---: | :---: | :---: | :---: | --- |
| `anl10_entfy1_pred_surps_v1_6484` | `analyst10` | `MATRIX` | `false` | **`100.00%`** | `1.0000` (✅ ≥5yr) | **`1`** | **首选**：FY1 税后盈利预测意外 v1 = `(SmartEst - Consensus) / Consensus`；天然无量纲、全覆盖、极低拥挤！注意警惕财年滚动（period roll）假跳变 |
| `anl10_entfy2_pred_surps_v1_6476` | `analyst10` | `MATRIX` | `false` | **`100.00%`** | `1.0000` (✅ ≥5yr) | **`1`** | FY2 税后盈利预测意外 v1；与 FY1 版本构成天然 `min(rank(expr_FY1), rank(expr_FY2))` 远近双强共振！ |
| `anl10_fcffy1_pred_surps_v1_6437` | `analyst10` | `MATRIX` | `false` | **`100.00%`** | `1.0000` (✅ ≥5yr) | **`1`** | **首选**：FY1 自由现金流预测意外 v1；现金流口径天然异于传统 EPS 共识，易出低 PC |
| `anl10_fcffy2_pred_surps_v1_6420` | `analyst10` | `MATRIX` | `false` | **`100.00%`** | `1.0000` (✅ ≥5yr) | **`1`** | FY2 自由现金流预测意外 v1（另有 `v2_6411` `aCnt=1`）；与 FY1 配对极佳 |
| `anl10_grmfq2_pred_surps_v1_6235` | `analyst10` | `MATRIX` | `false` | **`100.00%`** | `1.0000` (✅ ≥5yr) | **`1`** | Q2 毛利率预测意外 v1（另有 `v2_6266` `aCnt=1`）；捕捉盈利能力拐点 |
| `anl10_cpsfy2_pred_surps_v1_6286` | `analyst10` | `MATRIX` | `false` | **`100.00%`** | `1.0000` (✅ ≥5yr) | **`2`** | FY2 每股现金流（CPS）预测意外 v1；与 `anl10_cpssmun_2yf_6284`（覆盖分析师数）形成覆盖度×意外度双支组合 |
| `ebitda_y2_estimate_change_3m` | `analyst_factor_signals` | `MATRIX` | `false` | `81.36%` | `1.0000` (✅ ≥5yr) | `1` | FY2 EBITDA 一致预期 3 个月变动（2026-03 新建）；与 `ebitda_y1_estimate_change_3m`（`aCnt=5`）共振 |
| `ebitda_y1_estimate_asymmetry` | `analyst_factor_signals` | `MATRIX` | `false` | `68.23%` | `1.0000` (✅ ≥5yr) | `1` | FY1 EBITDA 预期分布不对称度；衡量分析师上调/下调尾部偏斜 |
| `ebitda_y2_estimate_coeff_var` | `analyst_factor_signals` | `MATRIX` | `false` | `68.31%` | `1.0000` (✅ ≥5yr) | `1` | FY2 EBITDA 预期变异系数（离散度/分歧度，通常低分歧或反向） |

**已知陷阱与避坑清单（GLB/analyst）**：
- **`analyst10` 纯元数据/ID 陷阱（严禁进入信号表达式）**：`*_det_analyst_*`（分析师 ID）、`*_det_anntime_*`（公告时间戳）、`*_det_estflag_*` / `*_det_excflag_*`（标志位）、`*_det_indicator_*`（ASCII 财期编码 `54/55/49/50`）。
- 财年滚动陷阱（`WL13229` `43567319117079`）：FY1/FY2 字段在财报季滚动切换时会制造虚假 `ts_delta` 跳变，做时序差分时优先用中短窗（`5–22`）或直接对现成 `pred_surps` 比率做横截面 `rank`/`group_rank`。

---

## 4. 战区 C：`GBR / TOP700 / D1` · `other`（`1.6×`，当前 `2/3`）

### 4.1 数据集核验摘要
| `dataset_id` | 名称 | 数据集覆盖率 | 字段总数 | 实测 `Alphas=0` 数 | 定位与推荐理由 |
| --- | --- | :---: | :---: | :---: | --- |
| **`dl_riskfree_returns`** | Deep Learning Risk Free Returns | **`76.45%`** | 133 | **11**（首 50 抽检，全 `cov>0` MATRIX） | **首推 FREE 队列（MATRIX）**：2026-07-01 新建，含 `cov=100%` 及 `cov=58.79%` 的前向 5/10/20/50/60 日分位数预测概率，**纯 MATRIX 无需 VECTOR 聚合**，直通免额度速赢！ |
| **`other250`** | details data（电商商品评分/畅销排名/价格） | **`52.06%`** | 12 | **8**（全 12 字段中 8 个 `Alphas=0`，`cov=52.06%`） | **高性价比 FREE 队列（VECTOR）**：2026-07-01 新建，仅 12 字段、全量 `dCov=1.0`，商品评分/评论数/畅销排名语义清晰 |
| **`other455`** | Relationship enhanced with AI/ML | **`93.81%`** | 1,500 | **25**（首 50 抽检，全 `cov=100%` GROUP） | **图聚类 GROUP 辅助神器**：Node2Vec 竞争关系聚类标签（`k=5/10/20`），可作 `group_rank(alpha, oth455_...)` 降 PC 或搭配同集 `*_pca_fact*_value`（MATRIX, `cov=71.9%`） |
| **`other696`** | （`y56zvK7` 定制推荐）文档级深度语义情绪 | `0.00%` *(元数据未算)* | 220 | **41**（首 50 抽检，`dCov=1.0`, `cov=0.0` 待探针） | **`y56zvK7` 免额度潜力库**：2026-07-01 新建，含正负现金流/订单积压/通胀/资产负债表情绪计数；**注意元数据 `coverage=0.0` 属于新集未回填统计**（`oth696_combined_sentiment_score` 已有 18 条 OS），须用 Stage-0 探针实测真实持仓覆盖率！ |
| **`other47`** | Web Intelligence Data（SEMrush 搜索流量） | `51.71%` | 18 | **1**（`oth47_organic_cost`, `cov=60.68%`） | **补充队列**：Google 自然/付费搜索流量与广告预算，经济直觉强 |

### 4.2 队列一：`Alphas = 0` 免额度队列（`FREE`，冻结至 `2026-12-06`，共计 **86 个**已核实）

#### (a) `dl_riskfree_returns`（MATRIX，实测 11 个 `Alphas=0`，首选免额度速赢）
| `field_id` | `type` | `is_fake_single_vector` | `coverage` | `date_coverage` (`≥5yr`) | `alpha_count` | 经济含义与已知陷阱 |
| --- | :---: | :---: | :---: | :---: | :---: | --- |
| `probability_label1_3quantile_60day_ohlcv` | `MATRIX` | `false` | **`100.00%`** | `0.9997` (✅ ≥5yr) | `0` (FREE) | 60 日前向市场中性收益落入 3 分位桶 index 1（中间桶）的 log-softmax 概率；**陷阱**：是 log 概率且为中间桶，需验方向并防与顶部/底部桶混淆 |
| `probability_label0_3quantile_5day_eur_ohlc_ma` | `MATRIX` | `false` | `58.79%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 5 日前向收益落入 3 分位最底桶（label0，看空概率）的概率（EUR OHLC MA 模型）；**方向提示**：label0 越高越偏空，先验负向 `reverse(rank(x))` |
| `probability_label0_3quantile_20day_eur_ohlc_ma` | `MATRIX` | `false` | `58.79%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 20 日前向收益落入 3 分位最底桶（label0）的 log 概率；中周期反转/动量信号，天然适合与 5 日/50 日做 `reverse(min(rank(A), rank(B)))` |
| `probability_label0_4quantile_20day_eur_ohlcma` | `MATRIX` | `false` | `58.79%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 20 日 4 分位最底桶概率（欧洲价格图表特征） |
| `probability_label0_4quantile_50day_eur_ohlc_ma` | `MATRIX` | `false` | `58.79%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 50 日 4 分位最底桶概率（低换手潜力高） |
| `probability_label0_5quantile_20day_eur_ohlcma` | `MATRIX` | `false` | `58.79%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 20 日 5 分位最底桶概率（尾部识别更锐利） |
| `probability_label1_3quantile_10day_eur_ohlc_ma` | `MATRIX` | `false` | `58.79%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 10 日 3 分位桶 1 log 概率 |
| `probability_label1_4quantile_5day_eur_ohlc_ma` | `MATRIX` | `false` | `58.79%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 5 日 4 分位桶 1 概率（另有 `10day`/`20day` 与 `5quantile_10day` 共 4 个同族 `Alphas=0`） |

#### (b) `other250`（VECTOR，实测 8 个 `Alphas=0`，`cov=52.06%`, `dCov=1.0`）
| `field_id` | `type` | `is_fake_single_vector` | `coverage` | `date_coverage` (`≥5yr`) | `alpha_count` | 经济含义与已知陷阱 |
| --- | :---: | :---: | :---: | :---: | :---: | --- |
| `oth250_rank` | `VECTOR` | `false`（单公司多 SKU） | `52.06%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 品类畅销排名（1 为最佳，越小越畅销，先验负向）；适合 `vec_min`（爆款单品）或 `vec_avg`（整体热销度） |
| `oth250_item_rating` | `VECTOR` | `false` | `52.06%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 商品平均星级评分（0–5）；适合与 `total_review_number` 组成口碑×销量 `min(rank(A), rank(B))` |
| `total_review_number` | `VECTOR` | `false` | `52.06%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 商品累计评论总数；做 `ts_delta` 捕捉需求加速，避免直接裸用受公司 SKU 规模偏差影响 |
| `oth250_item_display_price` | `VECTOR` | `false` | `52.06%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 站点本地货币标价；**陷阱**：绝对价格跨行业不可比，须做 `ts_returns` / `ts_rank` 看定价权变化 |
| `product_listed_price` | `VECTOR` | `false` | `52.06%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 美元标价；同上，用时序涨跌率或 `product_price_upper_bound / product_price_lower_bound`（均 `Alphas=0`）衡量溢价带宽度 |
| `oth250_price_range_min` / `product_price_lower_bound` / `product_price_upper_bound` | `VECTOR` | `false` | `52.06%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 商品价格区间上下限（USD/本币）；适合测 SKU 价格带扩张与结构升级 |

#### (c) `other696`（`y56zvK7` 定制推荐，VECTOR，首 50 抽检 **41 个 `Alphas=0`**，`dCov=1.0`，`cov=0.0` 须 Stage-0 实测）
- **高经济逻辑优选配对（全部 `Alphas=0`）**：
  - 资产负债表正/负情绪：`oth696_balancesheet_positive` vs `oth696_balancesheet_negative`
  - 订单积压正/负情绪：`oth696_backlog_positive` vs `oth696_backlog_negative`
  - 并购正/负情绪：`oth696_acquisitions_positive` vs `oth696_acquisitions_negative`
  - 产能与管理层正向：`capacity_positive_event_count`、`leadership_positive_event_count`
  - 通胀与指标恶化负向：`inflation_negative_event_count`、`negative_metrics_change_event_count`
- **陷阱**：文档事件型 VECTOR 极可能高度稀疏，须先跑 `ts_backfill(vec_avg(x), 66..126)` 并在 Stage-0 严检厂字型（`<8` 有效年即 `FAST_DEMOTED`）；切勿把非方向中性字段 `future_tense_neutral_statement_count` 当作看多信号。

#### (d) `other455`（GROUP，首 50 抽检 **25 个 `Alphas=0`**，`cov=100%`, `dCov=1.0`）& `other47`（1 个 `Alphas=0`）
- `other455` 代表免额度聚类：`oth455_competitor_n2v_p10_q200_w1_pca_fact1_cluster_5`、`w2_kmeans_cluster_20`、`w3_pca_fact1_cluster_10` 等（**仅作分组维度**，搭配同集或同免费字段使用；注意若与 `Alphas>0` 信号搭配则整条归入 NORMAL 队列）。
- `other47` 唯一免额度：`oth47_organic_cost`（VECTOR, `cov=60.68%`, `dCov=1.0`, `aCnt=0`）——等价自然搜索流量的 Google Ads 估算成本（USD），反映品牌自然流量护城河。

### 4.3 队列二：`Alphas > 0` 普通队列精粹（GBR/TOP700/D1 · `other`）
- `dl_riskfree_returns`：`probability_label0_4quantile_20day_ohlcv`（`cov=100%`, `aCnt=1`）、`probability_label1_4quantile_60day_ohlcv`（`cov=100%`, `aCnt=2`）
- `other545`（Linked Firms Momentum，VECTOR，`cov=48.78%`, `dCov=1.0`）：`oth545_mpd`（`aCnt=2`）、`oth545_score`（`aCnt=11`）、`oth545_pln_omen`（`aCnt=14`）
- `other47`：`paid_search_budget_estimate`（`cov=60.68%`, `aCnt=1`）、`oth47_organic_traffic`（`aCnt=3`）、`oth47_rank`（`aCnt=3`）
- `other696`：`oth696_combined_sentiment_score`（`aCnt=18`）、`oth696_cashflow_positive` / `oth696_cashflow_negative`（各 `aCnt=1`）

---

## 5. P1 速赢优先执行顺序（严守 Decision #3：禁 `+` / `*` / `trade_when`）
1. **最速破冰（1 槽 + FREE 免额度）**：`GBR/TOP700/D1` 跑 `dl_riskfree_returns` 11 个 `Alphas=0` MATRIX + `other250` 8 个 `Alphas=0` VECTOR（Stage-0 探针 24 条），极速补齐 `GBR/D1/other` `2→3`！
2. **次速冲塔（GLB 2 槽，低拥挤 Normal）**：`GLB/TOP3000/D1` 跑 `analyst10` 6 个 `aCnt=1–2` 全覆盖 `pred_surps_v1` MATRIX，搭配 `min(rank(FY1), rank(FY2))` 快速补齐 `GLB/D1/analyst` `2→3`！
3. **三塔全亮（GLB 2 槽，低拥挤 Normal）**：`GLB/TOP3000/D1` 跑 `fundamental23` 比率与新 PIT 字段 + `fundamental44` 会计质量模型，补齐 `GLB/D1/fundamental` `2→3`！
