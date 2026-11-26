# WorldQuant BRAIN D1 RA 批次复盘与阶段漏斗总账（自动生成）

- **生成时间 (UTC)**：`2026-11-26T00:35:28.613998+00:00`
- **总批次数**：`696`（等级分布：`{'BEST': 35, 'GOOD': 34, 'NORMAL': 352, 'BAD': 195, 'TIMEOUT_BUG': 80}`）
- **全库阶段过关统计**：有效完成 `4179` · 未观测 `623` · **一阶段 (`Sh≥0.80`) 过 `606` 个** · **二阶段 (`Sh≥1.25`) 过 `270` 个** · **三阶段 (`Sh≥1.58 & Fit≥1.0`) 过 `109` 个**（已核 0-FAIL `43` 个）

## 1. 分地区阶段漏斗统计

| 地区 | 完成数 | 未观测 | 一阶段过 (`≥0.80`) | 二阶段过 (`≥1.25`) | 三阶段过 (`≥1.58 & Fit≥1`) | 已核 0-FAIL |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **USA** | 2184 | 104 | 221 | 18 | 1 | 1 |
| **EUR** | 1004 | 432 | 367 | 252 | 108 | 42 |
| **DEU** | 430 | 8 | 2 | 0 | 0 | 0 |
| **ASI** | 104 | 7 | 11 | 0 | 0 | 0 |
| **KOR** | 98 | 16 | 0 | 0 | 0 | 0 |
| **CHN** | 90 | 24 | 0 | 0 | 0 | 0 |
| **HKG** | 73 | 0 | 1 | 0 | 0 | 0 |
| **GBR** | 73 | 0 | 0 | 0 | 0 | 0 |
| **GLB** | 67 | 8 | 4 | 0 | 0 | 0 |
| **IND** | 32 | 16 | 0 | 0 | 0 | 0 |
| **AMR** | 24 | 8 | 0 | 0 | 0 | 0 |

## 2. 过好批次（BEST · 重点核查可复现性与推广）

| 批次 ID | 地区/池 | 数据集 | 主字段 | 模板族 | 配置 | 过 S1/S2/S3 (0-FAIL) | Max Sh / 2Y / Mgn | 冠军 ID |
| --- | :-: | --- | --- | --- | --- | :-: | :-: | :-: |
| `RA-v4-EUR_M25_PCT_NORM-00-egion_percentile-COUNTRY` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `COUNTRY|d=0|tr=0.04` | 3/3/3 (0) | `3.29` / `2.3` / `0.0bp` | `88Go2dA7` |
| `RA-v4-EUR_M25_PCT_NORM-00-egion_percentile-INDUSTRY` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `INDUSTRY|d=0|tr=0.04` | 3/3/3 (0) | `3.16` / `2.27` / `0.0bp` | `legq0aml` |
| `S3-r1b-EUR-M25A-u2500_sub_d2_t06` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `S3-ADM-01-atom-gate30-vm, S3-ADM-02-atom-gate45-vm, S3-ADM-03-atom-bkt-vm (+5)` | `SUBINDUSTRY|d=2|tr=0.06` | 8/8/7 (3) | `3.12` / `2.84` / `21.2bp` | `0mGljvn2` |
| `S3-r1b-EUR-M25A-u2500_ind_d0_t04` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `S3-ADM-01-atom-gate30-vm, S3-ADM-02-atom-gate45-vm, S3-ADM-03-atom-bkt-vm (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/8/7 (3) | `3.07` / `2.58` / `21.48bp` | `LL8j5Jz1` |
| `S3-r1b-EUR-M25B-u2500_sub_d2_t06` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `S3-ADM-05-adv-gate35-vm, S3-ADM-06-adv-gate50-vm, S3-ADM-07-adv-bkt-vm (+5)` | `SUBINDUSTRY|d=2|tr=0.06` | 8/8/6 (1) | `3.05` / `2.55` / `19.81bp` | `kq87Jl3l` |
| `S3-r1b-EUR-M25A-u2500_cty_d2_t06` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `S3-ADM-01-atom-gate30-vm, S3-ADM-02-atom-gate45-vm, S3-ADM-03-atom-bkt-vm (+5)` | `COUNTRY|d=2|tr=0.06` | 8/8/5 (1) | `2.99` / `2.53` / `25.37bp` | `88GovNrv` |
| `S3-r1b-EUR-M25B-u2500_ind_d0_t04` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `S3-ADM-05-adv-gate35-vm, S3-ADM-06-adv-gate50-vm, S3-ADM-07-adv-bkt-vm (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/8/6 (2) | `2.98` / `2.42` / `19.42bp` | `6XG8AOvP` |
| `S3-r1b-EUR-M25A-u2500_ram_d4_t06` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `S3-ADM-01-atom-gate30-vm, S3-ADM-02-atom-gate45-vm, S3-ADM-03-atom-bkt-vm (+5)` | `REVERSION_AND_MOMENTUM|d=4|tr=0.06` | 8/5/4 (0) | `2.64` / `3.19` / `15.64bp` | `xAl61rXl` |
| `S3-r1b-EUR-M25B-u2500_cty_d2_t06` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `S3-ADM-05-adv-gate35-vm, S3-ADM-06-adv-gate50-vm, S3-ADM-07-adv-bkt-vm (+5)` | `COUNTRY|d=2|tr=0.06` | 8/8/6 (1) | `2.39` / `2.33` / `23.27bp` | `6XG8dVNJ` |
| `S3-r2-EUR-M25PCA-stat_d4_t06` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `S3PC-ADM-01-vmoe-ci, S3PC-ADM-02-vmoe-ci-sp2, S3PC-ADM-03-vm-avdiff126-ci (+5)` | `STATISTICAL|d=4|tr=0.06` | 7/7/1 (0) | `2.31` / `2.75` / `5.39bp` | `np6RJWYM` |
| `S3-r1b-EUR-M25B-u2500_mkt_d4_t08` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `S3-ADM-05-adv-gate35-vm, S3-ADM-06-adv-gate50-vm, S3-ADM-07-adv-bkt-vm (+5)` | `MARKET|d=4|tr=0.08` | 8/7/6 (3) | `2.25` / `2.33` / `31.59bp` | `rK030WX9` |
| `S3-r2-EUR-M25PCA-stat_d6_t08` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `S3PC-ADM-01-vmoe-ci, S3PC-ADM-02-vmoe-ci-sp2, S3PC-ADM-03-vm-avdiff126-ci (+5)` | `STATISTICAL|d=6|tr=0.08` | 7/7/1 (0) | `2.24` / `2.71` / `5.69bp` | `vRYqEALz` |
| `S3-r3b-EUR-FINA-stat_d5_t08` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `S3FIN-ADM-01-acc-adv40, S3FIN-ADM-02-acc-adv45, S3FIN-ADM-03-acc-adv50 (+5)` | `STATISTICAL|d=5|tr=0.08` | 8/8/3 (1) | `2.22` / `2.57` / `6.2bp` | `0mG3nGJ2` |
| `S3-r2-EUR-M25PCB-stat_d4_t06` | EUR/TOP2500 | `model25` | `model25_x_model238` | `S3PC-ADM-05-vm-shpref-ci, S3PC-ADM-06-vm-shchg-ci, S3PC-ADM-07-oe-shpref-ci (+5)` | `STATISTICAL|d=4|tr=0.06` | 8/6/1 (0) | `2.21` / `2.83` / `3.88bp` | `gJrA5OlJ` |
| `S3-r2-EUR-M25PCA-crd_d4_t06` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `S3PC-ADM-01-vmoe-ci, S3PC-ADM-02-vmoe-ci-sp2, S3PC-ADM-03-vm-avdiff126-ci (+5)` | `CROWDING|d=4|tr=0.06` | 7/7/2 (0) | `2.17` / `2.85` / `10.52bp` | `np6JGN2l` |
| `S3-r3b-EUR-FINA-crd_d4_t06` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `S3FIN-ADM-01-acc-adv40, S3FIN-ADM-02-acc-adv45, S3FIN-ADM-03-acc-adv50 (+5)` | `CROWDING|d=4|tr=0.06` | 8/8/6 (6) | `2.14` / `2.75` / `13.01bp` | `3qGrQQ8Q` |
| `S3-r2-EUR-M25PCB-stat_d6_t08` | EUR/TOP2500 | `model25` | `model25_x_model238` | `S3PC-ADM-05-vm-shpref-ci, S3PC-ADM-06-vm-shchg-ci, S3PC-ADM-07-oe-shpref-ci (+5)` | `STATISTICAL|d=6|tr=0.08` | 7/6/1 (0) | `2.13` / `2.81` / `4.22bp` | `LL8a6qa9` |
| `S3-r3b-EUR-FINA-crd_d5_t08` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `S3FIN-ADM-01-acc-adv40, S3FIN-ADM-02-acc-adv45, S3FIN-ADM-03-acc-adv50 (+5)` | `CROWDING|d=5|tr=0.08` | 8/8/5 (5) | `2.1` / `2.73` / `13.7bp` | `np6RxVz3` |
| `S3-r1b-EUR-M25B-u2500_ram_d4_t06` | EUR/TOP2500 | `model25` | `value_momentum_region_percentile` | `S3-ADM-05-adv-gate35-vm, S3-ADM-06-adv-gate50-vm, S3-ADM-07-adv-bkt-vm (+5)` | `REVERSION_AND_MOMENTUM|d=4|tr=0.06` | 8/6/6 (5) | `2.09` / `2.82` / `15.31bp` | `A1LWQvwR` |
| `S3-r2-EUR-M25PCB-crd_d4_t06` | EUR/TOP2500 | `model25` | `model25_x_model238` | `S3PC-ADM-05-vm-shpref-ci, S3PC-ADM-06-vm-shchg-ci, S3PC-ADM-07-oe-shpref-ci (+5)` | `CROWDING|d=4|tr=0.06` | 6/3/1 (0) | `2.07` / `2.13` / `6.76bp` | `d59XJOGg` |

## 3. 过差与超时异常批次（BAD / TIMEOUT_BUG · 排雷与逻辑复盘）

| 等级 | 批次 ID | 地区/数据集 | 主字段 | 配置 | 完成/未观测 | Max Sh | 根因诊断与避坑建议 |
| :-: | --- | --- | --- | --- | :-: | :-: | --- |
| **TIMEOUT_BUG** | `RA-AMR_M239_FREE-mdl239_combo_deltacrossd-SUBINDUSTRY` | AMR/`model239` | `mdl239_combo_deltacrossdelta` | `SUBINDUSTRY|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Missing child alpha_id) |
| **TIMEOUT_BUG** | `RA-CHN_OTH496_RATIOS_FREE-oth496_curr_ratio-SUBINDUSTRY` | CHN/`other496` | `oth496_curr_ratio` | `SUBINDUSTRY|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Unobserved after 1 reconcile: Poll timeout) |
| **TIMEOUT_BUG** | `RA-CHN_OTH496_RATIOS_FREE-oth496_lt_lev-SUBINDUSTRY` | CHN/`other496` | `oth496_lt_lev` | `SUBINDUSTRY|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Unobserved after 1 reconcile: Poll timeout) |
| **TIMEOUT_BUG** | `RA-v3-CHN_ANL45_FREE-06-urn_excluding_fx-SUBINDUSTRY` | CHN/`analyst45` | `aggregate_return_excluding_fx` | `SUBINDUSTRY|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Unobserved after 1 reconcile: POST exception: ConnectionError) |
| **TIMEOUT_BUG** | `RA-DEU_M264_FREE-mdl264_1l_ovp-INDUSTRY` | DEU/`model264` | `mdl264_1l_ovp` | `INDUSTRY|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Missing child alpha_id) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-00-t_opinion_metric-CROWDING` | EUR/`ai_equity_alpha` | `analyst_opinion_metric` | `CROWDING|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Unobserved after 1 reconcile: Poll stalled at progress=0.15 for 240s) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-00-t_opinion_metric-REVERSION_AND_MOMENTUM` | EUR/`ai_equity_alpha` | `analyst_opinion_metric` | `REVERSION_AND_MOMENTUM|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Sim ERROR: There was an error while running the simulation. Please try again or ) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-01-evision_factor_3-CROWDING` | EUR/`ai_equity_alpha` | `analyst_forecast_revision_factor_3` | `CROWDING|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Unobserved after 1 reconcile: Poll stalled at progress=0.15 for 240s) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-01-evision_factor_3-REVERSION_AND_MOMENTUM` | EUR/`ai_equity_alpha` | `analyst_forecast_revision_factor_3` | `REVERSION_AND_MOMENTUM|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Sim ERROR: There was an error while running the simulation. Please try again or ) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-02-opinion_metric_6-CROWDING` | EUR/`ai_equity_alpha` | `analyst_opinion_metric_6` | `CROWDING|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Unobserved after 1 reconcile: Poll stalled at progress=0.90 for 240s [zombie DEL) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-03-opinion_metric_8-CROWDING` | EUR/`ai_equity_alpha` | `analyst_opinion_metric_8` | `CROWDING|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Unobserved after 1 reconcile: Poll stalled at progress=0.15 for 240s [zombie DEL) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-03-opinion_metric_8-REVERSION_AND_MOMENTUM` | EUR/`ai_equity_alpha` | `analyst_opinion_metric_8` | `REVERSION_AND_MOMENTUM|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Sim ERROR: There was an error while running the simulation. Please try again or ) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-04-evision_factor_2-CROWDING` | EUR/`ai_equity_alpha` | `analyst_forecast_revision_factor_2` | `CROWDING|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Sim ERROR: There was an error while running the simulation. Please try again or ) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-04-evision_factor_2-REVERSION_AND_MOMENTUM` | EUR/`ai_equity_alpha` | `analyst_forecast_revision_factor_2` | `REVERSION_AND_MOMENTUM|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Sim ERROR: There was an error while running the simulation. Please try again or ) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-05-evision_factor_4-CROWDING` | EUR/`ai_equity_alpha` | `analyst_forecast_revision_factor_4` | `CROWDING|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Sim ERROR: There was an error while running the simulation. Please try again or ) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-05-evision_factor_4-REVERSION_AND_MOMENTUM` | EUR/`ai_equity_alpha` | `analyst_forecast_revision_factor_4` | `REVERSION_AND_MOMENTUM|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Sim ERROR: There was an error while running the simulation. Please try again or ) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-06-opinion_metric_7-CROWDING` | EUR/`ai_equity_alpha` | `analyst_opinion_metric_7` | `CROWDING|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Sim ERROR: There was an error while running the simulation. Please try again or ) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-06-opinion_metric_7-REVERSION_AND_MOMENTUM` | EUR/`ai_equity_alpha` | `analyst_opinion_metric_7` | `REVERSION_AND_MOMENTUM|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Unobserved after 1 reconcile: Poll stalled at progress=0.15 for 240s) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-07-yst_view_score_2-CROWDING` | EUR/`ai_equity_alpha` | `analyst_view_score_2` | `CROWDING|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Sim ERROR: There was an error while running the simulation. Please try again or ) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-07-yst_view_score_2-REVERSION_AND_MOMENTUM` | EUR/`ai_equity_alpha` | `analyst_view_score_2` | `REVERSION_AND_MOMENTUM|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Unobserved after 1 reconcile: Poll stalled at progress=0.15 for 240s) |
| **TIMEOUT_BUG** | `RA-v4-EUR_AIEQ_ALPHA_VEC_NORM-DUAL-REVERSION_AND_MOMENTUM-00` | EUR/`ai_equity_alpha` | `analyst_opinion_metric` | `REVERSION_AND_MOMENTUM|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Unobserved after 1 reconcile: Poll HTTP 500) |
| **TIMEOUT_BUG** | `RA-v4-EUR_M238_SMARTHOLDINGS_NORM-01-lignment_rank_d1-CROWDING` | EUR/`model238` | `global_screening_factor_alignment_rank_d1` | `CROWDING|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Unobserved after 1 reconcile: Poll stalled at progress=0.15 for 240s) |
| **TIMEOUT_BUG** | `RA-v4-EUR_M238_SMARTHOLDINGS_NORM-01-lignment_rank_d1-STATISTICAL` | EUR/`model238` | `global_screening_factor_alignment_rank_d1` | `STATISTICAL|d=0|tr=0.04` | 0/8 | `None` | Risk-model neutralization timeout/429 on wide universe; lower concurrency or raise timeout (Unobserved after 1 reconcile: Poll timeout) |
| **TIMEOUT_BUG** | `RA-v4-EUR_M238_SMARTHOLDINGS_NORM-02-eference_rank_d1-STATISTICAL` | EUR/`model238` | `regional_change_in_preference_rank_d1` | `STATISTICAL|d=0|tr=0.04` | 0/8 | `None` | Risk-model neutralization timeout/429 on wide universe; lower concurrency or raise timeout (Unobserved after 1 reconcile: Poll timeout) |
| **TIMEOUT_BUG** | `RA-v4-EUR_M238_SMARTHOLDINGS_NORM-03-eference_rank_d1-REVERSION_AND_MOMENTUM` | EUR/`model238` | `regional_institutional_preference_rank_d1` | `REVERSION_AND_MOMENTUM|d=0|tr=0.04` | 0/8 | `None` | All tasks unobserved (check HTTP 429 or poll timeout) (Sim ERROR: There was an error while running the simulation. Please try again or ) |

## 4. 全批次精简台账（展示前 120 / 696 批）

| 等级 | 地区 | 数据集 | 主字段 | 模板 | 配置 | 完成/未观测 | S1/S2/S3 | Max Sh | Avg Mgn |
| :-: | :-: | --- | --- | --- | --- | :-: | :-: | :-: | :-: |
| BAD | AMR | `model239` | `mdl239_combo_tickets` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.42` | `-2.23bp` |
| BAD | AMR | `model239` | `mdl239_shortlasso1d` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.39` | `0.89bp` |
| BAD | AMR | `model239` | `mdl239_combo_crossdeltaactivity` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.19` | `-0.85bp` |
| TIMEOUT_BUG | AMR | `model239` | `mdl239_combo_deltacrossdelta` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 0/8 | 0/0/0 | `None` | `Nonebp` |
| NORMAL | ASI | `price_signal_dl` | `asi_nv1_m22` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `REVERSION_AND_MOMENTUM|d=0|tr=0.04` | 8/0 | 1/0/0 | `1.21` | `0.0bp` |
| NORMAL | ASI | `price_signal_dl` | `normalized_volume_indicator_2` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `COUNTRY|d=0|tr=0.04` | 8/0 | 2/0/0 | `1.13` | `0.2bp` |
| NORMAL | ASI | `price_signal_dl` | `asi_nv2_m22` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `REVERSION_AND_MOMENTUM|d=0|tr=0.04` | 8/0 | 1/0/0 | `1.04` | `0.0bp` |
| NORMAL | ASI | `price_signal_dl` | `asi_nv2_m22` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `COUNTRY|d=0|tr=0.04` | 8/0 | 2/0/0 | `1.02` | `1.25bp` |
| NORMAL | ASI | `price_signal_dl` | `asi_nv0_m22` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `REVERSION_AND_MOMENTUM|d=0|tr=0.04` | 8/0 | 1/0/0 | `0.97` | `0.0bp` |
| NORMAL | ASI | `price_signal_dl` | `normalized_volume_indicator_1` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `COUNTRY|d=0|tr=0.04` | 8/0 | 1/0/0 | `0.96` | `0.91bp` |
| NORMAL | ASI | `price_signal_dl` | `asi_nv1_m22` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `COUNTRY|d=0|tr=0.04` | 8/0 | 1/0/0 | `0.88` | `1.11bp` |
| NORMAL | ASI | `price_signal_dl` | `normalized_volume_indicator_5` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `COUNTRY|d=0|tr=0.04` | 7/0 | 2/0/0 | `0.83` | `0.97bp` |
| NORMAL | ASI | `behavioral_signals` | `visual_price_path_shape_score` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `COUNTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.79` | `0.0bp` |
| NORMAL | ASI | `price_signal_dl` | `normalized_volume_indicator_0` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `COUNTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.75` | `1.03bp` |
| NORMAL | ASI | `price_signal_dl` | `asi_nv0_m22` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `COUNTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.65` | `0.71bp` |
| BAD | ASI | `price_signal_dl` | `asi_rt4_m22` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `REVERSION_AND_MOMENTUM|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.53` | `0.0bp` |
| BAD | ASI | `price_signal_dl` | `asi_rt4_m22` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `COUNTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.38` | `1.06bp` |
| NORMAL | ASI | `price_signal_dl` | `normalized_volume_indicator_0, normalized_volume_indicator_1, normalized_volume_indicator_5` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `COUNTRY|d=0|tr=0.04` | 1/7 | 0/0/0 | `-0.34` | `-1.22bp` |
| NORMAL | ASI | `price_signal_dl` | `normalized_volume_indicator_2` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `COUNTRY|d=0|tr=0.04` | 0/0 | 0/0/0 | `None` | `Nonebp` |
| NORMAL | ASI | `price_signal_dl` | `normalized_volume_indicator_0` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `COUNTRY|d=0|tr=0.04` | 0/0 | 0/0/0 | `None` | `Nonebp` |
| NORMAL | ASI | `price_signal_dl` | `normalized_volume_indicator_1` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `COUNTRY|d=0|tr=0.04` | 0/0 | 0/0/0 | `None` | `Nonebp` |
| NORMAL | ASI | `price_signal_dl` | `normalized_volume_indicator_5` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `COUNTRY|d=0|tr=0.04` | 0/0 | 0/0/0 | `None` | `Nonebp` |
| NORMAL | ASI | `behavioral_signals` | `extreme_daily_return_indicator` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `COUNTRY|d=0|tr=0.04` | 0/0 | 0/0/0 | `None` | `Nonebp` |
| NORMAL | ASI | `behavioral_signals` | `salience_weighted_return_score` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `COUNTRY|d=0|tr=0.04` | 0/0 | 0/0/0 | `None` | `Nonebp` |
| NORMAL | ASI | `behavioral_signals` | `price_path_curvature_measure` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `COUNTRY|d=0|tr=0.04` | 0/0 | 0/0/0 | `None` | `Nonebp` |
| BAD | CHN | `analyst45` | `risk_adjusted_return_treynor` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.39` | `-3.58bp` |
| BAD | CHN | `analyst45` | `relative_index_return_value_2` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.26` | `-4.73bp` |
| BAD | CHN | `analyst45` | `aggregate_return_percentage` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.22` | `-4.76bp` |
| BAD | CHN | `analyst45` | `risk_adjusted_performance_alpha` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.21` | `-4.16bp` |
| BAD | CHN | `analyst45` | `mean_daily_return_pct` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.2` | `-4.62bp` |
| BAD | CHN | `analyst45` | `net_exposure_value` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.11` | `-6.4bp` |
| BAD | CHN | `analyst45` | `mean_daily_relative_index_return_pct` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.1` | `-5.2bp` |
| BAD | CHN | `other496` | `oth496_rec_share` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `-0.21` | `-27.63bp` |
| BAD | CHN | `other496` | `oth496_curr_ratio` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 5/0 | 0/0/0 | `-0.23` | `-12.43bp` |
| BAD | CHN | `other496` | `oth496_lt_lev_raw` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 5/0 | 0/0/0 | `-0.29` | `-25.38bp` |
| BAD | CHN | `other496` | `oth496_pay_rec_power` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `-0.3` | `-22.79bp` |
| BAD | CHN | `other496` | `oth496_ar_ca_raw` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 5/0 | 0/0/0 | `-0.32` | `-16.95bp` |
| BAD | CHN | `other496` | `oth496_ap_ar_raw` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 3/0 | 0/0/0 | `-0.97` | `-14.34bp` |
| TIMEOUT_BUG | CHN | `other496` | `oth496_curr_ratio` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 0/8 | 0/0/0 | `None` | `Nonebp` |
| TIMEOUT_BUG | CHN | `other496` | `oth496_lt_lev` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 0/8 | 0/0/0 | `None` | `Nonebp` |
| TIMEOUT_BUG | CHN | `analyst45` | `aggregate_return_excluding_fx` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 0/8 | 0/0/0 | `None` | `Nonebp` |
| NORMAL | DEU | `fundamental6` | `fnd6_roa` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 4/0 | 1/0/0 | `0.9` | `7.21bp` |
| NORMAL | DEU | `fundamental6` | `fnd6_roe` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 4/0 | 1/0/0 | `0.85` | `5.64bp` |
| NORMAL | DEU | `model264` | `mdl264_1l_fmc` | `RA-DUAL-MIN-SUBINDUSTRY, RA-DUAL-REV-MIN-SUBINDUSTRY` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.78` | `0.0bp` |
| NORMAL | DEU | `model264` | `mdl264_1l_opp` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.71` | `-3.38bp` |
| NORMAL | DEU | `model264` | `mdl264_1l_opp` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.71` | `-3.58bp` |
| NORMAL | DEU | `model264` | `mdl264_1l_ist` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.69` | `-2.36bp` |
| NORMAL | DEU | `model264` | `mdl264_1l_icc` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.63` | `-3.79bp` |
| NORMAL | DEU | `model264` | `mdl264_1l_icc` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.63` | `-4.04bp` |
| NORMAL | DEU | `model264` | `mdl264_1l_ist` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.63` | `-2.53bp` |
| NORMAL | DEU | `model264` | `mdl264_1l_m1r_mtn_spfc_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.63` | `-5.4bp` |
| NORMAL | DEU | `model264` | `mdl264_1l_m1r_cer_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.62` | `-4.56bp` |
| NORMAL | DEU | `model264` | `mdl264_1l_ifm` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.61` | `-4.02bp` |
| BAD | DEU | `model264` | `mdl264_1l_opd` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.59` | `-2.44bp` |
| BAD | DEU | `model264` | `mdl264_1l_fmc, mdl264_1l_ifm` | `RA-DUAL-MIN-SUBINDUSTRY, RA-DUAL-REV-MIN-SUBINDUSTRY` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.57` | `0.0bp` |
| BAD | DEU | `model264` | `mdl264_1l_opd` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.57` | `-2.62bp` |
| BAD | DEU | `analyst93` | `anl93_recprofitabilityprev_analyst_profitability1` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.55` | `2.54bp` |
| BAD | DEU | `model264` | `mdl264_1l_ifm` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.55` | `-3.71bp` |
| BAD | DEU | `model264` | `mdl264_1l_m1r_1yf_van_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.54` | `-4.64bp` |
| BAD | DEU | `model264` | `mdl264_1l_ompd` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.54` | `-2.69bp` |
| BAD | DEU | `model264` | `mdl264_1l_ompd` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.54` | `-2.85bp` |
| BAD | DEU | `fundamental6` | `fnd6_gp_at` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.54` | `-5.93bp` |
| BAD | DEU | `model264` | `mdl264_1l_rta` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.53` | `-3.5bp` |
| BAD | DEU | `model264` | `mdl264_1l_rta` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.53` | `-3.77bp` |
| BAD | DEU | `model264` | `mdl264_1l_os` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.52` | `-2.0bp` |
| BAD | DEU | `model264` | `mdl264_1l_os` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.52` | `-2.06bp` |
| BAD | DEU | `analyst93` | `anl93_profitabilityprev_analyst_profitability2_60d` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.51` | `-3.49bp` |
| BAD | DEU | `model264` | `mdl264_1l_m1d_1yf_spd_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.51` | `-4.31bp` |
| BAD | DEU | `model264` | `mdl264_1l_ovp` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.51` | `-3.51bp` |
| BAD | DEU | `model264` | `mdl264_1l_m1d_gtl_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.5` | `-3.92bp` |
| BAD | DEU | `model264` | `mdl264_1l_m1r_mtn_spd_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.5` | `-4.3bp` |
| BAD | DEU | `model264` | `mdl264_1l_m3d_1yf_van_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.48` | `-2.18bp` |
| NORMAL | DEU | `fundamental6` | `fnd6_gp_at` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 4/0 | 0/0/0 | `0.48` | `6.79bp` |
| BAD | DEU | `model264` | `mdl264_1l_ips` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.47` | `-3.31bp` |
| BAD | DEU | `fundamental6` | `fnd6_roa` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.46` | `-11.02bp` |
| BAD | DEU | `fundamental6` | `fnd6_cash_at` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.46` | `-6.5bp` |
| BAD | DEU | `model264` | `mdl264_1l_lda` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.45` | `-3.09bp` |
| BAD | DEU | `model264` | `mdl264_1l_lda` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.45` | `-3.46bp` |
| BAD | DEU | `model264` | `mdl264_1l_m1r_gtl_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.44` | `-3.28bp` |
| BAD | DEU | `model264` | `mdl264_1l_m1d_cer_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.42` | `-2.82bp` |
| BAD | DEU | `model264` | `mdl264_1l_m1d_cer_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.42` | `-3.04bp` |
| BAD | DEU | `fundamental6` | `fnd6_roe` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.39` | `-8.47bp` |
| BAD | DEU | `model264` | `mdl264_1l_fmc` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.38` | `-3.22bp` |
| BAD | DEU | `model264` | `mdl264_1l_fmc` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.38` | `-3.5bp` |
| BAD | DEU | `model264` | `mdl264_1l_m1d_pt_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.37` | `-3.21bp` |
| BAD | DEU | `analyst93` | `anl93_profitabilityprev_estimator_profitability1` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.36` | `1.85bp` |
| BAD | DEU | `model264` | `mdl264_1l_ips` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.35` | `-3.52bp` |
| BAD | DEU | `model264` | `mdl264_1l_od` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.35` | `-3.41bp` |
| BAD | DEU | `model264` | `mdl264_1l_od` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.35` | `-3.72bp` |
| BAD | DEU | `other250` | `sales_position_rank` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.35` | `0.41bp` |
| BAD | DEU | `other250` | `oth250_item_display_price` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.33` | `0.36bp` |
| NORMAL | DEU | `fundamental6` | `fnd6_cash_at` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 4/0 | 0/0/0 | `0.27` | `6.44bp` |
| BAD | DEU | `other250` | `oth250_item_review_count` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.23` | `-0.33bp` |
| BAD | DEU | `other250` | `total_review_number` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.23` | `-0.33bp` |
| BAD | DEU | `model264` | `mdl264_1l_m1d_1yf_van_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.2` | `-0.13bp` |
| BAD | DEU | `analyst93` | `anl93_profitabilityprev_analyst_profitability1_60d` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 8/0 | 0/0/0 | `0.16` | `-2.85bp` |
| NORMAL | DEU | `analyst93` | `anl93_profitabilityprev_estimator_profitability1` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 3/0 | 0/0/0 | `-0.29` | `-4.71bp` |
| NORMAL | DEU | `analyst93` | `anl93_recprofitabilityprev_analyst_profitability1` | `RA-ADM-01-sub-grank-z66-pos, RA-ADM-02-rev-sub-grank-z66, RA-ADM-03-sub-grank-dec10 (+5)` | `SUBINDUSTRY|d=0|tr=0.04` | 3/0 | 0/0/0 | `-0.55` | `-7.24bp` |
| NORMAL | DEU | `model264` | `mdl264_1l_m1d_1yf_spd_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 0/0 | 0/0/0 | `None` | `Nonebp` |
| NORMAL | DEU | `model264` | `mdl264_1l_m1d_pt_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 0/0 | 0/0/0 | `None` | `Nonebp` |
| NORMAL | DEU | `model264` | `mdl264_1l_m1r_cer_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 0/0 | 0/0/0 | `None` | `Nonebp` |
| NORMAL | DEU | `model264` | `mdl264_1l_m1r_mtn_spd_se` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 0/0 | 0/0/0 | `None` | `Nonebp` |
| TIMEOUT_BUG | DEU | `model264` | `mdl264_1l_ovp` | `RA-ADM-01-rank-m22, RA-ADM-02-rev-rank-m22, RA-ADM-03-sub-grank-dec10 (+5)` | `INDUSTRY|d=0|tr=0.04` | 0/8 | 0/0/0 | `None` | `Nonebp` |
| BEST | EUR | `model25` | `value_momentum_region_percentile` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `COUNTRY|d=0|tr=0.04` | 8/0 | 3/3/3 | `3.29` | `0.0bp` |
| BEST | EUR | `model25` | `value_momentum_region_percentile` | `RA-ADM-01-sub-gz-m22-pos, RA-ADM-02-rev-sub-gz-m22, RA-ADM-03-sub-grank-dec10-pos (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 3/3/3 | `3.16` | `0.0bp` |
| BEST | EUR | `model25` | `value_momentum_region_percentile` | `S3-ADM-01-atom-gate30-vm, S3-ADM-02-atom-gate45-vm, S3-ADM-03-atom-bkt-vm (+5)` | `SUBINDUSTRY|d=2|tr=0.06` | 8/0 | 8/8/7 | `3.12` | `21.2bp` |
| BEST | EUR | `model25` | `value_momentum_region_percentile` | `S3-ADM-01-atom-gate30-vm, S3-ADM-02-atom-gate45-vm, S3-ADM-03-atom-bkt-vm (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 8/8/7 | `3.07` | `21.48bp` |
| BEST | EUR | `model25` | `value_momentum_region_percentile` | `S3-ADM-05-adv-gate35-vm, S3-ADM-06-adv-gate50-vm, S3-ADM-07-adv-bkt-vm (+5)` | `SUBINDUSTRY|d=2|tr=0.06` | 8/0 | 8/8/6 | `3.05` | `19.81bp` |
| BEST | EUR | `model25` | `value_momentum_region_percentile` | `S3-ADM-01-atom-gate30-vm, S3-ADM-02-atom-gate45-vm, S3-ADM-03-atom-bkt-vm (+5)` | `COUNTRY|d=2|tr=0.06` | 8/0 | 8/8/5 | `2.99` | `25.37bp` |
| BEST | EUR | `model25` | `value_momentum_region_percentile` | `S3-ADM-05-adv-gate35-vm, S3-ADM-06-adv-gate50-vm, S3-ADM-07-adv-bkt-vm (+5)` | `INDUSTRY|d=0|tr=0.04` | 8/0 | 8/8/6 | `2.98` | `19.42bp` |
| BEST | EUR | `model25` | `value_momentum_region_percentile` | `S3-ADM-01-atom-gate30-vm, S3-ADM-02-atom-gate45-vm, S3-ADM-03-atom-bkt-vm (+5)` | `REVERSION_AND_MOMENTUM|d=4|tr=0.06` | 8/0 | 8/5/4 | `2.64` | `15.64bp` |
| BEST | EUR | `model25` | `value_momentum_region_percentile` | `S3-ADM-05-adv-gate35-vm, S3-ADM-06-adv-gate50-vm, S3-ADM-07-adv-bkt-vm (+5)` | `COUNTRY|d=2|tr=0.06` | 8/0 | 8/8/6 | `2.39` | `23.27bp` |
| BEST | EUR | `model25` | `value_momentum_region_percentile` | `S3PC-ADM-01-vmoe-ci, S3PC-ADM-02-vmoe-ci-sp2, S3PC-ADM-03-vm-avdiff126-ci (+5)` | `STATISTICAL|d=4|tr=0.06` | 8/0 | 7/7/1 | `2.31` | `5.39bp` |
| BEST | EUR | `model25` | `value_momentum_region_percentile` | `S3-ADM-05-adv-gate35-vm, S3-ADM-06-adv-gate50-vm, S3-ADM-07-adv-bkt-vm (+5)` | `MARKET|d=4|tr=0.08` | 8/0 | 8/7/6 | `2.25` | `31.59bp` |
| BEST | EUR | `model25` | `value_momentum_region_percentile` | `S3PC-ADM-01-vmoe-ci, S3PC-ADM-02-vmoe-ci-sp2, S3PC-ADM-03-vm-avdiff126-ci (+5)` | `STATISTICAL|d=6|tr=0.08` | 8/0 | 7/7/1 | `2.24` | `5.69bp` |
| BEST | EUR | `model25` | `value_momentum_region_percentile` | `S3FIN-ADM-01-acc-adv40, S3FIN-ADM-02-acc-adv45, S3FIN-ADM-03-acc-adv50 (+5)` | `STATISTICAL|d=5|tr=0.08` | 8/0 | 8/8/3 | `2.22` | `6.2bp` |
| BEST | EUR | `model25` | `model25_x_model238` | `S3PC-ADM-05-vm-shpref-ci, S3PC-ADM-06-vm-shchg-ci, S3PC-ADM-07-oe-shpref-ci (+5)` | `STATISTICAL|d=4|tr=0.06` | 8/0 | 8/6/1 | `2.21` | `3.88bp` |
| BEST | EUR | `model25` | `value_momentum_region_percentile` | `S3PC-ADM-01-vmoe-ci, S3PC-ADM-02-vmoe-ci-sp2, S3PC-ADM-03-vm-avdiff126-ci (+5)` | `CROWDING|d=4|tr=0.06` | 8/0 | 7/7/2 | `2.17` | `10.52bp` |
| BEST | EUR | `model25` | `value_momentum_region_percentile` | `S3FIN-ADM-01-acc-adv40, S3FIN-ADM-02-acc-adv45, S3FIN-ADM-03-acc-adv50 (+5)` | `CROWDING|d=4|tr=0.06` | 8/0 | 8/8/6 | `2.14` | `13.01bp` |
| BEST | EUR | `model25` | `model25_x_model238` | `S3PC-ADM-05-vm-shpref-ci, S3PC-ADM-06-vm-shchg-ci, S3PC-ADM-07-oe-shpref-ci (+5)` | `STATISTICAL|d=6|tr=0.08` | 8/0 | 7/6/1 | `2.13` | `4.22bp` |
