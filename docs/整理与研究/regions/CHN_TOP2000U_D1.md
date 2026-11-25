# 地区独立作战档案：`CHN / TOP2000U / D1`（A 股市场 · 待 DEU 跑顺后展开）

## 1. A 股市场特征与 BRAIN 平台规则
- **市场微观结构**：散户占比高、T+1 制度与涨跌停板约束、短期量价反转高度拥挤；但低换手基本面财报结构比率、分析师覆盖动量与机构推荐跟踪（`analyst45`、`other496`）具有较高的超额收益持续性与高 Margin 安全垫。
- **平台硬门槛（全场最严，切忌与非 CHN 混为一谈）**：
  - **`Sharpe ≥ 2.08`** · `Fitness ≥ 1.0` · **`Returns ≥ 8%`** · **`Robust Universe ≥ 40%`** · 经验 **`Margin ≥ 20bp`** · `Weight < 10%`
  - 账号现状：当前 `0` 条 CHN OS（零本地 SC 包袱）；`other` 塔 **`1.9×`**（全场最高），`analyst` / `fundamental` / `macro` **`1.8×`**。

## 2. 备战字段与策略预案（严格区分字段 ≠ 模板 ≠ 表达式）
- **核心清洗字段卡**：[FLD-P4-CHN-TOP2000U-D1.md](../records/fields/FLD-P4-CHN-TOP2000U-D1.md)（74 个纯数值 `Alphas=0` 免额度字段：`other496` 财报比率 + `analyst45` 机构交易想法）与 Stage-0 WDS 蓝海集 `other561`（`RAM` 社区 Sharpe `1.581`）。
- **状态**：已进入高 Base 主力冲刺队列！
- **2026-11-25 18:15（30 分钟巡检 #2 · `other496` 爆发式突破！`|Sharpe| = 1.99`，距 `2.08` 门槛仅差 `0.09`！）**：
  - `CHN / TOP2000U / other496`（`Alphas=0` 免额，`other 1.9×` 全场最高倍率）：首波 `16` 条完成即命中 **`7` 条 `|Sh| ≥ 0.80`（43.8% 命中率）**、**`4` 条 `|Sh| ≥ 1.20`**！
    - **`58Gx273n`**（`AR / CurAssets` · `ts_rank(ts_decay_linear(...,10), 66)` + `subindustry`）：**`Sharpe = -1.99`、`2Y = -1.42`、`Fit = -1.19`、`TO = 4.24%`、`Margin = -20.99bp`**（因原模板与自定义表达式双重 `reverse` 负负得正变成反号 → **去掉多余 `reverse` 即为正向 `Sh = +1.99, Fit = +1.19, Margin = +20.99bp`！**）
    - **`WjYMxwKo`**（`AR / CurAssets`）：`Sh = -1.40, TO = 1.47%, Margin = -68.11bp`（翻转后 `+1.40 / +68.11bp`！）；**`akR6glNx`**（`AP / AR`）：`Sh = -1.37, 2Y = -1.59, TO = 5.38%, Margin = -14.95bp`（翻转后 `+1.37 / 2Y +1.59`！）。
  - **立即执行修正**：① 修复双 `reverse` 错号，将 `CHN_OTH496_BREAKOUT_FREE` 置顶为全队列第 1 优先级；② 加入 `signed_power(..., 1.5)` 拉升 `Returns`（当前 `4.45%–7.03%` → 冲破 `≥ 8%`）与同集双支 `min(rank(AR/CA), rank(AP/AR))`（保持 `100% Alphas=0 + ATOM`）；③ 同步部署 `poll_timeout_sec = 600s` 消除 CHN 300s 超时漏单（上波 16 条因 302s 超时落 `unobs`）。
