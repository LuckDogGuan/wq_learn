# ADR-0001 · DSH flash 会话保留与回写责任

Status: accepted · 2026-11-27 · 决定人：用户

- 子代理使用 `dsh-opencode-go/deepseek-v4.1-flash`，派发用 `tier=flash`、`effort=high`，启用前执行 `dsh_worker_probe`。探测结果只覆盖当次工具调用。
- 同一个子代理负责诊断、只读核验和最终回报。一轮指一次派单与回报。每个子代理最多 4 轮，达到上限后停止给该会话派单。保留 DSH 会话、对话及结果，后续任务按需开新会话。
- 默认直接回传结果。确需交付文件时，仅在派单指定且原先不存在的路径创建文件。由主 Agent 复核证据、决定方向、修改现有文件及落账。
- 长任务按检查点分段，检查点回传至同一会话。整体队列冗余沿用 `goal/run_config.json` 的巡检配置。

执行入口见 [派单模板](../agents/SUBAGENT_BRIEF_TEMPLATE.md) 和 [闭环技能](../../.agents/skills/wq-d1-closed-loop/SKILL.md)。
