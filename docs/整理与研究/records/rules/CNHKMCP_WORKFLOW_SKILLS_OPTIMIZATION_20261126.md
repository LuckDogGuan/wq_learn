# cnhkmcp 工作流与 Skills 拓展清单

日期 2026-11-26。范围为本项目 D1 研究、现有 cnhkmcp 工具、本机安装包随附资料和仓库当前实现。

**建议先做三件事**。校准 Stage 4 检查与 PC 证据，修正 Stage 0 字段检索的精确匹配，再把 Alpha 诊断做成现有 `wq-d1-closed-loop` 的按需入口。三件事均可用已有结果或离线样本验收。首轮新增回测预算建议为 0，后续按单个假设分配小批额度。

## 一、已经有什么

| 来源 | 现有内容 | 在本项目的用法 |
| --- | --- | --- |
| 本次会话的 cnhkmcp 注册表 | 39 个工具，覆盖设置、数据集/字段、算子、通知/文档/论坛、Alpha 详情/PnL/年度记录、回测、相关性、金字塔/竞赛/多样性，以及平台写入 | MCP 首选做实时元数据、已有 Alpha 取证和已知模拟链接排错。项目 runner 负责批次指纹、预算、恢复与落盘。 |
| 本机 Python 3.12 的 cnhkmcp 4.3.8 | 找到 45 个 `SKILL.md` 路径，计入嵌套和重复副本。安装包含 5 份 `示例工作流_*.md`，涵盖表达式解释、数据集探索、字段探查、Alpha 改进、日报 | 资料主要在安装包的 `cnhkmcp/untracked/skills/` 和 `cnhkmcp/untracked/AI打工人/ai-worker-skill/`。选择有用方法，逐个映射到项目已有实现。 |
| 发布与运行差异 | PyPI 发布页显示 4.3.17，本机包元数据为 4.3.8，当前 MCP 能力另以会话注册契约和试查为证 | 升级前比对工具参数和返回形状。当前服务进程版本未独立确认，4.3.17 的行为未实测。 |
| 仓库现有流程 | `wq-d1-closed-loop` 已串起 Stage 0、Stage 1–2、Stage 3、Stage 4 和经验回写。旧工作指引也已有 idea、evaluate、optimize、batch、report 等入口 | 先给现有入口添索引和产出格式，再按使用频率决定是否拆专项 Skill。冻结手册作为历史对照，冲突时按当前 `AGENTS.md` 执行。 |
| 社区项目和示例 | `worldquant-skill` 提供研究记录、批量回测、知识库检索。另一个公开仓库展示了「字段和算子解释」与「基线诊断 → 字段探针 → 改进」 | 借鉴结构化输入和证据记录。社区固定批量大小、门槛、自动写入策略及算子组合须按本项目规则重审。 |

来源：[PyPI 发布页](https://pypi.org/project/cnhkmcp/)、[社区 worldquant-skill](https://github.com/GRD-Chang/worldquant-skill)、[Alpha 改进示例](https://github.com/lori-kuo/world_quant_brain_worker/blob/main/cnhkmcp/untracked/%E7%A4%BA%E4%BE%8B%E5%B7%A5%E4%BD%9C%E6%B5%81_BRAIN_Alpha_Improvement_Workflow.md)、[项目闭环 Skill](../../../../.agents/skills/wq-d1-closed-loop/SKILL.md)、[旧工作指引索引](../../../../staging/playbooks/ai_work_guides/_INDEX.md)、[五个 Skill 实操课件](../../../official_guides/5_skill_workflow_courseware.md)。

### 值得借鉴的随包 Skills

| 想补的环节 | 随包资料 | 本项目落点 |
| --- | --- | --- |
| 字段与数据集侦察 | `brain-dataset-exploration-general`、`brain-datafield-exploration-general`、`wqb-field-family-scout` | Stage 0 先核验元数据和字段家族，再对少量陌生字段做更新频率探针。 |
| 经济假设与模板复用 | `wqb-hypothesis-designer`、`wqb-zero-order-field-factory`、`brain-enhance-template` | 每个候选只留可证伪预测、母版、唯一改动和失败判据。沿用现有剪枝与 AST。 |
| 诊断、归因和稳健性 | `brain-explain-alphas`、`brain-improve-alpha-performance`、`wqb-attribution-analyst`、`wqb-anti-overfit-gate` | 先读已有数据诊断失败原因，再决定是否做一层消融或邻域确认。 |
| 语法、终检和回测跟踪 | `alpha-expression-verifier`、`brain-alpha-judge`、`brain-calculate-alpha-selfcorrQuick`、`brain-simAlphasinBatch-and-track` | 对照本地 AST、RA 判定、SC/PC 与台账状态。语法通过、相关性数据可用、RA 过关分别记录。 |
| 复盘与资料发现 | `brain-nextMove-analysis`、`brain-forum-browse`、`wqb-memory-writer`、`wqb-self-diagnostic` | 把公告、证据与失败归因写成候选试验，复用批次台账和优化记录。 |

## 二、本次实试

| 尝试 | 观察 | 后续要验证什么 |
| --- | --- | --- |
| 官方文档与 D1 设置 | `get_documentations` 返回总数 11、当页 10 个模块并带 `next`。两篇正文 `simulation-settings` 与 `intermediate-pack-part-2` 成功读取。设置工具返回 18 个组合，其中 ASI/D1 列出 `MINVOL1M`、`MINVOL10M`、`TOP500`。 | 文档索引标明分页范围。设置结果记录查询日期，并按目标坐标提取。 |
| 字段精确检索 | ASI/MINVOL1M/D1/VECTOR 查询 `shrt3_bar`，返回总数 3,838、首批 50 行，无精确命中。限定 `analyst69` 后，对真实字段 `anl69_best_ndebt_lo` 与故意不存在的关键词分别查询，两次都报总数 687、返回 50 条，且都包含 `anl69_best_ndebt_lo`。 | 这组调用无法依赖 `search` 得到精确字段。首批无命中记为覆盖不完整，判断存在须核对 ID、类型、数据集和 D1 坐标。原因待定位。 |
| 一个既有 Alpha 的诊断 | 用冻结手册中的 `e71w5Qrl` 查询，年度统计返回 2014–2023 共 10 行，包含 Sharpe、Margin、Fitness、Drawdown、Long/Short Count 等。Record sets 查询外层未标错误，内层却返回 JSON 解析错误。 | 统一检查业务返回体。年度样本之外的阶段和记录集可用性待分别核实。 |
| 批次审计离线复现 | 对 `LOW_2Y_SHARPE` 分别给 `PENDING`、`WARNING`、`ERROR`、`PASS`，现有审计函数均记为零失败，只有 `FAIL` 返回否。生产漏斗导出调用这一审计。 | 用完整检查项和当前目标口径计算「已验证 0 FAIL」。独立保留 PC 查询、RA 硬检和 PPA 路径的语义。 |
| PC 直方图离线复现 | 固定数字 PC=0.74，省略 `records`、空 `records` 或给跨阈值桶 `[0.69, 0.75, 30]`，现有函数均判 `PC_RESCUE_NEAR_SPARSE`。给 `[0.70, 0.75, 30]` 判拥挤。 | PC 数值和分布证据分别判断。缺失及跨阈值无法拆分的桶保留未知或上下界。 |
| 现有离线测试 | 表达式、字段、SC/PC、批次审计和 runner/台账共 20 项通过。 | 上述新增边界已单独复现，后续实现时将其加入相应回归测试。 |

源码定位：[批次审计](../../../../wq_research_v2/src/wq_research_v2/batch_audit_logger.py#L21)、[生产漏斗调用处](../../../../wq_research_v2/src/wq_research_v2/daemon_ra_runner.py#L1255)、[RA 终检判定](../../../../wq_research_v2/src/wq_research_v2/ra_evaluator.py#L209)、[PC 直方图](../../../../wq_research_v2/src/wq_research_v2/pc_poller.py#L43)、[冻结手册](../../workflow/D1_RA_BASELINE_V1_MANUAL.md)。

## 三、可分开尝试的 15 个方向

预算以新增回测表达式计，均为建议上限。可以先并行做几个 0 回测项；需要新回测的试验按单个假设启动。

| 编号与优先级 | 方向 | 最小尝试与验收 |
| --- | --- | --- |
| 01 · P0 | **RA 终检证据一致性** | 离线回放空响应、缺项、PENDING、阻断 WARNING、普通 WARNING、FAIL、完整 PASS 和 PPA-first 样本。核对审计、RA evaluator 和检查来源。同一证据与目标规则给出一致的 RA 结论。0 回测。 |
| 02 · P0 | **PC 救援证据可靠性** | 用本次 0.74 样本加一个真实稀疏桶做回归。数字 PC 决定是否过线，完整直方图决定是否优先救援。复用 `pc_poller` 和已有队列。0 回测。 |
| 03 · P0 | **字段与设置精确核验** | 把本次有/无字段对照、旧 WDS 无覆盖的 DEU/GBR 样本加入试查。记录 ID、类型、覆盖、日期覆盖、数据集、坐标、时间和覆盖范围。用项目已有字段读取路径核对分页；缺值、过期、冲突单列。0 回测。 |
| 04 · P0 | **批次漏斗与额度对齐** | 抽一份含 FULL、QUICK、未观测、去重、缺项的快照，按 SQLite 逐项对账。当前审计的 `completed_full` 计入两种完成状态，按模式拆分。若广州实际出现内存压力，再用同一快照评估流式遍历。0 回测。 |
| 05 · P0 | **回测启动、跟踪和恢复** | 离线复用 SimRunner 和 ledger，覆盖 429、5xx、超时、缺子 ID 和重启。核对一次只读对账、原批次额度、已完成行保护和终态；保存已知 location 后可用 `lookINTO_SimError_message` 诊断。0 回测。 |
| 06 · P1 | **已有 Alpha 诊断卡** | 同一 Region/Universe 尽量选同母版的通过样本、单项失败样本、PC 待定样本。读取详情、年度统计、PnL 和可发现的记录集，画出失败年份、集中阶段、缺失证据与一条修复轴。记录集查询失败时保留错误类型。0 回测。 |
| 07 · P1 | **库存先于新回测** | 从未提交库存挑 5 条，用现行硬检、数字 SC/PC、池内正交和 Margin 复核。记录多少条值得推进、多少因证据缺失暂缓。遇 PPA 优先路径，确认实际目标门禁。0 回测。 |
| 08 · P1 | **数据集优先与跨集字段家族** | 在同一 D1 Region/Universe 对照同一经济概念的 2 个数据集。先核对描述、单位、发布日期/可用时点、覆盖和更新节奏，同名仅作为线索。先做 0 回测筛查，必要时对一个陌生字段用现有探针方案上限 8 条。 |
| 09 · P1 | **假设卡与批次多样性** | 用同一历史种子池离线对比旧排序与「经济机制、预测方向、反证条件、母版、唯一改动」候选卡排序。比较同族占比、近重复数与有效命中；跨族探索批与同母版控制变量批分别看。0 回测。 |
| 10 · P1 | **Stage 3 单轴修复与局部稳定性** | 先读出主失败项。若是 LOW_2Y_SHARPE，从已验证的窗口或中性化方向任选一轴，跑母版和 2 个变体，必要时多 1 个相邻点。固定其余设置，FULL 上限 4 条，同时观察 2Y、Fitness、Margin 和集中度。 |
| 11 · P1 | **QUICK 对 FULL 的排序保真** | 优先用历史同表达式、同设置配对，比命中前列和漏掉的 FULL 冠军，并列出缺失指标。若无足够配对数据，4 个表达式各跑 1 QUICK 与 1 FULL，上限 8 条。结果只用于 Stage 1–2 路由，Stage 3–4 用 FULL。 |
| 12 · P1 | **资料检索与规则变更待办** | 选一个明确问题，按项目 8:2 优先级查王哥、黄金顾问和管理员原创，保留原始日期、适用坐标、反例与单个最小验证。用 `get_messages`/文档更新记录队列，先复核临时活动、额度与门槛，再决定是否试点。0 回测。 |
| 13 · P2 | **组合空位与金字塔研究** | 用 `get_pyramid_alphas`、`get_pyramid_multipliers` 与已有规划对比，找一个可研究的 Region/Category 空位。已提交组合的 diversity 与未提交批次的多样性分别记录。倍率用于候选排序，质量按现行门禁判断。0 回测。 |
| 14 · P2 | **Python Alpha 与 SuperAlpha** | 分别建立独立试验卡，先读权限、合格库存与接口能力。当前 cnhkmcp 注册的常规模拟参数缺 Python 所需 `lookback`，仓库记录 Python 暂无 Multi-Sim。SuperAlpha 先做选池预览和互补性证据，单列目标与额度。0 回测启动。 |
| 15 · P2 | **cnhkmcp 版本对拍与上游建议** | 用真实/不存在字段、空相关性响应、已知 location、年度数据和 record sets 五类样本比对当前契约与候选版本。优先评估精确筛选和可验证分页、明确的业务状态和数字 PC、启动/状态读取分离。项目侧可先在消费处明确结果边界。0 回测。 |

实现与历史对照：[字段筛选与探针](../../../../wq_research_v2/src/wq_research_v2/field_screener.py)、[WDS 字段筛选报告](../fields/stage0_wds_d1_screening_report.md)、[模拟 runner](../../../../wq_research_v2/src/wq_research_v2/sim_runner.py)、[SQLite 台账](../../../../wq_research_v2/src/wq_research_v2/ledger_store.py)、[库存复核实例](../hypotheses/unsubmitted_60d_quickwins.md)、[PC 救援队列](../experiments/sc_pass_pc_rescue_queue.json)、[QUICK 观察](../../05_平台通知与优化线索.md)、[可复用经验](REUSABLE_D1_RA_EXPERIENCE_PLAYBOOK.md)、[Python 和 SuperAlpha 预研](WQ_RULES_PYTHON_AND_SUPER_ALPHA_RESEARCH_20261126.md)。

## 四、怎么接入现有流程

1. **首轮做四个小验证。** 01、02 用本次复现快速补证；03 增加一次可分页的字段对照；06 和 07 共用少量既有 Alpha 做诊断与库存复核。输出每个样本的证据、状态、下一步。05 已有 runner 和台账实现，按实际恢复异常安排回放。
2. **通过后做一轮因子研究。** 从 08 的候选数据集确定一个经济假设，先用现有结果判断是否需要探针。或从 10 选一个明确的 Stage 3 瓶颈，二者各自记账。每批记录母版、设置、唯一变量、真实消耗的额度、未观测项和阶段转化。
3. **有重复需求再固化 Skill。** 从 `wq-d1-closed-loop` 加「字段验真」「Alpha 诊断」「批次复盘」三个按需参考入口。正文只存触发条件、输入和输出。字段/检查语义留在已有模块，自动生成的台账继续通过对应程序产出。
4. **统一判断试验值不值得继续。** 0 回测方向看误判数、缺失率和人工复核时间。回测方向看每百条有可归属结果的 FULL 带来的终检候选数，同时报告实际消耗、未观测比例、最终 Margin 和证据完整度。以同母版或等风险基准作对照，达不到预先写定的目标就按本项目止损规则收口。

### 执行约束

- cnhkmcp 的 `create_multi_simulation` 契约为 2–8 个表达式、同组 settings，工具说明为等待全部完成且可能超过 8 分钟。当前注册参数没有 `simulationMode`。Stage 1–2 的 QUICK、跨 settings 对拍、后台恢复和正式批次继续走现有 runner。旧指引的论坛工具名称与当前注册接口有差异，按实际可用接口查阅。
- 新试验严格 D1，并按 AST 和现行禁用算子规则校验。RA 与 PPA 独立。按当前 `AGENTS.md` 执行严格 SC/PC 门槛、池内正交和 Margin 优先。旧冻结手册中的 PC 豁免和替补打标语义仅用于读历史。
- 新回测需要明确授权和预算。429、5xx、超时或缺子 ID 后按现行规则只读对账一次，仍不可归属则落 `RESULTS_UNOBSERVED`。后台试点沿用现有广州资源限制。标签和别名写入须显式确认，Alpha 提交保留人工流程。
- 本次实试覆盖单次注册契约、单个字段坐标、一个历史 Alpha 以及本机离线样本。平台试查均为只读，新增回测为 0，业务代码和 Skills 文件未编辑。

规则真源：[项目 AGENTS.md](../../../../AGENTS.md)、[四阶段配置](../../workflow/d1_4stage_pipeline.json)、[冻结基准 JSON](../../workflow/d1_ra_baseline_v1_frozen.json)。
