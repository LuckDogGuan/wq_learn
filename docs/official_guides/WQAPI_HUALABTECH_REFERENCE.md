# WorldQuant BRAIN 非官方 API 与算子目录归档（`wqapi.hualabtech.com`）

> **来源**：`https://wqapi.hualabtech.com/#api/`（Catalog 版本：`1.15.3`，共 **123** 个 API 操作、**167** 个算子定义；已同步离线保存完整机读文件至同目录 [api-catalog.json](wqapi_hualabtech/api-catalog.json) 与 [operator-reference.json](wqapi_hualabtech/operator-reference.json)）。
> **安全红线**：本目录仅供只读查表、回测模拟、相关性查询、比赛/SPC/标签管理与诊断使用；严禁脚本自动调用 `POST /alphas/{alphaId}/submit`。

## 高频关键端点速查（竞赛 AQP / 模拟 / 相关性 / 标签 / 活动）

| 分类 | Method | Path | Operation ID | 摘要 |
| --- | :-: | --- | --- | --- |
| `authentication` | `GET` | `/authentication` | `getAuthentication` | 读取当前认证状态 |
| `authentication` | `POST` | `/authentication` | `createAuthentication` | 建立 Cookie Session |
| `authentication` | `DELETE` | `/authentication` | `deleteAuthentication` | 注销当前会话 |
| `authentication` | `POST` | `/authentication/persona` | `createAuthenticationPersona` | 提交 Persona inquiry 并完成认证 |
| `authentication` | `POST` | `/authentication/workday` | `authenticateWorkday` | 通过 Workday 认证 |
| `authentication` | `POST` | `/authentication/brainlabs` | `authenticateBrainLabs` | 通过 BrainLabs 认证 |
| `competitions` | `GET` | `/competitions/{competitionId}/agreement` | `getCompetitionAgreement` | 读取比赛协议正文 |
| `tags` | `OPTIONS` | `/tags` | `getTagOptions` | 读取 Alpha List 创建选项 |
| `tags` | `POST` | `/tags` | `createTag` | 创建 Alpha List |
| `users` | `GET` | `/users/self/tags` | `listSelfTags` | 分页列出当前用户 Alpha List |
| `tags` | `GET` | `/tags/{tagId}` | `getTag` | 读取 Alpha List |
| `tags` | `PATCH` | `/tags/{tagId}` | `patchTag` | 更新 Alpha List |
| `tags` | `DELETE` | `/tags/{tagId}` | `deleteTag` | 删除 Alpha List |
| `tags` | `GET` | `/tags/{tagId}/correlations/inner` | `getTagInnerCorrelation` | 读取 Alpha List 内部相关性 |
| `tags` | `GET` | `/tags/{tagId}/correlations/self` | `getTagSelfCorrelation` | 读取 Alpha List 自相关性 |
| `users` | `GET` | `/users/self/alphas` | `listAlphas` | 筛选并分页列出当前用户 Alpha |
| `tags` | `GET` | `/tags/{tagId}/alphas` | `listTagAlphas` | 筛选并分页列出 Alpha List 中的 Alpha |
| `alphas` | `GET` | `/alphas/{alphaId}` | `getAlpha` | 读取 Alpha 详情 |
| `alphas` | `PATCH` | `/alphas/{alphaId}` | `patchAlpha` | 更新 Alpha 元数据或设置 |
| `alphas` | `PATCH` | `/alphas` | `bulkPatchAlphas` | 批量更新 Alpha |
| `alphas` | `GET` | `/alphas/{alphaId}/alphas` | `listRelatedAlphas` | 读取相关/派生 Alpha |
| `users` | `OPTIONS` | `/users/{userId}/alphas` | `getUserAlphaOptions` | 读取用户 Alpha 查询选项 |
| `alphas` | `POST` | `/alphas/{alphaId}/submit` | `submitAlpha` | 提交 Alpha |
| `alphas` | `GET` | `/alphas/{alphaId}/submit` | `pollAlphaSubmission` | 轮询 Alpha 提交状态 |
| `alphas` | `GET` | `/alphas/{alphaId}/check` | `getAlphaChecks` | 读取 Alpha 检查结果 |
| `alphas` | `GET` | `/alphas/{alphaId}/correlations/{correlationType}` | `getAlphaCorrelation` | 读取 Alpha 自相关、Power Pool 或生产相关性 |
| `alphas` | `GET` | `/alphas/{alphaId}/recordsets` | `listAlphaRecordsets` | 列出 Alpha 可用 recordset |
| `alphas` | `GET` | `/alphas/{alphaId}/recordsets/{recordsetType}` | `getAlphaRecordset` | 读取 Alpha 指定 recordset |
| `users` | `GET` | `/users/self/alphas/{alphaId}/before-and-after-performance` | `getSelfAlphaPerformance` | 读取个人 Alpha 前后表现 |
| `teams` | `GET` | `/teams/{teamId}/alphas/{alphaId}/before-and-after-performance` | `getTeamAlphaPerformance` | 读取团队 Alpha 前后表现 |
| `competitions` | `GET` | `/competitions/{competitionId}/alphas/{alphaId}/before-and-after-performance` | `getCompetitionAlphaPerformance` | 读取比赛 Alpha 前后表现 |
| `users` | `GET` | `/users/self/alphas/summary` | `getSelfAlphaSummary` | 读取当前用户 Alpha 汇总 |
| `alphas` | `GET` | `/alphas/{alphaId}/tutorial` | `getAlphaTutorial` | 读取 Alpha 教程内容 |
| `simulations` | `OPTIONS` | `/simulations` | `getSimulationOptions` | 读取 Simulation POST 选项 |
| `simulations` | `POST` | `/simulations` | `createSimulation` | 创建一个或多个模拟 |
| `simulations` | `GET` | `/simulations/{simulationId}` | `getSimulation` | 读取或轮询 Simulation |
| `simulations` | `DELETE` | `/simulations/{simulationId}` | `deleteSimulation` | 删除 Simulation |
| `simulations` | `GET` | `/simulations/super-selection` | `getSimulationSuperSelection` | 获取 Super Selection 建议 |
| `operators` | `GET` | `/operators` | `listOperators` | 列出表达式算子 |
| `data-fields` | `GET` | `/data-fields/summary` | `getExpressionFieldsSummary` | 读取全部表达式字段摘要 |
| `data-sets` | `GET` | `/data-sets` | `listDatasets` | 筛选并分页列出数据集 |
| `data-sets` | `GET` | `/data-sets/{datasetId}` | `getDataset` | 读取数据集详情 |
| `data-sets` | `GET` | `/data-sets/search` | `searchDatasets` | 搜索数据集 |
| `data-fields` | `GET` | `/data-fields` | `listDataFields` | 筛选并分页列出数据字段 |
| `data-fields` | `GET` | `/data-fields/{fieldId}` | `getDataField` | 读取数据字段详情 |
| `data-fields` | `POST` | `/data-fields/{fieldId}/visualize` | `visualizeDataField` | 生成数据字段可视化 |
| `competitions` | `GET` | `/competitions` | `listCompetitions` | 分页列出比赛 |
| `competitions` | `GET` | `/competitions/{competitionId}` | `getCompetition` | 读取比赛详情 |
| `users` | `GET` | `/users/{userId}/competitions` | `listUserCompetitions` | 列出用户参加的比赛 |
| `competitions` | `POST` | `/competitions/{competitionId}/accept` | `acceptCompetition` | 接受比赛协议并加入比赛 |
| `competitions` | `OPTIONS` | `/competitions/{competitionId}/boards/{boardType}` | `getCompetitionBoardOptions` | 读取比赛榜单筛选选项 |
| `competitions` | `GET` | `/competitions/{competitionId}/boards/{boardType}` | `listCompetitionBoard` | 分页读取比赛榜单 |
| `competitions` | `GET` | `/competitions/{competitionId}/submissions` | `listCompetitionSubmissions` | 列出比赛提交（含 SPC） |
| `competitions` | `POST` | `/competitions/{competitionId}/submissions` | `createCompetitionSubmission` | 创建比赛提交（含 SPC） |
| `competitions` | `OPTIONS` | `/competitions/spc/submissions` | `getSpcSubmissionOptions` | 读取 SPC 提交选项 |
| `competitions` | `GET` | `/competitions/spc/submissions/{submissionId}` | `getSpcSubmission` | 列出某次 SPC submission 的权重历史 |
| `competitions` | `PATCH` | `/competitions/spc/submissions/{submissionId}` | `patchSpcSubmission` | 更新 SPC 提交权重 |
| `users` | `GET` | `/users/self/activities` | `listSelfActivities` | 列出当前用户活动分类 |
| `users` | `GET` | `/users/self/activities/{activityName}` | `getSelfActivity` | 读取当前用户某类活动 |
| `users` | `GET` | `/users/self/activities/referrals` | `listActivityReferrals` | 读取推荐活动 |
| `users` | `GET` | `/users/self/activities/diversity` | `getActivityDiversity` | 读取活动多样性 |
| `users` | `GET` | `/users/self/activities/pyramid-alphas` | `getActivityPyramidAlphas` | 读取 Pyramid Alpha 活动 |
| `users` | `GET` | `/users/self/activities/pyramid-multipliers` | `getActivityPyramidMultipliers` | 读取 Pyramid 倍数 |
| `users` | `GET` | `/users/self/activities/simulations` | `getActivitySimulations` | 读取指定日期后的模拟活动 |
| `users` | `GET` | `/users/self/activities/submissions` | `getActivitySubmissions` | 读取指定日期后的提交活动 |

## 全量 123 个接口分组索引

### `accept` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `POST` | `/{resourceType}/{resourceId}/accept` | `acceptResourceAgreement` | 接受资源协议 |

### `agreements` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/agreements/{agreementId}/agreement` | `getPublicAgreement` | 读取公开协议正文 |

### `alphas` (11)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/alphas/{alphaId}` | `getAlpha` | 读取 Alpha 详情 |
| `PATCH` | `/alphas/{alphaId}` | `patchAlpha` | 更新 Alpha 元数据或设置 |
| `PATCH` | `/alphas` | `bulkPatchAlphas` | 批量更新 Alpha |
| `GET` | `/alphas/{alphaId}/alphas` | `listRelatedAlphas` | 读取相关/派生 Alpha |
| `POST` | `/alphas/{alphaId}/submit` | `submitAlpha` | 提交 Alpha |
| `GET` | `/alphas/{alphaId}/submit` | `pollAlphaSubmission` | 轮询 Alpha 提交状态 |
| `GET` | `/alphas/{alphaId}/check` | `getAlphaChecks` | 读取 Alpha 检查结果 |
| `GET` | `/alphas/{alphaId}/correlations/{correlationType}` | `getAlphaCorrelation` | 读取 Alpha 自相关、Power Pool 或生产相关性 |
| `GET` | `/alphas/{alphaId}/recordsets` | `listAlphaRecordsets` | 列出 Alpha 可用 recordset |
| `GET` | `/alphas/{alphaId}/recordsets/{recordsetType}` | `getAlphaRecordset` | 读取 Alpha 指定 recordset |
| `GET` | `/alphas/{alphaId}/tutorial` | `getAlphaTutorial` | 读取 Alpha 教程内容 |

### `authentication` (6)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/authentication` | `getAuthentication` | 读取当前认证状态 |
| `POST` | `/authentication` | `createAuthentication` | 建立 Cookie Session |
| `DELETE` | `/authentication` | `deleteAuthentication` | 注销当前会话 |
| `POST` | `/authentication/persona` | `createAuthenticationPersona` | 提交 Persona inquiry 并完成认证 |
| `POST` | `/authentication/workday` | `authenticateWorkday` | 通过 Workday 认证 |
| `POST` | `/authentication/brainlabs` | `authenticateBrainLabs` | 通过 BrainLabs 认证 |

### `competition-levels` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/competition-levels` | `listCompetitionLevels` | 列出比赛等级 |

### `competitions` (12)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/competitions/{competitionId}/agreement` | `getCompetitionAgreement` | 读取比赛协议正文 |
| `GET` | `/competitions/{competitionId}/alphas/{alphaId}/before-and-after-performance` | `getCompetitionAlphaPerformance` | 读取比赛 Alpha 前后表现 |
| `GET` | `/competitions` | `listCompetitions` | 分页列出比赛 |
| `GET` | `/competitions/{competitionId}` | `getCompetition` | 读取比赛详情 |
| `POST` | `/competitions/{competitionId}/accept` | `acceptCompetition` | 接受比赛协议并加入比赛 |
| `OPTIONS` | `/competitions/{competitionId}/boards/{boardType}` | `getCompetitionBoardOptions` | 读取比赛榜单筛选选项 |
| `GET` | `/competitions/{competitionId}/boards/{boardType}` | `listCompetitionBoard` | 分页读取比赛榜单 |
| `GET` | `/competitions/{competitionId}/submissions` | `listCompetitionSubmissions` | 列出比赛提交（含 SPC） |
| `POST` | `/competitions/{competitionId}/submissions` | `createCompetitionSubmission` | 创建比赛提交（含 SPC） |
| `OPTIONS` | `/competitions/spc/submissions` | `getSpcSubmissionOptions` | 读取 SPC 提交选项 |
| `GET` | `/competitions/spc/submissions/{submissionId}` | `getSpcSubmission` | 列出某次 SPC submission 的权重历史 |
| `PATCH` | `/competitions/spc/submissions/{submissionId}` | `patchSpcSubmission` | 更新 SPC 提交权重 |

### `configuration` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/configuration` | `getConfiguration` | 读取平台配置 |

### `consultant` (2)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `OPTIONS` | `/consultant/boards/{boardType}` | `getConsultantBoardOptions` | 读取顾问榜单筛选选项 |
| `GET` | `/consultant/boards/{boardType}` | `listConsultantBoard` | 分页读取顾问榜单 |

### `data-categories` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/data-categories` | `listDataCategories` | 列出数据分类 |

### `data-fields` (4)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/data-fields/summary` | `getExpressionFieldsSummary` | 读取全部表达式字段摘要 |
| `GET` | `/data-fields` | `listDataFields` | 筛选并分页列出数据字段 |
| `GET` | `/data-fields/{fieldId}` | `getDataField` | 读取数据字段详情 |
| `POST` | `/data-fields/{fieldId}/visualize` | `visualizeDataField` | 生成数据字段可视化 |

### `data-sets` (3)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/data-sets` | `listDatasets` | 筛选并分页列出数据集 |
| `GET` | `/data-sets/{datasetId}` | `getDataset` | 读取数据集详情 |
| `GET` | `/data-sets/search` | `searchDatasets` | 搜索数据集 |

### `events` (2)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/events` | `listEvents` | 筛选并列出事件 |
| `OPTIONS` | `/events` | `getEventOptions` | 读取事件筛选选项 |

### `messages` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `PATCH` | `/messages/{messageId}` | `patchMessage` | 更新消息状态 |

### `operators` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/operators` | `listOperators` | 列出表达式算子 |

### `proto-user` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `POST` | `/proto-user` | `createProtoUser` | 创建 proto-user |

### `reject` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `POST` | `/{resourceType}/{resourceId}/reject` | `rejectResourceAgreement` | 拒绝资源协议 |

### `search` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/search` | `searchPlatform` | 全局搜索 |

### `simulations` (5)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `OPTIONS` | `/simulations` | `getSimulationOptions` | 读取 Simulation POST 选项 |
| `POST` | `/simulations` | `createSimulation` | 创建一个或多个模拟 |
| `GET` | `/simulations/{simulationId}` | `getSimulation` | 读取或轮询 Simulation |
| `DELETE` | `/simulations/{simulationId}` | `deleteSimulation` | 删除 Simulation |
| `GET` | `/simulations/super-selection` | `getSimulationSuperSelection` | 获取 Super Selection 建议 |

### `suggest` (2)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/suggest/examples` | `listSimulationExamples` | 列出模拟示例 |
| `GET` | `/suggest/fields` | `getSuggestedFields` | 读取组合及选择语言字段 |

### `tags` (8)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `OPTIONS` | `/tags` | `getTagOptions` | 读取 Alpha List 创建选项 |
| `POST` | `/tags` | `createTag` | 创建 Alpha List |
| `GET` | `/tags/{tagId}` | `getTag` | 读取 Alpha List |
| `PATCH` | `/tags/{tagId}` | `patchTag` | 更新 Alpha List |
| `DELETE` | `/tags/{tagId}` | `deleteTag` | 删除 Alpha List |
| `GET` | `/tags/{tagId}/correlations/inner` | `getTagInnerCorrelation` | 读取 Alpha List 内部相关性 |
| `GET` | `/tags/{tagId}/correlations/self` | `getTagSelfCorrelation` | 读取 Alpha List 自相关性 |
| `GET` | `/tags/{tagId}/alphas` | `listTagAlphas` | 筛选并分页列出 Alpha List 中的 Alpha |

### `teams` (6)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/teams/{teamId}/agreement` | `getTeamAgreement` | 读取团队协议正文 |
| `GET` | `/teams/{teamId}/alphas/{alphaId}/before-and-after-performance` | `getTeamAlphaPerformance` | 读取团队 Alpha 前后表现 |
| `OPTIONS` | `/teams/{teamId}` | `getTeamOptions` | 读取团队更新选项 |
| `POST` | `/teams` | `createTeam` | 创建团队 |
| `PATCH` | `/teams/{teamId}` | `patchTeam` | 更新团队 |
| `POST` | `/teams/{teamId}/{action}` | `changeTeamState` | 接受、拒绝或终止团队关系 |

### `tutorial` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/tutorial/{tutorialId}` | `getTutorial` | 读取研究教程步骤内容 |

### `tutorial-pages` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/tutorial-pages/{pageId}` | `getTutorialPage` | 读取文档教程页面 |

### `tutorials` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/tutorials` | `listTutorials` | 列出文档教程 |

### `user` (7)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `POST` | `/user/email/verify` | `verifyEmail` | 使用 Bearer 验证邮箱 |
| `POST` | `/user/email/change` | `changeEmail` | 更换邮箱 |
| `POST` | `/user/email/reverify` | `reverifyEmail` | 重新发送邮箱验证 |
| `POST` | `/user/password/forgot` | `forgotPassword` | 发起忘记密码流程 |
| `POST` | `/user/password/change` | `changePassword` | 修改密码 |
| `POST` | `/user/password/reset` | `resetPassword` | 用重置凭据设置新密码 |
| `POST` | `/user/token` | `createUserToken` | 签发用户 Token |

### `users` (3)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `OPTIONS` | `/users` | `getUserRegistrationOptions` | 读取注册字段及枚举 |
| `POST` | `/users` | `createUser` | 注册用户 |
| `GET` | `/users/{userId}` | `getUser` | 读取用户 |

### `users/achievements` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/users/{userId}/achievements` | `getUserAchievements` | 读取用户成就 |

### `users/alphas` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `OPTIONS` | `/users/{userId}/alphas` | `getUserAlphaOptions` | 读取用户 Alpha 查询选项 |

### `users/competitions` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/users/{userId}/competitions` | `listUserCompetitions` | 列出用户参加的比赛 |

### `users/consultant` (2)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/users/{userId}/consultant/summary` | `getConsultantSummary` | 读取用户顾问摘要 |
| `GET` | `/users/{userId}/consultant` | `getConsultantPerformance` | 读取顾问表现 |

### `users/osmosis` (3)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/users/{userId}/osmosis/summary` | `getOsmosisSummary` | 读取 Osmosis 摘要 |
| `POST` | `/users/{userId}/osmosis/scale-points` | `createOsmosisScalePoints` | 启动 Osmosis scale-points 计算 |
| `GET` | `/users/{userId}/osmosis/scale-points/ALL` | `pollOsmosisScalePoints` | 轮询 Osmosis scale-points 计算 |

### `users/profile` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/users/{userId}/profile` | `getUserProfile` | 读取用户公开档案 |

### `users/researcher` (1)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/users/{userId}/researcher` | `getResearcherPerformance` | 读取用户研究者表现 |

### `users/self` (25)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `PATCH` | `/users/self` | `patchSelfUser` | 更新当前用户 |
| `DELETE` | `/users/self` | `deleteSelfUser` | 删除当前账户 |
| `GET` | `/users/self/agreements` | `listSelfAgreements` | 列出当前用户协议状态 |
| `GET` | `/users/self/tags` | `listSelfTags` | 分页列出当前用户 Alpha List |
| `GET` | `/users/self/alphas` | `listAlphas` | 筛选并分页列出当前用户 Alpha |
| `GET` | `/users/self/alphas/{alphaId}/before-and-after-performance` | `getSelfAlphaPerformance` | 读取个人 Alpha 前后表现 |
| `GET` | `/users/self/alphas/summary` | `getSelfAlphaSummary` | 读取当前用户 Alpha 汇总 |
| `GET` | `/users/self/teams` | `listSelfTeams` | 列出当前用户团队 |
| `GET` | `/users/self/messages` | `listSelfMessages` | 分页列出当前用户消息 |
| `GET` | `/users/self/messages/summary` | `getSelfMessageSummary` | 读取当前用户消息摘要 |
| `PATCH` | `/users/self/messages/summary` | `patchSelfMessageSummary` | 批量更新消息摘要状态 |
| `GET` | `/users/self/activities` | `listSelfActivities` | 列出当前用户活动分类 |
| `GET` | `/users/self/activities/{activityName}` | `getSelfActivity` | 读取当前用户某类活动 |
| `GET` | `/users/self/activities/referrals` | `listActivityReferrals` | 读取推荐活动 |
| `GET` | `/users/self/activities/diversity` | `getActivityDiversity` | 读取活动多样性 |
| `GET` | `/users/self/activities/pyramid-alphas` | `getActivityPyramidAlphas` | 读取 Pyramid Alpha 活动 |
| `GET` | `/users/self/activities/pyramid-multipliers` | `getActivityPyramidMultipliers` | 读取 Pyramid 倍数 |
| `GET` | `/users/self/activities/simulations` | `getActivitySimulations` | 读取指定日期后的模拟活动 |
| `GET` | `/users/self/activities/submissions` | `getActivitySubmissions` | 读取指定日期后的提交活动 |
| `GET` | `/users/self/tutorial/summary` | `getTutorialSummary` | 读取研究教程摘要 |
| `PATCH` | `/users/self/tutorial/summary` | `patchTutorialSummary` | 更新研究教程进度或启用状态 |
| `POST` | `/users/self/tutorial/summary` | `createTutorialSummary` | 初始化研究教程摘要 |
| `GET` | `/users/self/tutorial/steps` | `listTutorialSteps` | 列出研究教程步骤 |
| `GET` | `/users/self/consultant/tutorial/summary` | `getConsultantTutorialSummary` | 读取顾问教程摘要 |
| `PATCH` | `/users/self/consultant/tutorial/summary` | `patchConsultantTutorialSummary` | 更新顾问教程进度或启用状态 |

### `users/settings` (2)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/users/{userId}/settings/simulation` | `getSimulationSettings` | 读取用户模拟默认设置 |
| `POST` | `/users/{userId}/settings/simulation` | `updateSimulationSettings` | 更新用户模拟默认设置 |

### `video-courses` (2)

| Method | Path | Operation ID | 摘要 |
| :-: | --- | --- | --- |
| `GET` | `/video-courses` | `listVideoCourses` | 列出视频课程 |
| `GET` | `/video-courses/{courseId}` | `getVideoCourse` | 读取视频课程（已废弃） |
