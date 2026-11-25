# SPC Submissions API 参考

本文整理当前 SPC prompt 维护中实际用到的提交与权重管理接口，并记录已知平台限制与推荐调用顺序。

## 基础信息

- Base URL: `https://api.worldquantbrain.com`
- 鉴权: `Authorization: Bearer <token>`
- 内容类型: `Content-Type: application/json`

## 核心接口

| 用途 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 拉取全部 submissions | `GET` | `/competitions/spc/submissions?limit=<N>&offset=<M>` | 分页获取当前所有 SPC submissions |
| 查看单条 submission 详情 | `GET` | `/competitions/spc/submissions/{id}` | 用来读取真实状态，如 Stable / Unstable / Failed |
| 新建 prompt submission | `POST` | `/competitions/spc/submissions` | 提交新 prompt |
| 修改 weight | `PATCH` | `/competitions/spc/submissions/{id}` | 当前平台只允许修改 `weight` |
| 探测模型与字段约束 | `OPTIONS` | `/competitions/spc/submissions` | 探测当前可用模型族与可能的 `modelVersion` 约束 |

完整地址示例：

```text
GET     https://api.worldquantbrain.com/competitions/spc/submissions
GET     https://api.worldquantbrain.com/competitions/spc/submissions/{id}
POST    https://api.worldquantbrain.com/competitions/spc/submissions
PATCH   https://api.worldquantbrain.com/competitions/spc/submissions/{id}
OPTIONS https://api.worldquantbrain.com/competitions/spc/submissions
```

## 1. 新建 prompt submission

请求：

```http
POST /competitions/spc/submissions
Authorization: Bearer <token>
Content-Type: application/json
```

当前维护脚本实际提交的字段为：

```json
{
  "name": "AM999 Broad Quality Value Asia",
  "prompt": "You are a quantitative portfolio manager ...",
  "sampleOutput": "[{\"company_name\":\"Apple Inc.\",\"ticker\":\"AAPL\",\"isin\":\"US0378331005\",\"mic\":\"XNAS\",\"confidence_score\":0.82,\"investment_horizon\":22,\"return_prediction\":0.045}]",
  "model": "gpt",
  "modelVersion": "5.6",
  "weight": "0.00",
  "updateFrequency": "daily"
}
```

### 字段说明

- `name`: submission 名称
- `prompt`: 实际提交给平台的 prompt 文本
- `sampleOutput`: 样例输出，当前长期要求为 JSON 数组格式
- `model`: 模型族，例如 `gpt`、`gemini`、`claude`
- `modelVersion`: 该模型族当前可用的最高版本
- `weight`: 初始权重，常见做法是先以 `0.00` 作为试跑
- `updateFrequency`: 当前维护固定使用 `daily`

## 2. 修改 weight

请求：

```http
PATCH /competitions/spc/submissions/{id}
Authorization: Bearer <token>
Content-Type: application/json
```

提升为 active：

```json
{
  "weight": "1.00"
}
```

清零：

```json
{
  "weight": "0.00"
}
```

### 典型用途

- 清零不稳定、失败、非目标模板或需被替换的旧 prompt

## 3. 查看 submissions 列表

请求：

```http
GET /competitions/spc/submissions?limit=200&offset=0
Authorization: Bearer <token>
```

### 分页逻辑

维护脚本当前采用：

- `limit=200`
- `offset` 递增
- 直到返回结果为空或 `next` 为空为止

## 4. 查看单条 submission 详情

请求：

```http
GET /competitions/spc/submissions/{id}
Authorization: Bearer <token>
```

### 用途

列表接口里的 `status` 不一定足够可靠，所以维护中会进一步拉详情，优先从以下字段中读取真实状态：

- `statusLabel`
- `outputStatus`
- `reviewStatus`
- `state`
- `status`

当前维护把以下值视为稳定 active 状态：

- `Active`
- `Active: Stable Output`
- `Active - Stable Output`
- `Stable Output`

## 5. OPTIONS 探测模型与版本

请求：

```http
OPTIONS /competitions/spc/submissions
Authorization: Bearer <token>
```

### 用途

- 探测当前平台支持哪些 `model`
- 尝试读取 `POST` 动作的字段定义
- 如果平台暴露 `modelVersion` 备选值，则直接使用最高版本
- 如果平台不显式暴露版本，则回退到当前 submissions 与 `model_ledger.json` 中已被平台接受的最高版本

### 当前已观察到的可用模型族与目标版本

```json
{
  "gpt": "5.6",
  "gemini": "3.5",
  "claude": "3.5",
  "deepseek": "v4",
  "qwen": "3.0",
  "kimi": "2.6",
  "mistral": "large",
  "glm": "4.5",
  "llama": "3.1",
  "minimax": "abab-7"
}
```

## 当前平台限制

## 6. 只能 PATCH `weight`

当前平台不允许通过 `PATCH /competitions/spc/submissions/{id}` 原地修改：

- `prompt`
- `sampleOutput`

如果尝试修改，平台会返回类似错误：

```json
{
  "errors": [
    "Only 'weight' can be updated. Unexpected fields: ['prompt', 'sample_output']"
  ]
}
```

### 这意味着

- 旧 submission 的 prompt 不能原地升级
- 如果要换 prompt，只能新建一个新的 submission
- 然后通过 `weight` 切换新旧对象

## 7. active 数量上限

当当前 active submission 已满 50 个时，再 `POST` 新 submission，平台可能返回：

```text
429 SPC_ACTIVE_SUBMISSION_LIMIT_EXCEEDED
```

### 含义

- 当前活跃 submission 总量已触顶
- 替换流程必须遵循“先清零旧，再提升新”
- 在 50 满额时，不能依赖继续 `POST` 新对象来完成替换

## 8. 日新增限额

当天新增额度用尽时，平台可能返回：

```text
429 SPC_DAILY_SUBMISSION_LIMIT_EXCEEDED
```

### 含义

- 当天继续新增没有意义
- 应立即停止新增，保留已完成结果
- 下一次定时维护继续补位

## 推荐替换流程

## 9. 标准替换顺序

当要用新 prompt 替换旧 prompt 时，推荐顺序为：

1. `GET /competitions/spc/submissions` 拉全量列表
2. `GET /competitions/spc/submissions/{id}` 读取候选对象真实状态
3. 如果已有稳定的 `w=0` 试跑，优先复用，不必新建
4. 若无可复用对象，再 `POST /competitions/spc/submissions` 新建试跑
5. 确认新对象稳定后，`PATCH old_id` 把旧对象清零为 `0.00`
6. `PATCH new_id` 把新对象提升为 `1.00`
7. 如果第 6 步失败，应考虑回滚旧对象，避免 active 数量掉出目标值

## 10. 最小示例

### 新建一个试跑 submission

```json
POST /competitions/spc/submissions
{
  "name": "AM999 Broad Quality Value Asia",
  "prompt": "You are a quantitative portfolio manager ... Output JSON only ...",
  "sampleOutput": "[{\"company_name\":\"Apple Inc.\",\"ticker\":\"AAPL\",\"isin\":\"US0378331005\",\"mic\":\"XNAS\",\"confidence_score\":0.82,\"investment_horizon\":22,\"return_prediction\":0.045}]",
  "model": "gpt",
  "modelVersion": "5.6",
  "weight": "0.00",
  "updateFrequency": "daily"
}
```

### 清零旧 prompt

```json
PATCH /competitions/spc/submissions/EDr2k9D
{
  "weight": "0.00"
}
```

### 提升新 prompt

```json
PATCH /competitions/spc/submissions/xD9eweD
{
  "weight": "1.00"
}
```

## 11. 维护视角下的结论

真正和“提交 prompt / 修改 weight”直接相关的业务接口只有两个：

- `POST /competitions/spc/submissions`
- `PATCH /competitions/spc/submissions/{id}`

但要把维护做稳，通常还必须配套：

- `GET /competitions/spc/submissions`
- `GET /competitions/spc/submissions/{id}`
- `OPTIONS /competitions/spc/submissions`