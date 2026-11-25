# 指引：日报 / 复盘 / 收入

## 用途
生成每日报告、复盘表现、查看收入与金字塔覆盖。

## 最少路径
- 日报：`brain-nextMove-analysis`（平台动向→比赛→Alpha IS/OS→建议）。
- 多样性 / 价值因子：`value_factor_trendScore`（窗口内提交多样性，越高越好）。
- 收入：`get_daily_and_quarterly_payment`（基础 + 其他支付）。
- 金字塔 / 比赛：`get_pyramid_alphas` / `get_pyramid_multipliers`、`get_user_competitions` + `get_competition_details`。

## 限制
- 所有数据一律来自 MCP 实时拉取，禁止编造指标 / 排名。
- 比赛建议前必须读 `get_competition_agreement`（注意 universe / delay 限制，如 GAC 用 GLOBAL）。
- 数据收集优先并行调用以提速。

## 相关
- 提出优化建议：`optimize/guide.md`。
