# A. 提交门槛与审查规则

## 1. 硬性门槛（RA 通用，缺一不可）

| 指标 | 门槛 |
|---|---|
| Sharpe | > 1.58 |
| Fitness | > 1.0 |
| 2Y Sharpe (`IS_LADDER_SHARPE`) | > 1.6 |
| Margin | > 10bp |
| Turnover | 5% ~ 30% |
| Sub-universe Sharpe | > 平台动态阈值（依 universe 而定）|
| Self Correlation | < 0.7（提交候选 < 0.4）|
| Prod Correlation (PC) | ≤ 0.7 |

风险中性化后还须：Sharpe > 1、Fitness > 0.7、Margin > 10bp，operator count < 6。

## 2. 状态流转约束

```
DISCOVERED → OPTIMIZABLE / TRACK_ONLY
          → OPTIMIZATION_PROGRESS
          → OPTIMIZATION_PASS / BASE_PASS
          → ROBUST → READY_TO_SUBMIT
```

- 任何阶段失败 → `OPTIMIZATION_FAIL` 或 `REJECTED`
- 只有全部硬门槛 + 实时检查明确通过，才标记 `READY_TO_SUBMIT`
- 不得自动提交，所有提交由用户手动操作

## 3. 可优化候选门槛（OPTIMIZABLE）

同时满足：Sharpe ≥ 1.35、Fitness ≥ 0.75、2Y Sharpe ≥ 1.35、Margin ≥ 7bp、0.03 ≤ Turnover ≤ 0.50，则进入优化队列。

| 状态 | 含义 |
|---|---|
| `OPTIMIZABLE` | 3 项达标、至多 2 项缺失，有优化价值 |
| `TRACK_ONLY` | 仅 Margin/Turnover 问题，Sharpe ≥ 1.20、Fitness ≥ 0.60 |
| `REJECTED` | 超过 2 项不达标或已耗尽优化预算 |

## 4. Short Count = 0 处理规则

- `Short Count = 0` 一律不得进入提交候选
- 根本原因：`rank` 类算子将信号压为非负值，空头持仓为零
- **修复方向**：
  1. 用 `ts_zscore` / `ts_quantile` 替换裸 `rank`，保留负值区间
  2. 检查 coverage：若 NaN 过多，空头被过滤 → 换字段或换 Universe
  3. 使用 `group_rank` / `group_zscore` 在子组内重新平衡多空

## 5. Sub-universe Sharpe / Weight Concentration 问题

失败信息：`Weight is too strongly concentrated or too few instruments are assigned weight.`

**诊断顺序**：
```
Sub-universe Sharpe低 / Weight Concentration
  ├── NaN 过多？→ 更换字段 / 小窗口 backfill
  ├── 信号极值？→ rank / group_rank / 截断
  ├── 权重集中度高？→ hump / ts_decay_linear 小窗口
  ├── 模型/组合匹配？→ 检查 neutralization 设置
  └── 失败 → 记录稀疏字段，停止 Universe 扩展
```

## 6. 实时检查缺失处理

- 429 / 5xx / 超时 / Alpha ID 缺失 → 标记 `PENDING`，不计作通过
- `REGULAR_SUBMISSION` / `SUBMISSION_CHECK` 缺确认 PASS 证据 → 不得提交
- `LOW_2Y_SHARPE: WARNING` 等同失败
