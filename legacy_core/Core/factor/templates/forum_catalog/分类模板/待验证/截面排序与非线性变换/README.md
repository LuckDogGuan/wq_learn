# 截面排序与非线性变换：36个模板

全部本地合规通过，收益未验证；供爬山候选轮动，实际字段和范围仍须检查。

| 模板编号 | 表达式 | 来源帖子 |
|---|---|---|
| admin.catalog.acc17dcc23d62536 | `rank({field})` | 36183099180823 |
| admin.catalog.c16b95512285c994 | `scale(quantile({field}))` | 24957813446167 |
| admin.catalog.0a43374f428eab4f | `0.65 * rank(-{field})` | 39441605621911 |
| admin.catalog.6aaf4730f3d51ae1 | `ts_max_diff(scale({field},longscale=1,shortscale=0),252)` | 23807105368215 |
| admin.catalog.7d8a8a9d4aeabdb6 | `last_diff_value({field}, 5)` | 19831590714135 |
| admin.catalog.bde7ba8d9e2e5a46 | `{field} / ts_delay({field}, 5)` | 20284582494359 |
| admin.catalog.40e0fc605dcb3147 | `quantile({field})` | 35026706128279 |
| admin.catalog.42429575fc80b0cc | `{field} /ts_delay({field},1)-1` | 35490617356823 |
| admin.catalog.4b1b453de0d0a55c | `sqrt({field})` | 34208186164631 |
| admin.catalog.5b135c7d5d658d4b | `pasteurize({field})` | 40732429672343 |
| admin.catalog.5bdde2b0901f5468 | `rank({field})>0.7` | 33169668224919 |
| admin.catalog.75007fe58e0a4369 | `zscore({field})` | 40732429672343 |
| admin.catalog.7d899f431dc53345 | `rank({field}) < 0.4` | 22752141318167 |
| admin.catalog.969db6e6eb9293fc | `inverse({field})` | 34208186164631 |
| admin.catalog.dce17f367c5f5b92 | `scale({field}, scale=1, longscale=1, shortscale=1)` | 34208186164631 |
| admin.catalog.df9ee72494dfaeb1 | `{field} - ts_delay({field},1)` | 20278408956439 |
| admin.catalog.ec2678d1000f0c08 | `scale({field})` | 40732429672343 |
| admin.catalog.f2d4e34d895ab905 | `(rank({field})-0.5)*2` | 26671942422295 |
| admin.catalog.10569464d0e52df0 | `rank(ts_delay({field},5))` | 39225718749591 |
| admin.catalog.3cdaafd796ded422 | `(-1 * rank({field}))` | 39411791834647 |
| admin.catalog.3e65a29dc86086a0 | `normalize({field})` | 41076241014423 |
| admin.catalog.4a4fadf37fbf3e80 | `rank(-{field})` | 39411791834647 |
| admin.catalog.5ee09e6396309acf | `abs({field})` | 43529216017047 |
| admin.catalog.63e3248bd40188aa | `rank(abs({field}))` | 39411791834647 |
| admin.catalog.64b9570ebabe0382 | `abs({field})>=0.1` | 15227024028311 |
| admin.catalog.6bd9f132540bc052 | `max({field}, ts_delay({field}, 1), ts_delay({field}, 2), ts_delay({field}, 3), ts_delay({field}, 4))` | 43179860065303 |
| admin.catalog.7902a72244bb0c48 | `rank({field} - ts_delay({field}, 1))` | 39411791834647 |
| admin.catalog.83bdfe902b5071d7 | `rank({field}) - rank(ts_delay({field}, 1))` | 39411791834647 |
| admin.catalog.8cf6da5eaca76386 | `-sign({field})` | 43151729306647 |
| admin.catalog.916baf05aac2cbee | `({field} == ts_delay({field},1))` | 15390538468887 |
| admin.catalog.9fc2b549dbd45fc7 | `abs({field}) > 1` | 39225718749591 |
| admin.catalog.a4a84157b0fe7d1c | `-({field}-ts_delay({field},5))/{field}` | 19353819839639 |
| admin.catalog.c7b708fdc921fcd2 | `ts_delay({field}, 200)` | 17647293721239 |
| admin.catalog.da7c4db8c65ffaae | `log({field})` | 31280678526615 |
| admin.catalog.dd0ab1924189ab82 | `(1-{field})*ts_delay(1-{field},1)` | 15763503067543 |
| admin.catalog.e4c1d3e42b4a1bec | `log({field}/ts_delay({field},1))` | 20238317296791 |
