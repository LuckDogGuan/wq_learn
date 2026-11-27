# SPC 月榜怎么算

核验时间为 2026-11-27，北京时间。SPC 指 WorldQuant BRAIN 的 Systematic Predictions Challenge。

## 官方计分口径

1. 参赛者提交提示词，并指定模型、输出更新频率和提示词权重。平台在指定日期运行模型，生成股票多空及对应权重。
2. 平台汇总同一参赛者的提示词输出，并模拟这个组合在一个月内的表现。参赛者以组合的模拟表现计分，月末以排行榜名次决定获奖资格。
3. 官方协议未给出逐股合并公式、归一化细节、成本、计分统计量、最少有效天数或并列规则。公开榜单也未提供每条提示词的单独收益和月度贡献，无法从排名拆出某个模型的效果。[官方 SPC 协议第 9、10、13 条](https://api.worldquantbrain.com/competitions/spc/agreement)

可以把每条提示词想成一个给出持仓建议的子策略。一条给某股票做多建议，另一条给同一股票做空建议，在一个合并持仓的组合里，两者可能抵消。同方向的十条提示词也可能一起承担同一种风险。这是组合直觉，平台具体如何合并和归一化仍未核实。提示词数量可以影响信号覆盖和分散程度，官方列出的计分依据是合并组合的模拟表现。

## 11 月榜实际读到什么

以下是 `GET /consultant/boards/spc`，参数 `board=202611&aggregate=user` 的行数据。[11 月官方榜单 API](https://api.worldquantbrain.com/consultant/boards/spc?board=202611&aggregate=user&limit=100)

| 名次 | 用户 | Prompts | Total Instruments | Valid PNL Days | API Scaled Daily PNL |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | ST91222 | 50 | 486 | 15 | 0 |
| 11 | EM39206 | 3 | 56 | 14 | 0 |
| 2,469 | JG81923 | 50 | 920 | 17 | 0 |

全量分页核对了 11 月榜 2,487 人和 10 月榜 2,178 人。11 月前 50 名有 5 人显示 1–5 条，有 20 人显示 50 条。10 月前 50 名有 22 人显示 50 条，余下 28 人显示 6–49 条。两个榜的每条响应 `scaledDailyPnl` 均为数字 0。11 月全部 `dailyRankChange` 为 0，10 月只有 52 条为 0。截图中的 0.00 已在 API 原始字段复现，无法用两位小数显示来解释排名差，也无法把该字段当成本月真实盈亏或用它反推月榜公式。[10 月官方榜单 API](https://api.worldquantbrain.com/consultant/boards/spc?board=202610&aggregate=user&limit=100) · [本地全量核验汇总](../../data/spc_logs/20261127_check/scoring_leaderboard_totals.json)

11 月有 70 人、10 月有 144 人显示 0 条提示词且仍有正数有效 PnL 天数。这个现象意味着 `Prompts` 列不足以确认整月曾用过多少条提示词。第 11 名可以确认榜单上显示 3 条，平台未披露这些提示词的历史权重、模型和收益贡献。 `Total Instruments` 与 `Valid PNL Days` 分别报告标的数量与有效 PnL 日数，精确去重、累计窗口及日有效条件未核实。榜单 `OPTIONS` 提供月份和聚合类别，`GET` 提供账户级字段。官方帮助分类在此次 HTTP 核验中未能取得正文。[SPC 帮助分类](https://support.worldquantbrain.com/hc/en-us/categories/41681062887191) · [本地榜单与账户明细](../../data/spc_logs/20261127_check/scoring_leaderboard.json)

对自己的组合，适合先检查同市场、同方向或选股重叠造成的集中度，再用提示词或模型的单变量版本逐步比较。 `Active` 是输出状态，用它筛掉失败的生成记录。组合效果仍应结合有可比数据的计分期判断。[SPC 提交及状态 API 参考](SPC_SUBMISSIONS_API_REFERENCE.md) · [11 月 27 日更新记录](../整理与研究/records/experiments/osmosis_spc_20261127.md)
