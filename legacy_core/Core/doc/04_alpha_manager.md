# 04 — `Core/sim/alpha_manager.py` — Alpha 结果管理

## 职责

负责从平台批量检索 Alpha，对结果进行剪枝去重，以及协调 SC/PC 校验调度。本模块**不含任何 HTTP 调用**，所有网络通信委托给 `Core.api.sim_api`。

---

## 函数详解

### Alpha 批量检索

```python
def get_alphas(start_date, end_date, sharpe_th=1.25, fitness_th=1.0,
               region="USA", alpha_num=200, usage="submit") -> list
```

流程：
1. 若 `start_date/end_date` 为 None，自动计算最近 30 天窗口（以北京时间为准）。
2. 按 100 条/页分页调用 `get_user_alphas()`（多头）。
3. 若 `usage != "submit"`，同时拉取 `_get_user_alphas_negative()`（空头，Sharpe < -threshold）。
4. 对每条 Alpha 调用 `_recommend_decay()` 推荐新 Decay。
5. 仅 `longCount + shortCount > 100` 的 Alpha 才加入输出。
6. 每 200 条重新 `login()` 一次防 Session 过期。

**输出格式**（每条 9 字段 list）：
```
[alpha_id, exp, sharpe, turnover, fitness, margin, dateCreated, decay, rec_decay]
```

---

### Decay 推荐策略

```python
def _recommend_decay(turnover, decay) -> int
```

| Turnover 范围 | 推荐 Decay |
|---|---|
| > 70% | decay × 4 |
| > 60% | decay × 3 + 3 |
| > 50% | decay × 3 |
| > 40% | decay × 2 |
| > 35% | decay + 4 |
| > 30% | decay + 2 |
| ≤ 30% | decay（不变） |

---

### 表达式剪枝去重

```python
def prune(next_alpha_recs, prefix="", keep_num=5) -> list[[exp, decay]]
```

对同一字段名（通过 `prefix` 提取）只保留 Sharpe 最高的前 `keep_num` 个表达式，防止同质化。

- `prefix` 示例：`"fnd6_"` 提取字段名后缀部分。
- 负 Sharpe 的 Alpha 在字段 key 上添加 `-` 前缀，单独计数。

---

### SC/PC 值提取

```python
def get_sc_value(client, alpha_id) -> float | str
def get_pc_value(client, alpha_id) -> float | str
```

> **注意**：这两个函数直接包装 `get_alpha_check()`，**不使用本地 sc_engine 缓存**。适合在没有本地缓存时的快速校验场景。
> 如果需要使用本地快速计算，应调用 `validator.get_sc_check()` 和 `validator.get_ppac_check()`。

`get_sc_value` 返回：
- `float` — SC 值
- `"fail"` — 存在 FAIL 检查项
- `"sleep"` — Session 过期
- `"error"` — 解析异常

`get_pc_value` 返回：
- `float` — PC 值（PROD_CORRELATION，如缺失 fallback PPC）
- `"sleep"` — Session 过期
- `"error"` — 解析异常

---

### 批量提交前完整性校验

```python
def check_submission(alpha_bag, gold_bag, start=0) -> list
```

遍历 `alpha_bag` 中所有 Alpha，调用 `get_sc_value()` 验证：
- `"sleep"`：等待 100s 后重新 `login()`，追加到 `alpha_bag` 末尾延迟重试。
- `"fail"`：直接丢弃。
- `"error"`：加入 `depot`（待人工确认）。
- `float('nan')`：可能是 IS 未完成，等待后重试。
- 通过：添加到 `gold_bag`。

每 200 条重新 `login()`，每 5 条打印进度。

---

### 金子因子库查看

```python
def view_alphas(gold_bag) -> None
```

遍历 `(alpha_id, sc)` 元组，调用 `locate_alpha()` 获取详细指标，按 Sharpe 降序打印。
