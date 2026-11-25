# 指引：优化因子（分类）

## 用途
用户要「优化 / 改进 / 提升」已有 Alpha 时，按问题分类走最短路径。

## 分类路径
| 场景 | 路径 |
|------|------|
| 日常快速改进（1-2 轮） | `brain-improve-alpha-performance`（5 步：收集→评估字段→想法→批量模拟→验证）|
| 严格优化到可提交 | `wq-brain-alpha-optimization-v1`（每轮 8 候选，达 Sharpe>1.58 / Fitness>1 / PROD 相关<0.7）|
| 模板类优化 | `brain-enhance-template` |
| Sharpe 低 | 先稳定 PnL；负信号取反（`-expr`）；再对照阈值（`submit/guide.md`）|
| 相关性高 | 正交化（`regression_neut` / `vector_neut`）、换想法、控 ATOM |
| 换手高 | `ts_decay_linear`、`ts_target_tvr_*`、`hump` |
| 过不了测试 | 直接看 `submit/guide.md` |

## 限制
- 冻结基线核心字段 / 数据集，不换源。
- 每个表达式 AST 算子节点 `< 6`、唯一字段 1–2 个；每轮 ≤ 8 表达式。
- 严禁 `trade_when`、`add`、`multiply`；模拟前先本地校验。
- 不为了过校验删掉核心逻辑；失败先修错误点。

## 相关
- 字段评估：`evaluate/guide.md`；提交关卡：`submit/guide.md`。
