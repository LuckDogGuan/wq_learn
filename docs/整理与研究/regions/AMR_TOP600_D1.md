# 地区独立作战档案：`AMR / TOP600 / D1`（美洲除美市场 · `1.7×` 轻探针）

- **宇宙范围**：合法 D1 仅 **`TOP600`**（唯一主池，涵盖加拿大/拉美等非美美洲主要上市股）。
- **市场与规则（⚠️ 重要技术约束）**：
  - **仅支持 7 种中性化**：`NONE`, `STATISTICAL`, `MARKET`, `SECTOR`, `INDUSTRY`, `SUBINDUSTRY`, `COUNTRY` —— **严禁传入 `REVERSION_AND_MOMENTUM` / `CROWDING` / `FAST` / `SLOW` / `SLOW_AND_FAST`**！
  - 当前金字塔仅开放 2 个类别（`sentiment 1.7×`, `pv 1.4×`），账号当前 **`0` OS**，1 并发槽；因此作为轻探针市场按早停机制快速试水，不长时间占用高 Base 主力槽。
- **首轮实盘核验探针（2026-11-25 `cnhkmcp`）**：
  - **`model239`**（**`Alphas=0` 免额**, `VECTOR`, `cov=84.8%–94.8%`, `dCov=0.9507`）：`mdl239_shortlasso1d`, `mdl239_combo_tickets`, `mdl239_combo_crossdeltaactivity`, `mdl239_combo_deltacrossdelta`, `loan_rate_change_aggregated_metric`, `mdl239_combo_deltarate` *(严禁使用已捕获的纯 ID 陷阱 `mdl239_gvkey`, `mdl239_isin`！)*。
- **独立漏斗快照**：`data/exports/amr_ra_funnel_latest.json`。
- **2026-11-25 18:15（巡检 #2）**：`model239` 首波完成 24 条，`0` 命中 `|Sh| ≥ 0.80`（最高 `+0.42`），且 AMR 仅开放 2 塔 → 已降级至轮巡最末位，不挤占高 Base 槽位。
