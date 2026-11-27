# ADR-0001 · 子代理统一用 DSH flash，≤4 轮即弃

Status: accepted · 2026-11-27 · 决定人：用户

**决定**：子代理使用 `dsh-opencode-go/deepseek-v4.1-flash`，每次启用前先 `dsh_worker_probe`；每个子代理最多 4 轮对话，用满即丢弃并换新。方向判断与有效/无效归因由主 Agent 负责。

**原因**：子代理无对话上下文且长对话会遗忘，状态必须落在文件里（`docs/agents/TODO_20261127.md`、`.scratch/`、账本）。flash 适合机械、边界明确的活。

**未验证**：该 provider/model 名称是否可用 `[U]`；probe 只证明一次 no-op 调用成功，不证明具备 agent/工具能力。flash 做归因的可靠性 `[U]`。

**影响**：`goal/run_config.json → subagent_profile`、`.agents/skills/wq-d1-closed-loop/SKILL.md` Step C。原 Google Neon/medium 默认降为 legacy 预设。

## 修订 2026-11-27 15:46（用户确认）

- **闭环归一个子代理**：一个任务的“提出意见 → 修改 → 结果”由同一个子代理完整负责并回报；不得把同一流程拆给多个代理接力。主 Agent 负责派单、方向决策、`git diff`/测试复核及有效/无效归因落账。
- **默认 DSH**：子代理默认 DSH flash（`dsh-opencode-go/deepseek-v4.1-flash`）。
- **任务包 = 定时间隔 × 1.5**：例如 3h 巡检间隔备足约 4.5h 工作量，留冗余防断粮；`dsh_run_worker` 单次上限 7200s，更长的任务包由同一子代理分段推进，进度落文件。该“1.5 倍”的解释（对应 `schedule_and_redundancy.queue_redundancy_multiplier=1.5`）`[U]`，如有出入以用户为准。
- 与“≤4 轮即弃”并存：一轮 = 一次派单与回报；长任务靠检查点而不是堆对话轮数。
