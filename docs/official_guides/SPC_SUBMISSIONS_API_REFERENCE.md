# SPC Submissions API 参考（2026-11-26 实时核验版）

本文整理当前 WorldQuant BRAIN SPC（Stock Prediction Challenge）prompt 维护中实际用到的提交与权重管理接口、新版 `modelFamily` 枚举体系、已知平台限制与推荐安全替换顺序。

> **2026-11-26 重大变更说明**：平台已废弃旧版 `model` + `modelVersion` 双字段，统一改为单字段 **`modelFamily`**，并在 `OPTIONS /competitions/spc/submissions` 中正式暴露全部 9 个家族共 43 个可选底层模型 ID。

## 基础信息

- Base URL: `https://api.worldquantbrain.com`
- 鉴权: `POST /authentication`（Basic Auth 获取 Cookie/Session）或 `Authorization: Bearer <token>`
- 内容类型: `Content-Type: application/json`

## 核心接口

| 用途 | 方法 | 路径 | 实测说明 |
|---|---|---|---|
| 拉取全部 submissions | `GET` | `/competitions/spc/submissions?limit=100&offset=<M>` | 列表即包含完整 `prompt`、`sampleOutput`、`modelFamily`、`weight`、`updateFrequency`、`lastModified`、`status`；单页上限 100，须分页至 `next == null` 且校验 `len(rows) == count` |
| 查看单条权重历史 | `GET` | `/competitions/spc/submissions/{id}` | 返回分页的 `{date, weight}` 计权历史记录（**并非**生成状态详情，真实状态以列表 `status` 为准） |
| 新建 prompt submission | `POST` | `/competitions/spc/submissions` | 提交新 prompt（使用 `modelFamily`，推荐 `weight: "0.00"` 先试跑） |
| 修改 weight | `PATCH` | `/competitions/spc/submissions/{id}` | 当前平台仅允许修改 `weight`（`0.00` ~ `1.00`，保留 2 位小数） |
| 探测模型与字段约束 | `OPTIONS` | `/competitions/spc/submissions` | 返回完整 `POST` 字段校验规则、43 个 `modelFamily` 枚举、`updateFrequency` 枚举与 `status` 定义 |
| 删除实体 | `DELETE` | `/competitions/spc/submissions/{id}` | **不支持**（实测返回 `HTTP 405 Method Not Allowed`，只能将 `weight` 清零停用） |

## 1. 新建 prompt submission

```http
POST /competitions/spc/submissions
Content-Type: application/json
```

新版提交体示例（2026-11-26 实测通过）：

```json
{
  "name": "AM409 Early Revision-Mover GBR | R20261126 Claude Fable 5",
  "prompt": "You are a quantitative portfolio manager ...",
  "sampleOutput": "[{\"company_name\":\"HSBC Holdings plc\",\"ticker\":\"HSBA\",\"isin\":\"GB0005405286\",\"mic\":\"XLON\",\"confidence_score\":0.73,\"investment_horizon\":30,\"return_prediction\":0.036}]",
  "modelFamily": "us.anthropic.claude-fable-5",
  "weight": "0.00",
  "updateFrequency": "daily"
}
```

### 字段约束（来自 `OPTIONS`）

- `name`（必填，`maxLength: 200`）：submission 名称
- `prompt`（必填，`maxLength: 10000`）：提交给平台的 prompt 文本；推荐与 `sampleOutput` 条数严格一致
- `sampleOutput`（必填，`maxLength: 100000`）：JSON 数组字符串，每项包含 7 个字段：`company_name`、`ticker`、`isin`（12 位且校验位合法）、`mic`（4 位交易所代码）、`confidence_score`（`[0, 1]`）、`investment_horizon`（正整数交易日）、`return_prediction`（有限小数）
- `modelFamily`（必填，`maxLength: 100`）：须从 `OPTIONS` 返回的 `actions.POST.modelFamily.choices[].items[].value` 中选取
- `weight`（必填，`decimal`，`0.00` ~ `1.00`）：新建试跑固定用 `"0.00"`
- `updateFrequency`（必填）：可选 `daily`、`weekly`、`monthly`、`quarterly`，当前维护统一使用 `"daily"`

## 2. 修改 weight

```http
PATCH /competitions/spc/submissions/{id}
Content-Type: application/json
```

- 提升为活跃：`{"weight": "1.00"}`
- 清零停用：`{"weight": "0.00"}`

> 平台不允许通过 `PATCH` 原地修改 `prompt`、`sampleOutput` 或 `modelFamily`；升级模型或改 prompt 必须新建 submission 并通过 `weight` 安全切换。

## 3. 状态字段说明（来自 `OPTIONS`）

| `status` 值 | 含义 | 处置建议 |
|---|---|---|
| `Active` | `Active: Stable Output`（输出与样例一致） | 稳定可用；可设为活跃或保留作零权重备选 |
| `Unstable Output` | `Warning: Unstable Output`（输出与样例差异大） | 禁止激活；若当前有权重须清零并替换为稳定新版 |
| `Failed` | `Failed: No Output`（未能产出有效工具-权重输出） | 禁止激活；若当前有权重须清零并替换为稳定新版 |

## 4. `OPTIONS` 实时可用模型目录（2026-11-26 核验，共 9 家族 43 个模型）

以下为 `OPTIONS /competitions/spc/submissions` 实测返回的代表性旗舰与可用 `modelFamily` ID（完整清单以运行 `maintain_spc.py options` 实时拉取结果为准）：

| 家族 | 旗舰 / 推荐 `modelFamily` ID | 标签 | 备注 |
|---|---|---|---|
| **Claude** | `us.anthropic.claude-fable-5`<br>`us.anthropic.claude-opus-4-8`<br>`us.anthropic.claude-sonnet-5` | Claude Fable 5<br>Claude Opus 4.8<br>Claude Sonnet 5 | 另有 Opus 4.7/4.6/4.5、Sonnet 4.6/4.5、Haiku 4.5 |
| **DeepSeek** | `deepseek.v3.2` | DeepSeek V3.2 | 另有 `deepseek.v3-v1:0`（V3.1）、`us.deepseek.r1-v1:0`（R1） |
| **Gemini** | `gemini-3.8-flash`<br>`gemini-3.6-flash` | Gemini 3.8 Flash<br>Gemini 3.6 Flash | 另有 Gemini 3.5/3.1/2.5 系列（含 `gemini-2.5-pro`） |
| **GLM** | `zai.glm-5` | GLM 5 | 另有 `zai.glm-4.7`、`zai.glm-4.7-flash` |
| **Kimi** | `moonshotai.kimi-k2.5`<br>`moonshot.kimi-k2-thinking` | Kimi K2.5<br>Kimi K2 Thinking | 实测 `kimi-k2.5` 建单即 `Active` |
| **Qwen** | `qwen.qwen3-235b-a22b-2507-v1:0`<br>`qwen.qwen3-coder-480b-a35b-v1:0` | Qwen3 235B A22B 2507<br>Qwen3 Coder 480B A35B | 另有 Qwen3 VL 235B、Next 80B、32B 等 |
| **Nemotron** | `nvidia.nemotron-super-3-120b` | NVIDIA Nemotron 3 Super 120B | 另有 Nano 30B / 12B / 9B |
| **Llama** | `us.meta.llama4-maverick-17b-instruct-v1:0`<br>`us.meta.llama4-scout-17b-instruct-v1:0` | Llama 4 Maverick 17B<br>Llama 4 Scout 17B | 另有 Llama 3.3/3.1/3 系列 |
| **GPT** | `gpt-4o` | GPT 4o | **注意**：截至 2026-11-26 平台 GPT 族仅剩 `gpt-4o`，旧版自由字符串提交均被映射回 `gpt-4o` |

## 5. 平台限额与错误处理

- **活跃上限（50 条）**：当活跃（`weight > 0`）满 50 条时，直接提升新项或违规提交会触发 `429 SPC_ACTIVE_SUBMISSION_LIMIT_EXCEEDED`。因此替换必须严格遵循**先将旧项 `PATCH` 清零为 `0.00`，再将新项 `PATCH` 提升为 `1.00`**。
- **日新增限额**：触发 `429 SPC_DAILY_SUBMISSION_LIMIT_EXCEEDED` 时应立即停止继续 `POST`，保留已创建记录并在下一次维护补位。
- **网络异常 / 超时**：维护脚本会在每次 `POST`/`PATCH` 前写入 `INTENT` 日志，若遇异常只记 `PENDING`，先只读 `listing()` 对账再决定是否继续，绝不盲目重复发送。

## 6. 标准安全维护流程与常用命令

维护脚本位置：[legacy_core/pipelines/spc/maintain_spc.py](../../legacy_core/pipelines/spc/maintain_spc.py)（配套单测：[tests/unit/test_spc_maintenance.py](../../tests/unit/test_spc_maintenance.py)），运行日志统一写入 `data/spc_logs/<run_id>/`（已被 `.gitignore` 排除，避免提交大日志）。

```powershell
# 1. 拉取最新 OPTIONS 模型目录
python legacy_core/pipelines/spc/maintain_spc.py options --log data/spc_logs/20261126_upgrade

# 2. 只读体检快照与汇总（零写入）
python legacy_core/pipelines/spc/maintain_spc.py audit --log data/spc_logs/20261126_upgrade

# 3. 以 weight=0.00 批量试跑新模型（自动校验 sampleOutput 与 modelFamily，已存在则自动复用）
python legacy_core/pipelines/spc/maintain_spc.py create --log data/spc_logs/20261126_upgrade --payload <payloads.json>

# 4. 确认新试跑均为 Active 后，执行“先旧归零、再新激活（失败自动回滚旧稳态项）”安全切换
python legacy_core/pipelines/spc/maintain_spc.py replace --log data/spc_logs/20261126_upgrade --payload <swap_plan.json>

# 5. 运行本地离线回归单测
python -m pytest tests/unit/test_spc_maintenance.py -v
```
