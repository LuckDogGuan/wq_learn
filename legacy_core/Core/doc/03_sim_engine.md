# 03 — `Core/sim/sim_engine.py` — 模拟调度逻辑

## 职责

负责将 Alpha 表达式列表切分为任务池，并发提交模拟，轮询等待结果。本模块**不含任何 HTTP 调用**，所有网络通信委托给 `Core.api.sim_api`。

---

## 关键函数

### Payload 构建

```python
def build_sim_payload(alpha, decay, region, universe, neut, test_period='P0Y') -> dict
```

构建提交给平台的单条 simulation 请求体。固定参数：
- `instrumentType = "EQUITY"`
- `delay = 1`
- `truncation = 0.08`
- `pasteurization = "ON"`
- `unitHandling = "VERIFY"`
- `nanHandling = "ON"`
- `language = "FASTEXPR"`

爬山模板探索不会调用 `single_simulate`。其调用约束为：

- 每个 Multi-Simulation 包含 2～8 条表达式，通常固定为 8 条。
- 最后只剩一条时记录 `DEFERRED_SINGLETON`，不得回退到单条接口。
- `delay` 继承源 Alpha，不参与优化；当前值必须由平台实时设置确认。
- `decay` 的推荐候选为 `0/5/10/22/66`，首轮模板广度探索不会与所有模板做全组合。
- 父任务或子任务缺少 Location、Alpha ID、完整指标时记录 `RESULTS_UNOBSERVED`，不盲目重发。

`test_period`：
- 单 Alpha 模拟（`single_simulate`）用 `"P0Y"`（无额外测试周期）。
- Multi-simulation（`multi_simulate`）用 `"P2Y"`（含 2 年 OOS 测试周期）。

---

### 任务池切分

```python
def load_task_pool_single(alpha_list, limit) -> list
```
将 `[(alpha, decay), ...]` 按 `limit` 切分为小批次，每批次独立提交。

```python
def load_task_pool(alpha_list, limit_children, limit_multi) -> list
```
三层嵌套切分（用于 multi-simulation）：
- `limit_children`：单个 multi-sim 包含的子 Alpha 数（建议 ≤ 8）。
- `limit_multi`：同时并发提交的 multi-sim 组数。

---

### 单 Alpha 批量提交

```python
def single_simulate(alpha_pool, neut, region, universe, start=0)
```

流程：
```
login() → BrainClient
for batch in alpha_pool[start:]:
    for (alpha, decay) in batch:
        build_sim_payload() → post_simulation()  → progress_url
    for url in progress_urls:
        poll_simulation_progress(timeout=600)
    每批完成后打印日志
```

- 提交失败：等待 600s 后重新 `login()`，继续。
- `start` 参数用于**断点续传**（从指定批次恢复）。

---

### Multi-simulation 批量提交

```python
def multi_simulate(alpha_pools, neut, region, universe, start=0)
```

流程与 `single_simulate` 相同，但使用 `post_multi_simulation()` + `poll_simulation_progress(timeout=900)`。

`poll_simulation_progress()` 可直接接收平台返回的三种引用：完整 URL、
`/simulations/{id}` 相对路径、以及 Multi-Simulation `children` 中的裸 ID。
裸 ID 会统一转换为 `/simulations/{id}`，不会直接拼接到域名后。调用方可传入
`should_stop` 回调；停止时返回 `{"status": "INTERRUPTED"}`，包括长
`Retry-After` 等待期间也会及时响应。

```python
def generate_sim_data(alpha_list, region, universe, neut) -> list[dict]
```
为 multi-simulation 构造 payload 列表（每个 Alpha 一个 `build_sim_payload(test_period='P2Y')`）。
