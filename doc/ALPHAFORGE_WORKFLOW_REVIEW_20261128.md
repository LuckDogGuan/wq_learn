# AlphaForge 参赛文章摘记与 D1 流程优化建议

整理日期 2026-11-28。原文《AlphaForge：0成本云端 7×24 无人值守「每日 3+1」》由 YL96878 撰写，微信公众号「BRAIN智能助手」于 2026-11-23 发布。已从公开页面的正文节点读取并按章节整理。文中的平台表现来自作者披露。本文仅供评估，建议均未实施。 [公众号原文](https://mp.weixin.qq.com/s/7ggOI_oE5uD68S3R1nTA7w)

**最值得借鉴的是把规则放到实际执行入口，并把失败原因和批次证据传回原研究方向。** 仓库已有 systemd、SQLite、表达式校验、跨会话交接和轻量巡检。优先用历史数据验证两条已有明确现场证据的偏差：4500 常规回测完成前误切 Alpha0，以及重启后再次发出已完成一次对账的未观测指纹。其次评估同族失败反馈、候选库存和投入口径。 [当前状态快照](../docs/agents/CORE_STATE.json) · [巡检任务配置](../goal/run_config.json)

## 一、文章内容摘记

| 原文章节 | 设计与经验 |
| --- | --- |
| §1 核心设计 | 作者受账户 30 日提交数、单库 ATOM 占比、Pyramid 广度和 SuperAlpha 库存约束，将目标拆成 PPA、Pure ATOM、Pyramid/主题 RA、SuperAlpha 四槽。文章报告 PPA-first 403、规则长文截断、并发 429，以及 Pure ATOM 因近两年 Sharpe 反复卡关。作者按自身账户设定 ATOM 恢复模式，非 PPA 槽通过提高算子或字段数量避免进入其观察到的 PPA 路由。 |
| §2–3 角色与反馈 | Azure Linux VM 上的 systemd 调度器按美东日核对 OS，拉起主控。主控负责额度、候选终检和持久化，研究子代理最多同时两组。业务层以事件唤醒和串行 Check 组织。Pure ATOM 前两批不达标时，第三批转另一目标的双库 RA。PC 失败时把数值和拥挤归因传回原子代理，暂停同族重复送检。配套设计包括失败冷却续跑和模型订阅接力。 |
| §4 MCP 与运行工具 | 交互研究使用 MCP 读字段、数据集、公告、详情和已存 Check，也用 selection 预览 SuperAlpha 候选池。云端运行用受约束的 CLI 并共享认证会话。作者用 PreToolUse 管住工具入口，减少空转轮询、重复鉴权和绕开检查脚本的调用。 |
| §5 技能与知识 | 批量回测、表达式 AST 校验、本地 PnL 自相关、PPA 专项、字段质量和记录归因由专项技能覆盖。知识按精简常驻规则、跨日交接、分类模板索引和实战复盘四层加载。24 KB 左右截断来自作者当时的加载器，≤18 KB 是其自定上限。 |
| §6 Harness 与运维 | 主控运行在 Antigravity CLI。Python 守护进程配合 SQLite、日志事件、移动 Web 状态页、审批模式与停机控制，提供备份与运行可见性。作者将检测到验证码视作人工介入点。 |
| §7–8 实测与待改进 | 作者以平台回读 `stage == "OS"` 确认交付，记录到日内漏斗、运行时长和 Token。复盘重点包括低 localSC 仍可能高 PC、频繁鉴权、规则截断和空转。后续设想是用历史失败预测 PC 拥挤、统计单位产出的 Token 成本，以及巡检 SuperAlpha 组件池健康。 |

章节和两张流程图见 [公众号原文](https://mp.weixin.qq.com/s/7ggOI_oE5uD68S3R1nTA7w)。图 1 回看调度、主控、研究与 Check/OS 的分工，图 2 回看单槽迭代、失败分流和换向。

### 产出数字及其口径

| 观察窗口 | 作者披露结果 | 对比时的口径 |
| --- | --- | --- |
| 10-30 至 11-14，16 个自然日 | 62 篇 OS。Regular 31、SuperAlpha 16、PPA 15。单库 ATOM 17 篇，含 PPA+ATOM 重叠。 | ATOM 是交叉属性，17 不再加到 62。OS 以平台状态回读为准。 |
| 11-07 至 11-14，云端 8 天 | 30 篇 OS。11-08 至 11-14 连续 7 天每日 4/4。最快 11-08 美东 00:25 至 04:19，用时 3 小时 54 分。 | 云端窗口包含在前一行。4/4 是作者的日交付口径。最快单日是单个样本。 |
| 11-01 至 11-13 | 4,477 次仿真、54 篇正式提交。11-13 单日 426 次仿真、4 篇正式提交。 | 有别于 16 天 OS 窗口。未提供全部新仿真与 OS Alpha 的逐一谱系，无法把 54÷4,477 作为新回测的转化率。 |
| 11-07 至 11-14，44 次运行 | 59.73 小时。约 1,942 万输入、140 万输出、1.81 亿缓存读取 Token。 | 三类 Token 分列。标题中的零现金成本依赖云服务优惠与订阅试用。文章披露的基础收益为全账户统计，新增 62 篇的独立收益尚无归因。 |

文章报告的账户和日志侧数字没有独立复算。本仓库冻结手册的 `4,893 FULL/天` 是回测吞吐，近期 T17 的 15,193 条任务是另一个记录范围内的 6,865 FULL 加 8,328 QUICK，均应单列。 [公众号原文 §7](https://mp.weixin.qq.com/s/7ggOI_oE5uD68S3R1nTA7w) · [冻结基线手册](../docs/整理与研究/workflow/D1_RA_BASELINE_V1_MANUAL.md) · [T17 记录](../docs/agents/TODO_20261127.md#L111)

### 三个案例应该学什么

- **低 localSC 仍会撞 PC。** 作者的 `6XMv1QW7` 披露 localSC 0.507、PC 0.7303。封存 18 个同族候选后，改写所得 `bla5bXVp` 披露 PC 0.5952 并入 OS。字段、融合结构等同时改变，单例支持「保留失败证据并换向」这一做法，无法量化任一改动的独立贡献。其多源乘积表达式与本仓库算子禁令冲突。 [公众号原文 §7–8](https://mp.weixin.qq.com/s/7ggOI_oE5uD68S3R1nTA7w) · [项目红线](../AGENTS.md#L7)
- **双标与额外路线有各自的适用范围。** `YPaXn39W` 是作者在 GLB D1、`model250` 上报告的 PPA+ATOM 双标案例。`A1xqvXPw` 是德国区修复 2023 IS Ladder 的个案，`1YW6zewQ` 是台湾小池 SuperAlpha 个案。三者对应不同目标与规则，适合做后续定位线索。 [公众号原文 §7](https://mp.weixin.qq.com/s/7ggOI_oE5uD68S3R1nTA7w)

## 二、按优先级保留的建议

以下验收均为提议。P0 先用离线样本或已有巡检留档回放，预计新增回测预算为 0。新因子实验在另行安排时再确定预算。

| 优先级 | 建议与本地落点 | 最小验证与取舍 |
| --- | --- | --- |
| P0 | **复核额度切换和重启去重。** 11-28 快照记载，常规仅完成 3,384 条时发出了 8 条 Alpha0，另有 8 个已对账未观测指纹在重启后重发。沿现有 daemon、runner、ledger 检查发送入口与台账终态。把本地已有的 429 再 POST 分支列进同一回放，单独核对生产是否使用该分支。 | 回放低于/达到 4500、常规队列暂空、重启、429/5xx/超时/缺 ID。验收低于阈值违规发单 0 次，已终结指纹重发 0 次，`COMPLETED_FULL` 覆盖 0 条，失败指纹至多一次只读对账。先验证真实发送路径，复用已有 AST 与指纹。 [巡检快照](../docs/agents/CORE_STATE.json#L194) · [额度选择](../wq_research_v2/src/wq_research_v2/daemon_ra_runner.py#L1283) · [指纹去重](../wq_research_v2/src/wq_research_v2/ledger_store.py#L284) · [429 分支](../wq_research_v2/src/wq_research_v2/sim_runner.py#L415) |
| P0 | **把平台日与漏斗口径对齐。** 沿用美东平台日、额度响应头和按 `sim_tasks` 汇总的巡检。分别记录 NORMAL/Alpha0、QUICK/FULL、已排队/在途/待对账/未观测、实证通过终检和平台 OS。人工操作后的 OS 用平台回读确认。 | 用有混合完成类型和待判项目的历史日对账。按 alpha ID 去重，明确来源时间与未观测数。验收重复计数为 0、没有证据的结果不计作通过。T02 的缺失 PC 直方图与 T03 的 2Y/Ladder 仍沿既有工作项复核。 [巡检配置](../goal/run_config.json#L44) · [既有事项](../docs/agents/TODO_20261127.md#L96) |
| P1 | **把失败返回给原方向。** 复用交接模板和优化台账。每次留一个母版、目标 Region/Universe、截图或响应来源、主失败项、数值、已试变量及下一条可证伪假设。数字 PC 已过线、已高于门槛与待判分开。S3-r33 ASI 双过 Robust 却仍卡 JPN，以及 EUR 低 PC 却卡硬检，是本项目可回看的反例。 | 回放 ASI、EUR 两个历史失败批和一组低 localSC/高 PC 样本。验收每个方向能复述上轮结论、辨认同簇重复变体，并只提出一条待验证的修复轴。相似结构只辅助排序。全硬检、SC、正交和 PC 均过线后仍按 Margin 排优先级。 [交接模板](../docs/agents/SUBAGENT_BRIEF_TEMPLATE.md) · [优化台账](../docs/agents/OPTIMIZATION_LEDGER.json#L417) · [PC 查询](../wq_research_v2/src/wq_research_v2/pc_poller.py) |
| P1 | **为研究方向预留换向预算。** 借鉴前两批卡同一问题就改方向的思路，放进现有 2 小时复查。先判断是近 2Y、地区子检、Fitness、集中度还是 PC。已有记录报告，ASI `price_signal_dl` 的 QUICK 信号在 FULL 明显下降，USA 和 EUR 的多个初筛方向已触发早停，可用来辨别何时继续。 | 先看历史批次，在相同 Region/Universe、门禁与母版下比较继续迭代和转新数据集的新增合格数、重复变体和 FULL 消耗。待判与平台故障排除在失败归因之外。批数由已有证据和预算决定。 [D1 闭环技能](../.agents/skills/wq-d1-closed-loop/SKILL.md) · [优化台账](../docs/agents/OPTIMIZATION_LEDGER.json#L400) |
| P1 | **按目标归因 PPA-first。** 在现有 RA/PPA 独立分支的诊断中保留唯一算子/字段计数、项目已知豁免、目标及平台实际返回项。403 和页面单行 `Prod Correlation FAIL` 各自保留来源。 | 回放正常 RA、PPA-first、主题/描述失败与空体待判。逐条对照原始检查，能确认的才归因。作者账户上的 403 行为与 ATOM 2Y 门槛适用范围有限，后续查证时按当期公告和实际地区核对。 [项目 PPA-first 记录](../AGENTS.md#L23) · [RA evaluator](../wq_research_v2/src/wq_research_v2/ra_evaluator.py) |
| P1 | **巡检加入实际进度与交接耗时。** 现有广州巡检已有 systemd 状态、资源和 SQLite 计数。可评估加最近成功完成时间、最老等待时长和重启后首次完成时间。跨会话沿用 `CORE_STATE`、`OPTIMIZATION_LEDGER`、交接模板与按需查日志。 | 离线回看进程存活但批次不推进、队列耗尽、正常完成三类快照。比较定位所需时间、读取文件或 Token、统计缺项。沿用现有长任务检查节奏和资源限制。文章的 60 秒轮询和加载器字节限制仅作背景。 [广州巡检](../scripts/ops/check_guangzhou_v2.py#L32) · [任务时长与巡检](../goal/run_config.json#L25) |
| P2 | **给 Pyramid 人工复核准备三主一备。** 试取最近同一平台日的合格库存，按 Pyramid 空位、高 Margin、池内去重和证据时点挑备选。一主方向缺货时，用不同簇中的备选。报告实际可用数和缺口。 | 用历史库存分别生成现行复核清单和三主一备清单，对比家族重复率、可用类别覆盖、候选过期和人工核查时间。三主一备只是一种清单编排，不对应日提交配额、PPA/SA 槽或运行线程。 [当前主线](../docs/agents/CORE_STATE.json) · [库存复核建议 07、13](../docs/整理与研究/records/rules/CNHKMCP_WORKFLOW_SKILLS_OPTIMIZATION_20261126.md) |
| P2 | **用历史数据评估拥挤提示与单位产出。** 先按同 Region/Universe 的字段家族、AST 结构、中性化和既有 PC 结果做透明排序，记录每个方向的有效回测、终检样本和耗时。若已有模型日志，再补输入、输出、缓存 Token。 | 选历史段归纳特征、后段留出验证，以现行筛选为对照，记录少送检多少已知高 PC 候选、同时漏掉多少最终过线或高 Margin 候选。证据不足即保留未知，仅用于人工排序。SuperAlpha 组件池健康可留给独立路线做只读盘点。 [文章 §8.3](https://mp.weixin.qq.com/s/7ggOI_oE5uD68S3R1nTA7w) · [PC 救援记录](../docs/整理与研究/records/experiments/sc_pass_pc_rescue_queue.json) |

## 三、与现有流程对齐的执行口径

- **研究阶段。** Stage 1–2 的 QUICK 仅用于快筛，Stage 3–4 用 FULL，每轮 1–2 个控制变量。一个方向是否值得投入，用同坐标的配对或完整历史批次衡量。遵守禁用 `add`、`multiply`、`trade_when` 的规则，双支继续按现行 `min(rank(A), rank(B))` 或其 `reverse` 处理。 [项目红线](../AGENTS.md#L7) · [四阶段配置](../docs/整理与研究/workflow/d1_4stage_pipeline.json)
- **交付与实验终点。** D1 RA 交付遵循硬检 0 FAIL、`SC < 0.65`、池内正交 `<0.68`、`PC < 0.70` 和条件相同时 Margin 优先，PPA 独立判断。T17 的模板对照只记录 PC，仍应单独统计。项目保留人工提交，文章的自动提交、每日定额与自动重投不适用。 [现行规则](../AGENTS.md#L8) · [T17](../docs/agents/TODO_20261127.md#L111)
- **后台运维。** 沿用现有 SQLite 和低内存 systemd 方案，遵守广州 `MemoryMax=512M`、GLB 至多 3 线程、其他地区至多 4 线程、现有认证刷新和 WAL 管理。文章的 Azure 迁移、Web 控制台、账号接力和 12 次续跑服务于其自身架构。 [项目后台约束](../AGENTS.md#L12) · [广州巡检](../scripts/ops/check_guangzhou_v2.py)

建议后续先做两个 P0 的同一份历史窗口回放，再从 P1 选一个方向小范围验证。量化收益以每百条有结果 FULL 带来的实证终检候选数、同族重复消耗、误计数和人工核查时间评估。同步报告绝对样本数、待判比例与最终候选 Margin。

## 四、来源与检索记录

- 公众号页面的标题、作者、发布时间和正文均已取得，表格和章节摘记依据该页面。本文在项目 `doc/` 下保留正文的结构化摘记与原文链接。 [公众号原文](https://mp.weixin.qq.com/s/7ggOI_oE5uD68S3R1nTA7w)
- BRAIN 论坛使用 `cnhkmcp.search_forum_posts` 查询。`AlphaForge` 返回 0 条，`Alpha Agent Workflow`、`设计大赛`、`YL96878` 返回 `[Errno 22] Invalid argument`。按标题、作者和关键词核对近期 100 条站内通知也未命中。论坛对应帖的 ID、正文版本和评论均未核实。
- 项目侧依据 2026-11-28 的检查快照、当前工作树源码和已有研究记录。历史基线与当前规则发生差异时，按当前规则解释。 [当前状态与已知偏差](../docs/agents/CORE_STATE.json) · [既有调研](../docs/整理与研究/records/rules/CNHKMCP_WORKFLOW_SKILLS_OPTIMIZATION_20261126.md) · [项目规则](../AGENTS.md)
