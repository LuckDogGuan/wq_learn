# EUR 批量模拟：优化与重试总结

更新时间：2026-07-28

## 本轮停止原因

- 模拟提交链路把网络异常、429、权限/额度响应分开处理，没有统一的连续失败计数。
- POST 循环达到 `max_post_retries=3` 后会将当前任务标记失败并跳过；连续平台异常不能按“等待后继续”处理。
- 401/403、额度或权限文案没有明确进入 2 分钟恢复等待。
- `classify_post_exception` 被优化任务和后台任务共用，影响面较大，因此本次只修改模拟提交链路，不改公共重试策略。

## 已实施的调用层修复

- 不修改项目代码；仅在 MCP 批量调用逻辑中记录同一接口的连续失败次数。
- 单个平台接口连续失败达到 3 次：由调用层暂停 120 秒，然后继续提交同一个 8 条批次。
- 明确权限或额度阻塞：由调用层暂停 120 秒后继续，不跳过当前批次。
- MCP 返回确定性公式/字段错误时，不把它误判为网络失败；记录为负向优化结果并更换表达式。
- 本轮曾临时验证项目代码修复，但已全部撤销；项目代码和测试文件保持不变。

## 正向优化手段

- 每批固定 8 条，使用 `create_multi_simulation`，减少单接口调用次数。
- EUR / EQUITY / Delay 1 / TOP2500 为主，探索 TOP1200 作为交叉验证。
- 保持 `neutralization=NONE`、`max_trade=OFF`、`pasteurization=ON` 等任务设置不变。
- 通过 `ts_target_tvr_decay` 调节换手率；通过 `hump`、`zscore`、短期 `ts_delta` 组合改善信号稳定性。
- 当前较好的方向是 `hump(zscore(ts_delta(anl39_aepsinclxo, 3~5)))`；部分结果的 2Y Sharpe 已超过 1.8，换手率处于目标区间。

## 负向结果与淘汰手段

- 单纯 `rank(ts_mean(...))`：换手率过低，难以满足 0.05–0.30 的区间。
- `fundamental31` 多个高覆盖字段：换手率可调，但 Sharpe/Fitness 普遍偏低或为负。
- TOP1200 交叉验证：当前测试信号整体弱于 TOP2500。
- `hump` 与错误的双参数写法会被平台拒绝；实际平台 `hump` 只接受一个输入。
- 不满足 Sharpe、Fitness、2Y Sharpe、集中度任一硬门槛的 Alpha 不进入相关性、稳健性或 READY_TO_SUBMIT 流程。

## 后续周期

每完成一轮 8 条批量任务，记录：批次 ID、最佳 Sharpe/Fitness/Turnover/Margin、2Y Sharpe、失败原因、下一轮保留和淘汰的表达式方向。遇到连续 3 次平台失败或权限/额度阻塞，按本文件的 120 秒调用层恢复策略继续。

## 增量记录：2026-07-28 后续批次

- 第 20 批：MCP 成功创建 8 条，未触发接口失败；最佳方向继续使用 EUR/TOP2500 的 analyst39 短期变化信号。
- 第 21 批：multisimulation `b78ARdmi51w8PyszJUq97H`，成功创建 8 条；最佳约 Sharpe 1.29、Fitness 0.87、Turnover 0.199、2Y Sharpe 1.88。
- 正向结论：`hump(zscore(ts_delta(anl39_aepsinclxo,3~4)))` 配合 `ts_target_tvr_decay` 可以把换手率稳定在目标区间，并保持 2Y Sharpe 较高。
- 负向结论：该方向的原始 Sharpe/Fitness 仍低于硬门槛，且部分结果集中度失败；暂不进入相关性、稳健性或 READY_TO_SUBMIT 流程。
- 第 22 批首次调用出现 Windows 10053 连接中止；调用层按 1/3 记录并重试，第二次调用成功创建 8 条，证明当前调用层重试可以恢复单次接口中断。
- 第 22 批最佳约 Sharpe 1.23、Fitness 0.88、Turnover 0.173、2Y Sharpe 1.63；分析师 `anl39_spvbq` 方向弱于 `anl39_aepsinclxo`，`anl39_grosmgn5yr` 多数为负，列入负向方向。

## 增量记录：认证恢复尝试（2026-07-28）

- 第 23 批尚未提交：认证连续 4 次失败，先后返回 Windows 10054 连接中止及 `[Errno 22] Invalid argument`。
- 按连续平台失败规则等待 60 秒后再次认证仍失败；未调用 `create_multi_simulation`、`create_simulation` 或 `submit_alpha`。
- 下一步：平台认证恢复后先重新执行设置、数据集、字段、Pyramid 与未提交 Alpha 校验，再继续新批次；当前不把认证故障归因于表达式。

## 增量记录：跨数据集探索批次（2026-07-28）

- 认证恢复后重新核验：`EQUITY/EUR/D1` 合法 Universe 为 `TOP2500/TOP1200/TOP800/TOP400/ILLIQUID_MINVOL1M/TOPCS1600`；本轮固定 `TOP2500`、`NONE`、`pasteurization=ON`、`max_trade=OFF`。
- 第 23 批：`2BG9u4aIu4Fa8JOFAXrR3ng`，成功创建 8 条，覆盖 8 个 dataset：`analyst39`、`analyst10`、`analyst14`、`analyst69`、`ai_news_scores`、`risk68`、`pv47`、`model238`。所有表达式均为单字段、3 个操作符、未提交状态。
- 第 23 批结果摘要：`analyst39` Sharpe/Fitness/Turnover=`0.99/0.72/0.1745`；`analyst10`=`-0.42/-0.08/1.8502`；`analyst14`=`-0.19/-0.05/0.3886`；`analyst69`=`0.89/0.48/0.4248`；`ai_news_scores`=`-0.16/-0.02/1.4419`；`risk68`=`0.79/0.83/0.0199`；`pv47`=`-0.44/-0.18/0.015`；`model238`=`0.29/0.07/0.0068`。均未通过硬门槛，未进入相关性、稳健性或 READY_TO_SUBMIT。
- 第 24 批：`2lPAIOgJh57vaIx19wnycg7X`，首次因 `429` 等待 120 秒，随后一次 10054，恢复后成功创建 2 条，新增 `ai_factor_transfer` 与 `other327` 两个 dataset。
- 第 24 批结果：`ai_factor_transfer` Alpha `vRvZ8Jxz` Sharpe/Fitness/Turnover=`0.02/0/0.0059`，失败；`other327` Alpha `O0xRO5qp` 返回空 PnL、Fitness 缺失及检查错误，失败。累计完成 10 个不同 dataset，当前 0 个 Alpha 满足基础硬门槛。
- 下一轮优先方向：保留 `analyst39` 与 `risk68` 作为候选字段族继续做字段替换/短期窗口验证；淘汰本轮明显负向的 `analyst10`、`ai_news_scores`、`pv47`、`ai_factor_transfer`、`other327`，不对失败 Alpha 做后续 stress 或标签操作。

## 增量记录：目标换手率模板复测（2026-07-28）

- 第二轮批次：`3Wdm1Fgyz4Zm9N39qJf3cV5`；首次 10053、随后 429，等待 120 秒后成功创建 8 条。模板为 `ts_target_tvr_decay(hump(rank(ts_mean(field,20))), lambda_min=0, lambda_max=5, target_tvr=0.1)`，操作符数为 4。
- 最佳结果为 `model238` 字段 `global_institutional_preference_rank_d1`，Alpha `vRvZqnqr`：Sharpe `1.43`、Fitness `0.82`、Turnover `0.1000`、2Y Sharpe `1.56`，集中度通过，但仍未达到 `Sharpe>1.58`、`Fitness>1`、`2Y Sharpe>1.6`。
- 其他方向仍未通过基础硬门槛：`analyst39` Sharpe `0.71`、`analyst10` `1.01`、`analyst14` `0.35`、`analyst69` `0.77`、`risk68` `0.87`、`ai_news_scores` `-0.04`、`ai_factor_transfer` `0.11`；均不进入稳健性/相关性/READY 流程。
- 当前结论：已有 10 个不同 dataset 的首轮探索和第二轮模板复测，但 `READY_TO_SUBMIT=0`；继续沿 `model238` 的换手率模板做字段替换，不能宣称目标完成。
## 增量记录：现存 Alpha 对账与下一轮筛选（2026-07-28）

- 对上一轮 `model238` 单数据集扩展批次的超时结果不作成功判断；改用只读 `get_user_alphas(stage=IS, start_date=2026-07-28T07:00:00Z)` 对账，当前返回 69 条未提交 Alpha。
- 当前最接近硬门槛的是 `analyst39/anl39_qepsinclxo` 的 `ts_target_tvr_decay(hump(zscore(ts_delta(...,3))), target_tvr=0.25)` 系列：`omgR7b0m` 约为 Sharpe `1.52`、Fitness `0.96`、Turnover `0.2374`、2Y Sharpe `2.05`；`pwKxYpMj` 与 `O0xRQrq1` 的 Fitness 已约 `1.04`，但 Sharpe 仍约 `1.52`，且存在集中度告警。
- `d5RYpNbX` 约为 Sharpe `1.49`、Fitness `0.92`、Turnover `0.245`、2Y Sharpe `2.04`，仍有 Sharpe/Fitness/集中度检查未通过。上述 Alpha 均未进入 robust、相关性或 READY 流程。
- 下一轮只把上述结果作为参数模板，继续替换为其他 dataset 的单字段信号；在 Sharpe `>1.58`、Fitness `>1`、2Y Sharpe `>1.6`、Margin `>10bp`、Turnover `0.05~0.30` 全部通过前，不标记 READY、不设置提交标签。
## 增量记录：字段替换批次（2026-07-28）

- 批次 `327SqEalc5cU9IS18woN4Uql` 成功创建 8 条 EUR/TOP2500/D1/NONE Alpha，均为单字段、4 operators、未提交。
- 最好结果为 `xAdV8j9p`（`anl39_qepsinclxo`）：Sharpe `1.52`、Fitness `1.04`、Turnover `0.1977`、Margin `9.43bp`、2Y Sharpe `1.80`；Fitness/换手/2Y 通过，但 Sharpe 低于 `1.58`，且集中度告警，不能进入 READY。
- `anl69_analyst_best_eeps_cur_yr` 仅 Sharpe `0.84`、Fitness `0.44`；`rsk68_residual_return` 仅 Sharpe `0.03`；`fnd31_bmpo`、`anl14_median_eps_fp1`、`anl10_ndtinnovation_score_fy2`、`pv47_spret`、`global_change_in_preference_rank_d1` 均未通过 Sharpe/Fitness，继续淘汰。
- 结论：本轮仍为 `READY_TO_SUBMIT=0`；`xAdV8j9p` 是当前唯一值得做参数邻域复测的近门槛样本，但最终候选仍必须来自不同 dataset，并补做 robust、相关性和 submission check。
## 增量记录：近门槛参数邻域复测（2026-07-28）

- 批次 `4GrW4RgD45beb72etrMeOls` 成功创建 8 条 `anl39_qepsinclxo` 参数邻域样本，均未提交。
- 最好结果为 `9q7812Ro`（delta=2、target_tvr=0.20）：Sharpe `1.47`、Fitness `0.94`、Turnover `0.1928`、Margin `8.10bp`、2Y Sharpe `1.65`；`Vk3ZjR8Y` 的 Fitness `1.03`，但 Sharpe `1.48`。
- target_tvr=`0.30` 的 delta=3 样本 `78n3b2d5` 达到 Fitness `1.00`、2Y Sharpe `1.84`，但 Sharpe `1.49`；所有近门槛样本仍有集中度告警。
- 结论：改变 delta 与目标换手率未突破 Sharpe `1.58`，本轮不进入 robust/相关性/READY；继续转向其他 dataset 的有效信号，而不是重复扩大同一字段的无效搜索。
## 增量记录：跨 dataset 批次对账（2026-07-28）

- `get_datasets`/`get_datafields` 已确认可用的新增候选字段族，包括 `continuation_score`、`global_seasonal_model`、`risk70`、`sentiment21`、`model26`；字段描述分别覆盖图形延续、季节性预测置信度、行业暴露、情绪波动和分析师修正。
- 随后调用 `create_multi_simulation` 返回成功外层响应 `1990K2a434iWcmFJIxl47H2`，但 `alpha_results` 未返回 Alpha 详情；用 `get_user_alphas` 按创建时间及表达式关键词复核，未发现这 8 个新增字段表达式对应的可核验 Alpha ID，因此不把该批次计入有效样本。
- 该结果属于“外层成功、结果不可对账”的不确定状态；不重复提交同一批，下一轮先缩小为可明确回收结果的字段，并以 Alpha 详情为唯一统计依据。
## 增量记录：lambda 与短期窗口复测（2026-07-28）

- 批次 `X7U3DeWm4Te9wNUE2tLDyq` 成功创建 8 条 `anl39_qepsinclxo` 邻域样本。
- 最佳组合仍为 delta=3、`lambda_max=1`：`LLdEAp96` 的 Sharpe `1.52`、Fitness `1.04`、Turnover `0.1977`、Margin `9.43bp`、2Y Sharpe `1.80`；`lambda_min` 从 0 调到 0.1/0.2/0.3 没有改善 Sharpe。
- delta=1 明显变差；delta=2 的 2Y Sharpe 尚可但 Fitness 不足；`lambda_max=2` 只提高 2Y Sharpe 到 `2.05`，Fitness 和 Margin 反而下降。集中度告警持续存在。
- 结论：该字段参数邻域已基本收敛，仍无 Sharpe `>1.58` 且 Margin `>10bp` 的候选；不进入后续 READY 流程，下一步继续寻找其他 dataset 的有效信号。
## 增量记录：论坛方向与 decay 验证（2026-07-28）

- 实时设置核验确认目标文件实际为 `EQUITY/EUR/delay=1`；合法 Universe 包括 `TOP2500/TOP1200/TOP800/TOP400/ILLIQUID_MINVOL1M/TOPCS1600`。平台返回的 Pyramid multiplier 显示 EUR D1 的 analyst multiplier 为 `1.4`，但 `get_pyramid_alphas` 当前因平台接口 400 未能取得已点亮分布。
- 论坛搜索到近期高赞经验：EUR/TOP2500/analyst 类数据的 decay 可能在 `4~6` 出现 Sharpe 峰值；尝试读取正文和评论时平台认证代理连接失败，因此该经验仅作为待验证假设。
- 固定 decay=`5` 的 3 条小批量请求未返回 Alpha 详情；随后按创建时间和表达式复核，没有找到对应的 `anl39_qepsinclxo` decay=5 Alpha，故不计入有效批次、不重复提交。
- 当前仍无基础门槛通过者；`READY_TO_SUBMIT=0`，不进入 robust 或标签流程。
## 增量记录：decay=5 小批量复测（2026-07-28）

- 批次 `2EUae74zx4hT9FkihEPl3pk` 成功创建 2 条 Alpha，明确返回结果。
- `vRvZggLr`（`anl39_qepsinclxo`）为 Sharpe `1.17`、Fitness `0.82`、Turnover `0.1213`、Margin `10.02bp`、2Y Sharpe `1.02`；`O0xRaapR`（`anl39_aepsinclxo`）为 Sharpe `1.16`、Fitness `0.85`、Turnover `0.1056`、Margin `12.84bp`、2Y Sharpe `1.58`。
- decay=5 未改善核心信号，且两条均未通过 Sharpe/Fitness/2Y Sharpe，集中度仍告警；论坛经验不适用于当前模板参数。两条 Alpha 均未提交，不进入 robust 或 READY。
## 增量记录：model26 分析师修正信号（2026-07-28）

- 批次 `2mUn0FgEj4r4bLmV4u7iFqj` 成功创建 2 条 `model26` 单字段 Alpha：`analyst_revision_primary_earnings_score` 的 `pwKxO8po` Sharpe `2.17`、Fitness `1.65`、2Y Sharpe `1.70`、Margin `36.45bp`；`analyst_revision_revenue_score_d1` 的 `O0xRao2R` Sharpe `1.78`、Fitness `1.13`、Margin `26.29bp`。
- 两条的实际 Turnover 分别仅 `0.0398/0.0383`，均低于硬门槛 `0.05`，并有集中度失败；`O0xRao2R` 的 2Y Sharpe 也仅 `0.89`。因此不能进入 robust。
- 将 target_tvr 调到 `0.40` 的批次 `a7hzh1dF5jWclCuHZCraq4` 实际 Turnover 未变化，证明该字段的稀疏/集中问题不是目标换手参数可修复的。随后平滑 rank 骨架批次未返回可核验详情，不计入有效结果。
- 结论：`model26` 方向有强 IS 收益但不可交易性不足，暂列“高 Sharpe、低换手”失败模式；不设置 READY 标签。
## 增量记录：model26 变化排序骨架复测（2026-07-28）

- 批次 `1rOZhact4vtb769GkdvtWX` 成功创建 2 条 revision-change Alpha。
- `analyst_revision_primary_earnings_score` 结果为 Sharpe `-0.44`、Fitness `-0.11`、Turnover `0.0061`；`analyst_revision_revenue_score_d1` 结果为 Sharpe `-0.75`、Fitness `-0.25`、Turnover `0.0062`；两者均集中度失败。
- 结论：revision 字段的水平信号有较强 IS 收益但换手过低，变化排序信号则整体失效；model26 当前两种最小骨架均淘汰，不进入 robust/READY。
## 增量记录：model26 其余字段批次对账（2026-07-28）

- 针对 `analyst_recommendation_score_component` 与 `analyst_revision_secondary_earnings_score` 的 2 条批量请求未返回成功外层响应、批次 ID 或 Alpha 详情；按当前 Alpha 列表复核也没有可确认的新记录。
- 该批次不计入有效模拟，不据此判断字段优劣，也不重复提交同一表达式；model26 已有可核验结果仍只有“高 Sharpe/低换手”方向，未满足基础门槛。
## 增量记录：TOP1200 交叉 Universe 复测（2026-07-28）

- 按目标要求将 `model26` 两条最强水平信号从 TOP2500 切换到合法的 `TOP1200`，保持 EUR/D1/NONE/decay=0 及相同表达式。
- 请求未返回成功外层响应、批次 ID 或 Alpha 详情；随后按 `get_user_alphas` 的未提交结果及 `settings.universe=TOP1200` 复核，没有找到新记录，因此本轮不计入有效候选。
- TOP1200 已被实际尝试但结果不可观察；不把该次请求当作通过或失败指标，不进入 robust/READY。
## 增量记录：model26 revenue/secondary 字段复测（2026-07-28）

- 批次 `1lTRtz7XA4YBaE995zQ9720` 成功创建 2 条 Alpha。
- `j2roL8G5`（revenue score）Sharpe `1.78`、Fitness `1.13`、Margin `26.29bp`，但 Turnover `0.0383`、2Y Sharpe `0.89`、集中度失败。
- `1YzOvZKJ`（secondary earnings score）Sharpe `2.07`、Fitness `1.52`、Margin `31.89bp`，但 Turnover `0.0421`、2Y Sharpe `0.88`、集中度失败。
- 结论：model26 字段族反复呈现高 IS 指标但低换手、低 2Y 延续性，不能进入基础候选或 READY。
## 增量记录：pv1 动量与成交量复测（2026-07-28）

- 通过 `get_datafields` 确认 `pv1.returns` 与 `pv1.volume` 均为 EUR/TOP2500/D1 合法字段。
- 批次 `17dBBBcev55d9koMDU7UrOj` 成功创建 2 条 Alpha：20 日收益和的 Sharpe/Fitness=`0.52/0.25`、Turnover=`0.0143`；5 日成交量变化的 Sharpe/Fitness=`0.44/0.17`、Turnover=`0.1957`。
- 两条均未通过 Sharpe、Fitness、2Y Sharpe；成交量信号虽换手合格但 Margin 仅 `3.03bp`。无基础候选，不进入 robust/READY。
## 增量记录：sentiment21 情绪字段复测（2026-07-28）

- 通过 `get_datafields` 确认 `snt21_2pos_min_86` 与 `snt21_3pos_max` 为合法 EUR/TOP2500/D1 字段。
- 批次 `3DO3JgdTN4ix9E2jOiZe9Li` 成功创建 2 条 Alpha：正情绪最小值 Sharpe/Fitness=`0.17/0.06`、Turnover=`0.2388`、Margin=`2.92bp`；正情绪最大值 Sharpe/Fitness=`0.31/0.16`、Turnover=`0.241`、Margin=`5.29bp`。
- 两条均 Sharpe/Fitness/2Y 失败，集中度达到 `0.5` 失败；情绪字段该骨架淘汰，不进入 robust/READY。
## 增量记录：fundamental31 盈利/现金流复测（2026-07-28）

- 批次 `3Vzxgy3Pn4By9GEPutao8Au` 成功创建 2 条 Alpha。
- `fnd31_chg3yepsp`：Sharpe `-0.75`、Fitness `-0.35`、Turnover `0.0767`、Margin `-7.10bp`、2Y Sharpe `-0.76`。
- `fnd31_cfroi`：Sharpe `-0.75`、Fitness `-0.38`、Turnover `0.1279`、Margin `-5.10bp`、2Y Sharpe `-0.03`，集中度失败。
- 两个 Fundamental 变化信号均淘汰，不进入 robust/READY。
## 增量记录：risk62 风格 beta 复测（2026-07-28）

- 通过 `get_datafields` 确认 `rsk62_beta_1_100_growth` 与 `rsk62_beta_1_100_mts` 属于 risk62，覆盖率为 1。
- 批次 `2UVA8N5cf4Kjcvq9Qc6rUub` 成功创建 2 条 Alpha：growth beta Sharpe/Fitness=`-0.27/-0.07`、Turnover=`0.0413`；短期动量 beta Sharpe/Fitness=`-0.32/-0.10`、Turnover=`0.0408`；两者 Margin 为负且集中度失败。
- 风格 beta 变化方向淘汰，不进入 robust/READY。
## 增量记录：model26 primary earnings 短窗与 decay（2026-07-28）

- 批次 `35eY4MbFo4OebIIWNJczuzD`（decay=0）发现近门槛：delta=1 的 `RR19Za2d` Sharpe `2.54`、Fitness `2.11`、Turnover `0.1044`、Margin `16.56bp`；delta=2 的 `le3E6zQn` Sharpe `2.25`、Fitness `1.77`、Turnover `0.0568`、Margin `27.21bp`。两者 2Y Sharpe 分别 `1.24/1.34`，且集中度失败。
- 批次 `1yJSq562g4GB9c5M2XdQEdN`（decay=3）结果略降：delta=1 的 `np8mkPNz` Sharpe/Fitness=`2.33/1.86`、Turnover=`0.0694`、2Y=`1.12`；delta=2 的 `78n3q6z1` Turnover=`0.0498`、2Y=`1.30`。集中度仍失败。
- 结论：该方向首次同时通过 IS Sharpe、Fitness、Margin 和部分换手，但 2Y 与集中度硬门槛未通过；按过拟合规则冻结为 `ROBUST_FAIL/OVERFIT_FAIL`，不得进入 READY。
## 增量记录：model77 价值动量字段批次对账（2026-07-28）

- `get_datafields` 确认 `mdl77_qvm_rue_avq` 与 `deep_value_europe_composite_score` 为 model77/欧洲价值动量字段。
- 批量请求未返回成功外层响应、批次 ID 或 Alpha 详情；`get_user_alphas` 也未发现可核验的新记录，因此不把本轮当作有效回测，不重复提交。
## 增量记录：TOP800 交叉 Universe 复测（2026-07-28）

- 批次 `42g8sngeZ4Em96fs3hdIWDk` 成功创建 2 条 model26 primary earnings Alpha。
- TOP800/delta=1：Sharpe `0.80`、Fitness `0.33`、Turnover `0.2502`、Margin `3.46bp`、2Y Sharpe `0.15`；delta=2：Sharpe `0.76`、Fitness `0.37`、Turnover `0.1816`、Margin `4.71bp`、2Y Sharpe `-0.05`；两者集中度失败。
- 更窄 Universe 未改善 2Y，反而显著削弱收益；TOP800 方向淘汰，不进入 robust/READY。
## 增量记录：model110 质量/动量模型复测（2026-07-28）

- 通过 `get_datafields` 确认 `mdl110_quality` 与 `mdl110_price_momentum_reversal` 为 EUR/TOP2500/D1 合法字段，覆盖率 `0.8525`。
- 批次 `3dW6QJ1u44D4crq17qQYMVDY` 成功创建 2 条 Alpha：quality Sharpe/Fitness=`0.61/0.21`、Turnover=`0.0561`、Margin=`5.53bp`、2Y=`-0.07`；price momentum/reversal Sharpe/Fitness=`0.09/0.02`、Turnover=`0.0169`、2Y=`-0.23`。
- 两条均未通过收益与 2Y 门槛；model110 该骨架淘汰，不进入 robust/READY。
