# 波动与风险调整：40个模板

全部本地合规通过，收益未验证；供爬山候选轮动，实际字段和范围仍须检查。

| 模板编号 | 表达式 | 来源帖子 |
|---|---|---|
| admin.catalog.078e2390484905e8 | `ts_ir({field},20)` | 26054361848343 |
| admin.catalog.25a99e1965cb2b0d | `ts_zscore({field}, 252)` | 26054361848343 |
| admin.catalog.4d85042c2a9984de | `abs(ts_mean({field},252)/ts_std_dev({field},252))` | 26054361848343 |
| admin.catalog.f1b6274ef52c9cb6 | `ts_std_dev({field}/ts_delay({field}, 1)-1,20)` | 26054361848343 |
| admin.catalog.011f691eb30d4f07 | `ts_zscore(rank(ts_delta({field}, 5)), 30) * -1` | 39441605621911 |
| admin.catalog.1e9d189bf282f7c0 | `ts_zscore(rank(ts_delta({field}, 5)), 20)` | 39441605621911 |
| admin.catalog.2d67ac5ab50962df | `2.-ts_rank(ts_std_dev({field}, 66), 252)` | 39441605621911 |
| admin.catalog.62b3e3de800ec86c | `ts_std_dev({field}, 21) * sqrt(252)` | 24469914183575 |
| admin.catalog.8e1de8303b0e3410 | `ts_zscore(ts_delta({field}, 252), 252)` | 39441605621911 |
| admin.catalog.921283dc7cfcc9ed | `(1)-rank(ts_mean({field}, 5)) * ts_std_dev({field}, 20)` | 39441605621911 |
| admin.catalog.978316a1c66d6ef9 | `rank(ts_std_dev({field}, 20))` | 39441605621911 |
| admin.catalog.b69141b59d398690 | `-rank(ts_zscore(ts_delta({field},5),60))` | 33037839973783 |
| admin.catalog.bb8d1af25cad1e49 | `ts_zscore(ts_delta({field}, 1), 10) * -1` | 39441605621911 |
| admin.catalog.dbfc1baaad9be7ec | `ts_rank({field}, 20) * ts_std_dev(ts_delta({field}, 5), 20)` | 39441605621911 |
| admin.catalog.07b71f36b9fcd093 | `ts_mean(ts_zscore({field}, 252), 21)` | 41036889226263 |
| admin.catalog.1f6acfc7759649a6 | `rank(-ts_std_dev({field}, 20))` | 34208186164631 |
| admin.catalog.402ed00c72e33541 | `ts_delta(ts_zscore({field}, 252), 252)` | 42258807786391 |
| admin.catalog.6e00da3a170bb184 | `ts_kurtosis({field}, 60)-3` | 34535942900375 |
| admin.catalog.78e60961a9077eb0 | `ts_std_dev({field},130)<0.3` | 33169668224919 |
| admin.catalog.84f9f5d2016807fc | `(ts_mean({field}, 126) / ts_std_dev({field}, 126))` | 41877348653335 |
| admin.catalog.ac7b74e821c80964 | `rank(ts_delta(ts_zscore({field}, 252), 252))` | 42258807786391 |
| admin.catalog.b9808ec3ac6d9e29 | `ts_decay_linear(ts_zscore(ts_backfill({field}, 66), 132), 22)` | 41135490599063 |
| admin.catalog.c56519808471417e | `ts_zscore(ts_backfill({field},252), 252)` | 26994972215319 |
| admin.catalog.e7c7ead2d22cef3f | `ts_std_dev({field},130)>0.7` | 33169668224919 |
| admin.catalog.0465301f9e63b453 | `ts_std_dev({field}, 5) != 0` | 39411791834647 |
| admin.catalog.08f5ca92b13346d9 | `ts_mean({field}, 20) / (ts_std_dev({field}, 60) + 0.001)` | 39411791834647 |
| admin.catalog.0bf43417f737d521 | `ts_std_dev({field},21)/ts_mean({field},21)` | 35876513619607 |
| admin.catalog.20917c4733dfe7d9 | `-ts_sum(ts_zscore({field}, 5), 120)` | 42061123738903 |
| admin.catalog.271deb2bf79167b9 | `(1 - ts_std_dev({field}, 10))` | 39411791834647 |
| admin.catalog.347f94e6e247fabf | `ts_zscore(rank({field}), 250)` | 39845230299927 |
| admin.catalog.35d973c4051540d5 | `ts_zscore(ts_quantile({field}, 252), 252)` | 42801904467607 |
| admin.catalog.46d7fc9f7cda5d91 | `ts_zscore(ts_sum({field} - ts_delay({field}, 1), 20), 20)` | 39411791834647 |
| admin.catalog.5b12f64fbbabbcec | `zscore(ts_delta(rank(ts_zscore({field},60)),5))` | 33603438929047 |
| admin.catalog.6ade08c03b378dfe | `({field} - ts_mean({field}, 126)) / ts_std_dev({field}, 126)` | 39411791834647 |
| admin.catalog.91115548ebeb3f05 | `rank({field}) - rank(ts_std_dev({field}, 20))` | 39411791834647 |
| admin.catalog.92429b1f76de8de5 | `rank(ts_zscore({field}, 5))` | 39411791834647 |
| admin.catalog.a389cdc522c961c1 | `ts_std_dev({field}, 20)` | 17086182851223 |
| admin.catalog.e21690170a49fb6b | `ts_delta({field}, 5) > ts_std_dev({field}, 22)` | 43031577079575 |
| admin.catalog.e2c718f2d0db94f4 | `ts_zscore(ts_mean({field}, 60), 250)` | 39411791834647 |
| admin.catalog.eab90082fecf4355 | `rank(ts_decay_linear(ts_zscore({field}, 504), 9))` | 41119909511319 |
