# 文件索引（权威）

> 本目录按「功能」分文件夹，每个 guide 只覆盖一个意图域，避免无关上下文。
> 加载约定：先读根目录 `AGENTS.md` → 用本索引定位任务 → 只加载命中的 guide。

## 文件清单
| 路径 | 用途 | 何时加载 |
|------|------|----------|
| `AGENTS.md`（根） | 全局限制、工具顺序、因子硬规则 | 会话开始必读 |
| `guides/_INDEX.md` | 本文件 | 找文件 / 不确定时 |
| `guides/setup/guide.md` | 环境、凭据、认证 | 首次使用 / 认证失败 |
| `guides/idea/guide.md` | 找想法、特征生成 | 用户要新因子 |
| `guides/optimize/guide.md` | 优化已有因子 | 用户要改进 |
| `guides/evaluate/guide.md` | 理解 / 评估字段、表达式 | 解释、评估 |
| `guides/submit/guide.md` | 提交前审查、过测试 | 准备提交 |
| `guides/batch/guide.md` | 批量回测、跟踪 | 大批量模拟 |
| `guides/report/guide.md` | 日报、复盘、收入 | 汇报 / 复盘 |
| `guides/forum/guide.md` | 论坛浏览、贡献 | 逛论坛 / 发帖 |

## cnhkmcp 使用顺序（特别说明）

1. **认证**：需要平台数据时先调用 `authenticate`；凭据只传给工具，不写入文件或回复。
2. **确认合法设置**：先用 `get_platform_setting_options` 校验 Region、D1、Universe 和中性化组合。
3. **发现数据**：依次使用 `get_datasets`、`get_datafields`、`get_operators`，禁止猜测字段或算子。
4. **研究候选**：使用 `get_alpha_details`、`get_alpha_pnl`、`get_alpha_yearly_stats` 和 `check_correlation` 获取事实。
5. **回测**：只允许 `create_multi_simulation`；默认 `delay=1`，提交前先做 AST 与字段校验。
6. **排错**：批量回测异常用 `lookINTO_SimError_message`；429 出现后才等待。
7. **提交审查**：只调用 `get_submission_check`，把结果追加到 `guides/submit/submission_log.md`。
8. **知识降级**：cnhkmcp 无结果或报错 → 已安装 skill → 最后才使用论坛工具。
9. **论坛查询**：先 `search_specific_forum_fast`，必要时再 `search_all_forum_slow`，命中后用 `read_forum_post`。

### cnhkmcp 禁止项

- 永远禁止 `create_simulation` 和 `submit_alpha`。
- 禁止修改 cnhkmcp/chnkmcp 库、源码、依赖或内部配置。
- `set_alpha_properties`、发帖、评论、投票、删除等写操作，必须符合任务范围并先确认。
- 不得用别名、脚本或其他工具绕过禁令。
- cnhkmcp 认证失败时转 `guides/setup/guide.md`，不要反复重试或改库。

## 加载约定
- 每个 guide 只读自身；需要跨域先回 `_INDEX.md` 定位。
- 平台事实以 cnhkmcp 只读返回为准；skill 和论坛只作补充证据。
- guide 与 `AGENTS.md` 冲突时，以 `AGENTS.md` 为准。
