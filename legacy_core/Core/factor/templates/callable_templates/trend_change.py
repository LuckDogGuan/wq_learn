"""可直接调用的模板本体；未验证不代表有效，差表现由disabled_templates.py排除。"""

def scale_transform(field, d=252):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 scale、rank、ts_av_diff；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): scale(rank(ts_av_diff({field},252)))
    使用算子 (Operators Used): scale, rank, ts_av_diff
    参数建议 (Parameter Recommendations): d 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.67f904a55f58bef4
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/24957813446167
    """
    return f'scale(rank(ts_av_diff({field}, {d})))'


def quantile_transform(field, d=252):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 quantile、rank、ts_av_diff；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): quantile(rank(ts_av_diff({field},252)))
    使用算子 (Operators Used): quantile, rank, ts_av_diff
    参数建议 (Parameter Recommendations): d 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.cd14b36577bbd39c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/24957813446167
    """
    return f'quantile(rank(ts_av_diff({field}, {d})))'


def ts_delta_transform(field, d=3):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): -ts_delta({field},3)
    使用算子 (Operators Used): ts_delta
    参数建议 (Parameter Recommendations): d 默认3，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.e2254b045c01130c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/26054361848343
    """
    return f'-ts_delta({field}, {d})'


def ts_delta_transform_508f467b(field, d=4):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_delta({field}, 4) > 0.1
    使用算子 (Operators Used): ts_delta
    参数建议 (Parameter Recommendations): d 默认4，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.508f467b3f0331c5
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'ts_delta({field}, {d}) > 0.1'


def rank_transform_04a6e8c0(field, d=5):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 rank、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_delta({field}, 5))
    使用算子 (Operators Used): rank, ts_delta
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.04a6e8c0517e98db
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42215740602135
    """
    return f'rank(ts_delta({field}, {d}))'


def rank_transform_7091c264(field, d1=5, d2=5):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 rank、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): -ts_delta({field},5)-rank(ts_delta({field},5))
    使用算子 (Operators Used): rank, ts_delta
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.7091c26469bfc4a0
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/15238236356375
    """
    return f'-ts_delta({field}, {d1}) - rank(ts_delta({field}, {d2}))'


def ts_product_transform_918543c1(field, d1=122, d2=22):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 ts_product、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_product({field}, 122) + ts_delta({field}, 22)
    使用算子 (Operators Used): ts_product, ts_delta
    参数建议 (Parameter Recommendations): d1 默认122，窗口可比较20或60（必须重新验证）, d2 默认22，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.918543c1d44708fa
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/40734437350679
    """
    return f'ts_product({field}, {d1}) + ts_delta({field}, {d2})'


def ts_returns(field, d=1):
    """
    趋势变化与反转
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): ts_returns({field}, 1)
    使用算子 (Operators Used): ts_returns
    参数建议 (Parameter Recommendations): d 默认1，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.a1c2126ca09eff3c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/41732813691287
    """
    return f'ts_returns({field}, {d})'


def hump_transform(field, d=5):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 hump、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): hump(-ts_delta({field}, 5), hump=0.01)
    使用算子 (Operators Used): hump, ts_delta
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.e8bf34404148c2d4
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/37117908343831
    """
    return f'hump(-ts_delta({field}, {d}), hump=0.01)'


def rank_transform_15046bd5(field, d=20):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 rank、ts_returns；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_returns({field}, 20))
    使用算子 (Operators Used): rank, ts_returns
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.15046bd5cc815da8
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42259186135831
    """
    return f'rank(ts_returns({field}, {d}))'


def rank_transform_2859ed31(field, d1=5, d2=5):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 rank、ts_delta、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_delta(ts_mean({field}, 5), 5))
    使用算子 (Operators Used): rank, ts_delta, ts_mean
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.2859ed31e32d9933
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(ts_delta(ts_mean({field}, {d2}), {d1}))'


def ts_decay_linear_transform_496f9e9d(field, d1=10, d2=22):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 ts_decay_linear、rank、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_decay_linear(rank(ts_delta({field}, 22)), 10)
    使用算子 (Operators Used): ts_decay_linear, rank, ts_delta
    参数建议 (Parameter Recommendations): d1 默认10，窗口可比较20或60（必须重新验证）, d2 默认22，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.496f9e9d23f8a846
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_decay_linear(rank(ts_delta({field}, {d2})), {d1})'


def ts_delta_transform_5a6ebebc(field, d1=5, d2=5):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 ts_delta、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_delta(ts_mean({field}, 5), 5)
    使用算子 (Operators Used): ts_delta, ts_mean
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.5a6ebebc0826f636
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_delta(ts_mean({field}, {d2}), {d1})'


def ts_decay_linear_transform_6a3ff7a7(field, d1=5, d2=1):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 ts_decay_linear、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_decay_linear(ts_delta({field},1),5)
    使用算子 (Operators Used): ts_decay_linear, ts_delta
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认1，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.6a3ff7a7276eb0f6
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/35876513619607
    """
    return f'ts_decay_linear(ts_delta({field}, {d2}), {d1})'


def ts_delta_transform_7e55e257(field, d1=5, d2=5):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 ts_delta、ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_delta({field}, 5) / ts_delay({field}, 5)
    使用算子 (Operators Used): ts_delta, ts_delay
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.7e55e25728e3c86f
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_delta({field}, {d1}) / ts_delay({field}, {d2})'


def ts_delta_transform_81651b1f(field, d=5):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_delta({field}, 5) / {field}
    使用算子 (Operators Used): ts_delta
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.81651b1f435809ab
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42587179348119
    """
    return f'ts_delta({field}, {d}) / {field}'


def rank_transform_abc311a0(field, d=10):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 rank、ts_av_diff；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_av_diff({field}, 10))
    使用算子 (Operators Used): rank, ts_av_diff
    参数建议 (Parameter Recommendations): d 默认10，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.abc311a07ddacfb5
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(ts_av_diff({field}, {d}))'


def rank_transform_bb455e1c(field, d=5):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 rank、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(-ts_delta({field},5))
    使用算子 (Operators Used): rank, ts_delta
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.bb455e1cbf8c4e9b
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(-ts_delta({field}, {d}))'


def ts_delta_transform_bf64e4f7(field, d1=5, d2=5):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_delta(ts_delta({field}, 5), 5)
    使用算子 (Operators Used): ts_delta
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.bf64e4f7df68830e
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_delta(ts_delta({field}, {d2}), {d1})'


def rank_transform_cc364e2c(field, d1=5, d2=20):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 rank、ts_delta、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_delta(ts_backfill({field}, 20), 5))
    使用算子 (Operators Used): rank, ts_delta, ts_backfill
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.cc364e2c68e45f79
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/34738466323095
    """
    return f'rank(ts_delta(ts_backfill({field}, {d2}), {d1}))'


def average_difference(field, d=50):
    """
    趋势变化与反转
    逻辑 (Logic): 将当前值与滚动均值比较；正值表示高于窗口均值。
    模板 (Template): ts_av_diff({field}, 50)
    使用算子 (Operators Used): ts_av_diff
    参数建议 (Parameter Recommendations): d 默认50，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.e99dac58762fe3d6
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42187744015767
    """
    return f'ts_av_diff({field}, {d})'


def ts_delta_transform_f9804c94(field, d1=10, d2=5, d3=20):
    """
    趋势变化与反转
    逻辑 (Logic): 依次组合 ts_delta、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_mean({field}, 5) / ts_mean({field}, 20) * ts_delta({field}, 10)
    使用算子 (Operators Used): ts_delta, ts_mean
    参数建议 (Parameter Recommendations): d1 默认10，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）, d3 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.f9804c949ead271b
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_mean({field}, {d2}) / ts_mean({field}, {d3}) * ts_delta({field}, {d1})'
