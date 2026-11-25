# WorldQuant Brain: 因子提交状态判别工具 (check_submission)

本模块位于 `代码/优化代码/区分是否有提交/`，用于精准、权威、快速地判别任意 WorldQuant BRAIN Alpha 是**已提交 (Submitted / OS)** 还是 **未提交 (Unsubmitted / IS)**。

---

## 🔍 权威判据与差异分析

通过对比平台底层真实返回（以 `LL9x9aA2` 与 `ZY0Zbxqx` 为实测对照）：

| 字段 / 维度 | 已提交因子 (Submitted, 如 `LL9x9aA2`) | 未提交因子 (Unsubmitted, 如 `ZY0Zbxqx`) | 判别优先级与说明 |
|---|---|---|---|
| **`dateSubmitted`** | **非空 ISO 8601 时间戳** (如 `"2026-09-04T12:07:41-04:00"`) | **`null`** | ⭐⭐⭐ **第一黄金判据**（最绝对可靠，有时间即代表提交） |
| **`stage`** | **`"OS"`** (Out-of-Sample) | **`"IS"`** (In-Sample) | ⭐⭐⭐ **生命周期状态**（已提交进入样本外跟踪，未提交处于样本内） |
| **`status`** | `"ACTIVE"`, `"RETIRED"`, `"SUBMITTED"` 等 | `"UNSUBMITTED"`, `"IS_FAIL"` 等 | ⭐⭐ 业务状态标识 |
| **`os` 对象** | 包含样本外前瞻跟踪指标结构体（`startDate`, `checks` 等） | **`null`** | ⭐⭐ 结构标志 |
| **`train` / `test`** | 为 `null`（或归档） | 包含两段样本内切分测试详情 | ⭐ 结构特征 |
| **平台对应 URL** | `https://platform.worldquantbrain.com/alphas/submitted` | `https://platform.worldquantbrain.com/alphas/unsubmitted` | 网页端资产列表 |
| **底座 API 参数** | `GET /users/self/alphas?stage=OS` | `GET /users/self/alphas?stage=IS` | 列表查询阶段参数 |

---

## 🛠️ 使用方式

### 方式 1：使用独立脚本执行查询

在当前目录下直接运行：

```powershell
# 1. 默认对比模式（自动测试 LL9x9aA2 与 ZY0Zbxqx）
python check_submission.py

# 2. 指定单个或多个 Alpha ID 查询（空格或逗号分隔）
python check_submission.py LL9x9aA2 ZY0Zbxqx e79J9wRg

# 3. 统计账户资产全貌（查看已提交总数、未提交总数及最新提交的因子）
python check_submission.py --summary

# 4. JSON 格式输出（方便管道下游解析）
python check_submission.py LL9x9aA2 --json
```

---

### 方式 2：在 Python 代码中直接调用 Core 接口

本功能已完整合并入 `Core` 框架底座（`Core.api.sim_api` 与 `Core.machine_lib`）：

```python
from Core.api import login
from Core.machine_lib import (
    get_alpha_details,
    check_alpha_submission_status,
    is_alpha_submitted,
)

client = login()

# 1. 结构化诊断
status_info = check_alpha_submission_status(client, "LL9x9aA2")
print(f"Alpha {status_info['alpha_id']} 已提交: {status_info['is_submitted']}, 提交时间: {status_info['date_submitted']}")

# 2. 轻量级布尔判定（传入已获取的 alpha 详情字典）
details = get_alpha_details(client, "ZY0Zbxqx")
if not is_alpha_submitted(details):
    print("该因子尚未提交！")
```

---

### 方式 3：使用 `cnhkmcp` MCP 工具查看

1. **单因子详情查询**：
   调用 MCP 工具 `get_alpha_details(alpha_id="LL9x9aA2")`，观察返回值中的 `dateSubmitted` 是否为 null 以及 `stage` 是否为 `"OS"`。
2. **批量列表查看**：
   - 查看已提交列表：调用 `get_user_alphas(stage="OS", limit=30, order="-dateSubmitted")`。
   - 查看未提交列表：调用 `get_user_alphas(stage="IS", limit=30)`。
