# 12 — `activity_api.py` 用户活动与 Pyramid 分类

## 职责

`Core/api/activity_api.py` 提供用户活动统计和 Alpha Pyramid 分类的只读接口。模块只发出 GET 请求，不创建模拟、不修改 Alpha 属性，也不提交 Alpha。

## 接口

### `get_user_diversity(client)`

读取 `/users/self/activities/diversity`，成功时返回平台原始字典；请求失败、JSON 无效或响应不是对象时返回 `{}`。

### `get_alpha_pyramid_pass_info(client, alpha_id)`

读取 `/alphas/{alpha_id}`，查找：

```text
is.checks[name="MATCHES_PYRAMID"]
```

平台 pass 信息中的 `pyramids[].name` 直接作为 `categories`，不从表达式字段切分推断。因此一个 Alpha 可以对应多个范围。

返回结构：

```python
{
    "status": "PASS",       # PASS / NO_PASS / PENDING
    "alpha_id": "...",
    "categories": ["GBR/D1/MODEL"],
    "pyramids": [{"name": "GBR/D1/MODEL", "multiplier": 1.8}],
    "effective": 1,
    "multiplier": 1.8,
}
```

例如：

```python
{
    "status": "PASS",
    "categories": ["GLB/D1/PV", "GLB/D1/OTHER"],
    "effective": 2,
    "multiplier": 1.0,
}
```

`effective`、`multiplier` 和各 pyramid 的 multiplier 均保留平台原值。响应缺失、非 200、JSON 无效或没有完整 `MATCHES_PYRAMID` 检查时返回 `status="PENDING"`，不能解释为没有匹配或失败。

### `evaluate_pyramid_coverage(diversity_payload, pyramid_info)`

纯本地匹配两个接口的返回值，不发送网络请求。结果结构为：

```python
{
    "status": "ALL_PASS",  # ALL_PASS / HAS_GAP / PENDING
    "scopes": [...],
    "gap_scopes": [...],
    "reason": "所有关联塔均由平台判定为PASS",
}
```

匹配键固定为 `Region + Delay + Category`。同名 Category 不能跨 Region 或 Delay 借用 PASS；一个 Alpha 关联多个塔时，只有全部关联塔均为 PASS 才返回 `ALL_PASS`。成功的 diversity 快照中缺少关联塔返回 `HAS_GAP`，而整个响应不可用、Alpha 分类不可用或塔名称无法解析时返回 `PENDING`。

Category 优先使用平台 ID，并兼容名称大小写、空格以及 `pv / Price Volume`。`dataCategory.id/name` 都为空的地区汇总行不会被当成塔。

## 数据来源边界

- `categories` 是平台 Alpha pass 信息中的 Pyramid 范围。
- 本地字段目录中的 dataset/category 仍是另一套字段元数据，不能用来替代实时 Pyramid pass 结果。
- `PENDING` 表示结果未观测完整，不能作为 PASS 或 NO_PASS 使用。
- `dataDiversity.check` 是塔状态来源；`limit=0.3` 是平台门槛。当前接口不返回可供本地重算的实际占比，不能使用重叠的 `alphaCount` 自行推导。

## 测试与核验

API 单元测试使用 Mock，不发送真实 HTTP 请求：

```powershell
cd "代码/优化代码"
python -m unittest Core.tests.test_api_layer
```

真实 Alpha 核验应使用已认证的 `BrainClient` 进行只读 GET；凭据从 `Password/config.yaml` 读取且不写入日志或报告。
