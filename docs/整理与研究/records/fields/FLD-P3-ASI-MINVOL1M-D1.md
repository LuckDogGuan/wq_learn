# Field Card · P3 `ASI / MINVOL1M / D1` 唯一活跃 D1 Theme 战区（D1-Only）

> [!IMPORTANT]
> **范围硬锁**：严格锁定 **`ASI / MINVOL1M / Delay = 1 (D1)`**。所有元数据于 **`2026-11-25`** 经 `cnhkmcp` 只读实盘核验。
> **双重业务红利**：
> 1. **唯一活跃 D1 主题**：`ASI/D1 Power Pool Dec'26`（`7MZJV8A` + 今日官方手册 `7l6ZzrR`，窗口 **`2026-11-23 至 2026-12-20`**，**\$15,000 奖金池**，前 80 名有奖，需至少标 5 条 PPA）；且账号当前 **ASI 全部 16 个 D1 金字塔均为空白（`alphas = 0`）**！
> 2. **配额豁免铁律（`7GNvo8y` 2026-11-09）**：纯 Power Pool 受“日 1/月 10/域”限制，但 **`Power Pool + ATOM`（单数据集）与 `Power Pool + Regular` 完全免受配额限制**，且 `ts_backfill` 与 `group_backfill` 不计入 PP 8 算子上限！因此 ASI 战区**强制单数据集构造（ATOM）**，做到“一次产出同时吃透 Theme + 空白金字塔 + 免配额”。
> 3. **区域硬约束**：必须严守 **`Robust Universe ≥ 90%`**、**`maxTrade = ON`**、经验 **`Margin ≥ 15bp`**、`PPAC < 0.5`（若走 PPA）或 `Sharpe > 1.58`（若同时达 RA）；且 **Quick 模式会把 `1.0 ≤ Sharpe < 1.58` 的合格 PPA 标为 `FAIL`**，必须读具体数值并走 `Full` 终检！

---

## 1. 卡片头与 10 个官方推荐集全景

| 字段 | 核验值 |
| --- | --- |
| `card_id` | `FLD-P3-ASI-MINVOL1M-D1` |
| `region` | `ASI`（常驻 Gold） |
| `universe` | `MINVOL1M`（Sub-Universe 比值系数 `0.295`；可选 `TOP500` 仅作穷尽后对照） |
| `delay` | `1`（硬断言 `settings.delay == 1`） |
| `verified_date` | `2026-11-25` |
| `freeze_expiry` | `2026-12-06`（`Alphas=0` 免额度截止）；主题截止 `2026-12-20` |
| `pyramid_multipliers` | `model` (`1.3×`, `0 OS`) · `other` (`1.3×`, `0 OS`) · `news` (`1.3×`, `0 OS`) · `sentiment` (`1.4×`, `0 OS`) · `fundamental` (`1.1×`, `0 OS`) |
| `hard_region_guards` | `maxTrade = ON` · `Robust Universe ≥ 90%` · `Margin ≥ 15bp` · 单数据集 ATOM · 严查 `MINVOL1M` 流动性与 `hump` 锁死权重集中度陷阱（`SZ83096 #47`） |

### 1.1 `7MZJV8A` 核心 6 个核验数据集汇总（全部实测有权限）

| `dataset_id` | 塔类 & 倍率 | 覆盖率 | 总字段数 | 实测 `Alphas=0` 数 | 数据类型 | 定位 |
| --- | :---: | :---: | :---: | :---: | :---: | --- |
| **`ai_news_scores`** | `other` (`1.3×`) | `50.07%` | 105 | **34**（其中 **7 个纯 ASI+D1**，17 个 ASI 全系） | `MATRIX` | **首推 FREE + ATOM 矿脉**：零向量开销，正/负/中性情绪统计量齐全 |
| **`model307`** | `model` (`1.3×`) | **`78.22%`** | 15 | **5**（`cov=72.35%`, 剔除 4 个元数据 ID） | `VECTOR` | **意外挖出的 FREE 矿脉**：全球分区域营收占比（需验伪 VECTOR 与低频更新） |
| **`model207`** | `model` (`1.3×`) | `35.38%` | 5 | **2**（`cov=34.6%` / `14.3%`） | `VECTOR` | **补充 FREE 队列**：亚洲内部人交易，覆盖偏低须严查 `Robust ≥ 90%` |
| **`price_signal_dl`** | `model` (`1.3×`) | **`91.29%`** | 28 | `0`（全 Normal，低拥挤 `aCnt=1–12`） | `MATRIX` | **Normal 首推（最高覆盖）**：深度学习趋势/量能指标，极易保住 `Robust ≥ 90%`！ |
| **`behavioral_signals`** | `model` (`1.3×`) | **`87.54%`** | 7 | `0`（全 Normal，低拥挤 `aCnt=3–28`） | `VECTOR` *(疑似单值伪 VECTOR)* | **Normal 强备选**：行为金融 6 大异象指标（连涨/路径凸度/显著性加权收益），经济逻辑顶级 |
| **`mmp_nlp_sentiment`** | `other` (`1.3×`) | **`77.42%`** | 521 | `0`（首 50 全 Normal，`aCnt=1–21`） | `MATRIX` | **Normal 深度情绪库**：多语种新闻主题分（买入/回购/看空/降级/内部人主题），`cov=91%–100%` |

---

## 2. 队列一：`Alphas = 0` 免额度队列（`FREE`，冻结至 `2026-12-06`，共计 **41 个**已核实）

### 2.1 `ai_news_scores`（MATRIX，`other` `1.3×`，去重核验 `96/105` 字段 → **`34` 个 `Alphas=0`**）

> **⚠️ 重大数据语义陷阱（实盘抓获！）**：`ai_news_scores` 在 `ASI/MINVOL1M/D1` 下虽全部以 `delay=1` 提供，但字段描述中混合了 5 套 RavenPack 模型变体：
> - **`*_2`（variant `prv2`, ASI, D1）**：**最纯粹的亚洲 D1 新闻情绪系列（7 个 `Alphas=0`）**，应作为绝对首选！
> - **`*_4`（variant `prv22`, ASI, D0 offset）**：亚洲当日口径变体（平台在 D1 环境下做 D1 滞后供给，10 个 `Alphas=0`），作为第二梯队，注意实盘验是否存在跨日信息折损。
> - **无后缀 / `*_3` / `*_5`（USA `prv24`/`prv25`、EUR `prv23`）**：虽在 ASI 池中标注 `cov=50.07%`（`17` 个 `Alphas=0`），但原始新闻源偏欧美跨区映射，**优先度排后**，须在 Stage-0 核实有效非零持仓数与 `Robust ≥ 90%`。

| 梯队 | `field_id` | `type` | `coverage` | `date_coverage` (`≥5yr`) | `alpha_count` | 经济含义与方向假设 |
| :---: | --- | :---: | :---: | :---: | :---: | --- |
| **T1 · 纯 ASI D1** | `positive_score_median_value_2` | `MATRIX` | `50.07%` | `0.9003` (✅ ≥5yr) | `0` (FREE) | **首选正向**：ASI `prv2 D1` 单股日内正向新闻情绪中位数 `[0,1]`；抗单条极端新闻噪声 |
| **T1 · 纯 ASI D1** | `positive_score_confidence_lower_bound_2` | `MATRIX` | `50.07%` | `0.9003` (✅ ≥5yr) | `0` (FREE) | **首选稳健正向**：ASI `prv2 D1` 正向情绪均值的 95% 置信下界（只有高均值且低分歧/多条新闻一致看多才高！） |
| **T1 · 纯 ASI D1** | `positive_score_minimum_value_2` | `MATRIX` | `50.07%` | `0.9003` (✅ ≥5yr) | `0` (FREE) | ASI `prv2 D1` 日内最低正向情绪分（底线情绪保护） |
| **T1 · 纯 ASI D1** | `negative_score_minimum_value_2` | `MATRIX` | `50.07%` | `0.9003` (✅ ≥5yr) | `0` (FREE) | **首选负向配对**：ASI `prv2 D1` 日内最低负向情绪分（即使最轻的负面报道也偏高 = 严重利空，先验负向） |
| **T1 · 纯 ASI D1** | `neutral_score_median_value_2` | `MATRIX` | `50.07%` | `0.9003` (✅ ≥5yr) | `0` (FREE) | ASI `prv2 D1` 中性情绪中位数（反映“无情绪冲击/稳态关注”，切勿盲目当看多） |
| **T1 · 纯 ASI D1** | `neutral_score_minimum_value_2` | `MATRIX` | `50.07%` | `0.9003` (✅ ≥5yr) | `0` (FREE) | ASI `prv2 D1` 中性情绪最小值 |
| **T1 · 纯 ASI D1** | `neutral_score_standard_deviation_2` | `MATRIX` | `50.07%` | `0.9003` (✅ ≥5yr) | `0` (FREE) | ASI `prv2 D1` 中性情绪离散度（分歧度/事件不确定性度量） |
| **T2 · ASI prv22** | `positive_score_median_value_4` | `MATRIX` | `50.07%` | `0.9003` (✅ ≥5yr) | `0` (FREE) | ASI `prv22` 正向情绪中位数 |
| **T2 · ASI prv22** | `positive_score_maximum_value_4` | `MATRIX` | `50.07%` | `0.9003` (✅ ≥5yr) | `0` (FREE) | ASI `prv22` 正向情绪最大值（利好爆发度） |
| **T2 · ASI prv22** | `positive_score_confidence_upper_bound_4` | `MATRIX` | `50.07%` | `0.9003` (✅ ≥5yr) | `0` (FREE) | ASI `prv22` 正向情绪 95% 置信上界 |
| **T2 · ASI prv22** | `positive_score_standard_deviation_4` | `MATRIX` | `50.07%` | `0.9003` (✅ ≥5yr) | `0` (FREE) | ASI `prv22` 正向情绪标准差（多空报道分歧） |
| **T2 · ASI prv22** | `negative_score_median_value_4` | `MATRIX` | `50.07%` | `0.9003` (✅ ≥5yr) | `0` (FREE) | ASI `prv22` 负向情绪中位数（先验负向，与 `positive_score_median_value_4` 天然构成净情绪差 `subtract` 或 `min(rank(pos), rank(-neg))`！） |
| **T2 · ASI prv22** | `negative_score_minimum_value_4` | `MATRIX` | `50.07%` | `0.9003` (✅ ≥5yr) | `0` (FREE) | ASI `prv22` 负向情绪最小值（其余 4 个中性 `*_4` 亦为 `Alphas=0`） |

- **新闻类核心陷阱（`WL13229`）**：① 必先区分“缺新闻（`NaN`）vs 情绪为 0”，不可盲用 `ts_backfill(x, 252)` 把过期新闻陈旧化，推荐短中窗 `ts_backfill(x, 5..22)`；② 新闻因子在 ASI 极易高换手（40%–180%），注意单测短窗平滑并保住 `Margin ≥ 15bp`。

### 2.2 `model307`（Global Sales Allocation Model，VECTOR，`model` `1.3×`，**5 个 `Alphas=0`**）

| `field_id` | `type` | `is_fake_single_vector` | `coverage` | `date_coverage` (`≥5yr`) | `alpha_count` | 经济含义与陷阱 |
| --- | :---: | :---: | :---: | :---: | :---: | --- |
| `mdl307_sales_pct_emea` | `VECTOR` | `TBD_STAGE0`（疑似单值伪 VECTOR，先仅测 `vec_avg`！） | `72.35%` | `0.9507` (✅ ≥5yr) | `0` (FREE) | EMEA 地区营收占比 `[0,1]`；衡量亚洲企业出海欧洲/中东的全球化暴露与汇率/需求周期敏感度 |
| `mdl307_sales_pct_gb` | `VECTOR` | `TBD_STAGE0` | `72.35%` | `0.9507` (✅ ≥5yr) | `0` (FREE) | 英国地区营收占比 `[0,1]` |
| `australia_nz_sales_ratio` | `VECTOR` | `TBD_STAGE0` | `72.35%` | `0.9507` (✅ ≥5yr) | `0` (FREE) | 澳新地区营收占比 `[0,1]` |
| `canada_sales_fraction` | `VECTOR` | `TBD_STAGE0` | `72.35%` | `0.9507` (✅ ≥5yr) | `0` (FREE) | 加拿大营收占比 `[0,1]` |
| `mdl307_sales_pct_latam` | `VECTOR` | `TBD_STAGE0` | `72.35%` | `0.9507` (✅ ≥5yr) | `0` (FREE) | 拉美地区营收占比 `[0,1]` |
- **🚫 `model307` 强制剔除陷阱（4 个非数值元数据 VECTOR）**：`mdl307_cusip`（证券代码）、`mdl307_sector`（行业名）、`mdl307_atlas_unit_name`（名称）、`mdl307_country`（国家代码）——**严禁当作数值信号**！
- **经济陷阱**：区域营收占比为低频年度/半年度更新，大量亚太内需股在欧美/拉美占比为 `0`，截面容易出现大面积零值结（ties），建议配 `ts_delta(ts_backfill(vec_avg(x), 126), 252)` 测出海份额边际扩张，并在 Stage-0 核实非零持仓覆盖。

### 2.3 `model207`（Asian Insider Transaction Data，VECTOR，`model` `1.3×`，**2 个 `Alphas=0`**）

| `field_id` | `type` | `is_fake_single_vector` | `coverage` | `date_coverage` (`≥5yr`) | `alpha_count` | 经济含义与陷阱 |
| --- | :---: | :---: | :---: | :---: | :---: | --- |
| `post_transaction_share_balance` | `VECTOR` | `false`（日内多笔内部人交易） | `34.61%` | `0.9507` (✅ ≥5yr) | `0` (FREE) | 内部人交易后未复权持股数；**陷阱**：绝对股数受拆股/总股本影响大，须做 `ts_returns` 或 `ts_rank` + `ts_backfill(x, 66..126)`；因覆盖仅 34.6%，须警惕 ASI `Robust ≥ 90%` 与 Sub-Universe 挑战 |
| `security_transaction_unit_price_usd` | `VECTOR` | `false` | `14.26%` | `1.0000` (✅ ≥5yr) | `0` (FREE) | 内部人交易单价（USD）；覆盖过低（14.3%），单用极易厂字型，仅作与 `post_transaction_share_balance` 的辅助对照 |

---

## 3. 队列二：`Alphas > 0` 高覆盖 Normal 队列（攻克 ASI `Robust ≥ 90%` 的主力军）

> 原因：`ai_news_scores` 覆盖率 50%、`model207` 覆盖率 34.6%，在 ASI `Robust ≥ 90%` 硬门槛下容易出现样本缺口；而 **`price_signal_dl`（91.3%）**、**`behavioral_signals`（87.5%）** 与 **`mmp_nlp_sentiment`（91%–100%）** 具备超高覆盖率 + 极低拥挤度（`aCnt=1–12`），是冲击 **ASI/D1 Theme 前 80 名（≥5 条 PPA+ATOM）** 的最稳压舱石！

### 3.1 `price_signal_dl`（MATRIX，`model` `1.3×`，全 28 字段 `cov=90.6%–92.5%`）
| `field_id` | `type` | `coverage` | `date_coverage` (`≥5yr`) | `alpha_count` | 经济含义与已知陷阱 |
| --- | :---: | :---: | :---: | :---: | --- |
| `normalized_volume_indicator_2` | `MATRIX` | `91.90%` | `0.8694` (✅ ≥5yr) | **`1`** | 标准化量能深度特征 #3（极低拥挤！适合与趋势特征双支共振） |
| `normalized_volume_indicator_0` / `_1` / `_5` | `MATRIX` | `91.89%–92.28%` | `0.8694` (✅ ≥5yr) | **`2`** | 标准化量能深度特征 #1/#2/#6（低拥挤） |
| `normalized_volume_indicator_4` / `_3` | `MATRIX` | `92.28%` | `0.8694` (✅ ≥5yr) | `4` / `6` | 标准化量能深度特征 #5/#4 |
| `raw_trend_indicator_4` | `MATRIX` | `90.59%` | **`0.9507`** (✅ ≥5yr) | **`3`** | 未经重缩放的原始趋势指标 #4（时间覆盖长达 95%，抗早期缺失更好） |
| `normalized_trend_indicator_5` / `_3` / `_1` / `_2` | `MATRIX` | **`92.09%–92.46%`** | `0.8469` (✅ ≥5yr) | `6–8` | 标准化趋势深度特征 #6/#3/#2/#3；**提示**：趋势特征 + 量能特征同数据集内做 `min(rank(expr_trend), rank(expr_vol))`，天然保持 **ATOM + 低 PC**！ |
- **陷阱**：深度学习价量指标在 ASI 可能伴随较高日换手，须严控 `Turnover` 与 `Margin ≥ 15bp`，优先配 `ts_decay_linear`（先平滑后 `rank`）或小步平台 `decay`。

### 3.2 `behavioral_signals`（VECTOR，`model` `1.3×`，全 7 字段 `cov=87.54%`, `dCov=0.9507`）
> **⚠️ 伪 VECTOR 必检项（`JX14975 #100`）**：全部 7 个字段均为日度行为金融横截面因子，大概率是**单值伪 VECTOR（`is_fake_single_vector = LIKELY_TRUE`）**！Stage-0 **仅测 `vec_avg(x)`**（禁用 `vec_sum` 防 OS 漂移），省 80% 额度！

| `field_id` | `type` | `is_fake_single_vector` | `coverage` | `date_coverage` | `alpha_count` | 经济含义（经典行为金融论文因子） |
| --- | :---: | :---: | :---: | :---: | :---: | --- |
| `extreme_daily_return_indicator` | `VECTOR` | `LIKELY_TRUE`（只用 `vec_avg`） | `87.54%` | `0.9507` (✅) | **`5`** | 波动率标准化后的极端日收益度（博彩偏好/MAX 效应，通常负向反转） |
| `salience_weighted_return_score` | `VECTOR` | `LIKELY_TRUE` | `87.54%` | `0.9507` (✅) | **`7`** | 显著性理论（Salience Theory, Cosemans & Frehen）加权收益与等权收益之差；亚洲散户主导市场通常呈强负向反转！ |
| `price_path_curvature_measure` | `VECTOR` | `LIKELY_TRUE` | `87.54%` | `0.9507` (✅) | `10` | 价格路径凸度/凹度（捕捉投资者外推偏差引发的反转） |
| `visual_price_path_shape_score` | `VECTOR` | `LIKELY_TRUE` | `87.54%` | `0.9507` (✅) | `10` | 价格路径位于起终点连线上/下方的比例（视觉外推偏差） |
| `chronological_return_sequence_correlation` | `VECTOR` | `LIKELY_TRUE` | `87.54%` | `0.9507` (✅) | `12` | 日收益与时间顺序的相关性（近因偏差） |
| `consecutive_return_streak_length` | `VECTOR` | `LIKELY_TRUE` | `87.54%` | `0.9507` (✅) | `28` | 最近连续上涨/下跌天数（带正负号，动量/反转探针） |
| `total_equity_market_value_usd` | `VECTOR` | `LIKELY_TRUE` | `87.54%` | `0.9507` (✅) | `3` | 计算日美元总市值；**陷阱**：严禁裸作 Alpha（退化为小盘因子），仅作同集分组 `bucket(rank(vec_avg(x)))` 或 `vector_neut` 去市值暴露！ |

### 3.3 `mmp_nlp_sentiment`（MATRIX，`other` `1.3×`，`cov=91.05%–100%`, `dCov=1.0`, 2026-04 新建）
| `field_id` | `type` | `coverage` | `date_coverage` | `alpha_count` | 经济含义与已知陷阱 |
| --- | :---: | :---: | :---: | :---: | --- |
| `buy_recommendation_mention_sum` | `MATRIX` | **`100.00%`** | `1.0` (✅) | **`3`** | 新闻中“买入建议”提及总数；**注意**：计数类字段高覆盖可能含大量 0 值，须防大盘媒体曝光偏差（`WL13229` buzz 陷阱），宜做时序变化 `ts_zscore`/`ts_delta` 或行业内 `group_rank` |
| `buyback_mention_total` | `MATRIX` | **`100.00%`** | `1.0` (✅) | **`3`** | 回购主题提及总数（强公司治理/低估信号） |
| `bearish_topic_sum_bbgnews` | `MATRIX` | **`100.00%`** | `1.0` (✅) | `6` | 看空主题提及总数（先验负向；可与 `buy_recommendation_mention_sum` 构造 `subtract` 或 `min(rank(buy), rank(-bearish))`） |
| `avg_hold_topic_score` / `avg_insider_trading_topic_score` | `MATRIX` | `91.05%` | `1.0` (✅) | **`1`** | 持有评级 / 内部人交易主题平均分（极低拥挤，比率分无媒体总量偏差！） |
| `average_overweight_mention_score` | `MATRIX` | `91.05%` | `1.0` (✅) | **`2`** | 增持（Overweight）主题平均分（正向优选） |
| `avg_downgrade_topic_score` | `MATRIX` | `91.05%` | `1.0` (✅) | **`2`** | 下调评级（Downgrade）主题平均分（负向优选，与 `average_overweight_mention_score` 组成同集 ATOM 双支共振！） |
| `buy_topic_min_bbgnews` | `MATRIX` | `91.05%` | `1.0` (✅) | **`2`** | 买入建议主题最小值 |
| `buyback_mention_mad_bbgnews` | `MATRIX` | `91.05%` | `1.0` (✅) | **`2`** | 回购提及的中位数绝对偏差（突发事件冲击度量） |

---

## 4. ASI 战区执行与避坑总纲
1. **12-06 前免费探针**：先跑 `ai_news_scores` 纯 ASI D1（7 个 `*_2` `Alphas=0` MATRIX）+ `model307`（5 个 `Alphas=0` 出海营收占比 VECTOR），全程免计普通日额。
2. **12-20 冲榜主力（`PPA+ATOM` 免配额）**：主攻 `price_signal_dl`（92% 覆盖）+ `behavioral_signals`（87.5% 覆盖，只用 `vec_avg`）+ `mmp_nlp_sentiment`（91%–100% 覆盖），全部保持单数据集 ATOM + `maxTrade=ON` + `Margin ≥ 15bp` + `Robust ≥ 90%`！
3. **防踩坑**：在 `MINVOL1M` 谨慎使用 `hump`（`SZ83096 #47` 实测易锁死权重集中度），降换手优先试短窗 `ts_decay_linear`（平滑置于 `rank` 之前）或小步平台 `decay=1/3/5`。
