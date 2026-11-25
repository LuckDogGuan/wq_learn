# 地区独立作战档案：`ASI / MINVOL1M / D1`（亚太市场 · 独立 PPA 主题支线）

## 1. 亚太市场特征与 BRAIN 平台规则
- **市场微观结构**：多国混合市场（日本、香港、台湾、韩国、新加坡等），**必须重视 `COUNTRY` 中性化或 `group_cartesian_product(country, sector)`**，以通过日本子市场检查（`LOW_ASI_JPN_SHARPE ≥ 1.0`）。
- **平台硬规则**：必须开启 **`maxTrade = ON`**、满足 **`Robust Universe ≥ 90%`**；活跃 D1 Power Pool Theme（`7MZJV8A`, `11/23–12/20`），10 个官方推荐集均已验真有权限。
- **分离原则（不与 RA 主线混为一谈）**：本档案作为独立 PPA 支线保留，遵循 [d1_4stage_pipeline.json](../workflow/d1_4stage_pipeline.json) 的 `ppa_d1_standalone` 四阶段流程（`Sharpe ≥ 1.0` + `PPAC < 0.50` + 描述 `≥ 100` 字符 + 打独立标签 `PPA_Useful`），待主线 `DEU` RA 稳定放量后再择机单独启用。
- **核心字段卡**：[FLD-P3-ASI-MINVOL1M-D1.md](../records/fields/FLD-P3-ASI-MINVOL1M-D1.md)（注意 `behavioral_signals` 为已知伪 VECTOR，只测 `vec_avg`）。

- **2026-11-25 19:16（1 小时定时检查 #1 · `ASI / price_signal_dl` 单波爆发 5 条纯正向对称种子！）**：
  - 放宽 `600s` 超时后首波 `31/31` 零漏单完成，单波即出 **`5` 条正向 `POOL_B` 种子**（且正反完全对称验真：`6XG87dkJ = +0.98` vs `omP7keVv = -0.98`！）：**`kq8dY5nz` (`Sh=+1.13, 2Y=+1.40, Fit=0.57`)**、`6XG87dkJ` (`+0.98, 2Y=+0.97`)、`vRYq8P8b` (`+0.96`)、`O06YYNOv` (`+0.83`)、**`legd1PAN` (`+0.82, Margin=+15.28bp` 已过 ASI 15bp 安全垫！)**。
  - **加码方向**：提至全队列第 2 顺位，新增 `ASI_PRICEDL_DUAL_LOWTO`（前置 `ts_mean 22` 低换手高 Margin 变体 + `min(rank(vol), rank(trend))` 同集双支，保持 `maxTrade=ON` + `COUNTRY` + RA 与 PPA 严格隔离）。
