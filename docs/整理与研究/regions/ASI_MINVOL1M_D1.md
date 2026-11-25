# 地区独立作战档案：`ASI / MINVOL1M / D1`（亚太市场 · 独立 PPA 主题支线）

## 1. 亚太市场特征与 BRAIN 平台规则
- **市场微观结构**：多国混合市场（日本、香港、台湾、韩国、新加坡等），**必须重视 `COUNTRY` 中性化或 `group_cartesian_product(country, sector)`**，以通过日本子市场检查（`LOW_ASI_JPN_SHARPE ≥ 1.0`）。
- **平台硬规则**：必须开启 **`maxTrade = ON`**、满足 **`Robust Universe ≥ 90%`**；活跃 D1 Power Pool Theme（`7MZJV8A`, `11/23–12/20`），10 个官方推荐集均已验真有权限。
- **分离原则（不与 RA 主线混为一谈）**：本档案作为独立 PPA 支线保留，遵循 [d1_4stage_pipeline.json](../workflow/d1_4stage_pipeline.json) 的 `ppa_d1_standalone` 四阶段流程（`Sharpe ≥ 1.0` + `PPAC < 0.50` + 描述 `≥ 100` 字符 + 打独立标签 `PPA_Useful`），待主线 `DEU` RA 稳定放量后再择机单独启用。
- **核心字段卡**：[FLD-P3-ASI-MINVOL1M-D1.md](../records/fields/FLD-P3-ASI-MINVOL1M-D1.md)（注意 `behavioral_signals` 为已知伪 VECTOR，只测 `vec_avg`）。
