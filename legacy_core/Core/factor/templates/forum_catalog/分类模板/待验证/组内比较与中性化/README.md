# 组内比较与中性化：62个模板

全部本地合规通过，收益未验证；供爬山候选轮动，实际字段和范围仍须检查。

| 模板编号 | 表达式 | 来源帖子 |
|---|---|---|
| admin.catalog.6d45ce1b692bca90 | `group_zscore({field},sector)` | 26054361848343 |
| admin.catalog.829bd31f8bf03c42 | `group_mean({field},1,market)` | 26054361848343 |
| admin.catalog.f4ea125ae146da28 | `scale(group_neutralize(ts_av_diff({field},504),subindustry))` | 24957813446167 |
| admin.catalog.ff73b6d6e9d3713a | `quantile(group_neutralize(ts_av_diff({field},252),subindustry))` | 24957813446167 |
| admin.catalog.15c3fed1b5a7fe97 | `ts_product(1+group_mean({field},1,market),250)-1` | 19992945218711 |
| admin.catalog.3518a881e1223972 | `ts_zscore(group_neutralize(ts_delta({field}, 3), industry), 30) * -1` | 39441605621911 |
| admin.catalog.3d773bbce9f5fb8d | `group_rank(ts_backfill({field}, 66), industry)` | 33247252289943 |
| admin.catalog.48d3754fa477d65c | `group_zscore(ts_delta({field}, 5), industry)` | 39441605621911 |
| admin.catalog.4fc603eca09c27d7 | `group_mean({field}, 1 , densify(exchange))` | 20284582494359 |
| admin.catalog.5deb740763be054d | `group_rank(ts_quantile(ts_backfill({field}, 60), 60), densify(sector))` | 39441605621911 |
| admin.catalog.6a03b7ede8cd7e7c | `group_rank(ts_zscore(ts_delta({field}, 5), 60), sector)` | 39441605621911 |
| admin.catalog.7c3ddd81b6e966a1 | `group_neutralize(rank(ts_backfill({field}, 5)), sector)` | 39441605621911 |
| admin.catalog.8f97d7b4db20cac1 | `group_zscore(ts_zscore(ts_delta({field}, 2), 20), industry) * -1` | 39441605621911 |
| admin.catalog.977fd958136db55c | `group_neutralize(rank(ts_rank(-ts_delta({field}, 1), 252)), subindustry)` | 42278736684311 |
| admin.catalog.ac0a4ad104cc6e63 | `group_rank(ts_rank(ts_delta({field}, 20), 20), sector)` | 39441605621911 |
| admin.catalog.bc29fee0a723ee48 | `group_rank(ts_arg_max(ts_backfill({field}, 120), 22),densify(market))` | 40436845240087 |
| admin.catalog.e918b3905d29a78c | `group_count({field}, market)` | 29085671898775 |
| admin.catalog.f65371a4690a9262 | `ts_rank(group_neutralize({field}, industry), 10)` | 24497520676119 |
| admin.catalog.181ee1451874a033 | `group_neutralize(ts_rank(ts_delta({field}, 5), 60), densify(sector))` | 36221002981271 |
| admin.catalog.18c3ee043da23e99 | `{field}/group_sum({field},market)` | 34535942900375 |
| admin.catalog.29fb904d1fa5211f | `group_rank(-ts_delta({field}, 5), market)` | 36772449354519 |
| admin.catalog.3b002527d4296814 | `group_rank(ts_zscore(ts_backfill({field}, 66), 132), subindustry)` | 41135490599063 |
| admin.catalog.3e38dfd4df5c56b4 | `{field} - group_mean({field},1,market)` | 37245403025431 |
| admin.catalog.82cf1239ad79bcfd | `group_neutralize(zscore({field}), industry)` | 34670122621207 |
| admin.catalog.9118cb42b80ef01a | `group_neutralize(ts_rank(ts_mean({field}, 20), 60), densify(sector))` | 36221002981271 |
| admin.catalog.987be298b9f7cbc8 | `rank(group_mean({field}, 1, country))` | 42258807786391 |
| admin.catalog.9c25dd6913b0cd15 | `group_rank(ts_scale({field}, 240), industry)` | 40972941718807 |
| admin.catalog.ad967f9ce732c34f | `group_neutralize({field}, group_cartesian_product(country, industry))` | 34208186164631 |
| admin.catalog.b43b2a2f7306d1cc | `-group_backfill({field}, subindustry, 126, std = 4.0)` | 35090833341207 |
| admin.catalog.026c9d4962919908 | `group_rank(ts_delta({field}, 20), industry)` | 39411791834647 |
| admin.catalog.083babe84c644b32 | `ts_zscore({field}, 63) - ts_zscore(group_neutralize({field}, sector), 63)` | 42045578950551 |
| admin.catalog.0d7aa64ca33d8309 | `group_neutralize(rank({field})/ts_std_dev({field}, 10),industry)` | 39411791834647 |
| admin.catalog.1a65b86be62b7cdc | `group_neutralize(ts_rank(ts_rank({field}, 21) * ts_std_dev({field}, 10), 63), sector)` | 39411791834647 |
| admin.catalog.1aafdef3c1c0cead | `group_neutralize(ts_zscore({field}, 20), industry)` | 30640499518231 |
| admin.catalog.26b7770003e7f67a | `group_rank(ts_mean({field}, 20), industry)` | 37176161580823 |
| admin.catalog.27038cd424c17de9 | `group_rank(ts_sum({field}, 5), subindustry)` | 39411791834647 |
| admin.catalog.35d997f31b1d3b2f | `group_std_dev({field}, market)` | 19144966455959 |
| admin.catalog.3a0d64cc91eb21bc | `group_neutralize(rank({field}), industry)` | 39411791834647 |
| admin.catalog.3a5a5d561a547479 | `group_zscore(ts_zscore(ts_delta({field}, 22), 66), subindustry)` | 42021244122775 |
| admin.catalog.484e8e140e4c63ca | `group_rank(ts_backfill(ts_backfill({field}, 120), 120), subindustry)` | 39411791834647 |
| admin.catalog.486dea3a8955475b | `group_count({field}, densify(market))` | 28263052428055 |
| admin.catalog.4cba4fe9f9fa93af | `group_rank(ts_zscore({field}, 63), subindustry)` | 39411791834647 |
| admin.catalog.7a5fb1191d6172ba | `group_rank({field}, subindustry)` | 39411791834647 |
| admin.catalog.857d7c54c7cd0155 | `group_rank(ts_mean({field},20),country)>0.03` | 37473718017175 |
| admin.catalog.90dd328112854f99 | `ts_delay(ts_mean({field}-group_mean({field},1,market),20),20)` | 20089517507735 |
| admin.catalog.90f13264baf0f1fd | `group_rank({field}, densify(subindustry))` | 42662873714711 |
| admin.catalog.98806ef0d73b3a42 | `rank(group_rank({field}, industry))` | 39411791834647 |
| admin.catalog.98ab1a0dc9f607b6 | `group_zscore(ts_zscore(ts_mean({field}, 5) - ts_mean({field}, 22), 66), industry)` | 39411791834647 |
| admin.catalog.992a3726f07a002c | `group_neutralize(ts_rank({field}, 21), sector)` | 39411791834647 |
| admin.catalog.9dbfb149114b1868 | `group_zscore(ts_mean(ts_rank({field},126),5),subindustry)` | 42509573118999 |
| admin.catalog.a323df1a154a3669 | `ts_mean({field}-group_mean({field},1,market),5)` | 20089517507735 |
| admin.catalog.a65fab7cf9f15c1d | `group_rank(ts_rank(ts_mean({field}, 10), 40), subindustry)` | 39411791834647 |
| admin.catalog.af80a3d86052bff1 | `group_rank(ts_decay_linear({field}, 10), subindustry)` | 39411791834647 |
| admin.catalog.b52bf47837f9df38 | `group_rank(ts_rank({field}, 20), industry)` | 39411791834647 |
| admin.catalog.bdfe840cb8421769 | `rank(group_neutralize(ts_mean({field}, 5), industry))` | 39411791834647 |
| admin.catalog.d5a918734056cc0d | `-group_rank(ts_delta(ts_backfill(ts_backfill({field}, 120), 120), 252), industry)` | 39411791834647 |
| admin.catalog.da9212ca780efab0 | `min(group_rank({field}, sector), rank(ts_delta({field}, 66)))` | 32032672214807 |
| admin.catalog.e3fa541ba2c827d9 | `group_zscore(-ts_delta({field}, 2), sector)` | 39411791834647 |
| admin.catalog.e5c480d54fdd4d16 | `group_rank(ts_std_dev({field},60),sector)>0.7` | 40531412200471 |
| admin.catalog.ebbad5ec9f47a11b | `group_rank(ts_quantile(-ts_backfill({field}, 120), 126), subindustry)` | 43322521365143 |
| admin.catalog.f7bc659155753576 | `group_neutralize({field}, subindustry)` | 41134649919383 |
| admin.catalog.fe3b6dc2204a475a | `group_neutralize(group_zscore({field}, industry), industry)` | 42775887653399 |
