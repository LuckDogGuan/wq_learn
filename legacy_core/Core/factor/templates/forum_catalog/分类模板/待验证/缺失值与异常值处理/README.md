# 缺失值与异常值处理：5个模板

全部本地合规通过，收益未验证；供爬山候选轮动，实际字段和范围仍须检查。

| 模板编号 | 表达式 | 来源帖子 |
|---|---|---|
| admin.catalog.812d50a27bad3873 | `ts_backfill({field},1200)` | 24957813446167 |
| admin.catalog.4f4ac14a6961d3bc | `hump(rank({field}), hump=0.01)` | 29095615954071 |
| admin.catalog.913e24dabb702c9b | `rank(ts_backfill({field}, 66))` | 41135490599063 |
| admin.catalog.d18837cde767a196 | `rank(-ts_backfill({field},20))` | 39411791834647 |
| admin.catalog.f37cf5455b3c6ceb | `ts_backfill(ts_backfill({field}, 120), 66)` | 42720875852439 |
