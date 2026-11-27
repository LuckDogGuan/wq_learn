# WorldQuant BRAIN 仓库瘦身评估

2026-11-27 · 盘点基准 `e939645`

这个仓库同时承担 D1 研究、广州运行维护和历史证据查阅。当前主要负担是每轮加载重复文档、同一证据有多个实体副本，以及新引擎仍要区分哪些旧代码和历史批次可调用。**我的排序是先减日常加载和检索范围，再处理已证实的物理副本。** 如果目标是马上释放本机磁盘，优先级换成可重建的 GitNexus 索引。 [工作区说明](../README.md#L1) · [三条研究路线](TRACKS_AND_LOGS_GUIDE.md#L8)

## 体积和边界

| 口径 | 实测 | 对决策的意义 |
| --- | ---: | --- |
| 本机工作树 | **约 1,760 MiB**，不含 `.git` 和凭据目录 | 文件逻辑大小，包含本地数据、图片和索引。 |
| `legacy_core/Core/runtime_data/` | **1,308.08 MiB，1,532 个文件**，约占工作树 74.3% | 硬保护历史日志、数据库及状态。当前 Git 跟踪文件数为 0。 |
| `.gitnexus/` | **248.11 MiB** | 本机可重建索引，占工作树约 14.1%。当前索引落后于 HEAD。 |
| `docs/` | 本机 **88.98 MiB**，HEAD **20.92 MiB** | 课堂目录本机占 **86.60 MiB**，是本机资料和当前 Git 树里最明确的去重候选。 |
| `WebDataScope-1.0.6/` 和 `data/` | 本机分别 **36.77 MiB / 28.22 MiB** | 前者提供 Stage 0 离线字段来源，后者包含 SQLite、PnL 缓存、日志和派生导出。 |
| HEAD 当前 Git 树 | **54.13 MiB，1,372 个路径**，按唯一 blob 计 **43.75 MiB** | `reference/` 占 **18.90 MiB**，为硬保护参考库。`wq_research_v2/` 仅约 **0.64 MiB**。 |
| `.git/` | 本机 **14.28 MiB**，对象 pack **8.61 MiB**，松散对象 **5.41 MiB** | 当前已压缩历史较小。旧版本独有 blob 的逻辑大小约 **5.80 MiB**，压缩后约 **1.79 MiB**。历史重写的空间收益有限。 |

以上口径分别对应文件长度、`git ls-tree -r -l HEAD`、`git count-objects -vH` 和本地 refs 的对象枚举。`runtime_data/`、`reference/`、日志与台账均按既有保护要求计入固定资产。现行忽略规则已经覆盖运行数据、数据库、图谱和 WDS。README 的 Git 约 35 MB、GitNexus 约 160 MB 是旧口径，适合换成带日期的实测值及单位。 [保护规则](../AGENTS.md#L10) · [忽略规则](../.gitignore#L21) · [README 体积说明](../README.md#L55)

## 优先减少日常负担

### 1. 启动入口只留一条，归因日志按问题加载

三文件启动口令实际 **45,228 B**，仓库 Skill 列的五个文件为 **56,547 B**，加 Skill 正文为 **64,764 B**。`OPTIMIZATION_LEDGER.json` 最新就是 **27,568 B**。AGENTS、START_HERE、HANDOFF 和 Skill 各有入口，配置、当期状态和历史案例重复出现。另有 **31 处**启动、路线和冻结手册链接固定到本机 C 盘路径。 [启动规则](../AGENTS.md#L42) · [闭环 Skill](../.agents/skills/wq-d1-closed-loop/SKILL.md#L12) · [交接指南](agents/HANDOFF_GUIDE.md#L12)

**建议**　把规则、配置和当期状态分别留在已有责任文件里，客户端入口指向同一个仓库入口。每轮主动读取当期路线、生效范围、最近一两条结论和可回查的案例 ID。完整优化账本、地区档案和原始日志通过相对链接查看。`batch_audit_latest` 已由同一个 SQLite builder 导出，短入口只指向日期、批次或候选 ID。 [批审导出](../scripts/ops/export_guangzhou_batch_audit.py#L17) · [历史批次台账](整理与研究/records/experiments/batch_audit_ledger.md)

**验收**　分开量自动注入的指令和每轮主动读取量。在另一检出路径回查三条路线、同一批的原始状态和两个历史案例。优先复核同一配置的计划值与实际生效值，当前守护进程声明了 `--goal-config`，随后仍从其他 CLI 参数组装运行配置。 [入口参数](../wq_research_v2/src/wq_research_v2/daemon_ra_runner.py#L1954)

### 2. 让当前队列和历史重放各有明确入口

代码布置比代码体积更需要瘦身。当前离线构造得到 **2,169 个初筛规格和 210 个精修规格**。精修入口串起多轮旧实验。历史批次与当前候选一起进入默认构造，后续仍要靠台账识别已完成任务。 [初筛构造](../wq_research_v2/src/wq_research_v2/daemon_ra_runner.py#L1282) · [精修构造](../wq_research_v2/src/wq_research_v2/stage23_refiner.py#L1291) · [历轮 PC 实验](../wq_research_v2/src/wq_research_v2/pc_breakout_lab.py#L1676)

**建议**　仅把已经台账确认完结的旧实验移出默认待办，保留原规格和显式重放入口。旧定时提交脚本仍可到达 POST 提交方法，适合从可执行导航中退役并保留历史审计索引。本地仓库能证明代码路径，外部任务是否仍指向它要按实际部署另核。只读核查与有现行手册的 SPC 工具各自保留入口。 [旧定时入口](<../scripts/ops/定时提交因子/schedule_submit.py#L105>) · [旧提交实现](../legacy_core/Core/api/submission.py#L312) · [SPC 维护入口](official_guides/SPC_SUBMISSIONS_API_REFERENCE.md#L97)

**验收**　核对原 `batch_id`、任务指纹和 settings。对账中与未完成批次仍可续跑，`COMPLETED_FULL` 仍受保护。Stage 0 还从 `legacy_core/Core/tools/webdata_quality` 动态加载 WDS 逻辑，历史合并也实际读取旧证据。按入口处理，避免一次移动整个 `legacy_core/`。 [WDS 适配器](../wq_research_v2/src/wq_research_v2/wds_adapter.py#L48) · [旧数据读取](../wq_research_v2/src/wq_research_v2/legacy_merger.py#L465)

## 有明确实物依据的体积收益

### 3. 课堂原始证据保留一份，详细版和 GPU 版共用链接

三处 `原始转录/` 都有同样 53 份文件，文件名、Git blob ID 和本机 SHA-256 均一致。三份 `画面回看索引.txt` 也同哈希。保留一份实体后，当前 Git 树可少 **108 个路径、10,884,406 B（10.38 MiB）**，约为当前逐路径体积的 **19.2%**。Git 已对相同 blob 去重，收益主要体现在工作树体积和搜索结果。两版各自的讲解、摘要和原始转录完整保留。 [课堂入口](顾问课堂视频总结/README.md) · [图文详细版](顾问课堂视频总结/详细版/README.md) · [GPU 版](顾问课堂视频总结/GPU逐段详解/README.md)

本机 **503 张 JPG** 还发现 **124 组内容完全相同**。按哈希保留每组一份，最多减少 **127 个副本、17,865,521 B（17.04 MiB）**。这些图片和三份 CSV 索引未被 Git 跟踪。图片瘦身属于本机证据归并，应先确认原片索引和两版路径都能访问同一份截图。 [画面回看说明](顾问课堂视频总结/README.md#L13) · [媒体与数据忽略规则](../.gitignore#L40)

**验收**　先把两版 **106 条转录链接**及 GPU 版 **53 条索引链接**指向同一原始目录。更改前后逐条对照路径和哈希。图片如果另做一项，再对两版 503 个引用目标校验可读性。空检出环境要能定位 Git 之外的图片与 CSV 来源。

### 4. GitNexus 按需重建，磁盘收益单独计算

图谱目录 **248.11 MiB** 中，主索引约 **221.02 MiB**，其余主要是解析缓存。当前注册索引在 `eabad15`，工作区在 `e939645`。对于磁盘紧张或多检出的场景，可先选一个工作检出保留热索引，闲置副本到需要时再重建。约 **248 MiB** 是这一个索引在磁盘上的可回收上限，重建后还会占用空间。小型 Python 和测试缓存合计仅约 **1.6 MiB**，处理优先级较低。 [缓存忽略规则](../.gitignore#L74) · [仓库 Git 约定](../README.md#L55)

**验收**　批准清理某个索引前，记下对应工作区与当前注册关系。重建后确认索引指向当前提交，并用同一条查询核对 WDS 路径或 Stage 0 调用关系。

### 5. 论坛审计大件与 Notebook 输出等可复核后归档

`forum_blocks.json`、`unvalidated_blocks.json` 和 `full_scan_manifest.json` 三个已跟踪产物合计 **5,801,058 B（5.53 MiB）**。生成器和历史审计仍为它们提供出处。`admin_verified_catalog.json` 另有约 **1.27 MiB**，旧加载器和分类生成器确实读取。两份已忽略的论坛压缩包保存的是不同证据集合。 [扫描产物生成](../legacy_core/Core/tools/forum_template_audit.py#L402) · [审计保留说明](../legacy_core/Core/factor/templates/forum_catalog/quarantined/README.md#L3) · [模板加载器](../legacy_core/Core/factor/templates/forum_verified.py#L17)

**建议**　优先验证前三份原始证据能否从同一归档定位，再决定是否让主分支只保留索引、生成方式和摘要。分类展示是逻辑派生，缩减前先验 224 个模板的 ID、表达式、分类和来源一致。`staging/` 三本 Notebook 内嵌输出约 **1.17 MB**，两条生成路径仍依赖旧 WDS 版本。先留可检索的结果，并验证重建输入，再决定是否精简内嵌输出。 [分类生成器](../legacy_core/Core/tools/classify_forum_templates.py#L26) · [分类验收](../tests/unit/test_admin_catalog.py#L29) · [WDS Notebook 生成器](../staging/analysis_tools/wds_insights/generate_wds_ipynb.py#L33)

**验收**　归档条目按原提交、文件名与 SHA-256 可检索，抽查原帖、模板、审计结果和 Notebook 图表能对应。计划节省的是当前工作树或 HEAD 路径体积。压缩历史与新克隆传输量另测。

## 建议取舍

日常维护先选 **1**，Git 树与检索先选 **3**，磁盘紧张先选 **4**。**2** 减少旧入口误用和重复构建，按一个已完成批次做小范围对照即可判断可行性。**5** 等证据恢复路径验证后再决策。广州外部调度、历史任务的在线状态和服务器截图访问权限均需各自核验。与阶段门槛和双 2 相关的研究判断见 [D1 闭环复核](D1_CLOSED_LOOP_REVIEW_20261127.md)。

