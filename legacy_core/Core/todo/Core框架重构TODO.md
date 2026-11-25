# Core 框架重构 TODO

更新时间：2026-09-07

## 不变边界

- [x] 以当前源码和实际调用搜索为依据，不依赖落后的 GitNexus 索引。
- [x] 不调用真实平台写接口，不自动提交 Alpha。
- [x] 不删除 `Core/runtime_data/` 或业务目录中的历史缓存。
- [x] 新 Core 接口只承载通用机制；业务规则在业务层。旧便利接口按兼容契约保留，不扩展其中的规则。
- [x] 旧接口先保留兼容适配，确认无调用后再讨论删除。

## P0：安全和结果语义

- [x] 认证失败不得返回看似可用但未认证的 `BrainClient`。
- [x] Core 内网络请求统一经过 `BrainClient`，禁止绕过为 `client.session.get/post`。
- [x] 统一拉取结果：明确区分 `COMPLETE`、`PARTIAL`、`PENDING`，不得把失败解释为空结果。
- [x] 自动提交入口改成必须显式人工确认；定时任务不得获得隐式提交权限。
- [x] `factor/assembly` 中脚本导入不再联网；单条模拟探针已禁用，后续再整理目录。
- [x] 数据库清理脚本必须有显式入口和确认，导入不得执行 DELETE/DROP。

## P1：统一 Alpha 时间窗口拉取

- [x] 新增通用时间窗口分页拉取器，统一经 `BrainClient` 或旧调用兼容页加载器读取。
- [x] 支持每页 1–100 条、可配置密集窗口阈值、时间窗递归二分、ID 去重。
- [x] 统一使用带时区 datetime 和 `[start, end)` 半开区间。
- [x] 支持逐页检查点、失败范围记录和中断恢复。
- [x] 首先迁移“区分RA并标记”，保留原函数签名和历史 Alpha 记录；旧未完成分页会安全重取。
- [x] 比较迁移前后固定输入的 Alpha ID 集合、失败页和时间边界。
- [x] 再迁移“区分PPA并标记”，替换原 500 条时间戳游标。
- [x] 最后迁移 `alpha_manager`、`sc_engine` 中的重复分页循环。

## P1：职责边界

- [x] RA/PPA 的新拉取路径仅保留查询条件、业务门槛、SC/PC 顺序、标签和输出格式。
- [x] CatalogDB 只做本地 CRUD；平台目录同步移动到显式同步服务。
- [x] Validator 缺缓存时返回不可观测状态，不隐式下载远程数据。
- [x] 通用排序中的 Sharpe/Fitness/Margin 硬门槛、历史提交参考值集中 Core/sim/research_policy.py；爬山显式注入原策略，不作为全局默认。旧 get_alphas 默认参数仅保留兼容。
- [x] 单条模拟不从默认公共入口暴露；多模拟统一校验每批 2–8 条。

## P2：整理与兼容

- [x] `machine_lib.py` 改为显式兼容导出，停止新增通配符接口。
- [x] 明确操作符可用性、语法签名、模板和项目禁用规则的权威来源。
- [x] 合并测试目录；人工诊断和维护脚本分别归档到 `tools/manual`、`tools/maintenance`。
- [x] 修复或移出无法安全导入的 `factor/filter/alpha_evaluator.py`。
- [x] 更新 README/API 文档和真实测试数量。

## 契约测试

- [x] 单窗口覆盖 0、99、100、101、499、500、501 条。
- [x] 额外覆盖 999、1000、1001 条；相同 `dateCreated` 无法继续切分时明确返回 PARTIAL。
- [x] 覆盖跨日、月末、北京时间边界、纽约夏令时/冬令时。
- [x] 覆盖 401、429、超时、5xx、非法 JSON、缺失 `results/count`。
- [x] 覆盖中断恢复只请求缺失页，多窗口边界无重复 ID 或漏取。
- [x] 增加导入副作用测试：相关诊断和清理模块导入不联网、不修改数据库。

## 本轮验收记录

- [x] 修复 3q936AEN 手工入口：HTTP 200 + 空正文 + Retry-After 按计算中处理，有限只读等待，不绕过检查。
- [x] 按用户最新要求，通用提交机制集中 Core/api/submission.py；业务目录只留 ID 与手动运行入口，无二次确认；认证复用 Core。
- [x] 统一离线入口 testFile/core_regression/run_review_suite.py，162 项通过，默认禁止真实 HTTP。
- [x] 旧 RA 固定版本 51125a1310e6cc573f85fb5b224ff5e87ee5e02e：501 个密集样本 ID 一致；失败页与已观测 ID 集合一致。
- [x] PPA 原日缓存不变；新版北京时区检查点位于 beijing_v2，查询变更会重读。
- [x] 修复 SQLite 连接未关闭造成 Windows 文件占用的问题。
- [x] 原乱码评估脚本保留 .encoding-backup；未删除历史数据库、缓存或用户文件。

实现验收不等于平台验收：3q936AEN 的真实检查曾持续计算，尚未证明最终通过。
本轮不替用户提交、修改 Alpha 属性或运行模拟；最终由用户重新运行手工入口验证。
旧列表返回值、研究便利接口及单条模拟历史定义仅保留兼容，详见 doc/13_review_contract.md。
没有执行 Git 提交，也没有整体回滚原有脏工作区。

语法扫描另发现被忽略的历史临时文件 tools/webdata_quality/testFile/tmp.py 含 NUL；
不是运行模块，本轮保留不动。旧 Core/test/test_all_features.py 已修复为统一离线入口。
