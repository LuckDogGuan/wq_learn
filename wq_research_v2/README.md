# `wq_research_v2` — WorldQuant BRAIN D1-Only 模块化研究引擎

遵循 [experience_profile.md](file:///C:/Users/31186/.gemini/config/experience_profile.md)、[AGENTS.md](../AGENTS.md) 与 [CONTEXT.md](../CONTEXT.md) 构建的全新模块化 Python 研究引擎。

## 核心硬约束

1. **D1-Only**：全链路强制断言 `settings.delay == 1`，拒绝任何 D0 任务。
2. **Decision #3 永久禁令**：静态 AST 拦截 `+`、`*`、`add()`、`multiply()`、`trade_when()`；双分支组合采用表达式级 `min(rank(expr_A), rank(expr_B))` 与 `reverse(min(...))`。
3. **Gold 81 许可算子白名单**：拦截账号无权限的 `ts_median`、`left_tail`、`right_tail`、`generalized_rank`、`hump_decay`、`ts_decay_exp_window` 及旧 224 模板中的 42 条静态缺陷。
4. **绝不自动提交**：代码层无任何 `/alphas/{id}/submit` 写接口；`PATCH` 改属性须显式 `explicit_user_confirmed=True`。
5. **高可用与断点续传**：每 10 分钟自动刷新登录凭证 + 每 10 秒 `NetworkMonitor` 断线重连 + SQLite WAL 持久化 + 只对账一次绝不盲重发。

## 快速上手

```powershell
# 1. 环境与保护资产自检
python wq_research_v2/check_env.py

# 2. 跑通全套离线单测
python -m pytest wq_research_v2/tests -v

# 3. 安装为可编辑包（可选，亦可直接设 PYTHONPATH=wq_research_v2/src）
pip install -e wq_research_v2 --no-build-isolation --no-deps

# 4. Stage-0 字段筛选（WebDataScope-1.0.6/data D1 + 华子哥四大差距 + 管理员推荐）
$env:PYTHONPATH="wq_research_v2\src"
python -m wq_research_v2 screen fields --region GLB,ASI,CHN,DEU,GBR --export

# 5. 同步 92+ OS 本地 SC 缓存 & 候选池两两相关性矩阵
python -m wq_research_v2 sc sync
python -m wq_research_v2 sc matrix --alpha-ids mL6vGEzE,j287pqwO,bl8LnbA6,KPVlkqwE --region GBR

# 6. 只读轮询远程 PC 与 Alpha Pre-Submission Check
python -m wq_research_v2 pc check --alpha-ids KPVlkqwE,2rG8ZR8Z

# 7. 无 GUI 轻量标签工作流（默认只预览不写库，确认后加 --confirm-apply 打上 Useful 供网页端挑选提交）
python -m wq_research_v2 tag apply --alpha-ids 2rG8ZR8Z,1YGknEYQ --tag Useful
python -m wq_research_v2 tag apply --alpha-ids 2rG8ZR8Z,1YGknEYQ --tag Useful --confirm-apply

# 8. 高 Base 多市场 D1 RA 守护进程（含 Stage-2 轻参数 1.3-1.4 爬坡 + Stage-3 1.6+ 精修 + 相似种子剪枝 + 正向早停）
python -u -m wq_research_v2.daemon_ra_runner --region EUR,USA,GLB,ASI,DEU,HKG,KOR --slots 4 --batch-size 8 --mode FULL --daily-target 3000 --round-robin-waves 1 --early-stop-sims 48 --prune-jaccard 0.78 --prune-max-per-field 2 --prune-max-per-dataset 6 --loop

# 9. 只读审计广州服务器实时进展（30 分钟巡检脚本）
Get-Content -Raw scripts/ops/check_guangzhou_v2.py | ssh guangzhou "/root/miniconda3/bin/python -"

# 10. 只读流式合并 legacy_core/Core/runtime_data 历史库至 wq_v2_ledger.db 并分层筛选 D1 候选
python -m wq_research_v2 legacy merge
python -m wq_research_v2 legacy stats
python -m wq_research_v2 legacy screen --region USA,EUR,GLB --tier TIER_S_READY_CHECK,TIER_A_PARAM_TUNE --top 25
```

## 模块清单

详架构与 SQLite Schema 见 [doc/architecture.md](doc/architecture.md)。
