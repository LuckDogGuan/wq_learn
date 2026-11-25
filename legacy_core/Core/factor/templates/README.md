# 模板来源、适用边界与验证状态

审计日期：2026-10-12。本文依据本地保存的论坛正文、评论与当前实现；没有调用平台模拟，也没有确认当前账户算子权限或任何收益指标。按用户最新指令，管理员模板目录供 Core 与 `/root/worldquont/爬山代码` 使用；RA 禁止模板轮动，RA 的持续检测、参数设置和批次任务由其自身入口负责。本审计没有部署或平台写操作。

## 管理员分发的七个模板

`admin_distributed.py` 保留经济机制，并收窄到同一数据集中的 1–2 个字段。全部验证状态为 **UNVALIDATED**：其中六个注册为可轮动研究方向，PEG 保护版本登记 `enabled=False` 并隔离保存。可轮动项只有通过当前字段元数据、权限、语法及复杂度检查后，才可以在已授权目标内进入 8 路批量实验。代码生成成功不表示 `PPA_PASS`。

下表中的调用数仅是当前字符串的函数调用次数，不是平台 operator count。实现已增加 `operator_count`，保守统计函数及算术、比较、逻辑符号，并在管理员候选生成时执行总数 `<6` 检查；裸字段版本六个启用模板总数分别为 4、2、4、4、4、2，PEG 为 8。字段预处理包装还会增加复杂度，实际平台结果仍需确认。

| 实现 | 管理员分发帖 / 本地文件尾部编号 | 保留的机制 | 本地改编与适用条件 | 函数调用数 |
| --- | --- | --- | --- | --- |
| `profit_to_size` | [Machine Alpha 基础知识2](https://support.worldquantbrain.com/hc/zh-cn/community/posts/25066216209687) | 盈利/规模比率相对自身历史的位置 | 固定为 `ts_rank`，默认 66 日；增加规模 `>0` 的 NaN 防护。利润与规模必须同口径，销售额、资产、市值的经济意义不同。时序排名衡量历史位置，不直接证明利润改善或未来收益。 | 2 |
| `net_sentiment` | [Machine Alpha 基础知识3](https://support.worldquantbrain.com/hc/zh-cn/community/posts/25066287753367) | 正负情绪之差的时间序列比较 | 固定为 `ts_rank`，默认 22 日；省略原文可选的回填和截面排名。两侧必须同覆盖范围、同单位、同方向编码。正净情绪与高历史分位不是同一命题；零值与缺失值不可互换。 | 1 |
| `term_structure` | [Machine Alpha 进阶知识3](https://support.worldquantbrain.com/hc/zh-cn/community/posts/32092606398999) | 同指标不同预测期限的行业标准化差异 | 保留正文 `group_zscore/subtract/group_zscore` 骨架；两侧采用相同分组。同指标、同频率、同单位，禁止把季度 EPS 与年度 EPS 随机相减。`fy/fp` 名称规则只是初筛，还需元数据确认。符号为近期减远期，不等同于增长率。 | 4 |
| `dupont_difference` | [Machine Alpha 进阶知识4](https://support.worldquantbrain.com/hc/zh-cn/community/posts/32198029389207) | ROE 与利润率时序标准化后的行业内差异 | 固定相同 66 日窗口和行业分组。这不是完整杜邦分解，也不是资产周转率或杠杆的精确估计；ROE 与利润率须财报周期、预测/历史口径一致。 | 4 |
| `peg_relative_value` | [Machine Alpha 进阶知识6](https://support.worldquantbrain.com/hc/zh-cn/community/posts/32495294399895) | PEG 的行业内相对估值 | 输入现成 P/E 和增长字段，增加 P/E、增长均为正的 NaN 防护。增长 20% 的字段可能编码为 20 或 0.2，绑定前必须统一口径；行业 zscore 中常数 `-1` 本身不改变正常样本的标准分数。保守总算子计数为 8，已 `enabled=False` 隔离，不进入轮动。 | 3 |
| `group_residual` | [Machine Alpha 基础知识5](https://support.worldquantbrain.com/hc/zh-cn/community/posts/25329078901911) | 字段对同组均值的时序回归残差 | 保留 63 日回填、winsorize 和 252 日回归；将原帖 `log(ts_mean(cap,21))` 权重改为常数 1，避免额外经济字段。等权结果不继承市值权重表现。组均值包含自身，稀疏组、近常数序列和过度回填可能削弱残差信息。 | 4 |
| `group_beta` | [Machine Alpha 基础知识6](https://support.worldquantbrain.com/hc/zh-cn/community/posts/25526497127959) | 字段相对于同组另一字段均值的回归斜率 | `rettype=2` 保留斜率机制；改为等权组均值，省略原文双侧回填/修剪。只有两字段明确共享 `relation_group` 且同一数据集才绑定；斜率量纲取决于输入，普通字段斜率不能称为股票收益 CAPM Beta。 | 2 |

七帖的本地原始证据位于 `D:/code/WorldQuant Brain/管理员论坛爬取资料/WL13229/自己发布的帖子/`。标题筛选副本保存在原帖根目录的 `模板/20261012_管理员模板审计/`，副本保持相同相对路径；完整源路径及 SHA256 见该目录的 `标题筛选与来源清单.json`。原始帖禁止修改、删除。

出处只证明分发或译介关系。期限结构、杜邦、PEG 三帖正文分别注明英文原文 27963407565975、28298364912151、29985532824343；不能称为 WL13229 独立原创。其余四帖只确认本地帖头作者为 WL13229，不据此推定思想原创。帖子评论必须按评论作者归属：例如杜邦帖评论 #1 是 DX67257 的跨数据集例子；期限结构帖对 `oth455` 窗口的推断来自 LL87164，管理员肯定评论不等于核实字段定义。

## 合集正文与评论核对

| 资料 | 核对结果与使用边界 |
| --- | --- |
| [模板大师](https://support.worldquantbrain.com/hc/zh-cn/community/posts/24957813446167) | 正文明确说明是收集总结，并提醒严重 overfitting 风险；感谢所有作者。评论 #1（MQ62208）指出 `ts_rank(vec_avg({Fundamental}))` 缺少窗口；给出的修正仍含中文逗号，必须重新解析。不能将所有合集公式计为管理员原创或可直接运行模板。 |
| [可以尝试使用的 Alpha 模板](https://support.worldquantbrain.com/hc/zh-cn/community/posts/26054361848343) | 同样是合集而非收益认证。含禁用 `trade_when/add`、括号缺失、反斜杠转义、缺少语句分隔符、多数据源和较深嵌套；财务系列正文提醒复杂表达式、500 日回归、披露时点口径和过拟合风险。评论 #21（LW67640）建议减少算子和字段，不能将建议当作已经达标的证据。 |
| [模板大师2：GPT 增强版](https://support.worldquantbrain.com/hc/zh-cn/community/posts/26898478786711) | 正文明确社区共建及大模型优化，要求自行考察合理性。人工模板、GPT 输出必须分别归档；例如 GPT 输出使用 `ts_rank(..., group)`、额外字符串参数和禁用 `trade_when/add`，不能照抄。技术指标 ROC 示例使用未定义 `c`，需语法和语义修正。 |
| [模板大师3：GPT 增强补充](https://support.worldquantbrain.com/hc/zh-cn/community/posts/28107291019031) | 主要公式位于 WL13229 评论中，不在正文。包含概念字段、多信号组合、无法直接执行的说明文本；评论 #14 的同表达式相减为零，#19 使用禁用 `add`，#20 对利润率开平方的量纲解释不严谨，不能以“合理/合法”文案代替数据域与平台验证。 |

目录关系 `ADMIN_AUTHORED/ADMIN_REPLIED/LINKED_POST` 仅记录帖子存放关系，不代表其中每个代码块的原创作者。`BODY/COMMENT` 仅记录所在章节；当前目录未逐块解析评论作者，因此评论来源需返回原帖相应行核实。

## 论坛代码目录及旧实现登记

`forum_catalog/inventory_summary.json` 当前记录：原帖 2598 篇，筛标题复制 411 篇，正文与评论围栏代码 7101 块，按规范化空白后的文本去重 3768 块，其中 1113 块 `UNVALIDATED`、2655 块 `EXCLUDED_STATIC`。这些是代码块盘点数量，不能当作完整可轮动模板数、管理员原创模板数或经济机制多样性数。非围栏公式与纯概念不在代码块数量中；去重也不会合并改写后等价的公式。

| 原有实现 | 登记状态 | 证据与处置 |
| --- | --- | --- |
| `forum_advanced_solutions.resolve_reversion_component` | `IMPLEMENTATION_PLACEHOLDER` | 两个策略分支均 `pass`，最终返回原输入，属于 no-op；不得记为反转警告已修复。保留文件。 |
| `forum_advanced_solutions.apply_rank_by_side_and_diff` | `PERMISSION_UNVERIFIED` | 当前代码注释记录账户无 `rank_by_side` 权限；本次未查询平台，不能当作当前权限已实证。恢复可用前应隔离轮动，文案所述 Sharpe/Margin 改善均待验证。保留文件。 |
| `pc_control.pc_control_rank_by_side_wrapper` | `PERMISSION_AND_SIGNATURE_UNVERIFIED` | 代码自身标注“无效”，并把 group 字符串传给 `rank_by_side` 第二参数；本地 validator 将第二参数登记为数字。需实时权限与参数签名验证，不因在本地定义中出现而放行。保留文件。 |
| `forum_advanced_solutions.inner_group_neutralize_with_outer_ram` | `SETTINGS_NOT_APPLIED` | 返回建议设置字典，不会自动将 CROWDING/RAM 写入模拟参数；需调用方明确应用且记录。不能宣称风险中性化结果已通过。 |
| `forum_advanced_solutions.optimize_japan_robustness_sharpe` | `SINGLE_DATASET_UNVERIFIED` | 额外引入 `returns`，与任意 fundamental 输入未必同数据集；局部收益经验不能外推 GLB。需重新绑定字段、检查复杂度与完整门槛。 |

详细隔离分类和静态扫描局限见 `forum_catalog/quarantined/README.md`。缺少结果、认证错误、超时、429/5xx、响应不完整只能登记 `PENDING/RESULTS_UNOBSERVED`，不能算有效失败样本或触发字段 200 次淘汰；语法错误独立为 `SYNTAX_ERROR`。没有本次实时硬门槛及生产相关性证据时，禁止标记 `PPA_PASS/READY_TO_SUBMIT`，提交始终由用户手动执行。

## 全量单字段合规目录

`admin_verified_catalog.json` 是扩展扫描后的严格目录，顶层包含 `schema_version/status/coverage/templates`。只有 `strict_unary` 合规检查及现有 `verify_alpha_expression` 都通过的完整表达式才进入 `templates`；它不把被排除的复杂表达式内部子式采摘为通过模板。六个具名经济模板继续保留在原注册机制中。

全量工具 `Core/tools/forum_template_audit.py --full-scan` 对原帖根目录下、排除研究副本目录的全部 Markdown 逐文件读取正文及评论，提取可识别的围栏、inline、引用行、完整普通表达式行和可解码的嵌套 JSON 模板字符串。每个研究匹配帖复制到 `模板/20261012_管理员模板审计`；逐个验收副本 SHA256，扫描后重新读取所有原帖验证源 SHA256 没有变化。全量证据见 `forum_catalog/full_scan_manifest.json`、`full_scan_summary.json`、`full_scan_fragments.json`；排除证据见 `quarantined/full_scan_excluded.json`。此前 411 篇标题筛选结果与 3768 围栏去重盘点保留，不能与新的全量片段数相加。

本次已执行结果：2598/2598 文件扫描完成，1746 篇研究匹配副本验收通过；提取 75276 个来源片段，其中围栏 38566、普通行 31532、inline 3414、引用行 1690、JSON 字符串 74。严格目录收录 224 个去重骨架、966 个合法出处实例，74310 个实例逐条保存隔离理由。全部注册式再次独立运行本地合规、AST 参数域与 ID 一致性验证通过，总算子数最大为 5；原帖 SHA256 全部未变。

224 个骨架的代表来源分别为管理员亲发正文 21、管理员亲发帖评论 38、管理员参与回复帖正文 3、管理员参与回复帖评论 10、关联帖正文 45、关联帖评论 107。这里的“管理员亲发帖评论”并不表示评论者是管理员，必须看 `source_author`；关联帖也不能称为管理员原创。这一目录是管理员论坛资料的研究来源目录，严格通过条目中包含明确标注的社区/L2 来源，不将其混称 224 个管理员原创模板。

通过项必须只有一个明确经济字段或一个明确 FIELD 占位槽，其全部出现统一替换为 `{field}`。隐藏价量字段、多字段、未绑定窗口/算子/分组占位符、局部变量依赖、未知算子、Python/NLP、根字符串、字符串拼接内的函数与字段均排除。词汇白名单取本地 validator 支持表与 `all_operator_templates.py` 函数词汇交集，并保守排除回归、VECTOR 输入算子、`rank_by_side` 及项目禁用算子。本地权限词汇记录不等于当前平台权限确认。

本地 validator 自身已检查部分参数数量和类型，但会放过零/负/小数时序窗口及数值分组等，因此另外执行 `strict_parameter_check`：时序窗口为正整数，分组为合法维度或明确合法的组构造，`group_mean` 仅接受正数常量权重；kth 的窗口和 k 为正整数且 k≤窗口，回填窗口/std、quantile driver/sigma、normalize 布尔与 limit、scale/hump/rank/tail 数值参数均有显式规则。未知签名、回归返回类型及无法确认的 `ts_returns` mode 保守隔离。赋值变量采用本帖范围的保守依赖识别，可能隔离同名但无依赖的合法示例，以避免把未展开的上游数据依赖伪装为单 FIELD。

通过项使用 `LOCAL_PASS_UNVALIDATED` 状态与 `STATISTICAL_CONTROL` 分类、`stages=[2,3]`、`field_type=MATRIX`，不给新抽象的统计变换添加未经证实的经济信号标签。来源字段包括 `source_post_id/url/relation/section/author/path/line/sha256`、表达式哈希和所有 `origins`；管理员亲发正文优先作为代表，但管理员译介、合集、评论和 L2 均保留真实归属关系，不能推定原创。JSON 的 `source_line_scope=JSON_STRING_OR_CONTAINER_ANCHOR` 表示原始字符串或容器锚点行；解码后的换行不冒充原帖物理行号。

ID 根据 canonical formula skeleton 的 SHA256 生成。窗口、数字阈值、分组名、字符串参数、引号差异与最外层方向符号不分别计为新骨架，原来的合法表达式保存在 `variant_values`；主入口应只选择一个代表公式，不把这些参数变体夸称独立策略。替换实际字段及增加预处理后必须重新校验完整表达式、总操作符数与单数据集约束。

全文件扫描不等于穷尽识别所有写法：图片公式、链接外部正文、无函数调用的纯概念、损坏 JSON、Markdown 表格多列、代码变量依赖与复杂程序块不能保证自动恢复。低复杂度、本地语法通过也不证明量纲、正负数据域、NaN/零分母处理、信号变异、收益或可提交性；日志和回填长窗口尤其需要真实字段质量证据。
# 可直接调用的模板本体

224个论坛骨架已落实为 `callable_templates/` 的224个Python函数，按8类模块放置。每个函数含逻辑、公式、算子、参数建议及来源，接受field和窗口/分组参数，直接返回表达式。注册清单中的module/function真正指向这些函数，爬山不再用通用字符串render_formula替代模板本体。

```python
from Core.factor.templates.callable_templates.trend_change import average_difference
expression = average_difference("mdl110_value", d=20)
```

`disabled_templates.py` 集中隔离旧日志92个失败范围、21个模板编号，保留21段原函数/动态表达式本体和原因，调用隔离函数会明确抛错。注册和最终候选补位都检查停用范围，不能改名、改版本绕过。同公式检查保留区域、类别、阶段和参数，不把PENDING当作失败，也不删除其他区域已有优良模板。未验证的新函数留在候选池，真实结果通过后再记录效果。

