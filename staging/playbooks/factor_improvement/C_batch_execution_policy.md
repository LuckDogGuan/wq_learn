# C. 批量执行策略与文件规范

## 1. 批量规模

| 批次类型 | 规模 |
|---|---|
| 标准探索批 | 8 个表达式 |
| 异常恢复批 | 4 个（429/证书后恢复，逐批确认）|
| 优化批 | 2~4 个局部变体 |
| 末尾批 | 2~7 个（前批已无更好表达式）|
| 重复覆盖 | 同一表达式最多提交 2 轮 |

## 2. Dataset 约束

- 每批固定不超过 **3 个不同 dataset_id**
- 同一批次内所有表达式必须是同一 `dataset_id`
- Region、Universe、delay、settings 必须一致
- 每个 dataset 字段/模型状态须通过 MCP 核查

## 3. 异常处理

- 429 / 证书失败 / 超时：等待 `Retry-After`，保留批次结构重试
- 确定性错误（字段/表达式语法）：记录失败表达式，不重试
- 同接口连续 3 次失败：暂停 2 分钟后继续下一批次

## 4. 批次状态记录

每批必须记录：

```
batch_id | batch_size | dataset 列表 | compatible_group_key
retry_count | retry_reason | result_reconciliation_status
实际收到的 Alpha 成功/失败状态
```

| 状态 | 含义 |
|---|---|
| `RESULTS_RECONCILED` | Alpha 有效，可纳入字段探索统计 |
| `RESULTS_UNOBSERVED` | 成功但无法确认 Alpha 结果，标记 PENDING |
| `RETRYABLE_FAILED` | 硬件/429/证书，可重试 |
| `DETERMINISTIC_FAILED` | 字段/表达式确定性错误，不重试 |

## 5. 优化预算控制

- 同一 Alpha 最多 **5 轮**优化（Decay/中性化/窗口各维度）
- 达到预算上限未通过 → 标记 `OPTIMIZATION_BUDGET_EXHAUSTED` 归档
- 每 10 批次复盘：字段探索率、算子多样性、通过率趋势

## 6. 文件命名规范

```
YYYYMMDD__REGION__D{delay}__{UNIVERSE}__{purpose}__{status}__{id}.md
```

示例：
- `20260728__USA__D1__TOP3000__batch__B012.md`
- `20260728__EUR__D1__TOP2500__optimization__O02__pwKxO8po.md`

**Active 目录**（`总结/active/`）：只保留当前活跃状态文件（OPTIMIZABLE、TRACK_ONLY、ROBUST_PENDING）

**归档目录**（`总结/archive/YYYY-MM/`）：保存 OPTIMIZATION_PASS、REJECTED、OPTIMIZATION_FAIL 的静态记录
