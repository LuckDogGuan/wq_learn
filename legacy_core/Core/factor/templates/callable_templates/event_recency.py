"""可直接调用的模板本体；未验证不代表有效，差表现由disabled_templates.py排除。"""

def ts_arg_max_transform(field, d=150):
    """
    事件频率与距今时间
    逻辑 (Logic): 依次组合 ts_arg_max；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): 185*(65-ts_arg_max({field},150))/150
    使用算子 (Operators Used): ts_arg_max
    参数建议 (Parameter Recommendations): d 默认150，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.08f5a7f630a8b8db
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/24957813446167
    """
    return f'185 * (65 - ts_arg_max({field}, {d})) / 150'


def ts_arg_min_transform(field, d=150):
    """
    事件频率与距今时间
    逻辑 (Logic): 依次组合 ts_arg_min；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): 185*(65-ts_arg_min({field},150))/150
    使用算子 (Operators Used): ts_arg_min
    参数建议 (Parameter Recommendations): d 默认150，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.5fd725e4231d5ed7
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/24957813446167
    """
    return f'185 * (65 - ts_arg_min({field}, {d})) / 150'


def ts_count_nans_transform(field, d1=20, d2=5):
    """
    事件频率与距今时间
    逻辑 (Logic): 依次组合 ts_count_nans、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): -ts_count_nans(ts_backfill({field}, 5), 20)
    使用算子 (Operators Used): ts_count_nans, ts_backfill
    参数建议 (Parameter Recommendations): d1 默认20，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.24cbc202ff537b5b
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/36183099180823
    """
    return f'-ts_count_nans(ts_backfill({field}, {d2}), {d1})'


def ts_arg_min(field, d=252):
    """
    事件频率与距今时间
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): ts_arg_min({field},252)
    使用算子 (Operators Used): ts_arg_min
    参数建议 (Parameter Recommendations): d 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.90ad590da6401d62
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/23807105368215
    """
    return f'ts_arg_min({field}, {d})'


def ts_arg_min_transform_c404884b(field, d=252):
    """
    事件频率与距今时间
    逻辑 (Logic): 依次组合 ts_arg_min、scale；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_arg_min(scale({field},longscale=1,shortscale=0),252)
    使用算子 (Operators Used): ts_arg_min, scale
    参数建议 (Parameter Recommendations): d 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.c404884ba84bead3
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/23807105368215
    """
    return f'ts_arg_min(scale({field}, longscale=1, shortscale=0), {d})'


def days_from_last_change(field):
    """
    事件频率与距今时间
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): days_from_last_change({field})
    使用算子 (Operators Used): days_from_last_change
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.d81add19de48fd2a
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/20565001927063
    """
    return f'days_from_last_change({field})'


def pasteurize_transform(field, d=252):
    """
    事件频率与距今时间
    逻辑 (Logic): 依次组合 pasteurize、ts_arg_min；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): pasteurize(ts_arg_min({field},252))
    使用算子 (Operators Used): pasteurize, ts_arg_min
    参数建议 (Parameter Recommendations): d 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.fc41f73c064d673d
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/23807105368215
    """
    return f'pasteurize(ts_arg_min({field}, {d}))'


def ts_arg_min_transform_7e423cb4(field, d=25):
    """
    事件频率与距今时间
    逻辑 (Logic): 依次组合 ts_arg_min；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): (25 - ts_arg_min({field}, 25))/25*100
    使用算子 (Operators Used): ts_arg_min
    参数建议 (Parameter Recommendations): d 默认25，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.7e423cb43af8430c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/20278408956439
    """
    return f'(25 - ts_arg_min({field}, {d})) / 25 * 100'


def ts_arg_max_transform_885965bb(field, d=25):
    """
    事件频率与距今时间
    逻辑 (Logic): 依次组合 ts_arg_max；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): (25 - ts_arg_max({field}, 25))/25*100
    使用算子 (Operators Used): ts_arg_max
    参数建议 (Parameter Recommendations): d 默认25，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.885965bbd681af4d
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/20278408956439
    """
    return f'(25 - ts_arg_max({field}, {d})) / 25 * 100'


def ts_arg_max_transform_6e285644(field, d1=22, d2=22):
    """
    事件频率与距今时间
    逻辑 (Logic): 依次组合 ts_arg_max、ts_arg_min；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_arg_max({field}, 22) - ts_arg_min({field}, 22)
    使用算子 (Operators Used): ts_arg_max, ts_arg_min
    参数建议 (Parameter Recommendations): d1 默认22，窗口可比较20或60（必须重新验证）, d2 默认22，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.6e28564444cc3e83
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42403326870423
    """
    return f'ts_arg_max({field}, {d1}) - ts_arg_min({field}, {d2})'
