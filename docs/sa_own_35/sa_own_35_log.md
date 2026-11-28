# 路线 ⑤：SuperAlpha 独立路线（SuperAlpha Own v1.0）专属运行日志

> **规则**：本日志仅记录路线 ⑤ 的启动回执、额度预算、SA 回测批次、断点续传与只读 status/ammo 查询结果。全局可复用经验同步写回 [OPTIMIZATION_LEDGER.json](../agents/OPTIMIZATION_LEDGER.json)。

## 2026-11-28 · 路线 ⑤ 初始化建档

- `[TRACK:super_alpha_own_v1]` **初始化完成**：基于路线④（`alphaforge_agy_dsh_v4`）工程闭环 + 王哥/贺六浑/管理员 SuperAlpha 方法论，完成路线 ⑤ 建档。
- **额度预算**：SA `400/天`（硬上限）· RA 主线 `4,200/天`（`daily_target`/`alpha0_switch_threshold` 由 4,500 下调）· 合计 4,600 ≤ 5,000，安全垫 400。
- **代码落地**：
  - SA runner：`wq_research_v2/src/wq_research_v2/sa_runner.py`（`type=SUPER` 单发、`MAX_WORKERS=3`、断点续传、reconcile-once、绝不 `/submit`）
  - CLI：`python -m wq_research_v2 sa {preview,run,resume,status,ammo}`
  - 独立台账：`data/sa_own_ledger.db`（严禁写主线 `wq_v2_ledger.db`）
  - 单测：`wq_research_v2/tests/test_sa_runner.py`
- **当前状态**：`READY_FOR_MANUAL_LAUNCH`（不干扰广州正在运行的路线②主守护进程；SA 需 ≥100 OS 解锁，status 查询确认后手动启动）。
