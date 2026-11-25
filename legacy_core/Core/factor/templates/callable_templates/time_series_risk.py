"""可直接调用的模板本体；未验证不代表有效，差表现由disabled_templates.py排除。"""

def information_ratio(field, d=20):
    """
    波动与风险调整
    逻辑 (Logic): 按滚动波动调整窗口均值。
    模板 (Template): ts_ir({field},20)
    使用算子 (Operators Used): ts_ir
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.078e2390484905e8
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/26054361848343
    """
    return f'ts_ir({field}, {d})'


def time_series_zscore(field, d=252):
    """
    波动与风险调整
    逻辑 (Logic): 按历史均值和标准差标准化。
    模板 (Template): ts_zscore({field}, 252)
    使用算子 (Operators Used): ts_zscore
    参数建议 (Parameter Recommendations): d 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.25a99e1965cb2b0d
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/26054361848343
    """
    return f'ts_zscore({field}, {d})'


def abs_transform(field, d1=252, d2=252):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 abs、ts_mean、ts_std_dev；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): abs(ts_mean({field},252)/ts_std_dev({field},252))
    使用算子 (Operators Used): abs, ts_mean, ts_std_dev
    参数建议 (Parameter Recommendations): d1 默认252，窗口可比较20或60（必须重新验证）, d2 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.4d85042c2a9984de
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/26054361848343
    """
    return f'abs(ts_mean({field}, {d1}) / ts_std_dev({field}, {d2}))'


def ts_std_dev_transform(field, d1=20, d2=1):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_std_dev、ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_std_dev({field}/ts_delay({field}, 1)-1,20)
    使用算子 (Operators Used): ts_std_dev, ts_delay
    参数建议 (Parameter Recommendations): d1 默认20，窗口可比较20或60（必须重新验证）, d2 默认1，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.f1b6274ef52c9cb6
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/26054361848343
    """
    return f'ts_std_dev({field} / ts_delay({field}, {d2}) - 1, {d1})'


def ts_zscore_transform(field, d1=30, d2=5):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_zscore、rank、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_zscore(rank(ts_delta({field}, 5)), 30) * -1
    使用算子 (Operators Used): ts_zscore, rank, ts_delta
    参数建议 (Parameter Recommendations): d1 默认30，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.011f691eb30d4f07
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'ts_zscore(rank(ts_delta({field}, {d2})), {d1}) * -1'


def ts_zscore_transform_1e9d189b(field, d1=20, d2=5):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_zscore、rank、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_zscore(rank(ts_delta({field}, 5)), 20)
    使用算子 (Operators Used): ts_zscore, rank, ts_delta
    参数建议 (Parameter Recommendations): d1 默认20，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.1e9d189bf282f7c0
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'ts_zscore(rank(ts_delta({field}, {d2})), {d1})'


def ts_rank_transform(field, d1=252, d2=66):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_rank、ts_std_dev；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): 2.-ts_rank(ts_std_dev({field}, 66), 252)
    使用算子 (Operators Used): ts_rank, ts_std_dev
    参数建议 (Parameter Recommendations): d1 默认252，窗口可比较20或60（必须重新验证）, d2 默认66，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.2d67ac5ab50962df
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'2.0 - ts_rank(ts_std_dev({field}, {d2}), {d1})'


def ts_std_dev_transform_62b3e3de(field, d=21):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_std_dev、sqrt；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_std_dev({field}, 21) * sqrt(252)
    使用算子 (Operators Used): ts_std_dev, sqrt
    参数建议 (Parameter Recommendations): d 默认21，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.62b3e3de800ec86c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/24469914183575
    """
    return f'ts_std_dev({field}, {d}) * sqrt(252)'


def ts_zscore_transform_8e1de830(field, d1=252, d2=252):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_zscore、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_zscore(ts_delta({field}, 252), 252)
    使用算子 (Operators Used): ts_zscore, ts_delta
    参数建议 (Parameter Recommendations): d1 默认252，窗口可比较20或60（必须重新验证）, d2 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.8e1de8303b0e3410
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'ts_zscore(ts_delta({field}, {d2}), {d1})'


def rank_transform_921283dc(field, d1=20, d2=5):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 rank、ts_std_dev、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): (1)-rank(ts_mean({field}, 5)) * ts_std_dev({field}, 20)
    使用算子 (Operators Used): rank, ts_std_dev, ts_mean
    参数建议 (Parameter Recommendations): d1 默认20，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.921283dc7cfcc9ed
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'1 - rank(ts_mean({field}, {d2})) * ts_std_dev({field}, {d1})'


def rank_transform_978316a1(field, d=20):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 rank、ts_std_dev；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_std_dev({field}, 20))
    使用算子 (Operators Used): rank, ts_std_dev
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.978316a1c66d6ef9
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'rank(ts_std_dev({field}, {d}))'


def rank_transform_b69141b5(field, d1=60, d2=5):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 rank、ts_zscore、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): -rank(ts_zscore(ts_delta({field},5),60))
    使用算子 (Operators Used): rank, ts_zscore, ts_delta
    参数建议 (Parameter Recommendations): d1 默认60，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.b69141b59d398690
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/33037839973783
    """
    return f'-rank(ts_zscore(ts_delta({field}, {d2}), {d1}))'


def ts_zscore_transform_bb8d1af2(field, d1=10, d2=1):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_zscore、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_zscore(ts_delta({field}, 1), 10) * -1
    使用算子 (Operators Used): ts_zscore, ts_delta
    参数建议 (Parameter Recommendations): d1 默认10，窗口可比较20或60（必须重新验证）, d2 默认1，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.bb8d1af25cad1e49
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'ts_zscore(ts_delta({field}, {d2}), {d1}) * -1'


def ts_rank_transform_dbfc1baa(field, d1=20, d2=20, d3=5):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_rank、ts_std_dev、ts_delta；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_rank({field}, 20) * ts_std_dev(ts_delta({field}, 5), 20)
    使用算子 (Operators Used): ts_rank, ts_std_dev, ts_delta
    参数建议 (Parameter Recommendations): d1 默认20，窗口可比较20或60（必须重新验证）, d2 默认20，窗口可比较20或60（必须重新验证）, d3 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.dbfc1baaad9be7ec
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'ts_rank({field}, {d1}) * ts_std_dev(ts_delta({field}, {d3}), {d2})'


def ts_mean_transform_07b71f36(field, d1=21, d2=252):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_mean、ts_zscore；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_mean(ts_zscore({field}, 252), 21)
    使用算子 (Operators Used): ts_mean, ts_zscore
    参数建议 (Parameter Recommendations): d1 默认21，窗口可比较20或60（必须重新验证）, d2 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.07b71f36b9fcd093
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/41036889226263
    """
    return f'ts_mean(ts_zscore({field}, {d2}), {d1})'


def rank_transform_1f6acfc7(field, d=20):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 rank、ts_std_dev；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(-ts_std_dev({field}, 20))
    使用算子 (Operators Used): rank, ts_std_dev
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.1f6acfc7759649a6
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/34208186164631
    """
    return f'rank(-ts_std_dev({field}, {d}))'


def ts_delta_transform_402ed00c(field, d1=252, d2=252):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_delta、ts_zscore；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_delta(ts_zscore({field}, 252), 252)
    使用算子 (Operators Used): ts_delta, ts_zscore
    参数建议 (Parameter Recommendations): d1 默认252，窗口可比较20或60（必须重新验证）, d2 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.402ed00c72e33541
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42258807786391
    """
    return f'ts_delta(ts_zscore({field}, {d2}), {d1})'


def ts_kurtosis_transform(field, d=60):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_kurtosis；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_kurtosis({field}, 60)-3
    使用算子 (Operators Used): ts_kurtosis
    参数建议 (Parameter Recommendations): d 默认60，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.6e00da3a170bb184
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/34535942900375
    """
    return f'ts_kurtosis({field}, {d}) - 3'


def ts_std_dev_transform_78e60961(field, d=130):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_std_dev；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_std_dev({field},130)<0.3
    使用算子 (Operators Used): ts_std_dev
    参数建议 (Parameter Recommendations): d 默认130，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.78e60961a9077eb0
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/33169668224919
    """
    return f'ts_std_dev({field}, {d}) < 0.3'


def ts_mean_transform_84f9f5d2(field, d1=126, d2=126):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_mean、ts_std_dev；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): (ts_mean({field}, 126) / ts_std_dev({field}, 126))
    使用算子 (Operators Used): ts_mean, ts_std_dev
    参数建议 (Parameter Recommendations): d1 默认126，窗口可比较20或60（必须重新验证）, d2 默认126，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.84f9f5d2016807fc
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/41877348653335
    """
    return f'ts_mean({field}, {d1}) / ts_std_dev({field}, {d2})'


def rank_transform_ac7b74e8(field, d1=252, d2=252):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 rank、ts_delta、ts_zscore；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_delta(ts_zscore({field}, 252), 252))
    使用算子 (Operators Used): rank, ts_delta, ts_zscore
    参数建议 (Parameter Recommendations): d1 默认252，窗口可比较20或60（必须重新验证）, d2 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.ac7b74e821c80964
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42258807786391
    """
    return f'rank(ts_delta(ts_zscore({field}, {d2}), {d1}))'


def ts_decay_linear_transform(field, d1=22, d2=132, d3=66):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_decay_linear、ts_zscore、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_decay_linear(ts_zscore(ts_backfill({field}, 66), 132), 22)
    使用算子 (Operators Used): ts_decay_linear, ts_zscore, ts_backfill
    参数建议 (Parameter Recommendations): d1 默认22，窗口可比较20或60（必须重新验证）, d2 默认132，窗口可比较20或60（必须重新验证）, d3 默认66，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.b9808ec3ac6d9e29
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/41135490599063
    """
    return f'ts_decay_linear(ts_zscore(ts_backfill({field}, {d3}), {d2}), {d1})'


def ts_zscore_transform_c5651980(field, d1=252, d2=252):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_zscore、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_zscore(ts_backfill({field},252), 252)
    使用算子 (Operators Used): ts_zscore, ts_backfill
    参数建议 (Parameter Recommendations): d1 默认252，窗口可比较20或60（必须重新验证）, d2 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.c56519808471417e
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/26994972215319
    """
    return f'ts_zscore(ts_backfill({field}, {d2}), {d1})'


def ts_std_dev_transform_e7c7ead2(field, d=130):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_std_dev；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_std_dev({field},130)>0.7
    使用算子 (Operators Used): ts_std_dev
    参数建议 (Parameter Recommendations): d 默认130，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.e7c7ead2d22cef3f
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/33169668224919
    """
    return f'ts_std_dev({field}, {d}) > 0.7'


def ts_std_dev_transform_0465301f(field, d=5):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_std_dev；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_std_dev({field}, 5) != 0
    使用算子 (Operators Used): ts_std_dev
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.0465301f9e63b453
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_std_dev({field}, {d}) != 0'


def ts_mean_transform_08f5ca92(field, d1=20, d2=60):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_mean、ts_std_dev；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_mean({field}, 20) / (ts_std_dev({field}, 60) + 0.001)
    使用算子 (Operators Used): ts_mean, ts_std_dev
    参数建议 (Parameter Recommendations): d1 默认20，窗口可比较20或60（必须重新验证）, d2 默认60，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.08f5ca92b13346d9
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_mean({field}, {d1}) / (ts_std_dev({field}, {d2}) + 0.001)'


def ts_std_dev_transform_0bf43417(field, d1=21, d2=21):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_std_dev、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_std_dev({field},21)/ts_mean({field},21)
    使用算子 (Operators Used): ts_std_dev, ts_mean
    参数建议 (Parameter Recommendations): d1 默认21，窗口可比较20或60（必须重新验证）, d2 默认21，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.0bf43417f737d521
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/35876513619607
    """
    return f'ts_std_dev({field}, {d1}) / ts_mean({field}, {d2})'


def ts_sum_transform(field, d1=120, d2=5):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_sum、ts_zscore；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): -ts_sum(ts_zscore({field}, 5), 120)
    使用算子 (Operators Used): ts_sum, ts_zscore
    参数建议 (Parameter Recommendations): d1 默认120，窗口可比较20或60（必须重新验证）, d2 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.20917c4733dfe7d9
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42061123738903
    """
    return f'-ts_sum(ts_zscore({field}, {d2}), {d1})'


def ts_std_dev_transform_271deb2b(field, d=10):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_std_dev；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): (1 - ts_std_dev({field}, 10))
    使用算子 (Operators Used): ts_std_dev
    参数建议 (Parameter Recommendations): d 默认10，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.271deb2bf79167b9
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'1 - ts_std_dev({field}, {d})'


def ts_zscore_transform_347f94e6(field, d=250):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_zscore、rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_zscore(rank({field}), 250)
    使用算子 (Operators Used): ts_zscore, rank
    参数建议 (Parameter Recommendations): d 默认250，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.347f94e6e247fabf
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39845230299927
    """
    return f'ts_zscore(rank({field}), {d})'


def ts_zscore_transform_35d973c4(field, d1=252, d2=252):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_zscore、ts_quantile；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_zscore(ts_quantile({field}, 252), 252)
    使用算子 (Operators Used): ts_zscore, ts_quantile
    参数建议 (Parameter Recommendations): d1 默认252，窗口可比较20或60（必须重新验证）, d2 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.35d973c4051540d5
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42801904467607
    """
    return f'ts_zscore(ts_quantile({field}, {d2}), {d1})'


def ts_zscore_transform_46d7fc9f(field, d1=20, d2=20, d3=1):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_zscore、ts_sum、ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_zscore(ts_sum({field} - ts_delay({field}, 1), 20), 20)
    使用算子 (Operators Used): ts_zscore, ts_sum, ts_delay
    参数建议 (Parameter Recommendations): d1 默认20，窗口可比较20或60（必须重新验证）, d2 默认20，窗口可比较20或60（必须重新验证）, d3 默认1，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.46d7fc9f7cda5d91
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_zscore(ts_sum({field} - ts_delay({field}, {d3}), {d2}), {d1})'


def zscore_transform_5b12f64f(field, d1=5, d2=60):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 zscore、ts_delta、rank、ts_zscore；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): zscore(ts_delta(rank(ts_zscore({field},60)),5))
    使用算子 (Operators Used): zscore, ts_delta, rank, ts_zscore
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认60，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.5b12f64fbbabbcec
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/33603438929047
    """
    return f'zscore(ts_delta(rank(ts_zscore({field}, {d2})), {d1}))'


def ts_std_dev_transform_6ade08c0(field, d1=126, d2=126):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_std_dev、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ({field} - ts_mean({field}, 126)) / ts_std_dev({field}, 126)
    使用算子 (Operators Used): ts_std_dev, ts_mean
    参数建议 (Parameter Recommendations): d1 默认126，窗口可比较20或60（必须重新验证）, d2 默认126，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.6ade08c03b378dfe
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'({field} - ts_mean({field}, {d2})) / ts_std_dev({field}, {d1})'


def rank_transform_91115548(field, d=20):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 rank、ts_std_dev；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank({field}) - rank(ts_std_dev({field}, 20))
    使用算子 (Operators Used): rank, ts_std_dev
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.91115548ebeb3f05
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank({field}) - rank(ts_std_dev({field}, {d}))'


def rank_transform_92429b1f(field, d=5):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 rank、ts_zscore；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_zscore({field}, 5))
    使用算子 (Operators Used): rank, ts_zscore
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.92429b1f76de8de5
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(ts_zscore({field}, {d}))'


def rolling_volatility(field, d=20):
    """
    波动与风险调整
    逻辑 (Logic): 计算输入字段的滚动标准差。
    模板 (Template): ts_std_dev({field}, 20)
    使用算子 (Operators Used): ts_std_dev
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.a389cdc522c961c1
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/17086182851223
    """
    return f'ts_std_dev({field}, {d})'


def ts_delta_transform_e2169017(field, d1=5, d2=22):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_delta、ts_std_dev；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_delta({field}, 5) > ts_std_dev({field}, 22)
    使用算子 (Operators Used): ts_delta, ts_std_dev
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认22，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.e21690170a49fb6b
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/43031577079575
    """
    return f'ts_delta({field}, {d1}) > ts_std_dev({field}, {d2})'


def ts_zscore_transform_e2c718f2(field, d1=250, d2=60):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 ts_zscore、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_zscore(ts_mean({field}, 60), 250)
    使用算子 (Operators Used): ts_zscore, ts_mean
    参数建议 (Parameter Recommendations): d1 默认250，窗口可比较20或60（必须重新验证）, d2 默认60，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.e2c718f2d0db94f4
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_zscore(ts_mean({field}, {d2}), {d1})'


def rank_transform_eab90082(field, d1=9, d2=504):
    """
    波动与风险调整
    逻辑 (Logic): 依次组合 rank、ts_decay_linear、ts_zscore；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_decay_linear(ts_zscore({field}, 504), 9))
    使用算子 (Operators Used): rank, ts_decay_linear, ts_zscore
    参数建议 (Parameter Recommendations): d1 默认9，窗口可比较20或60（必须重新验证）, d2 默认504，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.eab90082fecf4355
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/41119909511319
    """
    return f'rank(ts_decay_linear(ts_zscore({field}, {d2}), {d1}))'
