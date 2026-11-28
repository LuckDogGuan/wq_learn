# WorldQuant BRAIN D1-Only 启动

## 默认路线 ④

```text
按 wq-d1-closed-loop 启动默认路线。应用 AGENTS.md，先读 forge handoff 摘要，按案例编号验真上轮有效和无效结果，再派 DSH 只读核验并确定下一轮的单一变量。保留完整日志和台账。
```

在仓库根目录执行。主控用 Codex CLI，子代理用 DSH。

```powershell
# 一行预览
python scripts/ops/launch_alphaforge_v4.py
# 只读验收 Codex CLI 和启动摘要
python scripts/ops/launch_alphaforge_v4.py --verify
# 从 Codex CLI 验收 DSH 工具链，成功时输出真实 job 回执
python scripts/ops/launch_alphaforge_v4.py --verify-dsh
# 正式运行一轮
python scripts/ops/launch_alphaforge_v4.py --execute
```

在现有 AI 会话中只读接手时，先生成摘要。

```powershell
$env:PYTHONPATH = 'wq_research_v2/src'
python -m wq_research_v2 forge handoff
```

指定地区、宇宙或数据集时，追加 `--region`、`--universe`、`--dataset`。切换路线时在口令里写明路线编号。默认路线以 [运行配置](run_config.json) 为准。

原始 CLI 日志保存在 `data/alphaforge_v4_runs/`。回执和上轮结论继续追加到 [路线 ④ 日志](../docs/alphaforge_v4/alphaforge_v4_log.md) 与 [归因台账](../docs/agents/OPTIMIZATION_LEDGER.json)。各路线入口见 [路线与日志指南](../docs/TRACKS_AND_LOGS_GUIDE.md)。
