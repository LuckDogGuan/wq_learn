# 亚太孤岛实验线（`[TRACK:asi_isolated]`）独立实验复盘日志

> **对应路线**：路线 ③ · **亚太孤岛实验线 (`ASI Isolated Track`)**  
> **隔离边界**：本日志与 `data/asi_isolated_ledger.db` 一一对应，**绝不混入**「多域星阵路径」的 `data/wq_v2_ledger.db` 或 `batch_audit_ledger.md`。  
> **配置真源**：[asi_isolated_config.json](file:///c:/Wq/WorldQuant%20Brain/docs/asi_d0_d1_isolated/asi_isolated_config.json) · **操作 SOP**：[ASI_D0_D1_WORKFLOW.md](file:///c:/Wq/WorldQuant%20Brain/docs/asi_d0_d1_isolated/ASI_D0_D1_WORKFLOW.md)

---

## 日志记录模板（每轮单变量实验追加一条）

- **日期 / 时间 (CST)**：
- **分支与标签**：`ASI-D1 (ASI_EXP_D1)` / `PPA_Useful`（`ASI-D0` 当前双重锁定禁跑）
- **目标数据集与字段**：
- **单变量改动轴**：（如 `neutralization: SLOW -> COUNTRY` / 降换手 `TO > 18%` 启用平滑；若 `TO < 8%` 明确标注 `SKIP_LOW_TURNOVER`）
- **核心指标**：`Sharpe` / `2Y` / `Fitness` / `Turnover` / `Margin (bp)` / `Robust Universe (%)` / `Japan Robustness` / `Local PPAC`
- **结论归因**：`[有效]` 或 `[无效]` + 下轮动作

---

## 历史记录

### 2026-11-26 · 初始化建档（零回测仿真）
- `[TRACK:asi_isolated]` 完成官方帖子 `45233242695703`（Getting Started with ASI/D1 Power Pool · Workshop 03）全文+评论调研与 158 个 ASI/D1 数据集只读权限核查。
- **关键实测事实**：ASI 平台无 `Delay=0`；本账号无 `shortinterest3` 与 `model77` 权限（可用 `shortinterest5` 替代）；新发现 `model25`/`model26` 高覆盖 `Alphas=0` 免费字段。
- **状态**：就绪待命（`attached_to_main_scheduler: false`，`allow_d0_override: false`），等待人工显式触发或主线完成 4,000 常规额度后独立按需启动。
