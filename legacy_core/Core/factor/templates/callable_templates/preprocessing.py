"""可直接调用的模板本体；未验证不代表有效，差表现由disabled_templates.py排除。"""

def ts_backfill(field, d=1200):
    """
    缺失值与异常值处理
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): ts_backfill({field},1200)
    使用算子 (Operators Used): ts_backfill
    参数建议 (Parameter Recommendations): d 默认1200，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.812d50a27bad3873
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/24957813446167
    """
    return f'ts_backfill({field}, {d})'


def hump_transform_4f4ac14a(field):
    """
    缺失值与异常值处理
    逻辑 (Logic): 依次组合 hump、rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): hump(rank({field}), hump=0.01)
    使用算子 (Operators Used): hump, rank
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.4f4ac14a6961d3bc
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/29095615954071
    """
    return f'hump(rank({field}), hump=0.01)'


def rank_transform_913e24da(field, d=66):
    """
    缺失值与异常值处理
    逻辑 (Logic): 依次组合 rank、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_backfill({field}, 66))
    使用算子 (Operators Used): rank, ts_backfill
    参数建议 (Parameter Recommendations): d 默认66，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.913e24dabb702c9b
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/41135490599063
    """
    return f'rank(ts_backfill({field}, {d}))'


def rank_transform_d18837cd(field, d=20):
    """
    缺失值与异常值处理
    逻辑 (Logic): 依次组合 rank、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(-ts_backfill({field},20))
    使用算子 (Operators Used): rank, ts_backfill
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.d18837cde767a196
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(-ts_backfill({field}, {d}))'


def ts_backfill_transform_f37cf545(field, d1=66, d2=120):
    """
    缺失值与异常值处理
    逻辑 (Logic): 依次组合 ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_backfill(ts_backfill({field}, 120), 66)
    使用算子 (Operators Used): ts_backfill
    参数建议 (Parameter Recommendations): d1 默认66，窗口可比较20或60（必须重新验证）, d2 默认120，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.f37cf5455b3c6ceb
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42720875852439
    """
    return f'ts_backfill(ts_backfill({field}, {d2}), {d1})'
