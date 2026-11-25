# 趋势变化与反转：22个模板

全部本地合规通过，收益未验证；供爬山候选轮动，实际字段和范围仍须检查。

| 模板编号 | 表达式 | 来源帖子 |
|---|---|---|
| admin.catalog.67f904a55f58bef4 | `scale(rank(ts_av_diff({field},252)))` | 24957813446167 |
| admin.catalog.cd14b36577bbd39c | `quantile(rank(ts_av_diff({field},252)))` | 24957813446167 |
| admin.catalog.e2254b045c01130c | `-ts_delta({field},3)` | 26054361848343 |
| admin.catalog.508f467b3f0331c5 | `ts_delta({field}, 4) > 0.1` | 39441605621911 |
| admin.catalog.04a6e8c0517e98db | `rank(ts_delta({field}, 5))` | 42215740602135 |
| admin.catalog.7091c26469bfc4a0 | `-ts_delta({field},5)-rank(ts_delta({field},5))` | 15238236356375 |
| admin.catalog.918543c1d44708fa | `ts_product({field}, 122) + ts_delta({field}, 22)` | 40734437350679 |
| admin.catalog.a1c2126ca09eff3c | `ts_returns({field}, 1)` | 41732813691287 |
| admin.catalog.e8bf34404148c2d4 | `hump(-ts_delta({field}, 5), hump=0.01)` | 37117908343831 |
| admin.catalog.15046bd5cc815da8 | `rank(ts_returns({field}, 20))` | 42259186135831 |
| admin.catalog.2859ed31e32d9933 | `rank(ts_delta(ts_mean({field}, 5), 5))` | 39411791834647 |
| admin.catalog.496f9e9d23f8a846 | `ts_decay_linear(rank(ts_delta({field}, 22)), 10)` | 39411791834647 |
| admin.catalog.5a6ebebc0826f636 | `ts_delta(ts_mean({field}, 5), 5)` | 39411791834647 |
| admin.catalog.6a3ff7a7276eb0f6 | `ts_decay_linear(ts_delta({field},1),5)` | 35876513619607 |
| admin.catalog.7e55e25728e3c86f | `ts_delta({field}, 5) / ts_delay({field}, 5)` | 39411791834647 |
| admin.catalog.81651b1f435809ab | `ts_delta({field}, 5) / {field}` | 42587179348119 |
| admin.catalog.abc311a07ddacfb5 | `rank(ts_av_diff({field}, 10))` | 39411791834647 |
| admin.catalog.bb455e1cbf8c4e9b | `rank(-ts_delta({field},5))` | 39411791834647 |
| admin.catalog.bf64e4f7df68830e | `ts_delta(ts_delta({field}, 5), 5)` | 39411791834647 |
| admin.catalog.cc364e2c68e45f79 | `rank(ts_delta(ts_backfill({field}, 20), 5))` | 34738466323095 |
| admin.catalog.e99dac58762fe3d6 | `ts_av_diff({field}, 50)` | 42187744015767 |
| admin.catalog.f9804c949ead271b | `ts_mean({field}, 5) / ts_mean({field}, 20) * ts_delta({field}, 10)` | 39411791834647 |
