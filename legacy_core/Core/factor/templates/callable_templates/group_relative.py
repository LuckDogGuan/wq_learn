"""可直接调用的模板本体；未验证不代表有效，差表现由disabled_templates.py排除。"""

def within_group_zscore(field, group='sector'):
    """
    组内比较与中性化
    逻辑 (Logic): 在同一组内标准化输入值。
    模板 (Template): group_zscore({field},sector)
    使用算子 (Operators Used): group_zscore
    参数建议 (Parameter Recommendations): group 默认'sector'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.6d45ce1b692bca90
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/26054361848343
    """
    return f'group_zscore({field}, {group})'


def group_mean(field, group='market'):
    """
    组内比较与中性化
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): group_mean({field},1,market)
    使用算子 (Operators Used): group_mean
    参数建议 (Parameter Recommendations): group 默认'market'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.829bd31f8bf03c42
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/26054361848343
    """
    return f'group_mean({field}, 1, {group})'


def scale_transform_f4ea125a(field, d=504, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 scale、group_neutralize、ts_av_diff；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): scale(group_neutralize(ts_av_diff({field},504),subindustry))
    使用算子 (Operators Used): scale, group_neutralize, ts_av_diff
    参数建议 (Parameter Recommendations): d 默认504，窗口可比较20或60（必须重新验证）, group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.f4ea125ae146da28
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/24957813446167
    """
    return f'scale(group_neutralize(ts_av_diff({field}, {d}), {group}))'


def quantile_transform_ff73b6d6(field, d=252, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 quantile、group_neutralize、ts_av_diff；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): quantile(group_neutralize(ts_av_diff({field},252),subindustry))
    使用算子 (Operators Used): quantile, group_neutralize, ts_av_diff
    参数建议 (Parameter Recommendations): d 默认252，窗口可比较20或60（必须重新验证）, group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.ff73b6d6e9d3713a
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/24957813446167
    """
    return f'quantile(group_neutralize(ts_av_diff({field}, {d}), {group}))'


def ts_product_transform(field, d=250, group='market'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 ts_product、group_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_product(1+group_mean({field},1,market),250)-1
    使用算子 (Operators Used): ts_product, group_mean
    参数建议 (Parameter Recommendations): d 默认250，窗口可比较20或60（必须重新验证）, group 默认'market'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.15c3fed1b5a7fe97
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/19992945218711
    """
    return f'ts_product(1 + group_mean({field}, 1, {group}), {d}) - 1'


def ts_zscore_transform_3518a881(field, d1=30, d2=3, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 ts_zscore、group_neutralize、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_zscore(group_neutralize(ts_delta({field}, 3), industry), 30) * -1
    使用算子 (Operators Used): ts_zscore, group_neutralize, ts_delta
    参数建议 (Parameter Recommendations): d1 默认30，窗口可比较20或60（必须重新验证）, d2 默认3，窗口可比较20或60（必须重新验证）, group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.3518a881e1223972
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'ts_zscore(group_neutralize(ts_delta({field}, {d2}), {group}), {d1}) * -1'


def group_rank_transform(field, d=66, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_backfill({field}, 66), industry)
    使用算子 (Operators Used): group_rank, ts_backfill
    参数建议 (Parameter Recommendations): d 默认66，窗口可比较20或60（必须重新验证）, group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.3d773bbce9f5fb8d
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/33247252289943
    """
    return f'group_rank(ts_backfill({field}, {d}), {group})'


def group_zscore_transform(field, d=5, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_zscore、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_zscore(ts_delta({field}, 5), industry)
    使用算子 (Operators Used): group_zscore, ts_delta
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）, group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.48d3754fa477d65c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'group_zscore(ts_delta({field}, {d}), {group})'


def group_mean_transform(field, group='exchange'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_mean、densify；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_mean({field}, 1 , densify(exchange))
    使用算子 (Operators Used): group_mean, densify
    参数建议 (Parameter Recommendations): group 默认'exchange'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.4fc603eca09c27d7
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/20284582494359
    """
    return f'group_mean({field}, 1, densify({group}))'


def group_rank_transform_5deb7407(field, d1=60, d2=60, group='sector'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_quantile、densify、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_quantile(ts_backfill({field}, 60), 60), densify(sector))
    使用算子 (Operators Used): group_rank, ts_quantile, densify, ts_backfill
    参数建议 (Parameter Recommendations): d1 默认60，窗口可比较20或60（必须重新验证）, d2 默认60，窗口可比较20或60（必须重新验证）, group 默认'sector'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.5deb740763be054d
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'group_rank(ts_quantile(ts_backfill({field}, {d2}), {d1}), densify({group}))'


def group_rank_transform_6a03b7ed(field, d1=60, d2=5, group='sector'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_zscore、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_zscore(ts_delta({field}, 5), 60), sector)
    使用算子 (Operators Used): group_rank, ts_zscore, ts_delta
    参数建议 (Parameter Recommendations): d1 默认60，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）, group 默认'sector'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.6a03b7ede8cd7e7c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'group_rank(ts_zscore(ts_delta({field}, {d2}), {d1}), {group})'


def group_neutralize_transform(field, d=5, group='sector'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_neutralize、rank、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_neutralize(rank(ts_backfill({field}, 5)), sector)
    使用算子 (Operators Used): group_neutralize, rank, ts_backfill
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）, group 默认'sector'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.7c3ddd81b6e966a1
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'group_neutralize(rank(ts_backfill({field}, {d})), {group})'


def group_zscore_transform_8f97d7b4(field, d1=20, d2=2, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_zscore、ts_zscore、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_zscore(ts_zscore(ts_delta({field}, 2), 20), industry) * -1
    使用算子 (Operators Used): group_zscore, ts_zscore, ts_delta
    参数建议 (Parameter Recommendations): d1 默认20，窗口可比较20或60（必须重新验证）, d2 默认2，窗口可比较20或60（必须重新验证）, group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.8f97d7b4db20cac1
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'group_zscore(ts_zscore(ts_delta({field}, {d2}), {d1}), {group}) * -1'


def group_neutralize_transform_977fd958(field, d1=252, d2=1, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_neutralize、rank、ts_rank、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_neutralize(rank(ts_rank(-ts_delta({field}, 1), 252)), subindustry)
    使用算子 (Operators Used): group_neutralize, rank, ts_rank, ts_delta
    参数建议 (Parameter Recommendations): d1 默认252，窗口可比较20或60（必须重新验证）, d2 默认1，窗口可比较20或60（必须重新验证）, group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.977fd958136db55c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42278736684311
    """
    return f'group_neutralize(rank(ts_rank(-ts_delta({field}, {d2}), {d1})), {group})'


def group_rank_transform_ac0a4ad1(field, d1=20, d2=20, group='sector'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_rank、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_rank(ts_delta({field}, 20), 20), sector)
    使用算子 (Operators Used): group_rank, ts_rank, ts_delta
    参数建议 (Parameter Recommendations): d1 默认20，窗口可比较20或60（必须重新验证）, d2 默认20，窗口可比较20或60（必须重新验证）, group 默认'sector'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.ac0a4ad104cc6e63
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'group_rank(ts_rank(ts_delta({field}, {d2}), {d1}), {group})'


def group_rank_transform_bc29fee0(field, d1=22, d2=120, group='market'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_arg_max、densify、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_arg_max(ts_backfill({field}, 120), 22),densify(market))
    使用算子 (Operators Used): group_rank, ts_arg_max, densify, ts_backfill
    参数建议 (Parameter Recommendations): d1 默认22，窗口可比较20或60（必须重新验证）, d2 默认120，窗口可比较20或60（必须重新验证）, group 默认'market'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.bc29fee0a723ee48
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/40436845240087
    """
    return f'group_rank(ts_arg_max(ts_backfill({field}, {d2}), {d1}), densify({group}))'


def group_count(field, group='market'):
    """
    组内比较与中性化
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): group_count({field}, market)
    使用算子 (Operators Used): group_count
    参数建议 (Parameter Recommendations): group 默认'market'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.e918b3905d29a78c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/29085671898775
    """
    return f'group_count({field}, {group})'


def ts_rank_transform_f65371a4(field, d=10, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 ts_rank、group_neutralize；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_rank(group_neutralize({field}, industry), 10)
    使用算子 (Operators Used): ts_rank, group_neutralize
    参数建议 (Parameter Recommendations): d 默认10，窗口可比较20或60（必须重新验证）, group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.f65371a4690a9262
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/24497520676119
    """
    return f'ts_rank(group_neutralize({field}, {group}), {d})'


def group_neutralize_transform_181ee145(field, d1=60, d2=5, group='sector'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_neutralize、ts_rank、densify、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_neutralize(ts_rank(ts_delta({field}, 5), 60), densify(sector))
    使用算子 (Operators Used): group_neutralize, ts_rank, densify, ts_delta
    参数建议 (Parameter Recommendations): d1 默认60，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）, group 默认'sector'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.181ee1451874a033
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/36221002981271
    """
    return f'group_neutralize(ts_rank(ts_delta({field}, {d2}), {d1}), densify({group}))'


def group_sum_transform(field, group='market'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_sum；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): {field}/group_sum({field},market)
    使用算子 (Operators Used): group_sum
    参数建议 (Parameter Recommendations): group 默认'market'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.18c3ee043da23e99
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/34535942900375
    """
    return f'{field} / group_sum({field}, {group})'


def group_rank_transform_29fb904d(field, d=5, group='market'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(-ts_delta({field}, 5), market)
    使用算子 (Operators Used): group_rank, ts_delta
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）, group 默认'market'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.29fb904d1fa5211f
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/36772449354519
    """
    return f'group_rank(-ts_delta({field}, {d}), {group})'


def group_rank_transform_3b002527(field, d1=132, d2=66, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_zscore、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_zscore(ts_backfill({field}, 66), 132), subindustry)
    使用算子 (Operators Used): group_rank, ts_zscore, ts_backfill
    参数建议 (Parameter Recommendations): d1 默认132，窗口可比较20或60（必须重新验证）, d2 默认66，窗口可比较20或60（必须重新验证）, group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.3b002527d4296814
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/41135490599063
    """
    return f'group_rank(ts_zscore(ts_backfill({field}, {d2}), {d1}), {group})'


def group_mean_transform_3e38dfd4(field, group='market'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): {field} - group_mean({field},1,market)
    使用算子 (Operators Used): group_mean
    参数建议 (Parameter Recommendations): group 默认'market'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.3e38dfd4df5c56b4
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/37245403025431
    """
    return f'{field} - group_mean({field}, 1, {group})'


def group_neutralize_transform_82cf1239(field, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_neutralize、zscore；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_neutralize(zscore({field}), industry)
    使用算子 (Operators Used): group_neutralize, zscore
    参数建议 (Parameter Recommendations): group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.82cf1239ad79bcfd
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/34670122621207
    """
    return f'group_neutralize(zscore({field}), {group})'


def group_neutralize_transform_9118cb42(field, d1=60, d2=20, group='sector'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_neutralize、ts_rank、densify、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_neutralize(ts_rank(ts_mean({field}, 20), 60), densify(sector))
    使用算子 (Operators Used): group_neutralize, ts_rank, densify, ts_mean
    参数建议 (Parameter Recommendations): d1 默认60，窗口可比较20或60（必须重新验证）, d2 默认20，窗口可比较20或60（必须重新验证）, group 默认'sector'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.9118cb42b80ef01a
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/36221002981271
    """
    return f'group_neutralize(ts_rank(ts_mean({field}, {d2}), {d1}), densify({group}))'


def rank_transform_987be298(field, group='country'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 rank、group_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(group_mean({field}, 1, country))
    使用算子 (Operators Used): rank, group_mean
    参数建议 (Parameter Recommendations): group 默认'country'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.987be298b9f7cbc8
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42258807786391
    """
    return f'rank(group_mean({field}, 1, {group}))'


def group_rank_transform_9c25dd69(field, d=240, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_scale；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_scale({field}, 240), industry)
    使用算子 (Operators Used): group_rank, ts_scale
    参数建议 (Parameter Recommendations): d 默认240，窗口可比较20或60（必须重新验证）, group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.9c25dd6913b0cd15
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/40972941718807
    """
    return f'group_rank(ts_scale({field}, {d}), {group})'


def group_neutralize_transform_ad967f9c(field, group1='country', group2='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_neutralize、group_cartesian_product；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_neutralize({field}, group_cartesian_product(country, industry))
    使用算子 (Operators Used): group_neutralize, group_cartesian_product
    参数建议 (Parameter Recommendations): group1 默认'country'，需有效分组字段, group2 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.ad967f9ce732c34f
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/34208186164631
    """
    return f'group_neutralize({field}, group_cartesian_product({group1}, {group2}))'


def group_backfill_transform(field, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): -group_backfill({field}, subindustry, 126, std = 4.0)
    使用算子 (Operators Used): group_backfill
    参数建议 (Parameter Recommendations): group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.b43b2a2f7306d1cc
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/35090833341207
    """
    return f'-group_backfill({field}, {group}, 126, std=4.0)'


def group_rank_transform_026c9d49(field, d=20, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_delta({field}, 20), industry)
    使用算子 (Operators Used): group_rank, ts_delta
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）, group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.026c9d4962919908
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'group_rank(ts_delta({field}, {d}), {group})'


def ts_zscore_transform_083babe8(field, d1=63, d2=63, group='sector'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 ts_zscore、group_neutralize；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_zscore({field}, 63) - ts_zscore(group_neutralize({field}, sector), 63)
    使用算子 (Operators Used): ts_zscore, group_neutralize
    参数建议 (Parameter Recommendations): d1 默认63，窗口可比较20或60（必须重新验证）, d2 默认63，窗口可比较20或60（必须重新验证）, group 默认'sector'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.083babe84c644b32
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42045578950551
    """
    return f'ts_zscore({field}, {d1}) - ts_zscore(group_neutralize({field}, {group}), {d2})'


def group_neutralize_transform_0d7aa64c(field, d=10, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_neutralize、rank、ts_std_dev；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_neutralize(rank({field})/ts_std_dev({field}, 10),industry)
    使用算子 (Operators Used): group_neutralize, rank, ts_std_dev
    参数建议 (Parameter Recommendations): d 默认10，窗口可比较20或60（必须重新验证）, group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.0d7aa64ca33d8309
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'group_neutralize(rank({field}) / ts_std_dev({field}, {d}), {group})'


def group_neutralize_transform_1a65b86b(field, d1=63, d2=21, d3=10, group='sector'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_neutralize、ts_rank、ts_std_dev；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_neutralize(ts_rank(ts_rank({field}, 21) * ts_std_dev({field}, 10), 63), sector)
    使用算子 (Operators Used): group_neutralize, ts_rank, ts_std_dev
    参数建议 (Parameter Recommendations): d1 默认63，窗口可比较20或60（必须重新验证）, d2 默认21，窗口可比较20或60（必须重新验证）, d3 默认10，窗口可比较20或60（必须重新验证）, group 默认'sector'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.1a65b86be62b7cdc
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'group_neutralize(ts_rank(ts_rank({field}, {d2}) * ts_std_dev({field}, {d3}), {d1}), {group})'


def group_neutralize_transform_1aafdef3(field, d=20, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_neutralize、ts_zscore；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_neutralize(ts_zscore({field}, 20), industry)
    使用算子 (Operators Used): group_neutralize, ts_zscore
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）, group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.1aafdef3c1c0cead
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/30640499518231
    """
    return f'group_neutralize(ts_zscore({field}, {d}), {group})'


def group_rank_transform_26b77700(field, d=20, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_mean({field}, 20), industry)
    使用算子 (Operators Used): group_rank, ts_mean
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）, group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.26b7770003e7f67a
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/37176161580823
    """
    return f'group_rank(ts_mean({field}, {d}), {group})'


def group_rank_transform_27038cd4(field, d=5, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_sum；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_sum({field}, 5), subindustry)
    使用算子 (Operators Used): group_rank, ts_sum
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）, group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.27038cd424c17de9
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'group_rank(ts_sum({field}, {d}), {group})'


def group_std_dev(field, group='market'):
    """
    组内比较与中性化
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): group_std_dev({field}, market)
    使用算子 (Operators Used): group_std_dev
    参数建议 (Parameter Recommendations): group 默认'market'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.35d997f31b1d3b2f
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/19144966455959
    """
    return f'group_std_dev({field}, {group})'


def group_neutralize_transform_3a0d64cc(field, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_neutralize、rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_neutralize(rank({field}), industry)
    使用算子 (Operators Used): group_neutralize, rank
    参数建议 (Parameter Recommendations): group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.3a0d64cc91eb21bc
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'group_neutralize(rank({field}), {group})'


def group_zscore_transform_3a5a5d56(field, d1=66, d2=22, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_zscore、ts_zscore、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_zscore(ts_zscore(ts_delta({field}, 22), 66), subindustry)
    使用算子 (Operators Used): group_zscore, ts_zscore, ts_delta
    参数建议 (Parameter Recommendations): d1 默认66，窗口可比较20或60（必须重新验证）, d2 默认22，窗口可比较20或60（必须重新验证）, group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.3a5a5d561a547479
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42021244122775
    """
    return f'group_zscore(ts_zscore(ts_delta({field}, {d2}), {d1}), {group})'


def group_rank_transform_484e8e14(field, d1=120, d2=120, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_backfill(ts_backfill({field}, 120), 120), subindustry)
    使用算子 (Operators Used): group_rank, ts_backfill
    参数建议 (Parameter Recommendations): d1 默认120，窗口可比较20或60（必须重新验证）, d2 默认120，窗口可比较20或60（必须重新验证）, group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.484e8e140e4c63ca
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'group_rank(ts_backfill(ts_backfill({field}, {d2}), {d1}), {group})'


def group_count_transform(field, group='market'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_count、densify；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_count({field}, densify(market))
    使用算子 (Operators Used): group_count, densify
    参数建议 (Parameter Recommendations): group 默认'market'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.486dea3a8955475b
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/28263052428055
    """
    return f'group_count({field}, densify({group}))'


def group_rank_transform_4cba4fe9(field, d=63, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_zscore；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_zscore({field}, 63), subindustry)
    使用算子 (Operators Used): group_rank, ts_zscore
    参数建议 (Parameter Recommendations): d 默认63，窗口可比较20或60（必须重新验证）, group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.4cba4fe9f9fa93af
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'group_rank(ts_zscore({field}, {d}), {group})'


def within_group_rank(field, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 比较输入值在同一组中的排名。
    模板 (Template): group_rank({field}, subindustry)
    使用算子 (Operators Used): group_rank
    参数建议 (Parameter Recommendations): group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.7a5fb1191d6172ba
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'group_rank({field}, {group})'


def group_rank_transform_857d7c54(field, d=20, group='country'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_mean({field},20),country)>0.03
    使用算子 (Operators Used): group_rank, ts_mean
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）, group 默认'country'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.857d7c54c7cd0155
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/37473718017175
    """
    return f'group_rank(ts_mean({field}, {d}), {group}) > 0.03'


def ts_delay_transform_90dd3281(field, d1=20, d2=20, group='market'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 ts_delay、ts_mean、group_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_delay(ts_mean({field}-group_mean({field},1,market),20),20)
    使用算子 (Operators Used): ts_delay, ts_mean, group_mean
    参数建议 (Parameter Recommendations): d1 默认20，窗口可比较20或60（必须重新验证）, d2 默认20，窗口可比较20或60（必须重新验证）, group 默认'market'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.90dd328112854f99
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/20089517507735
    """
    return f'ts_delay(ts_mean({field} - group_mean({field}, 1, {group}), {d2}), {d1})'


def group_rank_transform_90f13264(field, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、densify；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank({field}, densify(subindustry))
    使用算子 (Operators Used): group_rank, densify
    参数建议 (Parameter Recommendations): group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.90f13264baf0f1fd
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42662873714711
    """
    return f'group_rank({field}, densify({group}))'


def rank_transform_98806ef0(field, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 rank、group_rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(group_rank({field}, industry))
    使用算子 (Operators Used): rank, group_rank
    参数建议 (Parameter Recommendations): group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.98806ef0d73b3a42
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(group_rank({field}, {group}))'


def group_zscore_transform_98ab1a0d(field, d1=66, d2=5, d3=22, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_zscore、ts_zscore、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_zscore(ts_zscore(ts_mean({field}, 5) - ts_mean({field}, 22), 66), industry)
    使用算子 (Operators Used): group_zscore, ts_zscore, ts_mean
    参数建议 (Parameter Recommendations): d1 默认66，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）, d3 默认22，窗口可比较20或60（必须重新验证）, group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.98ab1a0dc9f607b6
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'group_zscore(ts_zscore(ts_mean({field}, {d2}) - ts_mean({field}, {d3}), {d1}), {group})'


def group_neutralize_transform_992a3726(field, d=21, group='sector'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_neutralize、ts_rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_neutralize(ts_rank({field}, 21), sector)
    使用算子 (Operators Used): group_neutralize, ts_rank
    参数建议 (Parameter Recommendations): d 默认21，窗口可比较20或60（必须重新验证）, group 默认'sector'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.992a3726f07a002c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'group_neutralize(ts_rank({field}, {d}), {group})'


def group_zscore_transform_9dbfb149(field, d1=5, d2=126, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_zscore、ts_mean、ts_rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_zscore(ts_mean(ts_rank({field},126),5),subindustry)
    使用算子 (Operators Used): group_zscore, ts_mean, ts_rank
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认126，窗口可比较20或60（必须重新验证）, group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.9dbfb149114b1868
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42509573118999
    """
    return f'group_zscore(ts_mean(ts_rank({field}, {d2}), {d1}), {group})'


def ts_mean_transform_a323df1a(field, d=5, group='market'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 ts_mean、group_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_mean({field}-group_mean({field},1,market),5)
    使用算子 (Operators Used): ts_mean, group_mean
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）, group 默认'market'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.a323df1a154a3669
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/20089517507735
    """
    return f'ts_mean({field} - group_mean({field}, 1, {group}), {d})'


def group_rank_transform_a65fab7c(field, d1=40, d2=10, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_rank、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_rank(ts_mean({field}, 10), 40), subindustry)
    使用算子 (Operators Used): group_rank, ts_rank, ts_mean
    参数建议 (Parameter Recommendations): d1 默认40，窗口可比较20或60（必须重新验证）, d2 默认10，窗口可比较20或60（必须重新验证）, group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.a65fab7cf9f15c1d
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'group_rank(ts_rank(ts_mean({field}, {d2}), {d1}), {group})'


def group_rank_transform_af80a3d8(field, d=10, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_decay_linear；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_decay_linear({field}, 10), subindustry)
    使用算子 (Operators Used): group_rank, ts_decay_linear
    参数建议 (Parameter Recommendations): d 默认10，窗口可比较20或60（必须重新验证）, group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.af80a3d86052bff1
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'group_rank(ts_decay_linear({field}, {d}), {group})'


def group_rank_transform_b52bf478(field, d=20, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_rank({field}, 20), industry)
    使用算子 (Operators Used): group_rank, ts_rank
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）, group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.b52bf47837f9df38
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'group_rank(ts_rank({field}, {d}), {group})'


def rank_transform_bdfe840c(field, d=5, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 rank、group_neutralize、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(group_neutralize(ts_mean({field}, 5), industry))
    使用算子 (Operators Used): rank, group_neutralize, ts_mean
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）, group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.bdfe840cb8421769
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(group_neutralize(ts_mean({field}, {d}), {group}))'


def group_rank_transform_d5a91873(field, d1=252, d2=120, d3=120, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_delta、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): -group_rank(ts_delta(ts_backfill(ts_backfill({field}, 120), 120), 252), industry)
    使用算子 (Operators Used): group_rank, ts_delta, ts_backfill
    参数建议 (Parameter Recommendations): d1 默认252，窗口可比较20或60（必须重新验证）, d2 默认120，窗口可比较20或60（必须重新验证）, d3 默认120，窗口可比较20或60（必须重新验证）, group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.d5a918734056cc0d
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'-group_rank(ts_delta(ts_backfill(ts_backfill({field}, {d3}), {d2}), {d1}), {group})'


def min_transform(field, d=66, group='sector'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 min、group_rank、rank、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): min(group_rank({field}, sector), rank(ts_delta({field}, 66)))
    使用算子 (Operators Used): min, group_rank, rank, ts_delta
    参数建议 (Parameter Recommendations): d 默认66，窗口可比较20或60（必须重新验证）, group 默认'sector'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.da9212ca780efab0
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/32032672214807
    """
    return f'min(group_rank({field}, {group}), rank(ts_delta({field}, {d})))'


def group_zscore_transform_e3fa541b(field, d=2, group='sector'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_zscore、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_zscore(-ts_delta({field}, 2), sector)
    使用算子 (Operators Used): group_zscore, ts_delta
    参数建议 (Parameter Recommendations): d 默认2，窗口可比较20或60（必须重新验证）, group 默认'sector'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.e3fa541ba2c827d9
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'group_zscore(-ts_delta({field}, {d}), {group})'


def group_rank_transform_e5c480d5(field, d=60, group='sector'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_std_dev；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_std_dev({field},60),sector)>0.7
    使用算子 (Operators Used): group_rank, ts_std_dev
    参数建议 (Parameter Recommendations): d 默认60，窗口可比较20或60（必须重新验证）, group 默认'sector'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.e5c480d54fdd4d16
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/40531412200471
    """
    return f'group_rank(ts_std_dev({field}, {d}), {group}) > 0.7'


def group_rank_transform_ebbad5ec(field, d1=126, d2=120, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_rank、ts_quantile、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_rank(ts_quantile(-ts_backfill({field}, 120), 126), subindustry)
    使用算子 (Operators Used): group_rank, ts_quantile, ts_backfill
    参数建议 (Parameter Recommendations): d1 默认126，窗口可比较20或60（必须重新验证）, d2 默认120，窗口可比较20或60（必须重新验证）, group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.ebbad5ec9f47a11b
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/43322521365143
    """
    return f'group_rank(ts_quantile(-ts_backfill({field}, {d2}), {d1}), {group})'


def group_neutralization(field, group='subindustry'):
    """
    组内比较与中性化
    逻辑 (Logic): 去除输入值的组间均值差异。
    模板 (Template): group_neutralize({field}, subindustry)
    使用算子 (Operators Used): group_neutralize
    参数建议 (Parameter Recommendations): group 默认'subindustry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.f7bc659155753576
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/41134649919383
    """
    return f'group_neutralize({field}, {group})'


def group_neutralize_transform_fe3b6dc2(field, group='industry'):
    """
    组内比较与中性化
    逻辑 (Logic): 依次组合 group_neutralize、group_zscore；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): group_neutralize(group_zscore({field}, industry), industry)
    使用算子 (Operators Used): group_neutralize, group_zscore
    参数建议 (Parameter Recommendations): group 默认'industry'，需有效分组字段
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.fe3b6dc2204a475a
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42775887653399
    """
    return f'group_neutralize(group_zscore({field}, {group}), {group})'
