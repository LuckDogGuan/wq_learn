# 分地区 D1 独立研究手册总目录（严禁跨地区混为一谈）

> [!IMPORTANT]
> **核心铁律**：
> 1. **概念严格分层**：`Dataset（数据集）≠ Data Field（数据字段）≠ Operator（算子）≠ Template（模板）≠ Expression（表达式）≠ Simulation Settings（设置）≠ Alpha`。
> 2. **地区严格隔离**：不同地区的平台门槛（如 CHN `Sharpe ≥ 2.08` vs 非 CHN `> 1.58`，ASI `maxTrade=ON & Robust ≥ 90%`）与股票市场微观结构（流动性、行业集中度、散户/机构占比、多国汇率与国家中性化需求）完全不同，**所有实验对比、筛选漏斗与优化复盘必须按地区分文件独立记录，严禁混池平均**。
> 3. **绝不丢弃好结果**：每轮回测生成的全部 Alpha（无论是否立刻过四关）均完整保留在 SQLite 账本与对应地区档案中；**整体提升 Sharpe 优先靠做好漏斗筛选（过滤低 Sharpe / 厂字型 / 低 2Y），而不是把低质量种子强行复杂化**。
> 4. **先聚焦单一地区打透**：当前首战唯一主攻地区为 **[DEU / TOP500 / D1](DEU_TOP500_D1.md)**（0 历史 OS 零自相关包袱、6 个 `1.8×` 空白金字塔、12-06 前 189 个免额度 `Alphas=0` 字段）。

## 地区独立作战档案

| 优先级 | 地区 / 股票池 / 延迟 | 平台硬门槛摘要 | 市场微观特征 | 独立档案入口 | 当前状态 |
| :-: | --- | --- | --- | --- | --- |
| **P0（当前专注）** | **`DEU / TOP500 / D1`** | `Sh>1.58`, `Fit>1.0`, `2Y>1.58`, `TO 1-70%`, `Weight<10%`, 经验 `M≥10bp` | 欧洲工业/制造/化工/汽车/金融为主，机构主导，500 只偏大中盘、无多国汇率杂音，0 已有 OS（零 SC 撞车） | [DEU_TOP500_D1.md](DEU_TOP500_D1.md) | **首战专注启动中** |
| **P1（次序展开）** | `CHN / TOP2000U / D1` | `Sh≥2.08`, `Fit≥1.0`, `Ret≥8%`, `Robust≥40%`, 经验 `M≥20bp` | A 股 T+1 + 散户占比高 + 短期反转/量价拥挤极高；低换手财务结构比率（`other496` `1.9×`）天然优势 | [CHN_TOP2000U_D1.md](CHN_TOP2000U_D1.md) | 计划就绪，待 DEU 跑顺后开启 |
| **P1（2→3 速赢）** | `GLB / TOP3000 / D1` | 非 CHN 常规 D1，经验 `M≥9bp`（占 2 并发槽） | 跨多国多币种大盘，`COUNTRY` / `RAM` 中性化关键；仅差 `fundamental` / `analyst` 各 1 条点亮 2→3 塔 | [GLB_TOP3000_D1.md](GLB_TOP3000_D1.md) | 计划就绪 |
| **P1（存量收割）** | `GBR / TOP700 / D1` | 非 CHN 常规 D1，经验 `M≥10bp` | 伦敦市场资源/金融权重高；现存 28 条 OS（`MODEL` 已饱和），优先零回测收割 `bl8LnbA6` / `xAbJ6grw` / `2rG8ZR8Z` | [GBR_TOP700_D1.md](GBR_TOP700_D1.md) | 存量审核包已出 |
| **独立 PPA 支线** | `ASI / MINVOL1M / D1` | `maxTrade=ON`, `Robust≥90%`, `JPN` 子检查；活跃 PPA Theme 至 12-20 | 多国市场（日/港/台/韩/新），强烈依赖 `COUNTRY` 或 `group_cartesian_product(country, sector)` | [ASI_MINVOL1M_D1.md](ASI_MINVOL1M_D1.md) | 与 RA 严格隔离，单独按需启用 |
