# 时序排名与区间位置：14个模板

全部本地合规通过，收益未验证；供爬山候选轮动，实际字段和范围仍须检查。

| 模板编号 | 表达式 | 来源帖子 |
|---|---|---|
| admin.catalog.3e31ccaa44da4394 | `ts_rank({field}, 60)` | 26054361848343 |
| admin.catalog.3f552d78bb2845a2 | `rank(ts_rank({field}, 100))` | 24957813446167 |
| admin.catalog.edfc15957e6d8a6e | `ts_quantile({field},80)` | 24957813446167 |
| admin.catalog.edb19fdad84fd35c | `(3)-1 * (ts_rank({field}, 5) - ts_rank({field}, 60))` | 39441605621911 |
| admin.catalog.4e0d9be33552b1ec | `ts_rank({field}, 126) * 0.4 + ts_rank({field}, 252) * 0.6` | 36335101288215 |
| admin.catalog.2a4ceb070e600ecb | `ts_rank({field}, 5) - ts_rank({field}, 20)` | 39411791834647 |
| admin.catalog.2f89d15e1aa9b409 | `ts_mean(ts_rank({field}, 10), 3)` | 40962586503191 |
| admin.catalog.3a855abd7c8584ba | `rank(-ts_rank(ts_delta({field}, 1), 5))` | 39411791834647 |
| admin.catalog.6a2b240a68aae7cd | `ts_scale({field},66)` | 31280678526615 |
| admin.catalog.9956015a36ca00c1 | `ts_decay_linear(ts_rank({field}, 252), 63)` | 39411791834647 |
| admin.catalog.c2d9cb6415d03a68 | `ts_scale(rank({field}), 660)` | 28107291019031 |
| admin.catalog.d54fa3ca12090f9e | `ts_rank(ts_mean({field}, 6), 252) - 0.5` | 39411791834647 |
| admin.catalog.de05f01449066924 | `ts_backfill(ts_rank({field}, 5), 3)` | 40972941718807 |
| admin.catalog.ea7a5eb895a16f6e | `ts_rank(ts_delta(ts_mean({field}, 5), 5), 10)` | 39411791834647 |
