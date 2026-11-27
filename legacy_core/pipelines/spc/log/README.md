# SPC 日志入口

## 2026-11-27 · SPC 计权核验与 DeepSeek 候选

- [Osmosis 与 SPC 更新记录](../../../../docs/整理与研究/records/experiments/osmosis_spc_20261127.md)记录了本轮前后快照、榜单基线、HTTP 429 对账及以 DeepSeek V3.2 为首的备选。

## 2026-11-26：适配 `modelFamily` 新接口、补齐第 50 位并升级 29 条旧模型至最新旗舰组合

- [API 实时核验与升级记录（2026-11-26）](API_实时核验_20261126.md)：补齐失效空缺的第 50 位（`AM409`），并将原 10 条 `gpt-4o`、15 条 `claude-opus-4-7`、4 条 `gemini-3.5-flash` 全部安全升级至多家族最新旗舰模型，同时保留 20 条 `deepseek.v3.2` 不动。
- [SPC Submissions API 参考（2026-11-26 更新版）](../../../../docs/official_guides/SPC_SUBMISSIONS_API_REFERENCE.md)：同步新版 `modelFamily` 枚举体系（9 家族 43 个模型）。
- [维护脚本](../maintain_spc.py) 与 [单元测试](../../../../tests/unit/test_spc_maintenance.py)：修复迁移路径、适配 `modelFamily` 校验与安全升级回滚机制（10/10 单测通过）。
- 本地完整运行日志（已被 `.gitignore` 忽略，不入库）：`data/spc_logs/20261126_upgrade/`（含 `operations.jsonl`、`options.json`、`model_catalog.json`、`replacements_completed.json`、`audit_summary.json`、`latest.json`）。

### 当前活跃池终态（2026-11-26 10:30）

- 活跃总数：**50 / 50**（100% `Active`，100% `daily`，50 个唯一策略）
- 模型分布：`deepseek.v3.2` (20)、`us.anthropic.claude-fable-5` (9)、`us.anthropic.claude-opus-4-8` (7)、`gemini-3.8-flash` (4)、`us.anthropic.claude-sonnet-5` (3)、`zai.glm-5` (3)、`moonshotai.kimi-k2.5` (2)、`qwen.qwen3-235b-a22b-2507-v1:0` (2)

### 后续只读体检命令

从项目根目录运行：

```powershell
python legacy_core/pipelines/spc/maintain_spc.py options --log data/spc_logs/check_latest
python legacy_core/pipelines/spc/maintain_spc.py audit --log data/spc_logs/check_latest
```

---

## 2026-10-12：稳定保留，失败与不稳定项替换（历史归档）

- [API 实时修正（2026-10-12）](API_实时核验_20261012.md)：原说明中的详情 GET 实际是权重日期记录；当时 `modelVersion` 没有枚举（现已于 2026-11-26 升级为 `modelFamily` 强枚举）；`DELETE` 实测 405。
- 原有 101 条平台稳定记录均不改配置，35 条原失败/不稳定策略切换为稳定修正版，历史实体因平台返回 405 无法删除，仅清零停用。
