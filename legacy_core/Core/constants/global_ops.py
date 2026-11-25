# ==============================================================================
# 全局操作符与基础参数分类库 (Global Operators & Configurations)
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. 核心操作符分类 (Core Operators)
# ------------------------------------------------------------------------------
# 基础横截面与变换操作符 (Cross-Sectional & Transformation)
basic_ops = [
    "reverse", "inverse", "rank", "zscore", "quantile", "normalize",
    "abs", "log", "sign", "sqrt", "pasteurize", "densify"
]

# 时序计算操作符 (Time-Series)
ts_ops = [
    "ts_rank", "ts_zscore", "ts_delta", "ts_sum", "ts_delay", 
    "ts_std_dev", "ts_mean", "ts_arg_min", "ts_arg_max", "ts_scale", "ts_quantile",
    "ts_ir", "ts_count_nans", "ts_decay_linear", "ts_step", "ts_returns", 
    "ts_max_diff", "ts_kurtosis", "ts_av_diff", "ts_product", "ts_backfill"
]

# 综合操作符全集
ops_set = basic_ops + ts_ops 


# ------------------------------------------------------------------------------
# 2. 截面分组函数与基本域 (Cross-Sectional Groups & Domains)
# ------------------------------------------------------------------------------
# 常规域分组
cap_group = "bucket(rank(cap), range='0.1, 1, 0.1')"
asset_group = "bucket(rank(assets),range='0.1, 1, 0.1')"
sector_cap_group = "bucket(group_rank(cap, sector),range='0.1, 1, 0.1')"
sector_asset_group = "bucket(group_rank(assets, sector),range='0.1, 1, 0.1')"

# 波动率与流动性分组
vol_group = "bucket(rank(ts_std_dev(returns,20)),range = '0.1, 1, 0.1')"
liquidity_group = "bucket(rank(close*volume),range = '0.1, 1, 0.1')"

# 全部分组集
groups = [
    "market", "sector", "industry", "subindustry",
    cap_group, asset_group, sector_cap_group, sector_asset_group, vol_group, liquidity_group
]


# ------------------------------------------------------------------------------
# 3. 区域静态特征与去均值特征集 (Regional Neutralization & Feature Groups)
# ------------------------------------------------------------------------------
# 【区域隔离设计原理】
# 不同国家/地区的市场结构（流动性、散户比例、政策限制）差异巨大，导致适用的去均值基准完全不同。
# 强行跨区域复用特征容易导致过拟合或信号失效。因此，需要为各区域预设专用的高胜率特征集：
#   * pv13: 量价高阶聚类特征，常带 universe(如 minvol) 和 去均值(如 sector) 后缀。适合捕获动量与反转。
#   * sta1 / sta2: 统计与基本面结构特征。常带 top3000、c20 等聚类后缀。适合用于做截面去均值基准或长周期过滤。

# -- 中国大陆 (CHN) --
# 偏向/特点：A股受散户资金驱动，短期量价博弈激烈，动量与反转效应强。
# 因此大量依赖 `pv13_di` (极速量价) 和 `rcsed` 等高频因子，偏好短周期。
chn_group_13 = ['pv13_h_min2_sector', 'pv13_di_6l', 'pv13_rcsed_6l', 'pv13_di_5l', 'pv13_di_4l', 
'pv13_di_3l', 'pv13_di_2l', 'pv13_di_1l', 'pv13_parent', 'pv13_level']
chn_group_1 = ['sta1_top3000c30','sta1_top3000c20','sta1_top3000c10','sta1_top3000c2','sta1_top3000c5']
chn_group_2 = ['sta2_top3000_fact4_c10','sta2_top2000_fact4_c50','sta2_top3000_fact3_c20']

# -- 中国香港 (HKG) --
# 偏向/特点：港股存在大量流动性极差的“仙股”，因此强依赖 `minvol_1m` (1个月最小波动/高流动性) 过滤。
# 去均值基准高度依赖 sector (行业)，防止单行业暴雷。
hkg_group_13 = ['pv13_10_f3_g2_minvol_1m_sector', 'pv13_10_minvol_1m_sector', 'pv13_20_minvol_1m_sector', 
'pv13_2_minvol_1m_sector', 'pv13_5_minvol_1m_sector', 'pv13_1l_scibr', 'pv13_3l_scibr',
'pv13_2l_scibr', 'pv13_4l_scibr', 'pv13_5l_scibr']
hkg_group_1 = ['sta1_allc50','sta1_allc5','sta1_allxjp_513_c20','sta1_top2000xjp_513_c5']
hkg_group_2 = ['sta2_all_xjp_513_all_fact4_c10','sta2_top2000_xjp_513_top2000_fact3_c10',
   'sta2_allfactor_xjp_513_13','sta2_top2000_xjp_513_top2000_fact3_c20']

# -- 台湾 (TWN) --
# 偏向/特点：台股受半导体/科技周期影响极深，高度依赖 `minvol_1m_sector` 将科技股行情进行行业剥离。
twn_group_13 = ['pv13_2_minvol_1m_sector','pv13_20_minvol_1m_sector','pv13_10_minvol_1m_sector',
'pv13_5_minvol_1m_sector','pv13_10_f3_g2_minvol_1m_sector','pv13_5_f3_g2_minvol_1m_sector',
'pv13_2_f4_g3_minvol_1m_sector']
twn_group_1 = ['sta1_allc50','sta1_allxjp_513_c50','sta1_allxjp_513_c20','sta1_allxjp_513_c2',
   'sta1_allc20','sta1_allxjp_513_c5','sta1_allxjp_513_c10','sta1_allc2','sta1_allc5']
twn_group_2 = ['sta2_allfactor_xjp_513_0','sta2_all_xjp_513_all_fact3_c20',
   'sta2_all_xjp_513_all_fact4_c20','sta2_all_xjp_513_all_fact4_c50']

# -- 美国 (USA) --
# 偏向/特点：美股机构化程度极高，市场有效性强，量价异常往往是微观结构导致。
# 大量依赖 `3000` (大市值股票池) 和 `focused_pureplay` 做精细的行业去均值。
usa_group_13 = ['pv13_h_min2_3000_sector','pv13_r2_min20_3000_sector','pv13_r2_min2_3000_sector',
'pv13_r2_min2_3000_sector', 'pv13_h_min2_focused_pureplay_3000_sector']
usa_group_1 = ['sta1_top3000c50','sta1_allc20','sta1_allc10','sta1_top3000c20','sta1_allc5']
usa_group_2 = ['sta2_top3000_fact3_c50','sta2_top3000_fact4_c20','sta2_top3000_fact4_c10']
usa_group_6 = ['mdl10_group_name']

# -- 亚洲除日股 (ASI) --
# 偏向/特点：包含了诸多新兴市场，流动性和波动率参差不齐，因此同样极度依赖 `minvol1m` (最小波动) 控制尾部风险。
asi_group_13 = ['pv13_20_minvol_1m_sector', 'pv13_5_f3_g2_minvol_1m_sector', 'pv13_10_f3_g2_minvol_1m_sector',
'pv13_2_f4_g3_minvol_1m_sector', 'pv13_10_minvol_1m_sector', 'pv13_5_minvol_1m_sector']
asi_group_1 = ['sta1_allc50', 'sta1_allc10', 'sta1_minvol1mc50','sta1_minvol1mc20',
   'sta1_minvol1m_normc20', 'sta1_minvol1m_normc50']

# -- 日本 (JPN) --
# 偏向/特点：日股独有 `jpn_513` 聚类特征，因日股价值/质量风格长期主导，依赖这类特异性基本面组合。
jpn_group_1 = ['sta1_alljpn_513_c5', 'sta1_alljpn_513_c50', 'sta1_alljpn_513_c2', 'sta1_alljpn_513_c20']
jpn_group_2 = ['sta2_top2000_jpn_513_top2000_fact3_c20', 'sta2_all_jpn_513_all_fact1_c5',
   'sta2_allfactor_jpn_513_9', 'sta2_all_jpn_513_all_fact1_c10']
jpn_group_13 = ['pv13_2_minvol_1m_sector', 'pv13_2_f4_g3_minvol_1m_sector', 'pv13_10_minvol_1m_sector',
'pv13_10_f3_g2_minvol_1m_sector', 'pv13_all_delay_1_parent', 'pv13_all_delay_1_level']

# -- 韩国 (KOR) --
# 偏向/特点：高度受财阀与头部集团影响，经常复用部分 ASI 通用 `minvol` 逻辑，同时叠加特定 `xjp` (除日本外) 特征。
kor_group_13 = ['pv13_10_f3_g2_minvol_1m_sector', 'pv13_5_minvol_1m_sector', 'pv13_5_f3_g2_minvol_1m_sector',
'pv13_2_minvol_1m_sector', 'pv13_20_minvol_1m_sector', 'pv13_2_f4_g3_minvol_1m_sector']
kor_group_1 = ['sta1_allc20','sta1_allc50','sta1_allc2','sta1_allc10','sta1_minvol1mc50',
   'sta1_allxjp_513_c10', 'sta1_top2000xjp_513_c50']
kor_group_2 =['sta2_all_xjp_513_all_fact1_c50','sta2_top2000_xjp_513_top2000_fact2_c50',
  'sta2_all_xjp_513_all_fact4_c50','sta2_all_xjp_513_all_fact4_c5']

# -- 欧洲 (EUR) --
eur_group_13 = ['pv13_5_sector', 'pv13_2_sector', 'pv13_v3_3l_scibr', 'pv13_v3_2l_scibr', 'pv13_2l_scibr',
'pv13_52_sector', 'pv13_v3_6l_scibr', 'pv13_v3_4l_scibr', 'pv13_v3_1l_scibr']
eur_group_1 = ['sta1_allc10', 'sta1_allc2', 'sta1_top1200c2', 'sta1_allc20', 'sta1_top1200c10']
eur_group_2 = ['sta2_top1200_fact3_c50','sta2_top1200_fact3_c20','sta2_top1200_fact4_c50']

# -- 全球 (GLB) --
glb_group_1 = ['sta1_allc20', 'sta1_allc10', 'sta1_allc50', 'sta1_allc5']
glb_group_2 = ['sta2_all_fact4_c50', 'sta2_all_fact4_c20', 'sta2_all_fact3_c20', 'sta2_all_fact4_c10']
glb_group_13 = ['pv13_2_sector', 'pv13_10_sector', 'pv13_3l_scibr', 'pv13_2l_scibr', 'pv13_1l_scibr',
'pv13_52_minvol_1m_all_delay_1_sector','pv13_52_minvol_1m_sector','pv13_52_minvol_1m_sector'] 

# -- 美洲其它 (AMR) --
amr_group_13 = ['pv13_4l_scibr', 'pv13_1l_scibr', 'pv13_hierarchy_min51_f1_sector',
'pv13_hierarchy_min2_600_sector', 'pv13_r2_min2_sector', 'pv13_h_min20_600_sector']


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# 4. 事件触发与退出条件模板 (Event Triggers & Exits)
# ------------------------------------------------------------------------------
# 【事件驱动设计原理】
# 除了连续信号外，某些因子仅在特定条件（如财报发布、新闻爆出、情绪极值）下有效。
# WQ 平台允许使用 `trade_when` 或 `AND` 条件限制建仓与退出。
# 跨区域直接复用事件特征是极其危险的，因为不同国家的舆情/数据提供商完全不同。

# 建仓开仓事件 (Open Events)
# 偏向/特点：偏重于使用【量价异常】作为触发条件。
# 如 `ts_arg_max(volume, 5) == 0` (今日成交量创5日新高)，这是一种极短期的强动量确认信号。
# 或是 `ts_corr(close, volume, 5) < 0` (量价背离)，常作为反转信号的入场确认。
open_event_templates = [
    "ts_arg_max(volume, 5) == 0", "ts_corr(close, volume, 20) < 0",
    "ts_corr(close, volume, 5) < 0", "ts_mean(volume,10)>ts_mean(volume,60)",
    "group_rank(ts_std_dev(returns,60), sector) > 0.7", "ts_zscore(returns,60) > 2",
    "ts_arg_min(volume, 5) > 3",
    "ts_std_dev(returns, 5) > ts_std_dev(returns, 20)",
    "ts_arg_max(close, 5) == 0", "ts_arg_max(close, 20) == 0",
    "ts_corr(close, volume, 5) > 0", "ts_corr(close, volume, 5) > 0.3", "ts_corr(close, volume, 5) > 0.5",
    "ts_corr(close, volume, 20) > 0", "ts_corr(close, volume, 20) > 0.3", "ts_corr(close, volume, 20) > 0.5",
    "ts_regression(returns, %s, 5, lag = 0, rettype = 2) > 0",
    "ts_regression(returns, %s, 20, lag = 0, rettype = 2) > 0",
    "ts_regression(returns, ts_step(20), 20, lag = 0, rettype = 2) > 0",
    "ts_regression(returns, ts_step(5), 5, lag = 0, rettype = 2) > 0"
]

# 退出止损/止盈事件 (Exit Events)
# 偏向/特点：强行平仓条件。如绝对收益率超过 10% (0.1) 则退出，防止过度暴露。"-1" 可能是永远不主动触发，交由主逻辑控制。
exit_events = ["abs(returns) > 0.1", "-1"]

# -- 各个国家特定舆情与情绪事件 --

# -- 美国 (USA) --
# 偏向/特点：美股市场新闻数据覆盖最全。高度依赖 `rp_css` (RavenPack 新闻商业情绪) 
# 和 `mws / nws` (MarketPsych 社交媒体及新闻情绪)，以及 `pcr_oi` (期权看跌/看涨比例) 这种成熟市场特有指标。
usa_events = [
    "rank(rp_css_business) > 0.8", "ts_rank(rp_css_business, 22) > 0.8", "rank(vec_avg(mws82_sentiment)) > 0.8",
    "ts_rank(vec_avg(mws82_sentiment),22) > 0.8", "rank(vec_avg(nws48_ssc)) > 0.8",
    "ts_rank(vec_avg(nws48_ssc),22) > 0.8", "rank(vec_avg(mws50_ssc)) > 0.8", "ts_rank(vec_avg(mws50_ssc),22) > 0.8",
    "ts_rank(vec_sum(scl12_alltype_buzzvec),22) > 0.9", "pcr_oi_270 < 1", "pcr_oi_270 > 1"
]

# -- 亚洲除日股 (ASI) --
# 偏向/特点：由于新兴市场数据参差不齐，仅保留最基础的跨区域通用综合情绪指标 (`mws38_score`)。
asi_events = ["rank(vec_avg(mws38_score)) > 0.8", "ts_rank(vec_avg(mws38_score),22) > 0.8"]

# -- 欧洲 (EUR) --
# 偏向/特点：除了基础新闻情绪，加入了极强的卖方研究机构数据偏好，
# 例如 `oth429_research_reports` (研究报告关键词提取) 和 `mdl110_analyst_sentiment` (分析师情绪评分)。
eur_events = [
    "rank(rp_css_business) > 0.8", "ts_rank(rp_css_business, 22) > 0.8",
    "rank(vec_avg(oth429_research_reports_fundamental_keywords_4_method_2_pos)) > 0.8",
    "ts_rank(vec_avg(oth429_research_reports_fundamental_keywords_4_method_2_pos),22) > 0.8",
    "rank(vec_avg(mws84_sentiment)) > 0.8", "ts_rank(vec_avg(mws84_sentiment),22) > 0.8",
    "rank(vec_avg(mws85_sentiment)) > 0.8", "ts_rank(vec_avg(mws85_sentiment),22) > 0.8",
    "rank(mdl110_analyst_sentiment) > 0.8", "ts_rank(mdl110_analyst_sentiment, 22) > 0.8",
    "rank(vec_avg(nws3_scores_posnormscr)) > 0.8",
    "ts_rank(vec_avg(nws3_scores_posnormscr),22) > 0.8",
    "rank(vec_avg(mws36_sentiment_words_positive)) > 0.8",
    "ts_rank(vec_avg(mws36_sentiment_words_positive),22) > 0.8"
]

# -- 全球 (GLB) --
# 偏向/特点：仅使用覆盖率最广的新闻情绪 `nws20` 与模型新闻预测 `mdl109`，因为局部小国无特定高级特征。
glb_events = [
    "rank(vec_avg(mdl109_news_sent_1m)) > 0.8",
    "ts_rank(vec_avg(mdl109_news_sent_1m),22) > 0.8",
    "rank(vec_avg(nws20_ssc)) > 0.8",
    "ts_rank(vec_avg(nws20_ssc),22) > 0.8",
    "vec_avg(nws20_ssc) > 0",
    "rank(vec_avg(nws20_bee)) > 0.8",
    "ts_rank(vec_avg(nws20_bee),22) > 0.8",
    "rank(vec_avg(nws20_qmb)) > 0.8",
    "ts_rank(vec_avg(nws20_qmb),22) > 0.8"
]

# -- 中国大陆 (CHN) --
# 偏向/特点：中国 A 股特供的本土化散户情绪指标，这是其它市场完全没有的特征。
# 包括 `xueqiu...` (雪球论坛讨论度与情感极性) 和 `guba...` (东方财富股吧讨论情绪)。
chn_events = [
    "rank(vec_avg(oth111_xueqiunaturaldaybasicdivisionstat_senti_conform)) > 0.8",
    "ts_rank(vec_avg(oth111_xueqiunaturaldaybasicdivisionstat_senti_conform),22) > 0.8",
    "rank(vec_avg(oth111_gubanaturaldaydevicedivisionstat_senti_conform)) > 0.8",
    "ts_rank(vec_avg(oth111_gubanaturaldaydevicedivisionstat_senti_conform),22) > 0.8",
    "rank(vec_avg(oth111_baragedivisionstat_regi_senti_conform)) > 0.8",
    "ts_rank(vec_avg(oth111_baragedivisionstat_regi_senti_conform),22) > 0.8"
]

# -- 韩国 (KOR) --
# 偏向/特点：除了亚洲通用的 `mws38_score`，韩国市场对分析师情感评分 (`mdl110`) 的反应极其有效。
kor_events = [
    "rank(vec_avg(mdl110_analyst_sentiment)) > 0.8",
    "ts_rank(vec_avg(mdl110_analyst_sentiment),22) > 0.8",
    "rank(vec_avg(mws38_score)) > 0.8",
    "ts_rank(vec_avg(mws38_score),22) > 0.8"
]

# -- 台湾 (TWN) --
# 偏向/特点：由于其强烈的半导体科技周期属性，特定的商业新闻情绪 (`rp_ess_business`) 对于捕捉行业拐点较为敏锐。
twn_events = [
    "rank(vec_avg(mdl109_news_sent_1m)) > 0.8",
    "ts_rank(vec_avg(mdl109_news_sent_1m),22) > 0.8",
    "rank(rp_ess_business) > 0.8",
    "ts_rank(rp_ess_business,22) > 0.8"
]


# ------------------------------------------------------------------------------
# 5. 提交前 Alpha 校验与检测 (Submission Checks)
# ------------------------------------------------------------------------------
# 【校验门槛设计原理】
# 所有的 Alpha 候选者在经过批量模拟后，都必须满足以下硬门槛，否则必须弃用或进入优化循环。
# 此处定义的阈值将作为 `machine_lib.py` 和上层策略验证的统一标准参考。

from Core.sim.research_policy import submission_thresholds  # Deprecated compatibility alias.

# 【提交前黄金法则】
# 1. 只有通过全部基础门槛、单数据集约束和实时检查后，才允许进入最终候选池。
# 2. 生产相关性 (PROD_CORRELATION) 缺失或大于 0.7，一律不得进入提交候选。
# 3. 如果缺少实时检查、接口超时或报 429 错误，必须将其标记为 `PENDING`，决不允许假定为“通过”。
