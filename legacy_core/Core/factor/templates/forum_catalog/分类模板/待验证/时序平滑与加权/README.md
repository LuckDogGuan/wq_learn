# 时序平滑与加权：35个模板

全部本地合规通过，收益未验证；供爬山候选轮动，实际字段和范围仍须检查。

| 模板编号 | 表达式 | 来源帖子 |
|---|---|---|
| admin.catalog.1d33b0f5f49bf145 | `ts_mean({field},28)<2.7*ts_mean({field},60)` | 24957813446167 |
| admin.catalog.e9f07db33de028a3 | `-ts_mean({field},504)` | 23934004353687 |
| admin.catalog.3ddf50f0f6db5179 | `rank(ts_mean(log({field}), 25))` | 39441605621911 |
| admin.catalog.6548eba5b164900b | `ts_mean({field}, 252) > 100` | 42163760922903 |
| admin.catalog.aad2bf5b9f764fcd | `ts_product({field}+1,250)-1` | 19992945218711 |
| admin.catalog.6d7bc44da7d773d3 | `ts_product(1+{field},22)` | 36876447664023 |
| admin.catalog.9e63e81d44c2c71c | `ts_product({field}, 3)` | 34208186164631 |
| admin.catalog.ae1c7b226f3f8b8d | `ts_sum({field},252)` | 33316272949527 |
| admin.catalog.bf47dcfb335bafaf | `ts_product(1 + {field}, 20) - 1` | 34208186164631 |
| admin.catalog.daa199f9fd84af8d | `ts_mean(ts_backfill({field},80),126)` | 37273554019863 |
| admin.catalog.fb92e53bac86bb3e | `abs(ts_mean({field},20)/ts_mean({field},60)-1)` | 20278408956439 |
| admin.catalog.fd5b4f3b720a968e | `log(ts_mean({field}, 44)) - log(ts_mean({field}, 20))` | 37117908343831 |
| admin.catalog.19bc8bcf95e470a4 | `rank(ts_decay_linear({field}, 5))` | 39411791834647 |
| admin.catalog.1b016199c1feb309 | `ts_mean({field}, 5) - ts_mean({field}, 10)` | 39411791834647 |
| admin.catalog.2a64b13ebeeeaf96 | `rank(ts_sum({field}, 60))` | 39411791834647 |
| admin.catalog.2e2670f291281c93 | `rank(ts_product(1+{field}, 22) - 1)` | 31988597274903 |
| admin.catalog.33528af61acb862b | `rank(ts_mean({field}, 20))` | 39411791834647 |
| admin.catalog.338282a17ffeefe6 | `{field} - ts_mean({field}, 20)` | 39411791834647 |
| admin.catalog.3870d31af4e9921c | `rank(ts_decay_linear(ts_backfill({field}, 20), 5))` | 39411791834647 |
| admin.catalog.533608b0a6d94dda | `ts_mean(rank({field}), 5)` | 39411791834647 |
| admin.catalog.589c57b3b2e81921 | `zscore({field}) - ts_mean(zscore({field}), 20)` | 39225718749591 |
| admin.catalog.5b0868482126352f | `rank({field}) - ts_mean(rank({field}),5)` | 42078917602455 |
| admin.catalog.60133bcef05a77ce | `rank(-ts_sum({field},5))` | 41796491619351 |
| admin.catalog.72897ecb231c2982 | `ts_decay_linear(ts_backfill({field}, 60), 5)` | 39411791834647 |
| admin.catalog.7b8f904f4b7f84ef | `rank(ts_mean({field}, 20)) >= 0.20` | 38669179039255 |
| admin.catalog.976f4cf56209964c | `ts_mean({field}/ts_delay({field},1)-1,20)` | 19137620283415 |
| admin.catalog.c4cefbed8b7a198e | `ts_sum({field}, 20) - ts_sum({field}, 60)` | 42407253630359 |
| admin.catalog.c9e24297a35c4a45 | `rank(ts_mean({field}, 5) - ts_mean({field}, 20))` | 39411791834647 |
| admin.catalog.cc7ae197c41f34d2 | `rank(ts_sum({field} > 5, 10))` | 39411791834647 |
| admin.catalog.cf38bf10b735fb1d | `rank(ts_mean({field}, 22) - ts_delay({field}, 22))` | 39411791834647 |
| admin.catalog.d46c2df1ad86352e | `{field} > ts_mean({field}, 20) * 1.5` | 39411791834647 |
| admin.catalog.d6855faf105ab478 | `log(ts_mean({field}, 21))` | 32394129497239 |
| admin.catalog.d9c03b495fc0adf4 | `ts_decay_linear({field}, 20)` | 39411791834647 |
| admin.catalog.db6d99b196cb7c21 | `{field} / ts_mean({field}, 22)` | 42740521405463 |
| admin.catalog.e92359cb9f4a9fc7 | `rank({field} / ts_mean({field}, 20))` | 39411791834647 |
