# WorldQuant BRAIN 平台规则激励机制、Python Alpha 实战与 SuperAlpha 调研报告（2026-11-26）

> [!IMPORTANT]
> **零干扰声明**：本报告及配套数据快照 [wq_rules_d0_unused_python_sa_snapshot_20261126.json](wq_rules_d0_unused_python_sa_snapshot_20261126.json) 均通过只读 API（`cnhkmcp`）与本地黄金顾问语料库（遵循 8:2 优先级：王哥 + Top10 黄金顾问 + 官方文档优先）采集保存，**未对当前正在运行的 D1-Only 流水线、配置或代码做任何修改**。

---

## 一、核心结论速览

| 核心问题 | 实证结论 | 关键证据与数据 |
| --- | --- | --- |
| **1. 平台是否在鼓励 D0、未用字段与 Python 因子，以拓宽因子覆盖面？** | **是的，高度确凿。** 平台正通过「金字塔倍率倾斜 + 主题 2×/3× 加成 + 未用字段免额度 + 竞赛激励」四重杠杆，将顾问算力从拥挤的传统 FastExpr D1 热门池引导至低拥挤蓝海。 | 全平台 216 个金字塔中：**D0 均值 1.633×（75.8% ≥1.5×，43.9% ≥1.8×）** vs **D1 均值 1.332×（32.0% ≥1.5×，6.7% ≥1.8×）**；Top 20 倍率中 **19 个为 D0**；`Alphas=0` 免 5,000 日额度至 **2026-12-06**；近期多期主题给 **Python Alpha 3×（Regular 2×）**。 |
| **2. 主题倍率是“相乘积”吗？** | **注意纠偏：Theme 与 Pyramid 之间不是相乘，而是“去重相加”；只有最后乘 Osmosis 时才是相乘！** | 官方公告 `R9E6wkR`（2026-11-17）：`合并倍数 = Σ适用倍数 − 倍数个数 + 1`，再乘 `Osmosis (1~2×)`。例如 Pyramid `2×` + Theme `2×` = **`3×`**（非 `4×`）；且仅放大每日 Base Payment 的 Quality Factor，不直接乘季度奖。 |
| **3. SuperAlpha 是否占用每天 5,000 次回测额度？** | **占用！共享每日 5,000 次回测上限。** 但每日**提交配额独立**（SA 单独 1 条/天，不占 4 条 RA/天）。 | 官方文档 `understanding-simulation-limits` 明确：**All successful simulations are counted**（含 `POST /simulations` 下所有类型）；Rank 6 贺六浑帖子实战验证：5,000 限额生效后 SA 暴力回测失效，必须走结构化小批量 + 断点续传。 |
| **4. 未满 100 个因子（尚无 SA 权限）当下该怎么准备？** | **当前约 95/100，仅差临门一脚；切忌为凑 100 塞入低质高 PC 因子！** | Gold 级解锁后**只能组 `own`（自有池）SA**，子因子质量与同区域多类别多样性直接决定 SA 上限（Garbage in, garbage out）。当前应重点补强 `USA/D1` 与 `EUR/D1` 的跨类别低相关 D1 RA 弹药。 |

---

## 二、问题 1 深度调研：平台规则激励方向与实证数据

### 2.1 实时金字塔倍率对比（D0 vs D1，2026-11-26 采集 216 条全量数据）

完整原始 JSON 已落盘至 [wq_rules_d0_unused_python_sa_snapshot_20261126.json](wq_rules_d0_unused_python_sa_snapshot_20261126.json)。

#### 全局 Delay 对比

| Delay | 金字塔总数 | 平均倍率 | 最高倍率 | `≥ 1.5×` 数量（占比） | `≥ 1.8×` 数量（占比） |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Delay 0 (D0)** | 66 | **1.633×** | 1.9× | **50 (75.8%)** | **29 (43.9%)** |
| **Delay 1 (D1)** | 150 | **1.332×** | 1.9× | **48 (32.0%)** | **10 (6.7%)** |

#### 双 Delay 区域逐一对比（全部 6 个同时开放 D0/D1 的区域，D0 均值全面高于 D1）

| Region | D0 均值 | D1 均值 | 差值 (D0 − D1) | D0 最高 | D1 最高 |
| --- | ---: | ---: | ---: | ---: | ---: |
| **USA** | 1.533× | 1.188× | **+0.346×** | 1.8× | 1.5× |
| **GBR** | 1.664× | 1.406× | **+0.258×** | 1.9× | 1.7× |
| **DEU** | 1.850× | 1.613× | **+0.237×** | 1.9× | 1.8× |
| **EUR** | 1.408× | 1.207× | **+0.201×** | 1.7× | 1.5× |
| **AMR** | 1.700× | 1.550× | **+0.150×** | 1.9× | 1.7× |
| **CHN** | 1.738× | 1.608× | **+0.129×** | 1.9× | 1.9× |

> 全平台倍率 Top 20 中，**19 个属于 D0（1.8×–1.9×）**，唯一进入 Top 20 的 D1 是 `CHN/D1/Other (1.9×)`。

### 2.2 近期核心规则与主题公告汇总（验证平台“拓宽因子范围”的战略意图）

| 公告 ID | 日期 | 机制名称 | 核心规则与激励 | 对当前 D1 流程的启发 |
| --- | --- | --- | --- | --- |
| **`R9EQM1R`** | 2026-11-06 | **D0 Theme**（`11/09–12/06`） | D0 全区 2×；**单数据集 + 至少 1 个未用字段 3×**；月度 30 条 D0 提交上限临时取消（日限仍 4 条）。 | 明确体现平台对 D0 + 未用字段的高溢价；*当前继续严格隔离，不打断 D1 主线*。 |
| **`yjwedz7`** | 2026-11-17 | **未用字段（`Alphas=0`）无限回测** | 表达式中**全部经济字段**均为 `Alphas=0`（可搭用 9 个 PV1 辅助字段）时**不计入每日 5,000 次回测上限**；名单锁定至 **2026-12-06**；并发槽位仍为 8（GLB 占 2）。 | **D1 完全适用！** 是 12-06 前最直接的零额度红利。 |
| **`A19OvZA`** / **`ygwKrOy`** | 2026-10-09 / 09-11 | **USA/D1 TOP1000** & **DEU/GBR D1 Theme** | 连续两期非 D0 常规主题均采用：**Regular Alpha 2×，Python Alpha 3×**（直接给 Python 高出 +1× 的加成）；2026-06 还举办了专门的 **PAC2026（Python Alphas Competition）**。 | 说明 **D1 主题同样高频扶持 Python Alpha**，未来 D1 主题极可能延续 3× 激励。 |
| **`7MZJV8A`** | 2026-11-22 | **ASI/D1 Power Pool Dec'26**（`11/23–12/20`） | 4 周、\$15,000 奖金池（前 80 名有奖）；结合 `7GNvo8y` 规则，`Power Pool + ATOM` 不受 1/日、10/月纯 PP 配额限制。 | 当前唯一活跃 D1 主题，可作为 D1 支线储备。 |
| **`R9E6wkR`** | 2026-11-17 | **BRAIN Tips 003：Theme 倍数计算官方口径** | `合并倍数 = 所有适用倍数之和 − 倍数个数 + 1`；`最终质量因子倍数 = 合并倍数 × Osmosis(1~2×)`。 | **纠偏重点**：Theme 与 Pyramid 不是连乘，而是线性叠加去重；仅作用于每日 Base 的 Quality Factor（相对排名缩放），不影响季度奖。 |

### 2.3 平台底层动机解析：为什么同时推 D0 + 未用字段 + Python？

从机构量化资产管理（WorldQuant 实盘组合）视角看，这三项政策本质是解决同一个核心痛点——**传统信号池过度拥挤（Alpha Crowding）**：
1. **字段拥挤**：大量顾问集中在 `USA/D1` 的 `pv1 / fundamental / 热门 model` 字段上，导致 `Prod Correlation` 居高不下、新增因子对实盘组合边际贡献递减 → 于是用 `Alphas=0` 免额度 + 金字塔动态高倍率把算力驱赶到冷门字段与非美区（`DEU/CHN/GBR/ASI`）。
2. **频率拥挤**：多数顾问只做隔日开盘/收盘的 D1 信号，日内/盘尾即时信息（D0）供给稀缺 → 于是给 D0 全面高出 `+0.13× ~ +0.35×` 的金字塔倍率与 3× 主题。
3. **计算范式拥挤**：Fast Expression 语法树有限，全平台数万顾问组合来组合去容易撞车 → **Python Alpha** 释放了自定义状态流（`store`）、非线性滤波、鲁棒统计、聚类别分组与轻量 ML，天然降低与传统 FastExpr 生产库的 `Prod Correlation`！

---

## 三、Python Alpha 完整使用与优化指南（官方文档 + 华子哥 Rank 9 + 贺六浑 Rank 6）

### 3.1 官方硬规范与避坑红线（来源：`getting-started-brain-python-alphas` & `how-translate-fast-expression-alpha-python-alpha`）

1. **核心契约（`@alpha` 装饰器）**：
   - 必须是**完全自包含的单文件/单代码块**，不能 `import` 本地自定义模块；提交到远端时**严禁**保留 `from brain import Brain, BrainCache` 或 `SimulationSettings`（仅保留 `from brain.alphas import alpha`、`numpy`、`scipy` 等标准/科学计算库）。
   - 函数签名固定接收 2 个参数：`def my_alpha(data, store) -> npt.NDArray[np.float32]:`。
   - 返回值**必须**为 1D `np.float32` 数组（shape `[n_instruments]`），因 `np.nanmean/nanstd` 等操作会悄悄升维到 `float64`，结尾务必 `.astype(np.float32)`，否则报错 `Alpha vector is not float32`。
2. **数据数组与 `store` 必踩坑**：
   - `data.<field>` 是 **只读 2D 数组** `[rows, n_instruments]`，最新一天是 `[-1]`；修改前必须 `.copy()`，否则抛 `ValueError: assignment destination is read-only`。
   - `data.universe` 默认自带（1=池内，0=池外），**不要写进 `data=[...]` 列表**。
   - **冷启动保护**：前几步窗口行数可能小于 `lookback+1`，用切片 `[-d:]` 安全，点索引 `[-1-d]` 必须先检查 `shape[0]`。
   - **整数与除权字段**：`int32` 字段缺失值不是 `NaN` 而是 `np.iinfo(np.int32).min`，需转 `float32` 替换；价格与每股基本面（`close/open/high/low/eps` 等）需用 `adjfactor` 复权（`returns` 已复权）。
   - **`store` 类型声明严格校验**：推荐字典声明 `{"name": "buf", "dims": "xi", "extend": np.float32(np.nan)}`（`"i"`=1D 股票轴，`"xi"`=2D `[窗口, 股票]`，新股票入池自动按 `extend` 扩展）。**`extend` 严禁写裸 `np.nan` 或 Python `0`**，必须写精确 NumPy 标量（如 `np.float32(np.nan)` / `np.float64(0)`）。
3. **当前平台硬限制（必读！）**：
   - 仅支持 **MATRIX** 字段（**不支持 VECTOR 字段**）；
   - **暂不支持 `GLB` 区域**；
   - **暂不支持 Multi-Sim（批量复合请求）**；
   - API 提交时 `settings.language = "PYTHON"`，代码依然放在 JSON 的 `"regular"` 字段中，且须设置 `settings.lookback`（通常 `min(max_ts_window * 2, 504)`）。

### 3.2 双轨开发流：省 5,000 额度的核心利器

| 路径 | 运行位置 | 速度与精度 | 是否占 5,000 日额度 | 适用场景 |
| --- | --- | --- | --- | --- |
| **Path 1：BrainLabs 本地模拟** | BRAIN Labs Jupyter（`BrainCache` + `generate_alpha_matrix / positions / stats`） | 极快（本地缓存数据），指标为近似值 | **不占远端回测 API 额度！** | 逻辑调试、Bug 排查、粗粒度参数扫频、算子实验 |
| **Path 2：Actual 远端模拟** | `POST /simulations`（`language="PYTHON"`）或网页 UI | 较慢，全量精确（含完整中性化/衰减/截断/相关性） | **占 5,000 日额度** | 精选候选终验、指标核对、正式提交 |

### 3.3 黄金顾问团 Python Alpha 实战优化建议（华子哥 Rank 9 + 贺六浑 Rank 6）

1. **反模式警告：不要止步于“1:1 翻译 Fast Expression”！**
   - 贺六浑（Rank 6）与官方总部培训均明确指出：单纯把已有 FastExpr 等价翻译成 Python（如华子哥实测信号相关性高达 `0.984`），本质仍是同一个因子，既无增量研究价值，又极易与自己原有因子撞 SC / 与生产库撞 PC。
   - **正确定位**：把「FastExpr → Python 自动转换」当作**基线验证器与入门跳板**，真正的提效与降 PC 来自后续三步升级。
2. **优化路径 A：因子结构压缩（Factor Compression，贺六浑 Rank 6）**
   - 把原本 6–7 层嵌套的 FastExpr 在 Python 中逐层拆解，做消融实验（Ablation），砍掉对 Sharpe/Fitness 贡献极微弱的“装饰性外层算子”，保留最纯粹的核心信号链，显著降低过拟合风险并优化 Genius 评分中的 `Avg distinct Operators/Alpha`。
3. **优化路径 B：借 Python 实现 Gold 账号的“算子平权”（华子哥 Rank 9）**
   - Gold 级别只开放约 **45% 的平台算子**（例如本账号实测没有 `ts_median`）。在 Python Alpha 中，只要会写 NumPy/SciPy，就能直接实现高阶算子，**完全突破 Gold 算子权限壁垒**！
   - 华子哥实盘验证的四大高效向量化扩展方向（可直接内联至 `@alpha` 中，只依赖 `numpy/scipy`）：
     - **鲁棒清洗类**：`MAD Winsorize`、`Robust Z-score = (x - median) / (1.4826 * MAD)`、Savitzky-Golay 滤波（`scipy.signal.savgol_filter`）——比默认 `zscore` 更抗极端值。
     - **技术/波动融合类**：向量化 `EMA / DEMA / MACD / Wilder RSI / NATR / Williams %R`（华子哥案例 `E5KO9Rg0`：用 `Williams %R(10)` 反转 + `NATR(14)` 低波避险各 50% 融合 + MAD 标准化 + `SLOW_AND_FAST`，将 Sharpe 从 `1.29` 提升至 `1.75`、2Y Sharpe `2.54`、`PC = 0.617` 全部 PASS！）。
     - **计量统计类**：向量化 OLS **均值回复半衰期**（`ts_half_life`）、滚动自相关（`ts_autocorr`）、滚动 Sharpe。
     - **截面残差剥离类**：`rank_residual`（对已知风险/风格因子的截面最小二乘残差提取纯净信号），或结合官方建议用轻量聚类构造**自定义动态行业分组**。
4. **优化路径 C：状态化流水线（Stateful Pipeline，贺六浑 & 华子哥）**
   - 利用 `store` 维护跨日中间特征缓冲（单/双缓存 FIFO + `lookback` 暖启动）或**平滑自适应参数**（华子哥在复现 `ts_target_tvr_decay` 时发现：直接二分搜瞬时 `λ` 当 `λ>2` 会因 `|1-λ|>1` 振荡拖垮 Sharpe；对 `λ` 本身做 `λ_eff = 0.9*λ_prev + 0.1*λ_raw` 指数平滑后，Sharpe 立刻从 `1.57` 恢复至 `1.69` 且稳定）。
   - **边界纪律**：如果研究假设本身是无状态的当日截面清洗/残差计算，优先保持 `store=[]`，避免无意义的状态复杂度；同时牢记官方忠告——**绝不为了 +0.05 的微弱 Sharpe 强上重型 ML/DL 模型**。
5. **数值对齐细节（华子哥实测）**：
   - `ts_std_dev` / `ts_variance` 与 FastExpr 对齐时使用 `ddof=0`（总体标准差）。
   - 若从 FastExpr 迁移改造，建议在平台给 Python Alpha 打上原 FastExpr Alpha ID 的 Tag 便于溯源。

---

## 四、问题 2 深度调研：SuperAlpha 额度机制与“破百前后”实战资料汇编

### 4.1 核心答疑：SuperAlpha 占不占每天 5,000 次回测额度？

**明确答案：占用！必须把三套独立概念彻底区分清楚：**

| 额度类型 | 规则详情 | SA 与 RA 的关系 | 权威来源 |
| --- | --- | --- | --- |
| **1. 每日回测额度（Simulation Limit）** | **5,000 次/天**（冬令时北京时间 **13:00** / EST 00:00 重置；API 响应头 `X-Ratelimit-Limit / Remaining / Reset` 实时返回） | **共享！** Regular、Python、SuperAlpha 全部走 `POST /simulations`，任何成功的回测均计入 5,000 上限（仅全 `Alphas=0` 的 RA 表达式至 12-06 免计）。并发方面 SA 较重，顾问脚本一般开 `MAX_WORKERS = 3`。 | 官方文档 `understanding-simulation-limits` + Rank 6 贺六浑 SA 实战帖确认 |
| **2. 每日提交配额（Submission Quota）** | **SuperAlpha 每日固定 1 条** | **完全独立！** 不占用每日 4 条 Regular Alpha 提交额度；且可贡献每日额外 **\$1–\$60 Base Payment**（并计入 Genius 信号数与 Combined Performance）。 | 官方文档 `brain-genius` + 置顶 SA 手册 |
| **3. 扩展池配额（Expanded Pool Quota）** | Gold 仅限 `own`（自有池）；Expert（同校）/ Master（同国）/ GM（全球）可用他人池 | **1:1 赚取制**：每提交 1 条 `own` SA，获得 1 次使用扩展池（`not own`）提交 SA 的机会（每日总提交仍上限 1 条）。 | 官方文档 `brain-genius` |

### 4.2 本账号当前状态与“95 → 100 解锁前”的精准准备建议

结合 2026-11-26 实时采集的账号数据（`JG81923` · **Gold** · 已点亮 14 个 D1 金字塔，距离 100 条解锁仅差最后几条）：

| Region × Delay | 当前金字塔命中总数 | 类别分布结构（实测） | 对未来 `own` SA 的诊断 |
| --- | ---: | --- | --- |
| **`GBR_D1`** | 35 | `Model(23)`, `Other(3)`, `Analyst(3)`, `Fundamental(3)`, `Sentiment(3)` | 数量最厚，但 **Model 占比过高（66%）**，组 `own` SA 容易撞高 PC，需排除或降权部分 Model |
| **`EUR_D1`** | 28 | `Fundamental(12)`, `PV(9)`, `Other(4)`, `Model(1)`, `Analyst(1)`, `Risk(1)` | **当前最适合率先起飞 `own` SA 的区域！** 类别较均衡，继续补 `Model / Analyst / Sentiment` 即可成型 |
| **`GLB_D1`** | 20 | `PV(5)`, `Model(5)`, `Other(3)`, `Risk(3)`, `Fundamental(2)`, `Analyst(2)` | 类别覆盖广（6 类），需注意 GLB SA 官方要求：`COUNTRY` 中性化、先在 `TOP3000` 快调再上 `MINVOL1M` + `Max Trade ON` |
| **`USA_D1`** | 15 | `Analyst(8)`, `Fundamental(6)`, `Model(1)` | 总量尚薄且偏基本面/分析师，后续在 `USA/D1` 持续补充 `Model / Sentiment / News / Other / PV` 对 `own` SA 收益极大 |

#### 尚未满 100 条（无权限阶段）最值得立刻做的 4 件事：
1. **绝不为了凑 100 塞低质/过拟合因子**：王哥（Rank 3）复盘 IQC Global Final 实证指出——SuperAlpha 的样本外衰减比想象中更残酷（`OS/IS ≥ 0.3` 的都很少），根本原因在于底层 RA 的细微过拟合会在组合中被系统性放大（**Garbage in, garbage out**）。
2. **有意识地按“未来 `own` SA 弹药库”标准补齐类别多样性**：Gold 阶段只能用自己的因子，而 `own` SA 想做到“三五标准”（`Sharpe > 5, Fitness > 5, PC < 0.5`），核心前提是**同一 Region × Delay 内有足够多不同 `datacategories` 且彼此低相关的优质 RA**。当前主攻 `USA/D1` 与 `EUR/D1` 时，多补 `Analyst / Sentiment / Other / Model` 空白类别，一鱼两吃（既点亮金字塔，又直接喂厚 `own` SA 池）。
3. **养成干净的元数据与标签习惯**：SA 的 Selection 表达式可直接按 `tags`、`color`、`name`、`prod_correlation`、`turnover`、`operator_count` 筛选。保持已提交 RA 低 `PC`、低复杂度，后续用 `prod_correlation > 0` 即可一键过滤掉早期 User 阶段的无 PC 过拟合因子。
4. **提前理解并备好 SA 轻量化资料框架**（等破 100 解锁当天直接零踩坑起跑）。

### 4.3 解锁 100 条后（Gold `own` SA）核心方法论与模板库（黄金顾问团精选）

#### A. Selection Expression（选择表达式）避坑与高胜率模板
- **可用属性全集**（官方接口 `GET /suggest/fields`）：`own`, `own_university`, `own_country`, `turnover`, `long_count`, `short_count`, `decay`, `universe`, `operator_count`, `datafield_count`, `dataset_count`, `datacategory_count`, `self_correlation`, `prod_correlation`, `neutralization`, `truncation`, `datacategories`, `datasets`, `datafields`, `classifications`, `competitions`, `themes`, `name`, `color`, `category`, `favorite`, `tags`, `os_start_date` 等。
- **三大铁律**：
  1. **严禁用历史 Sharpe / Returns 做 Selection 排序**（极端过拟合，OS 直接崩盘）。
  2. **过滤早期/高拥挤因子**：必备 `own && (prod_correlation > 0) && (prod_correlation < 0.6)`（`prod_correlation > 0` 可剔除 User 阶段因子）。
  3. **多样性分层法（王哥 Turnover 分层 + 橘子姐连拿 \$60/天 DataCategory 分层）**：把低重合度的 `datacategories` 分成独立小池（如基本面类 `[fnd/anl/ern]`、量价/模型类、另类/情绪类 `[news/sentiment/other/risk]`），再用 `||` 拼接保证每个桶都能选到因子：
     ```text
     own && (prod_correlation > 0) && (prod_correlation < 0.65) && (
       (in(datacategories, "fundamental") && turnover < 0.15) ||
       (in(datacategories, "analyst") && turnover < 0.25) ||
       (in(datacategories, "model") && operator_count <= 8) ||
       (in(datacategories, "other") || in(datacategories, "sentiment") || in(datacategories, "pv"))
     )
     ```
  4. **贺六浑（Rank 6）Gold `own` 三五 SA 破局术（随机上色 + 排除法）**：当 `own` 池能组出 `Sharpe>5 & Fitness>5` 但 `PC` 卡在 `0.6–0.8` 时，用脚本把顾问期之后的自有 RA 随机均分染上 `NONE / RED / YELLOW / GREEN / BLUE / PURPLE` 6 色，再配合：
     - `own && (color != 'RED') && (prod_correlation < 0.6)`
     - `own && (not(in(datacategories, 'model')))`
     - `own && (neutralization != 'SUBINDUSTRY')`
     做小规模可控扫描（配合 SQLite 断点续传与每日配额预算，绝不无脑暴力刷完 5,000）。

#### B. Combo Expression（组合表达式）黄金法则
1. **等权永远是第一基准（WL13229 + IQC Final 韩国研究员 + 王哥共识）**：
   ```text
   1
   ```
   稳健性最高、过拟合风险最低；**复杂花哨的 Combo 在 OS 绝大多数跑不赢等权**。
2. **进阶三板斧（Combo 算子严控 `≤ 3` 个，且永不给因子负权重）**：
   - **平台内置去相关组合**：`combo_a(alpha, mode='algo1')`（韩国研究员实测 `algo1` 综合最佳，支持多窗口如 `nlength=40/160/250`）
   - **波动率倒数风险平价**：
     ```text
     stats = generate_stats(alpha);
     1 / ts_std_dev(stats.returns, 252)
     ```
   - **相关性平方和惩罚（低相关加权）**：
     ```text
     stats = generate_stats(alpha);
     1 / reduce_powersum(ts_corr(stats.returns, stats.returns, 252), constant=2)
     ```
   - **台湾第一（Rank 1 `YW82626`）波动率状态切换 Combo**：用 `ts_std_dev(stats.returns, 20)` 相对 10 日均线划分高/低波状态，高波切均值回归、低波切动量，并用 `ts_rank(..., 10)` 平滑权重（**须开启 OS Activation 复验**）。

#### C. 官方防过拟合必检：`Component Activation = OS`
- 官方 `superalpha-overview` 强烈推荐工作流：**先用 `IS Activation` 初研（10 年长历史），定稿前必须切换 `OS Activation` 做 Reality Check**——只有子因子在各自真正的样本外期间（`os_start_date` 之后）组合依然有效，才说明没有叠加过拟合！

---

## 五、对当前流程的零冲突行动建议（节奏规划）

1. **当下（2026-11-26 ~ 12-06，未来 10 天）**：
   - **严守当前 D1-Only 节奏不动摇**：优先利用 `Alphas=0` 免额度窗口（12-06 截止），高质收割最后 5 条冲过 **100 条 OS 门槛**，并顺手夯实 `USA/D1`、`EUR/D1` 的跨类别因子库。
   - **绝不因 D0 倍率分心切线**：D0 主题 12-06 就结束了，临时切线不仅打乱已有 4,893 FULL/天 稳定流水线，还会消耗宝贵的 5,000 常规额度。
2. **中期（破 100 解锁 SA 后）**：
   - **额度隔离预算**：给 SA 分配独立小额预算（例如每天 300–500 次以内，并发 ≤3），绝不抢占 D1 RA 主线的 4,000+/日产能；首批优先从 `EUR_D1`（类别最均衡）和 `GBR_D1`（过滤部分 Model）做 `own` 等权/`combo_a` SA，把每天 1 条独立 SA 提交额度吃起来。
3. **择机支线（下一期出现 `D1 Python Alpha 3×` 主题或竞赛时）**：
   - 优先在 **BrainLabs 本地（0 远端额度消耗）** 复用华子哥的向量化算子库（MAD / NATR / Williams %R / `rank_residual`）+ 贺六浑的“因子结构压缩”思路，针对 `USA/D1` 或 `EUR/D1` 已有高 Margin 种子做 **Python 增强改造（而非 1:1 翻译）**，用极低远端额度吃下 Python 3× 加成与 Gold 算子平权红利。
