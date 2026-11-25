"""可直接调用的模板本体；未验证不代表有效，差表现由disabled_templates.py排除。"""

def time_series_rank(field, d=60):
    """
    时序排名与区间位置
    逻辑 (Logic): 计算当前值在历史窗口中的排名。
    模板 (Template): ts_rank({field}, 60)
    使用算子 (Operators Used): ts_rank
    参数建议 (Parameter Recommendations): d 默认60，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.3e31ccaa44da4394
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/26054361848343
    """
    return f'ts_rank({field}, {d})'


def rank_transform(field, d=100):
    """
    时序排名与区间位置
    逻辑 (Logic): 依次组合 rank、ts_rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_rank({field}, 100))
    使用算子 (Operators Used): rank, ts_rank
    参数建议 (Parameter Recommendations): d 默认100，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.3f552d78bb2845a2
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/24957813446167
    """
    return f'rank(ts_rank({field}, {d}))'


def ts_quantile(field, d=80):
    """
    时序排名与区间位置
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): ts_quantile({field},80)
    使用算子 (Operators Used): ts_quantile
    参数建议 (Parameter Recommendations): d 默认80，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.edfc15957e6d8a6e
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/24957813446167
    """
    return f'ts_quantile({field}, {d})'


def ts_rank_transform_edb19fda(field, d1=5, d2=60):
    """
    时序排名与区间位置
    逻辑 (Logic): 依次组合 ts_rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): (3)-1 * (ts_rank({field}, 5) - ts_rank({field}, 60))
    使用算子 (Operators Used): ts_rank
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认60，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.edb19fdad84fd35c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'3 - 1 * (ts_rank({field}, {d1}) - ts_rank({field}, {d2}))'


def ts_rank_transform_4e0d9be3(field, d1=126, d2=252):
    """
    时序排名与区间位置
    逻辑 (Logic): 依次组合 ts_rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_rank({field}, 126) * 0.4 + ts_rank({field}, 252) * 0.6
    使用算子 (Operators Used): ts_rank
    参数建议 (Parameter Recommendations): d1 默认126，窗口可比较20或60（必须重新验证）, d2 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.4e0d9be33552b1ec
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/36335101288215
    """
    return f'ts_rank({field}, {d1}) * 0.4 + ts_rank({field}, {d2}) * 0.6'


def ts_rank_transform_2a4ceb07(field, d1=5, d2=20):
    """
    时序排名与区间位置
    逻辑 (Logic): 依次组合 ts_rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_rank({field}, 5) - ts_rank({field}, 20)
    使用算子 (Operators Used): ts_rank
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.2a4ceb070e600ecb
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_rank({field}, {d1}) - ts_rank({field}, {d2})'


def ts_mean_transform_2f89d15e(field, d1=3, d2=10):
    """
    时序排名与区间位置
    逻辑 (Logic): 依次组合 ts_mean、ts_rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_mean(ts_rank({field}, 10), 3)
    使用算子 (Operators Used): ts_mean, ts_rank
    参数建议 (Parameter Recommendations): d1 默认3，窗口可比较20或60（必须重新验证）, d2 默认10，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.2f89d15e1aa9b409
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/40962586503191
    """
    return f'ts_mean(ts_rank({field}, {d2}), {d1})'


def rank_transform_3a855abd(field, d1=5, d2=1):
    """
    时序排名与区间位置
    逻辑 (Logic): 依次组合 rank、ts_rank、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(-ts_rank(ts_delta({field}, 1), 5))
    使用算子 (Operators Used): rank, ts_rank, ts_delta
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认1，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.3a855abd7c8584ba
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(-ts_rank(ts_delta({field}, {d2}), {d1}))'


def ts_scale(field, d=66):
    """
    时序排名与区间位置
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): ts_scale({field},66)
    使用算子 (Operators Used): ts_scale
    参数建议 (Parameter Recommendations): d 默认66，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.6a2b240a68aae7cd
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/31280678526615
    """
    return f'ts_scale({field}, {d})'


def ts_decay_linear_transform_9956015a(field, d1=63, d2=252):
    """
    时序排名与区间位置
    逻辑 (Logic): 依次组合 ts_decay_linear、ts_rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_decay_linear(ts_rank({field}, 252), 63)
    使用算子 (Operators Used): ts_decay_linear, ts_rank
    参数建议 (Parameter Recommendations): d1 默认63，窗口可比较20或60（必须重新验证）, d2 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.9956015a36ca00c1
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_decay_linear(ts_rank({field}, {d2}), {d1})'


def ts_scale_transform(field, d=660):
    """
    时序排名与区间位置
    逻辑 (Logic): 依次组合 ts_scale、rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_scale(rank({field}), 660)
    使用算子 (Operators Used): ts_scale, rank
    参数建议 (Parameter Recommendations): d 默认660，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.c2d9cb6415d03a68
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/28107291019031
    """
    return f'ts_scale(rank({field}), {d})'


def ts_rank_transform_d54fa3ca(field, d1=252, d2=6):
    """
    时序排名与区间位置
    逻辑 (Logic): 依次组合 ts_rank、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_rank(ts_mean({field}, 6), 252) - 0.5
    使用算子 (Operators Used): ts_rank, ts_mean
    参数建议 (Parameter Recommendations): d1 默认252，窗口可比较20或60（必须重新验证）, d2 默认6，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.d54fa3ca12090f9e
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_rank(ts_mean({field}, {d2}), {d1}) - 0.5'


def ts_backfill_transform(field, d1=3, d2=5):
    """
    时序排名与区间位置
    逻辑 (Logic): 依次组合 ts_backfill、ts_rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_backfill(ts_rank({field}, 5), 3)
    使用算子 (Operators Used): ts_backfill, ts_rank
    参数建议 (Parameter Recommendations): d1 默认3，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.de05f01449066924
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/40972941718807
    """
    return f'ts_backfill(ts_rank({field}, {d2}), {d1})'


def ts_rank_transform_ea7a5eb8(field, d1=10, d2=5, d3=5):
    """
    时序排名与区间位置
    逻辑 (Logic): 依次组合 ts_rank、ts_delta、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_rank(ts_delta(ts_mean({field}, 5), 5), 10)
    使用算子 (Operators Used): ts_rank, ts_delta, ts_mean
    参数建议 (Parameter Recommendations): d1 默认10，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）, d3 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.ea7a5eb895a16f6e
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_rank(ts_delta(ts_mean({field}, {d3}), {d2}), {d1})'
