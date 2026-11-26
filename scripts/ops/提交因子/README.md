# 手动提交 Alpha 入口说明

入口脚本：[submit_alphas.py](submit_alphas.py)，核心协议实现位于 [legacy_core/Core/api/submission.py](../../../legacy_core/Core/api/submission.py)。

## 提交流程（两阶段异步协议）

1. **前置只读状态检查**：查询 `GET /alphas/{id}`，若已处于 `OS / ACTIVE` 则跳过。
2. **提交前校验等待**：按 `Retry-After` 只读轮询 `GET /alphas/{id}/check`，全部 `PASS / WARNING` 后冷却 `1s`。
3. **单次提交触发**：仅发送 **1 次** `POST /alphas/{id}/submit`（遇 `429 / 5xx / 超时` 绝不盲重发，显式打印真实状态码或进入只读对账）。
4. **异步结果轮询**：收到 `HTTP 201 / 202` 或 `Retry-After` 后，按 `Retry-After` 有界只读轮询 `GET /alphas/{id}/submit`（默认最长 `180s`）：
   - `200`（无 `Retry-After`）：再通过 `GET /alphas/{id}` 双重确认 `stage=OS` 与 `dateSubmitted`；
   - `403`：完整打印平台拒绝的 `is.checks` 失败项（若仅 `ALREADY_SUBMITTED` 则直接判定已提交）；
   - `404`：先复查详情状态，未入库则明确报提交任务超时失效；
   - 超出轮询上限：输出 `PENDING` 并提示切勿立刻重跑，改用 `--check-only` 复核。

## 常用命令

```powershell
# 使用脚本内 ALPHA_IDS 检查并提交
python "scripts/ops/提交因子/submit_alphas.py"

# 命令行传入指定 Alpha ID（支持空格、逗号、分号分隔）
python "scripts/ops/提交因子/submit_alphas.py" e71w5Qrl

# 只读复核提交状态与 /check 结果（绝不发送 POST /submit）
python "scripts/ops/提交因子/submit_alphas.py" --check-only e71w5Qrl

# 自定义 GET /submit 最长等待秒数（如队列较慢时调大至 300 秒）
python "scripts/ops/提交因子/submit_alphas.py" --poll-timeout 300 e71w5Qrl
```
