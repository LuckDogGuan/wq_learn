# B. 优化方向与实验结论

## 1. PC（Prod Correlation）降低策略

**有效方法（已验证）**：

| 方法 | 案例 | 效果 |
|---|---|---|
| `group_zscore → group_neutralize` | 6Xe: 0.79→0.72；9q75: 0.84→0.71 | 有效，但每次仅降 0.01 量级，需多轮 |
| 双层 `ts_zscore`（内层/外层） | mLV: 0.75→0.62~0.66；9q75 d=120: 0.68 | 稳健，推荐配合 d=120/512/768/1024 扫频 |
| `ts_zscore → ts_scale`（sector 中性化 + d=120） | 6Xe: 0.71→0.49~0.69 | d=120 最优，需同时验证 Margin、Sub、2Y |
| `group_neutralize`（长期 d=768~1024） | 多个 GLB/EUR 案例 | PC 降低最稳定路径 |

**无效方法（已排除）**：

| 方法 | 结论 |
|---|---|
| `ts_zscore → ts_quantile` | PC 反升至 0.73~0.78，Sub 恶化 |
| `ts_delta(ts_av_diff)` | Sharpe=-0.35~0.44，Fitness 极低，完全失效 |
| `ts_mean` / `ts_decay_linear` 单独加 | 仅均值平滑，无法有效降 PC |
| `ts_ir(x, 20~504)` 扫频 | PC 确实下降(0.51~0.63)，但 Sharpe 崩溃(-0.19~0.98)，2Y 全部未达标 |
| `signed_power`、`hump` 调 TVR | 仅在 Turnover 合格时有效，无法解决 PC 问题 |
| `group_vector_proj`/`vec_choose`/`ts_median` | 平台实时算子列表中不支持，停止实验 |

**PC 优化执行顺序**：
```
group_neutralize 替换 → 双层 ts_zscore → ts_scale(d=120) → 多轮取 PC，每步确认 Margin/Sub/2Y 不退化
```

## 2. 2Y Sharpe 提升策略

- **时间窗口调整**：窗口从 512 → 768，`78z8gkO8` 的 2Y Sharpe 从 2.61 通过，但 Margin 仅 9.01bp（不足 10bp）
- **decay=3 补偿**：在 768 基础上加 decay=3，Margin 升至 10.81bp，Sub/2Y 同时通过 → `O0G09QeJ` 有效
- **但 PC 未降低**：同一因子 PC=0.8244，Self=0.8244，不可提交
- **结论**：2Y/Sub 优化可通过 decay + 窗口调整实现，但与 PC 优化存在正交冲突，需分轨解决

## 3. Sub-universe Sharpe 提升

对 QPG 基础因子的验证：
- `ts_decay_linear(x, d=3/5/10/20)` 扫频：4/4 失败，Sub 全部不达标，PC 反升（0.76→0.78）
- **结论**：`ts_decay_linear` 对 Sub-universe 无改善效果，停止扫频

## 4. 有效的综合案例

| Alpha | 关键操作 | 结果 |
|---|---|---|
| `YPv6rQ7J` | 6Xe sector + 双层 `ts_scale(d=120)` | PC=0.69（从 0.71 降），Sharpe=2.28，Margin=10.27bp，Sub 通过 |
| `6Xp78zlK` | 同上 d=60 | PC=0.59，Sharpe 同量级，通过全部基础门槛 |
| `O0G09QeJ` | 78z8 系列 + decay=3 + d=768 | 2Y/Sub/Margin 全通过，但 Self=0.82 不可提交 |
