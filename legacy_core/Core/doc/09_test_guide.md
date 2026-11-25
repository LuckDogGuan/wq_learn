# 09 — `Core/tests/` 测试体系与 Mock 规范

## 运行方式

```powershell
cd Core/tests
python run_all.py
# 当前: 24 个测试全部 OK
```

---

## 测试文件清单

| 文件 | 测试内容 | 网络依赖 |
|---|---|---|
| `test_api_layer.py` | BrainClient 重试/429退避、平台响应解析、模拟提交/轮询 | **禁止**（全 Mock） |
| `test_auth.py` | `login()` 返回 `BrainClient` 实例 | 允许（凭据存在时） |
| `test_data.py` | SQLite 建表、upsert、查询隔离 | 无 |
| `test_factor_utils.py` | 因子过滤、关键词频率分析 | 无 |
| `test_validator.py` | AST 表达式语法校验（合法/非法/参数错误） | 无 |

---

## Mock 规范

### 基本原则

> **所有 `Core.api.*` 函数的单元测试必须使用 Mock，禁止发真实 HTTP 请求。**

违反此规则将导致：
1. 平台 429 限频（消耗你的 API 配额）
2. CI 因网络波动随机失败
3. 测试结果不可重现

### 标准 Mock 模式

```python
from unittest.mock import MagicMock, patch

# 模拟 BrainClient
mock_client = MagicMock(spec=BrainClient)

# 模拟 200 响应
mock_resp = MagicMock()
mock_resp.status_code = 200
mock_resp.json.return_value = {"results": [...]}
mock_client.get.return_value = mock_resp

# 模拟 429 后重试
mock_429 = MagicMock()
mock_429.status_code = 429
mock_429.headers = {"Retry-After": "0.01"}

mock_200 = MagicMock()
mock_200.status_code = 200
mock_200.headers = {}

mock_request.side_effect = [mock_429, mock_200]  # 第一次429，第二次200
```

### 新增 API 函数的测试清单

每个新增的 `Core.api.*` 函数必须覆盖以下三个场景：
1. ✅ 正常响应（200/201）
2. ⚠️ 异常响应（None / 4xx / 5xx）
3. 🔄 429 限频退避（`side_effect` 注入）

### SC/PPAC 测试注意事项

`get_sc_check()` 和 `get_ppac_check()` 依赖本地 pickle 缓存，测试时需：
- 使用临时目录 `tmp_path`（pytest fixture）作为 `cache_dir`。
- 构造伪 pickle 数据注入缓存，不依赖真实 OS Alpha 数据。
- `get_pc_check()` 应同时 Mock 专用 `/correlations/prod` 结果与单次 `/check` 降级。
