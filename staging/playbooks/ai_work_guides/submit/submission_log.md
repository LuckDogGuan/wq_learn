# 因子审查与人工提交记录

> AI 只记录候选、检查与建议；严禁调用 `submit_alpha`。

## 记录模板

## 2026-08-09 — non-Model/PV Sentiment26 and field-discovery refresh

- 表达式：`hump(rank(vec_avg(snt26_relpopularity08_43)))`、`hump(rank(vec_avg(snt26_relpopularity1_35)))`
- Alpha ID：`wpaRjzLv`、`e73OQlLE`
- AST 算子节点数：每条 3；唯一字段：每条 1；无禁用算子
- 设置：GLB / D1 / TOPDIV3000；neutralization=INDUSTRY；truncation=0.01
- 指标：wpaRjzLv S=0.78/F=0.42/TO=0.1389/margin=0.000570；e73OQlLE S=0.79/F=0.42/TO=0.1394/margin=0.000574
- 决策：Sentiment26 信号已确认但低于 Sharpe/Fitness 门槛；未提交
- 新字段：`oth546_busnet_strength`、`oth546_analystnet_common`、`relative_interest_score_4`、`oth635_sentiment`、`mws36_relevance`、`mws36_novelty`、`oth296_sentiment`、`oth296_prob_pos`
- 结果：首次调用 HTTP 429；等待 120 秒后重试，cnhkmcp 继续等待 300 秒超时，记录时账户尚未确认 Alpha ID。重试批次误用 TOP3000，不能计入本 TOPDIV3000 目标。

## 2026-08-09 — account confirmation for additional VECTOR batch

- 账户扫描确认 8 条结果，但平台记录设置为 GLB / D1 / TOP3000，而目标为 TOPDIV3000，全部排除：
  `58pwglO1` S=0.16/F=0.03/TO=0.0872,
  `npNgP78M` S=0.17/F=0.02/TO=0.0869,
  `omNKWqgn` S=0.94/F=0.20/TO=0.6820,
  `ZYEpA7KQ` S=0.05/F=0.00/TO=1.1010,
  `MPGp37Lr` S=-0.15/F=-0.01/TO=1.6000,
  `GrGwOlGJ` S=0.29/F=0.03/TO=1.5385,
  `vRNL2jNd` S=0.24/F=0.04/TO=1.6263,
  `d5Zx1jZY` S=-0.59/F=-0.15/TO=1.6339。
- 决策：不计入 PPA；未调用 `submit_alpha`。当前合格数仍为 0/5。

## 2026-08-09 — TOPDIV3000 Sentiment21/22 first-order screen

- 设置：GLB / D1 / TOPDIV3000；neutralization=INDUSTRY；truncation=0.01
- 结果：`npNgAXzM` `rank(snt21_2neg_mean)` S=0.63/F=0.10/TO=1.5164；`omNKokzn` `rank(snt21_2dts_gen_391)` S=0.41/F=0.05/TO=1.4467；`qMNAEwmv` `rank(snt22_2pos_mean_395)` S=0.22/F=0.02/TO=1.5245；其余同批次为负或更弱
- AST：1 each；唯一字段：1 each；category 为 Sentiment，非 Model/PV
- 决策：全批次淘汰，主要问题是低 Sharpe/Fitness 和极高换手；未进入多角度优化

## 2026-08-09 — GA recommendation applied

- 参考：`testFile/GA_results.md` 的代际筛选、亲本保留、窗口/decay/中性化变异与相关性去重流程，并按当前硬限制重写为单字段优先的 genotype
- 当前亲本：`N1bpe5LX` `rank(vec_avg(relative_interest_score_4))`，TOPDIV3000/INDUSTRY，S=0.95/F=0.22/TO=0.6694
- 约束：不使用 Model/PV 字段，不使用 `multiply`/`add`/`trade_when`，AST<6，unique fields<=2；仅在亲本有改善后进入相关性与提交前检查
- `relative_interest_score_4` 的八变体和后续两变体调用均在 cnhkmcp 300 秒等待上超时；截至账户扫描尚无对应 Alpha ID，故不记录为已验证结果

## 2026-08-09 — Fundamental17 first-order screen and relative-interest parent

- Fundamental17 TOPDIV3000/INDUSTRY 一阶结果：`fnd17_alldelay1_fcf1a` 最强，S=0.36/F=0.17/TO=0.0190；`fnd17_alldelay1_ttmgrosmgn` S=0.31/F=0.11；`fnd17_alldelay1_tcpngmpoq` S=0.28/F=0.12；其余候选 S≤0.06 或为负
- 结论：Fundamental17 本轮全部淘汰，不进入多角度优化
- Relative-interest 变异：`rank(ts_zscore(vec_avg(relative_interest_score_4),60))`（`GrGwmPRQ`）S=1.25/F=0.24/TO=1.1406；`rank(ts_av_diff(vec_avg(relative_interest_score_4),60))`（`omNKa7db`）S=1.20/F=0.24/TO=1.0566；两者为信号但换手和 Fitness 不达标
- 其余 relative-interest 变异：`group_zscore` S=0.94/F=0.20/TO=0.6778；`group_neutralize` S=0.82/F=0.17/TO=0.7256；`hump` S=0.11/F=0.02/TO=0.0063；均不合格
- 当前合格数：0/5；未调用 `submit_alpha`

- 时间：
- 候选 ID：
- 表达式：
- AST 算子节点数：
- 唯一字段：
- Region / Delay / Universe：
- cnhkmcp 检查结果：
- skill 或论坛补充依据：
- Universe 是否变更及理由：
- 决策：淘汰 / 继续优化 / 建议人工提交
- 人工提交结果：未提交 / 成功 / 失败
- 备注：

## 2026-08-09 — GLB/D1/TOPDIV3000 first-order screen

- 表达式：`rank(returns)`, `rank(adv20)`, `rank(mdl53_ms5_1year)`, `rank(mdl53_ms5_5year)`, `rank(mdl177_global_actrtn6m)`, `rank(fnd31_adpmoc)`
- AST 算子节点数：每条 1
- 唯一字段：每条 1
- Region / Delay / Universe：GLB / 1 / TOPDIV3000
- cnhkmcp 检查结果：平台设置只读校验通过；多模拟调用连续返回 HTTP 429，未获得回测结果
- 决策：暂不计入合格 PPA，待平台限流恢复后继续
- 人工提交结果：未提交
- 备注：本轮使用认证配置文件完成认证；未记录或泄露凭据
## 2026-08-10 - GLB/D1 Power Pool Aug`26 2: five verified manual-submission candidates

- Verified unique candidates: `GrGG0M8P`, `WjAAdvqo`, `wpaa10xp`, `omNNvx5v`, `QPGGmqPG`.
- Common settings: GLB / delay=1 / TOPDIV3000 / neutralization=INDUSTRY; category is not Model or Price Volume; dataset is analyst47, not MODEL110; each expression has 2 AST nodes and 1 unique field.
- All five passed HT_HIGH_TURNOVER_RETURNS_RATIO and `get_submission_check` returned `all_passed=true`; production/self max correlations are respectively 0.6038/0.0500, 0.6087/0.0544, 0.6059/0.0484, 0.6124/0.0488, and 0.6255/0.0481.
- Manual submission remains pending. No `submit_alpha` call was made.

## 2026-08-11 - Strict Fitness/PC gate correction and continuation

- The five IDs listed in the previous section are not valid under the later explicit gate `Fitness > 0.5` and `PC < 0.6`: their verified Fitness values are 0.34–0.38. Strict verified count is therefore 0/5; no manual submission was made.
- The required theme settings remain GLB / delay=1 / TOPDIV3000 with non-NONE neutralization; Model, Price Volume, and MODEL110 remain forbidden.
- Risk70 `strevrsl` `ts_av_diff` variants produced Fitness 0.54–0.66, but all six returned `HT_HIGH_TURNOVER_RETURNS_RATIO` WARNING (0.5843–0.6237), so none was counted.
- Risk70 alternative-field, `srtindcnt` smoothing, and Analyst47 grouped-ranking batches each timed out or returned no exact Alpha ID after the permitted reconciliation. They remain `RESULTS_UNOBSERVED` and were not resent.
- Parent `9qppM6qd` was rejected: production correlation 0.7171 exceeds the 0.6 gate and platform HIGH_TURNOVER failed at turnover 1.3183, despite Fitness 0.52 and HT ratio 0.7779.
- Current strict verified count: 0/5. Submission remains manual and no `submit_alpha` call was made.
- Reverse `strevrsl` z-score batch `3GUzc0fA4TpbrdxMPEksdr` was fully observed but all six variants had negative Fitness and HT ratio WARNING; no candidate added.
- `insider_agg_matrix` batches `13hGrdgDH4Oxa8VD0CfM3Z1` and `3gEVPgf2v5bv9ij3D2AaVxD` were fully observed. The category and dataset were eligible and HT ratio checks passed in most/all variants, but Fitness stayed below 0.5; no candidate added.
- Parent scan found eligible Risk70 `XgoovVal` with Fitness 1.25, but HT ratio -0.0108 and an incomplete correlation response; it was rejected. Its six z-score window mutations timed out with no Alpha IDs and remain `RESULTS_UNOBSERVED`.
- Six Risk70 country-count parent expressions (Australia/US/Russia/Peru/Monaco/Israel) also timed out; exact reconciliation found no Alpha IDs. No candidate was counted.
- `constituent_count_argentina` backfill variants reproduced the sparse parent and failed concentration/HT ratio. The `anlystsn` z-score population timed out with no Alpha IDs. Strict count remains 0/5.
- Risk70 `strevrsl` MARKET variants achieved Fitness 0.55–0.72 and concentration PASS but HT ratio WARNING; winsorization did not change the metrics. The SUBINDUSTRY retry timed out with no Alpha IDs. No candidate added.
- `srtindcnt` z-score variants had HT ratio PASS but negative Fitness; reverse variants produced no Alpha IDs after reconciliation. No candidate added.
- The GLB platform settings read-only check confirmed SECTOR is valid; its six `strevrsl` variants timed out with no Alpha IDs. No candidate added.
- A COUNTRY-neutralized six-field Risk70 country-count request failed at the proxy before creation; exact reconciliation found no Alpha IDs. It remains `RESULTS_UNOBSERVED` and was not resent.
- The COUNTRY-neutralized `strevrsl` six-window batch also timed out with no Alpha IDs; no candidate was counted.
- The REVERSION_AND_MOMENTUM `strevrsl` batch completed but Fitness was only 0.02–0.11; no candidate added.
- The STATISTICAL `strevrsl` batch timed out with no Alpha IDs; no candidate added.
- The SLOW `strevrsl` batch timed out with no Alpha IDs; no candidate added.
- The CROWDING `strevrsl` batch timed out with no Alpha IDs; no candidate added.
- The FAST `strevrsl` z-score batch (six windows, GLB/D1/TOPDIV3000, decay=6, truncation=0.001) was reconciled exactly after the request produced no usable result. No Alpha IDs matched; recorded as `RESULTS_UNOBSERVED` and not resent. Strict verified count remains 0/5.
- Batch `2fEMkJ7sF4WEa3nmmWevc6a`: six Risk70 `strevrsl` `ts_av_diff` windows with MARKET/decay=6/truncation=0.001 returned no Alpha IDs; exact reconciliation found no matches. Recorded as `RESULTS_UNOBSERVED`, not resent; strict count remains 0/5.
- Batch `352eb2fjS4nZcDZ1deFCiJ7E`: six Risk70 `srtindcnt` `ts_av_diff` windows with MARKET/decay=0/truncation=0.01 completed. HT ratio passed (about 0.757–0.778), but Fitness was -0.35 to -0.44 and HIGH_TURNOVER failed at turnover about 1.275–1.279. No candidate added; strict count remains 0/5.
- Batch `1Yn3Kz2qJ4DP92EuWlMLtLw`: six reverse Risk70 `srtindcnt` `ts_av_diff` windows with MARKET/decay=0/truncation=0.01 completed. Fitness improved to 0.35–0.44 and HT ratio passed at about 0.757–0.778, but Fitness remained below 0.5 and HIGH_TURNOVER failed at turnover about 1.275–1.279. No candidate added; strict count remains 0/5.
- Reverse Risk70 `srtindcnt` z-score windows (20/30/40/60/90/120) with MARKET/decay=6/truncation=0.001 hit a proxy disconnect before creation. Exact reconciliation found no Alpha IDs; recorded as `RESULTS_UNOBSERVED`, not resent. Strict count remains 0/5.
- Six reverse Risk70 `srtindcnt` `ts_av_diff` windows with INDUSTRY/decay=6/truncation=0.001 timed out after 300 seconds; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent. Strict count remains 0/5.
- Six reverse Risk70 `srtindcnt` `ts_av_diff` windows with SUBINDUSTRY/decay=6/truncation=0.001 timed out after 300 seconds; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent. Strict count remains 0/5.
- Six reverse Risk70 `srtindcnt` `ts_delta` windows with INDUSTRY/decay=6/truncation=0.001 timed out after 300 seconds; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent. Strict count remains 0/5.
- Batch `1xDhPch154VgbpzFD93LMSm`: six reverse Risk70 `srtindcnt` raw/`ts_backfill` variants with MARKET/decay=0/truncation=0.01 completed. All had Fitness=0.47 and HT ratio=0.7716; Fitness failed the strict >0.5 gate. No candidate added; strict count remains 0/5.
- Six reverse Risk70 `srtindcnt` raw/`ts_backfill` variants with INDUSTRY/decay=0/truncation=0.01 timed out; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent. Strict count remains 0/5.
- Six reverse Risk70 `srtindcnt` raw/`ts_backfill` variants with SUBINDUSTRY/decay=0/truncation=0.01 timed out; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent. Strict count remains 0/5.
- Late async reconciliation corrected Batches 100/101: `E5Gv3L9m` (F=0.94, HT=0.7534) failed production PC with max=0.9052. `blQRpneq` (F=0.94, HT=0.7553), `e739AvXJ` (F=0.85, HT=0.7740), and `mL5gO2eE` (F=0.80, HT=0.7554) met observable Fitness/HT gates, but repeated production-correlation reads returned incomplete response errors; PC remains `UNOBSERVED`. None counted; strict count remains 0/5.
- Six reverse Risk70 `srtindcnt` `ts_av_diff` windows with SLOW_AND_FAST/decay=6/truncation=0.001 timed out; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent. Strict count remains 0/5.
- Batch `3Y6Kbz9M54DeagKtZUccgeu`: six reverse Risk70 `srtindcnt` `ts_av_diff` windows with SECTOR/decay=6/truncation=0.001 completed. Fitness=0.79–0.93 and turnover=0.6332–0.6367; only `88p3Oakz` (20d) had HT ratio PASS=0.7566, while the other five were WARNING. PC/Power Pool correlation is pending; no submission or candidate count change.
- Corrected 12-factor GLB turnover baseline: `omNNvx5v`, `wpaa10xp`, `WjAAdvqo`, `GrGG0M8P`, `QPGGmqPG`, `MPGGwPwL`, `j2665V75`, `58ppZGKJ`, `3qpe8VVe`, `RRm1gmVd`, `gJ89XPqM`, `58pROv3M`, with user-supplied Fitness/turnover/ppc values. All are GLB/D1/TOPDIV3000; subsequent variants must retain these settings and lower turnover without losing Fitness/PC/HT gates.
- Six smoothed reverse Risk70 `srtindcnt` `ts_av_diff` variants with SECTOR/decay=6/truncation=0.001 timed out; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent. Strict count remains 0/5.
- Six reverse Risk70 `srtindcnt` `ts_av_diff` windows with SECTOR/decay=10/truncation=0.001 timed out; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent. Strict count remains 0/5.
- Six `ts_target_tvr_decay` variants on the reverse `srtindcnt` 40-day parent (target_tvr 0.30–0.55, SECTOR/decay=6/truncation=0.001) timed out; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent. This follows the advisor skill's target-turnover method.
- `88p3Oakz` was rejected after live production correlation max=0.87 (>0.6), despite Fitness=0.79 and HT ratio=0.7566.
- Six `ts_decay_linear` variants on the reverse `srtindcnt` 40-day parent with SECTOR/decay=6/truncation=0.001 timed out; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent.
- Six `ts_target_tvr_hump` variants on the reverse `srtindcnt` 40-day parent with target_tvr=0.30/0.35/0.40/0.45/0.50/0.55 and SECTOR/decay=6/truncation=0.001 timed out after 300 seconds. The operator was confirmed platform-supported; one exact read-only reconciliation found no matching Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent; strict count remains 0/5.
- Six `hump` variants on the reverse `srtindcnt` 40-day parent with hump=0.001/0.003/0.005/0.01/0.02/0.05 and SECTOR/decay=6/truncation=0.001 were exposed after a 300-second timeout. Five failed Fitness (0.07–0.09); `ak1L1jkx` had Fitness=0.78 and HIGH_TURNOVER=PASS but HT ratio=0.6488 WARNING, so none counted. No submission was made; strict count remains 0/5.
- Six `hump` variants with hump=0.001 and reverse `srtindcnt` parent windows 20/30/40/50/60/80, SECTOR/decay=6/truncation=0.001 timed out after 300 seconds. Exact reconciliation found no new Alpha IDs; the existing `ak1L1jkx` was not counted again. Recorded as `RESULTS_UNOBSERVED`, not resent; strict count remains 0/5.
- Live audit of the corrected 12-factor GLB PPA baseline: `j2665V75`, `58ppZGKJ`, and `3qpe8VVe` lacked a passed HT returns-ratio result; `9qpqQLve` had HT ratio=0.1633 WARNING; `JjGnR9Jn` had HT ratio=0.7931 PASS but production PC=0.8625 FAIL. Other baseline entries failed Fitness or the HT requirement. None counted; no submission was made; strict count remains 0/5.
- Batch 115 `strevrsl` short-window z-score variants and Batch 116 `anl47_rawsentiment` sector z-score variants each timed out after 300 seconds; exact reconciliation found no new IDs. Both are `RESULTS_UNOBSERVED` and were not resent.
- Authoritative OS PPA inventory contained five GLB/D1/TOPDIV3000 PPA-tagged records; all failed at least one strict gate (JjGnR9Jn PC=0.8625; 58pROv3M Fitness=0.44/PC=0.6023; 9qpqQLve HT=0.1633/PC=0.719; qMNMqb6K HT=0.1672/PC=0.6016; RR1gvYg0 Fitness=0.41). No stored PPA counted.
- Batch 117 `current_accruals_quality_percentile` z-score window variants with CROWDING/decay=0/truncation=0 timed out; exact reconciliation found no IDs. Recorded as `RESULTS_UNOBSERVED`, not resent; strict count remains 0/5.
- Batch 118 `current_accruals_quality_percentile` linear-decay windows 5/10/20/30/40/60 completed with Fitness 0.53–0.58 and margin 0.002542–0.002789, but HT ratio was WARNING 0.1652–0.2011 for all; none counted.
- Batch 119 `current_accruals_quality_percentile` ts_delta windows 5/10/20/30/40/60 timed out; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent; strict count remains 0/5.
- Batch 120 `constituent_count_argentina` ts_av_diff windows 5/10/20/40/60/120 with SUBINDUSTRY/decay=0/truncation=0.01 timed out; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent; strict count remains 0/5.
- Current IS inventory scan found no additional authoritative GLB/D1/TOPDIV3000 record satisfying both Fitness>0.5 and HT returns-ratio PASS. No submission was made.
- Batch 121 `current_earnings_quality_regional_percentile` sector z-score variants timed out; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent.
- Batch 122 `strevrsl` sector group-neutralized delta variants timed out; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent; strict count remains 0/5.
- Field audit confirmed `likelihood_fifth_quantile_one_day_bucket_four_4` is `Other / AI-ML Data` from `techindi_model`, not Model/Price Volume and not MODEL110; its PPA parent `58pROv3M` still fails Fitness/PC.
- Batch 123 sector group-neutralized and Batch 124 ungrouped `likelihood_fifth_quantile_one_day_bucket_four_4` quantile/z-score variants both timed out; exact reconciliations found no IDs. Recorded as `RESULTS_UNOBSERVED`, not resent; strict count remains 0/5.
- Batch 125 `constituent_count_argentina` ts_rank windows 5/10/20/40/60/120 timed out; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent.
- Updated coverage screen found 22 eligible GLB/D1/TOPDIV3000 fields with coverage >=70% after excluding Model, Price Volume, and MODEL110; `accounts_payable_notes` coverage=94.74%, `accounts_total_receivables_current`=86.83%, and `accrued_assets_total`=86.16%.
- Batch 126 high-coverage Fundamental23 field variants timed out; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent; strict count remains 0/5.
- Batch 127 raw-rank variants on coverage-qualified Fundamental23 fields timed out; exact reconciliation found no Alpha IDs. Recorded as `RESULTS_UNOBSERVED`, not resent; strict count remains 0/5.
- Batch 128 interrupted Analyst Consensus vector batch was reconciled after interruption and produced no Alpha IDs; recorded as `RESULTS_UNOBSERVED`, not resent.
- Batch 129 high-coverage Analyst Consensus vector batch returned HTTP 429, then returned HTTP 429 again after the required 5-minute cooldown. No Alpha was created and no further retry was made; recorded as `PENDING/RESULTS_UNOBSERVED`, strict count remains 0/5.
- `blQRpneq` was rejected after live production correlation max=0.8994 (>0.6), despite Fitness=0.94 and HT ratio=0.7553.
- User-supplied 12-factor baseline re-recorded: `P0ObaGdp`, `78zWgaXQ`, `e73LA0qd`, `pwN8OW1x`, `6XpzvWAY`, `QPGnlAxG`, `QPG2Wxkr`, `LLGlYMaa`, `A1GOeX7R`, `KPGwGnjj`, `QPGEl9mr`, `ak1olPOW`. Platform/attachment evidence shows EUR/TOP2500 settings; the first two violate Model/Price Volume/MODEL110 restrictions. They are not counted toward GLB PPA qualification.
- Batch 130 coverage-qualified Fundamental23/Analyst field `ts_delta` variants returned HTTP 429; after the required 5-minute cooldown the one permitted retry returned HTTP 429 again. No Alpha was created, no further retry was made, and the batch is recorded as `PENDING/RESULTS_UNOBSERVED`; strict count remains 0/5.
- Batch 131 six coverage-qualified Fundamental23 matrix-field `rank(ts_mean(ts_delta(field,20),3))` variants returned HTTP 429; after the required 5-minute cooldown the one permitted retry returned HTTP 429 again. No Alpha was created, no further retry was made, and the batch is recorded as `PENDING/RESULTS_UNOBSERVED`; strict count remains 0/5.
- Batch 132 six high-coverage `accounts_payable_notes` smoothing-window variants returned HTTP 429; after the required 5-minute cooldown the one permitted retry returned HTTP 429 again. No Alpha was created, no further retry was made, and the batch is recorded as `PENDING/RESULTS_UNOBSERVED`; strict count remains 0/5.
- Batch 133 six coverage-qualified Fundamental23 `rank(ts_av_diff(field,40))` variants returned HTTP 429. No Alpha was created; the batch is recorded as `PENDING/RESULTS_UNOBSERVED`, with no retry in this turn; strict count remains 0/5.
- Batch 134 six coverage-qualified Fundamental23 `rank(ts_decay_linear(field,20))` variants returned HTTP 429. No Alpha was created; the batch is recorded as `PENDING/RESULTS_UNOBSERVED`, with no retry in this turn; strict count remains 0/5.
- Batch 135 six coverage-qualified Fundamental23 reverse short-window `rank(-ts_av_diff(field,20))` variants returned HTTP 429. No Alpha was created; the batch is recorded as `PENDING/RESULTS_UNOBSERVED`, with no retry in this turn; strict count remains 0/5.

## 2026-08-10 — EUR/D1/TOP1200 analyst_revision_horizons campaign closed

- 范围：21个精确八式payload；11批、88个Alpha完整观测；其余按429冷却和精确对账标为UNOBSERVED且不重发。
- 最佳重复信号：年度revenue surprise，S=1.08/F=0.49/2Y=0.95/TO约2%/Margin约25bp，RN S=0.88，仍不满足基础、换手和RN门槛。
- 论坛最后合规补救批次 `4heKJfgJ14AWaUG17mmJoSEQ` 最佳基础S=0.54、最佳RN S=0.79，0个基础全过。
- 决策：无候选、无GA父代；robust、严格过拟合、相关性、submission check和属性设置均未运行；未提交。
- 后续：在完成第20轮多样性审计和论坛复核后，按规则切换至 `predictive_starmine` 单数据集继续。

## 2026-08-13 — GLB/MINVOL1M batch225 downstream review

- Candidates: `npNaKe6l`, `N1bPQJKL`, `6XpMroGp`; all `REGULAR`, `UNSUBMITTED`, `DATA_USAGE:SINGLE_DATA_SET`, one field, one operator, `GLB/MINVOL1M/D1`, `COUNTRY`, `max_trade=OFF`.
- Base and risk-neutral metrics were complete and above the requested gates. Robust evidence: sub-universe Sharpe `2.01` for all; RN Sharpe/Fitness `3.82/2.28`, `3.76/2.22`, `3.71/2.16`.
- Strict overfit review used current 2014–2023 yearly stats. All years except 2020 were positive; 2020 Sharpe/Fitness were `-0.09/-0.02`, `-0.11/-0.03`, `-0.17/-0.05`, respectively. The common weak year is retained as a risk, not erased.
- Numeric production correlation: `0.7782`, `0.7786`, `0.7793`; all fail the user hard limit `<=0.7`. SELF maxima were `0.0075`, `0.0109`, `0.0171` and do not override the production failure.
- Pairwise aligned PnL-change correlations were `0.9990/0.9956/0.9970` raw and `0.9950/0.9810/0.9859` risk-neutralized; this is one redundant lookback family, not three `<0.4` strategies.
- Decision: `FAIL`; no property write and no submission. Count remains `0/5`; continue with a new unlit dataset and materially different strategy style.

## 2026-08-13 — GLB/MINVOL1M other327 batch226

- Eight new single-dataset VECTOR templates on `oth327_sirc_lev` / `oth327_sirc_sl` were reconciled after a 300-second timeout and the required 300-second cooldown. Eight Alpha IDs were found; the original payload was not resent.
- All eight failed the base gate. Best raw result was `rK27REP9` with Sharpe `0.06`, Fitness `0`, 2Y Sharpe `0.80`, turnover `36.31%`, margin `0.06bp`, RN Sharpe `0.42`, RN Fitness `0.03`; it is not a candidate.
- No robust, strict-overfit, correlation, property-setting, or submission action was run. `other327` remains a failed strategy family for these templates; count remains `0/5`.
- 2026-08-13 batch227：GLB/MINVOL1M/D1，Risk70 `rsk70_mfm2_gemtrd_profit`，8 路 `create_multi_simulation` 超时；完成 300 秒冷却后精确只读对账得到 8 个 UNSUBMITTED Alpha。所有候选均未通过基础门槛（最高 Sharpe 0.66、Fitness 0.32、2Y Sharpe 0.88；RN Sharpe 最高 0.68、RN Fitness 0.16，且低换手/低 RN Margin），记录为 FAIL；未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch228：GLB/MINVOL1M/D1，Risk70 `rsk70_mfm2_gemtrd_earnqlty`，8 路 `create_multi_simulation` 超时；完成 300 秒冷却后精确只读对账得到 8 个 UNSUBMITTED Alpha。全部基础门槛失败，最高 Sharpe 0.89、Fitness 0.41、2Y Sharpe 1.04，RN Sharpe 最高 1.20 但常规指标不足；记录为 FAIL，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch229：GLB/MINVOL1M/D1，Risk70 `rsk70_mfm2_gemtrd_invsqlty`，8 路 `create_multi_simulation` 超时；完成 300 秒冷却后精确只读对账未找到目标 Alpha ID。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch230：GLB/MINVOL1M/D1，Risk70 `rsk70_mfm2_gemtrd_dsrt`，8 路 `create_multi_simulation` 超时；完成 300 秒冷却后精确只读对账得到 8 个 Alpha。全部表现为负，记录为 FAIL；未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch231：GLB/MINVOL1M/D1，Other335 SHIELD 字段，8 路请求超时；冷却后对账得到 7 个 Alpha，1 条 mean10 无 ID。7 条完整结果均未通过基础门槛，整批保留 PARTIAL PENDING/UNOBSERVED 语义；未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch232：GLB/MINVOL1M/D1，Other335 linear 字段，8 路请求超时；冷却后精确只读对账未找到目标 Alpha ID。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch233：GLB/MINVOL1M/D1，Fundamental17 `annual_debt_to_total_capital`，8 路请求超时；冷却后精确只读对账得到 8 个 Alpha，全部基础门槛失败。未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch234：GLB/MINVOL1M/D1，Other296 `oth296_topic_count`，8 路请求超时；冷却后精确只读对账未找到目标 Alpha ID。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch235：GLB/MINVOL1M/D1，Fundamental17 `annual_cash_per_share`，multisimulation 创建成功但 8 个子结果均无 Alpha ID；一次精确只读对账仍为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch236：GLB/MINVOL1M/D1，Fundamental17 `annual_total_assets_value`，8 路请求超时；冷却后精确只读对账得到 8 个 Alpha，全部基础门槛失败。未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch237：GLB/MINVOL1M/D1，Other635 `headline_word_count`，8 路请求超时；冷却后精确只读对账得到 8 个 Alpha，全部基础门槛失败。未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch239：GLB/MINVOL1M/D1，Risk70 `hedge_fund_ownership_percent_global`，8 路请求超时；冷却后精确只读对账未找到目标 Alpha ID。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch240：GLB/MINVOL1M/D1，Fundamental17 `annual_normalized_net_income_common`，8 路请求超时；冷却后精确只读对账得到 8 个 Alpha，全部基础门槛失败。未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch241：GLB/MINVOL1M/D1，Fundamental31 `equity_cds_spread_to_dividend_ratio`，8 路请求超时；冷却后精确只读对账得到 8 个 Alpha，全部基础门槛失败。未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch242：GLB/MINVOL1M/D1，Fundamental31 `fnd31_adpmoc`，8 路请求超时；冷却后精确只读对账得到 8 个 Alpha，全部基础门槛失败。未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch243：GLB/MINVOL1M/D1，Fundamental31 `fnd31_60dsigma`，请求阶段 Proxy/RemoteDisconnected；冷却 300 秒后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch244：GLB/MINVOL1M/D1，Fundamental22 `fnd22_s1_value`，低覆盖字段使用 120 日回填；8 路请求超时，冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch245：GLB/MINVOL1M/D1，Other635 `headline_sentiment_score`，8 路请求超时；冷却后精确只读对账得到 8 个 Alpha，全部基础门槛失败。未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch246：GLB/MINVOL1M/D1，Other635 `oth635_sentiment`，8 路请求超时；冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch247：GLB/MINVOL1M/D1，Fundamental31 `change_in_ebitda_to_debt_ratio`，8 路请求超时；冷却后精确只读对账得到 8 个 Alpha，全部基础门槛失败。未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch248：GLB/MINVOL1M/D1，Risk70 `hedge_fund_owner_count_global`，8 路请求超时；冷却后精确只读对账得到 8 个 Alpha，全部基础门槛失败。未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch250：GLB/MINVOL1M/D1，Risk70 `rsk70_mfm2_gemtrd_anlystsn` 的 8 个窗口/方向变体，`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch251：GLB/MINVOL1M/D1，Fundamental23 `annual_interest_income_nonperforming` 的 8 个单字段骨架，`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch252：GLB/MINVOL1M/D1，Fundamental23 `bank_borrowings_total` 的 8 个单字段骨架，`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch253：GLB/MINVOL1M/D1，Other296 `oth296_confidence` 的 8 个单字段骨架（`vec_avg`+60 日回填），`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch254：GLB/MINVOL1M/D1，Other296 `oth296_prob_pos` 的 8 个单字段骨架（`vec_avg`+60 日回填），`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch255：GLB/MINVOL1M/D1，Other424 `dividend_growth_factor_score` 的 8 个单字段骨架，`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch256：GLB/MINVOL1M/D1，Other424 `oth424_divyld` 的 8 个单字段骨架（120 日回填），请求阶段 Proxy/RemoteDisconnected；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch257：GLB/TOPDIV3000/D1，Fundamental44 `fnd44_working_capital_accruals` 的 8 个单字段骨架，`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch258：GLB/TOPDIV3000/D1，Fundamental44 `fnd44_modified_jones_cf_accruals` 的 8 个单字段骨架，`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch259：GLB/TOPDIV3000/D1，Risk68 `rsk68_residual_return` 的 8 个单字段骨架，`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch260：GLB/TOPDIV3000/D1，Risk68 `rsk68_weight_volatility_short` 的 8 个单字段骨架，`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch261：GLB/MINVOL10M/D1，Other699 `oth699_sharestraded_58` 的 8 个单字段骨架（`vec_avg`+120 日回填），`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch262：GLB/MINVOL10M/D1，Other699 `oth699_newnumofshares_63` 的 8 个单字段骨架（`vec_avg`+120 日回填），`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch263：GLB/MINVOL10M/D1，Risk68 `rsk68_beta` 的 8 个单字段骨架，`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch264：GLB/MINVOL10M/D1，Risk68 `rsk68_weight_dadv` 的 8 个单字段骨架，`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch265：GLB/MINVOL10M/D1，Risk66 `rsk66_globalindustry_basedata_cap_usd` 的 8 个单字段骨架，`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch266：GLB/MINVOL10M/D1，Risk60 `rsk60_crowding` 的 8 个单字段骨架（`vec_avg`+60 日回填），`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch267：GLB/MINVOL10M/D1，Risk60 `lending_fee_bid_rate` 的 8 个单字段骨架（`vec_avg`），请求等待 300 秒超时；完成 5 分钟冷却后精确对账得到 8 个 Alpha。全部基础门槛失败，最佳 `XgoN0A18` 的 RN Sharpe/Fitness/Margin 仅 0.51/0.14/1.45bp。未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch268：GLB/MINVOL10M/D1，Other327 `oth327_sirc_lev` 的 8 个单字段骨架（`vec_avg`），multisimulation 创建 8 个模拟但 8 个子结果均无 Alpha ID；一次精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch269：GLB/MINVOL10M/D1，Other327 `oth327_sirc_sl` 的 8 个单字段骨架（`vec_avg`），`multi_create_simulate` 等待 300 秒后超时；完成 5 分钟冷却后精确只读对账为 0 命中。记录为 UNOBSERVED，不重发、不推断指标，未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch270：GLB/MINVOL10M/D1，Other/search_interest `relative_interest_score_4` 的 8 个单字段骨架（`vec_avg`），8 个 Alpha 成功创建并完整可读；全部基础门槛失败，最佳 `P0Gx0nqw` 仍为 Sharpe/Fitness/2Y/Turnover/Margin/RN Sharpe/RN Fitness/RN Margin = 1.26/0.53/2.09/37.92%/3.53bp/1.21/0.32/1.36bp。未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch271：GLB/MINVOL10M/D1，Other/search_interest `relative_interest_score_2`（VECTOR，coverage=0.7124）的 8 个 `vec_avg` 单字段模板；请求超时，完成 5 分钟冷却后只读精确对账获得 8 个 Alpha ID，未重发。全部基础门槛失败（最佳 `RRm9jae1`：S=0.32/F=0.12/2Y=0.67/TO=7.09%/Margin=4.90bp/RN S=0.22/RN F=0.04/RN Margin=1.29bp），记录为 FAIL；未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch272：GLB/MINVOL10M/D1，Other/search_interest `relative_interest_score_13`（VECTOR，coverage=0.3888）使用 120 日回填的 8 个单字段模板；multisimulation 创建 8 个子模拟但均无 Alpha ID。完成 5 分钟冷却后精确只读对账仍为 0，记录为 UNOBSERVED；未重发、未推断指标、未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch273：GLB/MINVOL10M/D1，Fundamental/fundamental25 `fnd25_metricvalue`（VECTOR，coverage=0.1504）使用 120 日回填的 8 个单字段模板完成；8/8 可观测但全部基础门槛失败，最佳 `blQJkV2Z` S=0.42/F=0.18/2Y=-0.22/TO=9.69%/Margin=5.00bp/RN S=-0.04/RN F=0/RN Margin=-0.14bp。记录 FAIL；未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch274：GLB/MINVOL10M/D1，Other/event_relation `relation_strength_score_general`（VECTOR，coverage=0.7311）的 8 个单字段骨架完成；8/8 可观测但全部基础门槛失败，换手约 126.74%–148.01%，最佳 `kqPv7YMk` S=0.22/F=0.02/2Y=0.81/TO=141.33%/Margin=0.14bp/RN S=-0.23/RN F=-0.02/RN Margin=-0.10bp。记录 FAIL；未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch275：GLB/MINVOL10M/D1，Other/other128 `oth128_score_44`（VECTOR，coverage=0.5138）使用 120 日回填的 8 个单字段模板完成；8/8 可观测但全部基础门槛失败，最佳 `ZYEg3wr0` S=0.38/F=0.16/2Y=0.85/TO=2.04%/Margin=21.70bp/RN S=0.09/RN F=0.01/RN Margin=1.10bp。记录 FAIL；未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch276：GLB/MINVOL10M/D1，Other/finnews_nlp_scores `average_positive_sentiment_score_1`（MATRIX，coverage=0.4621）使用 120 日回填的 8 个单字段模板；请求 300 秒超时，完成 5 分钟冷却后精确只读对账为 0 个 Alpha ID，记录 UNOBSERVED；未重发、未推断指标、未执行 downstream、未设置属性、未提交。
- 2026-08-13 batch277：GLB/MINVOL10M/D1，Other/finnews_nlp_scores `average_negative_sentiment_score_1`（MATRIX，coverage=0.4621）计划运行 8 个 120 日回填单字段模板；创建请求两次均 HTTP 401（第二次在 5 分钟冷却后按原 payload 单次重试），认证随后连续返回 `[Errno 22] Invalid argument`。只读精确对账无 Alpha ID，记录 PENDING/UNOBSERVED；不重发、不推断指标、未执行 downstream、未设置属性、未提交。
- 2026-08-13 GLB auth round288：认证报错后完成 5 分钟分段冷却并按原入口单次重试，`authenticate({})` 仍返回 `[Errno 22] Invalid argument`；随后只读 `get_platform_setting_options({})` 同样失败。未查询字段、未创建回测、未执行 downstream、未设置属性、未提交，记录 `UNOBSERVED`。
- 2026-08-13 GLB auth round289：上轮认证故障后完成 5 分钟分段冷却并单次调用 `authenticate({})`，仍返回 `[Errno 22] Invalid argument`。随后会话恢复；GLB/TOPDIV3000 Analyst10 batch288 已完成一次精确只读对账，找到 8/8 Alpha ID，全部基础门槛失败，记录转为 FAIL；未重发、未执行 downstream、未设置属性、未提交。
- 2026-08-13 GLB auth round290：再次完成 5 分钟分段冷却后单次认证，仍返回 `[Errno 22] Invalid argument`。同一外部会话故障已连续多个目标回合重复；未创建回测，batch288 不重发，未执行 downstream、属性设置或提交。
- 2026-08-14 batch297：GLB/TOP3000/D1，Other/other296 `oth296_prob_neg`（VECTOR，coverage=74.46%）使用 `vec_avg` 的 8 路浅层模板。创建请求超时；冷却 5 分钟后精确只读对账得到 8/8 Alpha ID。最佳 Sharpe=-0.26/Fitness=-0.06/2Y=-0.03/RN Sharpe=-0.02，换手 105.91%–162.05%，margin 全部为负；记录 FAIL，未执行 downstream、属性设置或提交。
