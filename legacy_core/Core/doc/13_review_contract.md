# Core Review 当前契约（2026-09-07）

本页优先于 01–12 文档中的旧接口描述。当前源码和调用测试是事实来源；
GitNexus 索引已知落后，不在脏工作区重建。所有示例均不授权平台写入。

## 能力、调用方与副作用

| 模块/接口 | 输入和输出 | 实际调用方 | 副作用/缓存 |
| --- | --- | --- | --- |
| api.auth.login / login_hk | 凭据路径 → 已认证 BrainClient，失败抛异常 | API 客户端、手工提交 | 认证请求；不记录账号密码 |
| api.client.BrainClient | 方法、URL、请求参数 → Response 或 None | Core API、RA/PPA 拉取 | GET 限速、401 续签、429/超时/5xx 有界重试；写请求不重试传输故障 |
| api.alpha_retrieval.fetch_alpha_window | 时区区间、查询、切片策略 → AlphaFetchResult | RA、PPA | 只读平台；按指定路径原子保存检查点 |
| api.pagination.iter_alpha_pages | 页加载器、页大小、扫描上限 → 逐页数据或 AlphaPageUnavailable | alpha_manager、sc_engine | 调用方定义只读请求；不内置业务排序 |
| data.catalog_db.CatalogDB | 本地记录/条件 → DataFrame 或写入 | 字段检索、本地评估、目录同步 | SQLite CRUD；默认 runtime_data/catalog.db；退出关闭连接 |
| catalog_sync.sync_catalog | CatalogDB、可选 client、skip 参数 → status/failures | 旧 fetch_all_scopes 兼容入口 | 显式平台读取及本地 upsert，不再自己按三小时重登录 |
| sim.validator / sc_engine | Alpha ID、参考池、缓存 → SC/PC/PPAC 或不可观测状态 | RA/PPA、爬山 | 参考池缺失不自动下载；目标详情/PnL仍可能只读平台 |
| sim.sim_engine.load_task_pool | Alpha 列表、批大小、并发组数 → 任务池 | 批量研究 | 无网络；不足两条报错等待补批 |
| api.sim_api.post_multi_simulation | 2–8 条 payload → 平台响应 | 显式授权的批量研究 | 平台写接口；本轮未执行 |
| api.submission | 本次手动运行授权的 ID → 成功/未确认 | submit_alphas.py | 通用检查等待、一次提交和一次核验；无业务门槛 |

“COMPLETE”仅描述列表查询完整性，不表示 Alpha 通过任何研究/提交门槛。
旧列表返回接口仍保留 list/tuple 返回值，以免一次性破坏调用方；新代码使用结构化结果。

## 五类问题与处置

| 分类 | 处置 | 收益 | 迁移风险 | 优先级 |
| --- | --- | --- | --- | --- |
| 明确重复 | RA/PPA 的分页、分窗、断点机制合并 | 同一边界与失败契约 | 新 PPA 缓存首次需要重读 | P1 |
| 明确重复 | alpha_manager / sc_engine 共用普通分页器 | 缺字段/截断页不再假完成 | 旧不规范模拟响应需补齐 count | P1 |
| 表面重复 | 保留时间窗与按 Sharpe/dateSubmitted 排序两种模式 | 不改变候选顺序、OS 缓存边界 | 不强行用同一时间游标 | P1 |
| 表面重复 | SC、PC、PPAC 不合为一种指标 | 防止本地相关性代替生产相关性 | 保留各自不可观测语义 | P0 |
| 职责冲突 | 同步移出 CatalogDB；通用提交机制集中 api.submission | 本地 CRUD、API 机制与业务配置分离 | 提交业务目录只留 ID 与运行入口 | P1 |
| 职责冲突 | 硬门槛/历史排序集中 Core/sim/research_policy.py | 策略与通用候选管理分开 | 爬山显式注入原策略；通用默认排序不等价于研究策略 | P1 |
| 接口不一致 | 缺结果、count、非法 JSON、重复页统一报不可观测 | 不再把平台失败认作空数据 | 缺 count 的非标准页加载器需迁移 | P0 |
| 缺失能力 | Retry-After 的有界只读检查等待 | 修复手工提交空检查提前退出 | 仍可能因平台持续计算返回 PENDING | P0 |
| 缺失能力 | 检查点范围校验、日期微秒、查询变更失效 | 避免失效缓存漏取与分窗不收敛 | 旧版本检查点会安全重读 | P1 |
| 职责冲突 | 测试/诊断/维护分目录；导入不触发动作 | 避免导入即联网、清库 | 保留旧文件作为入口，不按减少文件数合并 | P2 |

## 策略与兼容边界

- 业务决定查询条件、窗口业务范围、排序偏好、SC/PC 顺序、标签和输出。
- Core 决定如何读取、分页、记录失败、恢复和去重；默认 100/500 可配置。
- 新接口严格要求结果页含整数 count。count 或 ID 集合中途变化按不可观测处理。
- 检查点不是数据库快照。使用固定输入测试可证明边界语义；平台在读取中改变数据仍需重新核对。
- 检查点暂不支持多进程并写，调用方必须使用独立路径/单写入者。
- PPA 原日缓存不删除、不覆盖；新 beijing_v2 缓存具有时间范围和查询签名。
- RA 旧记录保留、旧未完成分页重取。迁移前后的 501 条密集样本 ID 一致；
  100 条已观测后 offset=100 失败的 ID 集合与失败上下文也一致。
- 旧 get_alphas 默认筛选参数、推荐 Decay 等便利逻辑仅为兼容保留；
  不把它作为新通用读取接口。扫描上限仍按旧接口的整页粒度处理。
- Core.constants.global_ops.submission_thresholds 仅是旧参考值兼容别名，
  不代表当前 RA/PPA 标准，不得用它代替实时检查。
- 单条模拟函数不从 Core.api/machine_lib 默认导出；历史定义暂保留，不在本项目授权使用。
- Core.api.submission 负责通用提交机制，业务目录负责 ID 与手动启动；不二次询问，定时配置不能代替本次启动授权。

## 操作符来源

| 问题 | 权威来源 | 不可替代的内容 |
| --- | --- | --- |
| 当前账号可用哪些操作符 | 平台只读 /operators 及其当前响应 | global_ops 列表或模板不证明账号权限 |
| 本地语法、参数结构是否成立 | factor/filter/expression_verifier/validator.py | 本地通过不证明模拟成功 |
| 本地可用名称白名单 | BRAIN_VALID_OP_PATH 指定的 validOp.json；否则校验器向父目录查找 | 缺文件或旧文件不是最新平台事实 |
| 研究模板怎么拼 | factor/templates/ 与 factor/generator/ | 示例是候选素材，不是通用规则/效果保证 |
| 本项目禁止哪些操作 | 当前 AGENTS.md 和用户明确指令 | 模板存在不授权 trade_when/add/multiply 或单条模拟 |

## 验证与回滚

- 统一入口：仓库根目录运行 python testFile/core_regression/run_review_suite.py。
- 本轮 162 项定向测试通过，默认阻断真实 HTTP；不能等同于全仓库或真实平台验收。
- 覆盖 0、99、100、101、499、500、501、999、1000、1001；
  月末、北京时间、纽约夏令时/冬令时；401、429、超时、5xx、非法结构和恢复。
- 本轮没有真实 Alpha 提交、属性写回、模拟、数据库清理或 Git 提交。
- 真实只读诊断曾观测 3q936AEN 的 /check 返回 200、空正文、Retry-After；
  有界查询内未取得最终检查，不能宣称该 Alpha 已通过或已提交。
- 后续由用户在手工入口验证实际平台结果；仍 PENDING 时保留原因，不绕过检查。
- 回滚按模块查看本轮差异并使用旧适配入口，不整体 reset、不删除历史缓存。
  乱码评估脚本的原始字节另有 .encoding-backup 备份。
- 全目录语法扫描发现被忽略的历史临时文件 tools/webdata_quality/testFile/tmp.py 含 NUL，
  保留不动并从运行代码语法验收排除。旧 Core/test/test_all_features.py 已转为离线兼容入口。
