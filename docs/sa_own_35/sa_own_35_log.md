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

## 2026-11-28 17:58 CST · 单条平台验收

- [V] 账号为 GOLD。显式过滤 `type=REGULAR&status=ACTIVE` 返回全账号 100 条，EUR D1 有 20 条。原查询的 10,000 含未提交记录，不能视为解锁证据。
- [V] 预览生成 EUR/TOP2500 D1 的 `SUPER` payload。单条实跑 `SA-EUR-OWN-20261128-001-000` 返回 HTTP 400，未取得模拟或 Alpha ID，独立台账保留 `RESULTS_UNOBSERVED`。只读 `OPTIONS /simulations` 只有 `REGULAR` 与 `REGION_AGNOSTIC`，选腿接口返回 HTTP 403。当前账号尚未验证可运行 SuperAlpha，未重发，未提交。
- [V] CLI 修复 SA 和 RA 台账隔离，`status` 显示平台能力，`run` 在没有 `SUPER` 时于 POST 前退出。`resume` 当前列出未结任务，自动恢复轮询待实现。
- [V] DSH 已完成独立只读核验，确认 `resume` 只打印待处理任务。Job `hub-14-mx08g1q0`，`dsh-opencode-go/deepseek-v4.1-flash`，`done`，输入 12,537 / 输出 13,979 tokens，读取 2 次。
