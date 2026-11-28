# WorldQuant BRAIN D1-Only 极简一键启动指令 (`goal/START_HERE.md`)

## 1. 默认一键启动指令（新开对话 / 切换 AI 工具 / `/compact` 后直接复制这一句）

```text
请读取 AGENTS.md、docs/agents/CORE_STATE.json 和 docs/agents/OPTIMIZATION_LEDGER.json，按 wq-d1-closed-loop 技能启动「主Agent方向决策 + 子Agent控制变量优化」闭环，先检查上轮结果哪些有效、哪些无效，再决定下一轮优化方向。
```

> **说明**：所有固定细则（严进种子筛选 → Stage 1-2 `QUICK` 快筛 + 10% 管理员模板评测 `5:5->8:2` → Stage 3 `FULL` 控制变量 `decay∈{0,5,20}` 专一优化、2–3 轮无果止损打标休眠、PC 范围分布表 `[min, max, alphas]` 1–2 轮止损、`PC>0.70` 保守不交、`E5mWLW0J` 已转 `SC_PASS` 搁置、2–4 小时巡检配 **1.5× 一半冗余队列**、子代理默认 `dsh-opencode-go/deepseek-v4.1-flash`（先 probe，最多 4 轮，保留会话，默认只回传结果）；无新指令时按 [docs/agents/TODO_20261127.md](docs/agents/TODO_20261127.md) 自上而下执行 pending 项）**均已写死在 [goal/run_config.json](file:///c:/Wq/WorldQuant%20Brain/goal/run_config.json)、[CORE_STATE.json](file:///c:/Wq/WorldQuant%20Brain/docs/agents/CORE_STATE.json) 与 [.agents/skills/wq-d1-closed-loop/SKILL.md](file:///c:/Wq/WorldQuant%20Brain/.agents/skills/wq-d1-closed-loop/SKILL.md) 中自动读取，无需在启动口令里重复输入！**

---

## 2. 若需临时改方向/改子代理（仅在上面那句话后面追加半句即可）

- **例 1（指定地区/宇宙/类别）**：`...决定下一轮优化方向（本轮专注 USA / TOP3000 / model）。`
- **例 2（临时改子代理）**：`...决定下一轮优化方向（子代理改用 xxx）。`（默认见 `goal/run_config.json` → `subagent_profile`）

---

## 3. 关联真源（均已同步保存至 GitHub）

- **四条正式路线与日志一一对应手册**：[docs/TRACKS_AND_LOGS_GUIDE.md](file:///c:/Wq/WorldQuant%20Brain/docs/TRACKS_AND_LOGS_GUIDE.md)（① `基础优化路径` · ② `多域星阵路径` · ③ `亚太孤岛实验线` · ④ `锻造闭环路径 AlphaForge AGY-DSH v4.0`）
- 路线 ④（Antigravity CLI 主控 + DSH 子代理）SOP 与启动器：[docs/alphaforge_v4/ALPHAFORGE_V4_WORKFLOW.md](file:///c:/Wq/WorldQuant%20Brain/docs/alphaforge_v4/ALPHAFORGE_V4_WORKFLOW.md) · [scripts/ops/launch_alphaforge_v4.py](file:///c:/Wq/WorldQuant%20Brain/scripts/ops/launch_alphaforge_v4.py)
- 方向与冗余参数配置：[goal/run_config.json](file:///c:/Wq/WorldQuant%20Brain/goal/run_config.json)
- 动态闭环流程图：[goal/PIPELINE_FLOWCHART.md](file:///c:/Wq/WorldQuant%20Brain/goal/PIPELINE_FLOWCHART.md)
- 核心状态脉搏：[docs/agents/CORE_STATE.json](file:///c:/Wq/WorldQuant%20Brain/docs/agents/CORE_STATE.json)
- 有效/无效归因账本：[docs/agents/OPTIMIZATION_LEDGER.json](file:///c:/Wq/WorldQuant%20Brain/docs/agents/OPTIMIZATION_LEDGER.json)
- 基础版 v1.0 冻结归档：[docs/整理与研究/workflow/d1_ra_baseline_v1_frozen.json](file:///c:/Wq/WorldQuant%20Brain/docs/整理与研究/workflow/d1_ra_baseline_v1_frozen.json)
