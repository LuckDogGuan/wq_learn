# WorldQuant BRAIN D1 闭环复核

2026-11-27 · 供筛选后续试验 · 仓库基准 `e939645`

## 研究问题与结论

**Sharpe 的提升难度要按区间分别验证。** “1.25 到 1.60”和“1.60 到 1.85”是说明区间难度可能不同的例子，在本文只作为统计切点。两个例子的步长分别为 0.35 和 0.25，难度比较要同时看等步长的分段结果和同母版的实际改善率。双 2 留到末段定向优化。常规 RA 候选按适用门槛进入终检。早期允许多参数组合，定向修复与双 2 冲刺按单参数归因。 [现有四阶段流程](<整理与研究/workflow/d1_4stage_pipeline.json#L38>) · [现有 RA 门槛](<../wq_research_v2/config/d1_thresholds.json#L5>)

| 阶段 | 研究目标 | 判断依据 |
| --- | --- | --- |
| Stage 0–1 找种子 | 用华子哥 WDS 找值得试的数据集，验证信号有无正向表现。 | 结合经济方向、覆盖、命中率和表达式多样性。早期可以组合调整窗口、中性化和衰减。 |
| Stage 2 筛选 | 轻量参数与结构组合，保留不同信号家族供 FULL 验证。 | 交付母版、参数组合、全期及可见的分期指标。QUICK 可作排序依据，缺项标记未验。 |
| Stage 3 FULL | 用 FULL 检查达到适用 RA 门槛的情况，再按已定位的短板优化。 | 看全期、2Y、子池、换手和风险指标。已达标候选与仍待优化母版分别计数。 |
| Stage 3 末段到 Stage 4 | 对少量有明确缺口的候选开启双 2 支线。每次只动一个参数。 | 同母版、同窗口、同 FULL 口径比较收益、Sharpe、Fitness、换手与 Margin。RA、SC、PC、池内正交独立验收，合格后按 Margin 取舍。 |

## 不同 Sharpe 区间的样本难度

**近期 BRAIN IS 样本。** 2026-11-25 至 27 日北京时间固定 20 分钟切片，`get_user_alphas` 返回 1,122 个不同 ID。保留 D1 并排除 CHN、AMR、DEU、IND 后剩 1,106 个，FULL 与 QUICK 分列。下表所有数值均为同批样本的累积达标数。`>2` 与 `≥2` 分开核对，本批计数相同。

| 范围 | 有效 N | ≥0.80 | ≥1.25 | ≥1.58 | ≥1.60 | ≥1.85 | >2.00 | 双 2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FULL 合计 | 537 | 206 | 138 | 58 | 54 | 22 | 19 | 0 |
| EUR FULL | 196 | 109 | 83 | 42 | 41 | 22 | 19 | 0 |
| USA FULL | 257 | 55 | 23 | 7 | 5 | 0 | 0 | 0 |
| ASI FULL | 48 | 40 | 32 | 9 | 8 | 0 | 0 | 0 |
| GLB / KOR FULL | 16 / 20 | 2 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| QUICK 合计 | 569 | 94 | 25 | 6 | 5 | 2 | 2 | 0 |

FULL 中，已达 `0.80` 的候选有 **138/206（67.0%）** 同时达到 `1.25`。从 `1.25` 看 `1.60` 为 **54/138（39.1%）**，从 `1.60` 看 `1.85` 为 **22/54（40.7%）**。两段跨度不同。同样提高 `0.25` 时，`1.25 → 1.50` 为 **80/138（58.0%）**，`1.60 → 1.85` 为 **22/54（40.7%）**。这批样本在等步长比较中，起点较高的一段达标比例低 17.2 个百分点。这个差值描述样本分布。实际调参难度还要看各地区、Universe 和模板族中，同等预算下有多少母版得到同等幅度的改善。

FULL 的 **19 条 Sharpe > 2 全部在 EUR，18 条集中于 11 月 27 日的切片，只涉及 6 个不同表达式**。19 条的 Fitness 都有值，最高 **1.64**。因此，`>2|≥1.85` 虽然观察到 **19/22**，却主要反映同一地区的一簇参数变体。**近期双 2 是 0 个观测，实际概率仍未知。**

**历史交叉对照。** 2026-07-28 至 08-31 的本地 D1 旧库包含 EUR、GBR、GLB、USA 共 **22,105** 条，`>2` 实测 **26.07%**，双 2 有 **2,528** 条。旧库含定向爬山和模板记录，且没有 `simulationMode`。用该旧池的均值和标准差拟合正态，`>2` 会估成 **35.77%**，`>5` 会估成 **0.28%**，后者实测 **2.76%**。旧库和近期的构成差异很大，适合报告分层经验比例。 [本地 SQLite 旧库](<../data/wq_v2_ledger.db>)

**真实晋级的证据较少。** 旧库按 `source_alpha_id` 找母子，限定同地区、Universe、D1、完全相同的存档 settings，且子记录时间不早于母记录、表达式有变化，仅有 **14 个母版、82 条子记录**。其中 GBR 母版在 `[1.25,1.58)` 的 **5 个母版**中，**1 个**到 `1.58`（`O0GYPGQ7 → leWqOWL5`），这组 **9 个子结果均未到 1.60**。`[1.85,2)` 没有严格配对。真实晋级率应以母版为分母，在相同尝试预算下统计达到下一档的母版数，未观测另记。 [本地 SQLite 旧库](<../data/wq_v2_ledger.db>)

## 末段双 2 的判断依据

BRAIN 的 `Fitness = Sharpe × √(|年化收益| / max(换手, 0.125))`。换手低于 12.5% 时，继续压换手对分母没有直接收益。ASI `A1L67JZg` 的 Sharpe **2.62**、Fitness **1.61**、换手 **12.10%**、收益 **4.72%**。固定 Sharpe 和换手，收益需超过 **7.28%** 才能达成双 2，且该因子的 Robust 检查仍失败。它适合先解决稳健性和收益缺口。 [BRAIN 指标说明](https://platform.worldquantbrain.com/learn/documentation/interpret-results/parameters-simulation-results) · [ASI 结果](<整理与研究/regions/ASI_MINVOL1M_D1.md#L35>)

高换手一侧有局部强对照。GBR/TOP700 的 `model38` 三条旧结果 settings 完全相同，母式外层平滑从无到 5 日、10 日，换手 **16.73% → 14.47% → 13.10%**，Fitness **2.72 → 2.80 → 2.78**，Sharpe **2.82 → 2.76 → 2.67**。只支持在类似母式上试一档轻平滑。三个 ID 为 `88lOnYwV / GrlnoLZO / E5lqKE9P`，当前终检状态待复核。 [本地 SQLite 旧库](<../data/wq_v2_ledger.db>)

## WARNING 要按原因处理

537 个近期 FULL 中，`MATCHES_THEMES`、`MATCHES_COMPETITION` 各有 **537** 条 WARNING，`CLUSTER_TEST` 有 **526** 条。主题和竞赛结果按对应目标解释。Cluster、PPA 与普通 RA 分别看适用检查；数据缺项、`PENDING` 或 `ERROR` 先核证据。仓库 RA evaluator 当前把 `CONCENTRATED_WEIGHT`、`LOW_2Y_SHARPE`、`IS_LADDER_SHARPE`、`LOW_SUB_UNIVERSE_SHARPE` 四类 WARNING 列为阻断。低全期 Sharpe 和 Fitness 另外有明确的数值门槛。 [本地 RA 判定](<../wq_research_v2/src/wq_research_v2/ra_evaluator.py#L209>) · [BRAIN 顾问检查](https://platform.worldquantbrain.com/learn/documentation/consultant-information/consultant-submission-tests)

| 短板 | 已观察到的结果 | 可检验的修法 |
| --- | --- | --- |
| 全期 Sharpe / Fitness 偏低 | USA `wpNV7mxd` 的 2Y **2.96** 已过，全期 Sharpe **1.20** 和 Fitness **0.62** 仍是 WARNING。 | 先看弱年份的收益与波动。仅靠近期走强不足以修全期。信号窗口或中性化择一试，保留原式对照。 |
| 2Y 与 Ladder | USA `xAl8R0mp` 的 `LOW_2Y_SHARPE` WARNING 是 **0.60/1.58**。EUR `1YG578aX` 的 **2.25/2.02** 来自 Ladder **第 3 年**。当前入库会把任意首条 Ladder 值也写进 `sharpe_2y`。 | 先按检查名和年份归位，再按失败窗口试一档窗口或平滑。修复字段口径可以先用已有结果验收。 [入库代码](<../wq_research_v2/src/wq_research_v2/sim_runner.py#L644>) |
| 权重集中 | GBR `qMNZ9aMA` 为 WARNING，Sharpe **2.30**。同一 `model26` 信号族的 `xANwPGQq`、`qMNkPGvj` 等过集中度检查，Sharpe **2.02、2.07**。字段及多项参数也有变化。 | 已在该族观察到可以过线的邻域。集中来源先查有效股票数与尾部暴露，再单试截尾、分组或短平滑的一项。单项效果待验。 |
| 子池、ASI 日本与 Robust | ASI `A1L67JZg` 与 `9qGo72A1` 日本检查都过，Robust Sharpe **2.10/2.36**、**1.85/1.92** 和 Robust 收益均 FAIL。以第二条为例，`1.85/1.92` 是达门槛 **96.4%**，以全池 Sharpe **2.13** 为分母约 **86.9%**。 | 分开看日本、Robust Sharpe、Robust 收益与池内范围。先查筛出的是流动性还是信号本身，再固定 `decay` 做单轴。当前的 COUNTRY 与 CROWDING 对照同时改了 `decay`。 [ASI 结果](<整理与研究/regions/ASI_MINVOL1M_D1.md#L35>) |
| 单位与覆盖 | USA `9qRa7wde` 有 `UNITS:WARNING`，同时 Ladder 通过。 | 核对字段单位、比例分母及缺失值处理，再决定是否改表达式。 |
| 换手与目标路径 | GLB `9qppM6qd` 普通 `HIGH_TURNOVER` 为 **1.3183/0.70 FAIL**，同时 HT 换手和 HT 收益比通过。 | 按目标选择换手方向。常规 RA 看换手与收益的权衡，HT 则看新增换手的收益贡献。 [GLB 历史路径记录](<../staging/playbooks/ai_work_guides/submit/submission_log.md#L76>) |

## 华子哥离线数据还能提供哪些筛选

六个可用区 USA/EUR/GLB/ASI/KOR/HKG 的快照共 **1,108 个地区 × 数据集组合**。其中各有 **742** 个样本量 ≥100、**440** 个 Sharpe 高于地区均值、**409** 个 Sharpe 和 Fitness 都高于地区均值、**149** 个进原甜区。按地区和 category，在数据集样本数 ≥50、可比较数据集至少 8 个的组内，**200** 个进入社区 Sharpe 前四分之一。适合并列保留「样本充足」「区内强」「类别内强」「甜区」四类线索。各类可单独筛选，有几条证据就写几条。 [WDS 聚合读取](<../wq_research_v2/src/wq_research_v2/wds_adapter.py#L80>) · [WDS 差距计算](<../wq_research_v2/src/wq_research_v2/wds_adapter.py#L164>)

| 候选线索 | 证据与适用范围 |
| --- | --- |
| **社区样本量、相对 Sharpe/Fitness、同类分位** | 可给不同类别各自排队。样本少的高值留作探索；旧社区均值用于选材。真实候选自身的收益、方向和近期门槛仍需对应结果。 |
| **中性化分布** | **881** 个组合有 ≥20 样本的中性化建议，现有推荐中 **88** 个组合含至少一项份额 ≥50%。可找「样本够、表现好、没那么拥挤」的替代档，保留样本率和分组口径。 |
| **OSIS 与拥挤** | ISO 快照止于 2026 年 2 月，独立 OSIS 止于 2025 年 10 月。**275/1,108** 缺独立 OSIS，另有 **110** 个共同条目的 OSIS 计数超过 ISO。内嵌 `neutralization…osis_count` 的求和等于 ISO 样本数。老产率只作提示，缺项记未知，动态拥挤看同坐标的实时元数据。 |
| **精确字段 .bin** | 六区可解析 **27,599** 条，历史覆盖槽、更新频率标签、分布变化和 T1/T2 可独立筛。HKG 这份快照无字段 bin，EUR 19 个精确 bin 文件均属 TOP1200。历史覆盖槽用于找稀疏或漂移线索，当前 EUR/TOP2500 要查实时字段。可用正负占比、偏度、离散性和历史分桶辅助挑选模板及诊断稀疏。 [字段解析](<../legacy_core/Core/tools/webdata_quality/webdata_quality.py#L191>) · [分层规则](<../legacy_core/Core/tools/webdata_quality/tier_rules.json#L5>) |

这些 WDS 聚合可直接支持候选排序。换手、Margin、近期 2Y、Robust、风控中的表现及具体信号方向需要相应的 Alpha 结果。有 Alpha ID 时读详情和年度；新字段按 D1、Region、Universe、Dataset 和精确 ID 查。对软筛条件的后续判断，固定地区、模板族和预算，每次只比较一条筛选线索带来的变化，指标用每百条有结果 FULL 的合格候选和未观测比例。 [字段 API](<official_guides/WQAPI_HUALABTECH_REFERENCE.md#L53>)

## 地区和经验的适用边界

**主线长期覆盖所有已确认可用的允许地区。** 当前候选为 USA、EUR、GLB、ASI、KOR、HKG、GBR。每波聚焦 **2–3 个地区，每个地区最多两个 category**。不同地区可选不同类别。例如 EUR 选 Model 与 Analyst，ASI 可选 Analyst 与 Sentiment。高 Pyramid 倍率用于合格候选的排序，地区切换时优先用本地证据。独立 ASI 实验线和冻结基线按各自范围运行。 [路线索引](<TRACKS_AND_LOGS_GUIDE.md#L12>) · [Pyramid 接口](<official_guides/WQAPI_HUALABTECH_REFERENCE.md#L72>)

- **可通用的是定义和核查方法。** Fitness 分母下限、FULL 检查是否覆盖目标、证据缺失的标记、单轴对照逻辑可跨区复用。
- **经济假设和模板可作为异地候选。** 在 USA/GLB 同为 D1/TOP3000、字段历史覆盖有效的 **733** 个共同 Dataset+Field 中，**281** 个分处 75% 覆盖两侧。`analyst15/anl15_ind_div_cos` 的历史尾三槽覆盖均值约为 USA **68.1%**、GLB **88.8%**。迁移时重新核对单位、可见时点、更新频率、覆盖和信号方向。 [字段解析](<../legacy_core/Core/tools/webdata_quality/webdata_quality.py#L191>)
- **参数和好因子先按原坐标使用。** 同在 EUR/TOP2500，流动性门控在 `model25` 族出现有效结果，在 `model77/finstmtrank` 却伴随 Sharpe 由 **1.89–1.97** 降到 **1.20–1.47**，子池仍失败。两组只能证明该改法依赖信号家族。跨区沿用假设，先在目标区做小样本，保留本地有效的窗口与中性化。 [EUR 结果](<整理与研究/regions/EUR_TOP2500_D1.md#L56>) · [反例记录](<agents/OPTIMIZATION_LEDGER.json#L170>)

## 复核坐标

- **近期样本**　`get_user_alphas(stage="IS", order="dateCreated", limit=100)`。北京时间 11 月 25、26 日窗口为 `00:50–01:10` 和之后每四小时同样的 20 分钟窗，27 日仅前三个窗口。每窗至多两页，按 Alpha ID 去重，按 `settings.delay`、`region`、`simulationMode`、`is.sharpe`、`is.fitness` 复核。窗口内返回 1,122 个，剔除 DEU 16 个。FULL 中六条缺 Fitness，全部在 Sharpe 2 以下。结果只覆盖切片内的 IS 库存，批次内变体存在依赖。
- **旧档案**　`data/wq_v2_ledger.db → legacy_alphas`，D1、有数值 Sharpe、排除四区。分段条件比例用「达到上档条数 ÷ 达到下档条数」。母子配对另用 `child.source_alpha_id = parent.alpha_id`、相同 `settings_json` 及时间顺序。可按文中 Alpha ID 查官方详情。
- **验证范围**　本报告是对仓库配置、结构化结果与 BRAIN 只读数据的复核。Antigravity 范围限目标和结果。

