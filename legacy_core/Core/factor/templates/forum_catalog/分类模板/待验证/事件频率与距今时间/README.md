# 事件频率与距今时间：10个模板

全部本地合规通过，收益未验证；供爬山候选轮动，实际字段和范围仍须检查。

| 模板编号 | 表达式 | 来源帖子 |
|---|---|---|
| admin.catalog.08f5a7f630a8b8db | `185*(65-ts_arg_max({field},150))/150` | 24957813446167 |
| admin.catalog.5fd725e4231d5ed7 | `185*(65-ts_arg_min({field},150))/150` | 24957813446167 |
| admin.catalog.24cbc202ff537b5b | `-ts_count_nans(ts_backfill({field}, 5), 20)` | 36183099180823 |
| admin.catalog.90ad590da6401d62 | `ts_arg_min({field},252)` | 23807105368215 |
| admin.catalog.c404884ba84bead3 | `ts_arg_min(scale({field},longscale=1,shortscale=0),252)` | 23807105368215 |
| admin.catalog.d81add19de48fd2a | `days_from_last_change({field})` | 20565001927063 |
| admin.catalog.fc41f73c064d673d | `pasteurize(ts_arg_min({field},252))` | 23807105368215 |
| admin.catalog.7e423cb43af8430c | `(25 - ts_arg_min({field}, 25))/25*100` | 20278408956439 |
| admin.catalog.885965bbd681af4d | `(25 - ts_arg_max({field}, 25))/25*100` | 20278408956439 |
| admin.catalog.6e28564444cc3e83 | `ts_arg_max({field}, 22) - ts_arg_min({field}, 22)` | 42403326870423 |
