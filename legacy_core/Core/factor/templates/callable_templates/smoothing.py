"""可直接调用的模板本体；未验证不代表有效，差表现由disabled_templates.py排除。"""

def ts_mean_transform(field, d1=28, d2=60):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_mean({field},28)<2.7*ts_mean({field},60)
    使用算子 (Operators Used): ts_mean
    参数建议 (Parameter Recommendations): d1 默认28，窗口可比较20或60（必须重新验证）, d2 默认60，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.1d33b0f5f49bf145
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/24957813446167
    """
    return f'ts_mean({field}, {d1}) < 2.7 * ts_mean({field}, {d2})'


def ts_mean_transform_e9f07db3(field, d=504):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): -ts_mean({field},504)
    使用算子 (Operators Used): ts_mean
    参数建议 (Parameter Recommendations): d 默认504，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.e9f07db33de028a3
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/23934004353687
    """
    return f'-ts_mean({field}, {d})'


def rank_transform_3ddf50f0(field, d=25):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 rank、ts_mean、log；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_mean(log({field}), 25))
    使用算子 (Operators Used): rank, ts_mean, log
    参数建议 (Parameter Recommendations): d 默认25，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.3ddf50f0f6db5179
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'rank(ts_mean(log({field}), {d}))'


def ts_mean_transform_6548eba5(field, d=252):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_mean({field}, 252) > 100
    使用算子 (Operators Used): ts_mean
    参数建议 (Parameter Recommendations): d 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.6548eba5b164900b
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42163760922903
    """
    return f'ts_mean({field}, {d}) > 100'


def ts_product_transform_aad2bf5b(field, d=250):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 ts_product；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_product({field}+1,250)-1
    使用算子 (Operators Used): ts_product
    参数建议 (Parameter Recommendations): d 默认250，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.aad2bf5b9f764fcd
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/19992945218711
    """
    return f'ts_product({field} + 1, {d}) - 1'


def ts_product(field, d=22):
    """
    时序平滑与加权
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): ts_product(1+{field},22)
    使用算子 (Operators Used): ts_product
    参数建议 (Parameter Recommendations): d 默认22，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.6d7bc44da7d773d3
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/36876447664023
    """
    return f'ts_product(1 + {field}, {d})'


def ts_product_9e63e81d(field, d=3):
    """
    时序平滑与加权
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): ts_product({field}, 3)
    使用算子 (Operators Used): ts_product
    参数建议 (Parameter Recommendations): d 默认3，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.9e63e81d44c2c71c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/34208186164631
    """
    return f'ts_product({field}, {d})'


def ts_sum(field, d=252):
    """
    时序平滑与加权
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): ts_sum({field},252)
    使用算子 (Operators Used): ts_sum
    参数建议 (Parameter Recommendations): d 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.ae1c7b226f3f8b8d
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/33316272949527
    """
    return f'ts_sum({field}, {d})'


def ts_product_transform_bf47dcfb(field, d=20):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 ts_product；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_product(1 + {field}, 20) - 1
    使用算子 (Operators Used): ts_product
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.bf47dcfb335bafaf
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/34208186164631
    """
    return f'ts_product(1 + {field}, {d}) - 1'


def ts_mean_transform_daa199f9(field, d1=126, d2=80):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 ts_mean、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_mean(ts_backfill({field},80),126)
    使用算子 (Operators Used): ts_mean, ts_backfill
    参数建议 (Parameter Recommendations): d1 默认126，窗口可比较20或60（必须重新验证）, d2 默认80，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.daa199f9fd84af8d
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/37273554019863
    """
    return f'ts_mean(ts_backfill({field}, {d2}), {d1})'


def abs_transform_fb92e53b(field, d1=20, d2=60):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 abs、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): abs(ts_mean({field},20)/ts_mean({field},60)-1)
    使用算子 (Operators Used): abs, ts_mean
    参数建议 (Parameter Recommendations): d1 默认20，窗口可比较20或60（必须重新验证）, d2 默认60，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.fb92e53bac86bb3e
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/20278408956439
    """
    return f'abs(ts_mean({field}, {d1}) / ts_mean({field}, {d2}) - 1)'


def log_transform(field, d1=44, d2=20):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 log、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): log(ts_mean({field}, 44)) - log(ts_mean({field}, 20))
    使用算子 (Operators Used): log, ts_mean
    参数建议 (Parameter Recommendations): d1 默认44，窗口可比较20或60（必须重新验证）, d2 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.fd5b4f3b720a968e
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/37117908343831
    """
    return f'log(ts_mean({field}, {d1})) - log(ts_mean({field}, {d2}))'


def rank_transform_19bc8bcf(field, d=5):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 rank、ts_decay_linear；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_decay_linear({field}, 5))
    使用算子 (Operators Used): rank, ts_decay_linear
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.19bc8bcf95e470a4
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(ts_decay_linear({field}, {d}))'


def ts_mean_transform_1b016199(field, d1=5, d2=10):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_mean({field}, 5) - ts_mean({field}, 10)
    使用算子 (Operators Used): ts_mean
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认10，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.1b016199c1feb309
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_mean({field}, {d1}) - ts_mean({field}, {d2})'


def rank_transform_2a64b13e(field, d=60):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 rank、ts_sum；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_sum({field}, 60))
    使用算子 (Operators Used): rank, ts_sum
    参数建议 (Parameter Recommendations): d 默认60，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.2a64b13ebeeeaf96
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(ts_sum({field}, {d}))'


def rank_transform_2e2670f2(field, d=22):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 rank、ts_product；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_product(1+{field}, 22) - 1)
    使用算子 (Operators Used): rank, ts_product
    参数建议 (Parameter Recommendations): d 默认22，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.2e2670f291281c93
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/31988597274903
    """
    return f'rank(ts_product(1 + {field}, {d}) - 1)'


def rank_transform_33528af6(field, d=20):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 rank、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_mean({field}, 20))
    使用算子 (Operators Used): rank, ts_mean
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.33528af61acb862b
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(ts_mean({field}, {d}))'


def ts_mean_transform_338282a1(field, d=20):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): {field} - ts_mean({field}, 20)
    使用算子 (Operators Used): ts_mean
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.338282a17ffeefe6
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'{field} - ts_mean({field}, {d})'


def rank_transform_3870d31a(field, d1=5, d2=20):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 rank、ts_decay_linear、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_decay_linear(ts_backfill({field}, 20), 5))
    使用算子 (Operators Used): rank, ts_decay_linear, ts_backfill
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.3870d31af4e9921c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(ts_decay_linear(ts_backfill({field}, {d2}), {d1}))'


def ts_mean_transform_533608b0(field, d=5):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 ts_mean、rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_mean(rank({field}), 5)
    使用算子 (Operators Used): ts_mean, rank
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.533608b0a6d94dda
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_mean(rank({field}), {d})'


def zscore_transform(field, d=20):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 zscore、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): zscore({field}) - ts_mean(zscore({field}), 20)
    使用算子 (Operators Used): zscore, ts_mean
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.589c57b3b2e81921
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39225718749591
    """
    return f'zscore({field}) - ts_mean(zscore({field}), {d})'


def rank_transform_5b086848(field, d=5):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 rank、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank({field}) - ts_mean(rank({field}),5)
    使用算子 (Operators Used): rank, ts_mean
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.5b0868482126352f
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42078917602455
    """
    return f'rank({field}) - ts_mean(rank({field}), {d})'


def rank_transform_60133bce(field, d=5):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 rank、ts_sum；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(-ts_sum({field},5))
    使用算子 (Operators Used): rank, ts_sum
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.60133bcef05a77ce
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/41796491619351
    """
    return f'rank(-ts_sum({field}, {d}))'


def ts_decay_linear_transform_72897ecb(field, d1=5, d2=60):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 ts_decay_linear、ts_backfill；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_decay_linear(ts_backfill({field}, 60), 5)
    使用算子 (Operators Used): ts_decay_linear, ts_backfill
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认60，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.72897ecb231c2982
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_decay_linear(ts_backfill({field}, {d2}), {d1})'


def rank_transform_7b8f904f(field, d=20):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 rank、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_mean({field}, 20)) >= 0.20
    使用算子 (Operators Used): rank, ts_mean
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.7b8f904f4b7f84ef
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/38669179039255
    """
    return f'rank(ts_mean({field}, {d})) >= 0.2'


def ts_mean_transform_976f4cf5(field, d1=20, d2=1):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 ts_mean、ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_mean({field}/ts_delay({field},1)-1,20)
    使用算子 (Operators Used): ts_mean, ts_delay
    参数建议 (Parameter Recommendations): d1 默认20，窗口可比较20或60（必须重新验证）, d2 默认1，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.976f4cf56209964c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/19137620283415
    """
    return f'ts_mean({field} / ts_delay({field}, {d2}) - 1, {d1})'


def ts_sum_transform_c4cefbed(field, d1=20, d2=60):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 ts_sum；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_sum({field}, 20) - ts_sum({field}, 60)
    使用算子 (Operators Used): ts_sum
    参数建议 (Parameter Recommendations): d1 默认20，窗口可比较20或60（必须重新验证）, d2 默认60，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.c4cefbed8b7a198e
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42407253630359
    """
    return f'ts_sum({field}, {d1}) - ts_sum({field}, {d2})'


def rank_transform_c9e24297(field, d1=5, d2=20):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 rank、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_mean({field}, 5) - ts_mean({field}, 20))
    使用算子 (Operators Used): rank, ts_mean
    参数建议 (Parameter Recommendations): d1 默认5，窗口可比较20或60（必须重新验证）, d2 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.c9e24297a35c4a45
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(ts_mean({field}, {d1}) - ts_mean({field}, {d2}))'


def rank_transform_cc7ae197(field, d=10):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 rank、ts_sum；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_sum({field} > 5, 10))
    使用算子 (Operators Used): rank, ts_sum
    参数建议 (Parameter Recommendations): d 默认10，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.cc7ae197c41f34d2
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(ts_sum({field} > 5, {d}))'


def rank_transform_cf38bf10(field, d1=22, d2=22):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 rank、ts_mean、ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_mean({field}, 22) - ts_delay({field}, 22))
    使用算子 (Operators Used): rank, ts_mean, ts_delay
    参数建议 (Parameter Recommendations): d1 默认22，窗口可比较20或60（必须重新验证）, d2 默认22，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.cf38bf10b735fb1d
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(ts_mean({field}, {d1}) - ts_delay({field}, {d2}))'


def ts_mean_transform_d46c2df1(field, d=20):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): {field} > ts_mean({field}, 20) * 1.5
    使用算子 (Operators Used): ts_mean
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.d46c2df1ad86352e
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'{field} > ts_mean({field}, {d}) * 1.5'


def log_transform_d6855faf(field, d=21):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 log、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): log(ts_mean({field}, 21))
    使用算子 (Operators Used): log, ts_mean
    参数建议 (Parameter Recommendations): d 默认21，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.d6855faf105ab478
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/32394129497239
    """
    return f'log(ts_mean({field}, {d}))'


def ts_decay_linear(field, d=20):
    """
    时序平滑与加权
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): ts_decay_linear({field}, 20)
    使用算子 (Operators Used): ts_decay_linear
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.d9c03b495fc0adf4
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'ts_decay_linear({field}, {d})'


def ts_mean_transform_db6d99b1(field, d=22):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): {field} / ts_mean({field}, 22)
    使用算子 (Operators Used): ts_mean
    参数建议 (Parameter Recommendations): d 默认22，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.db6d99b196cb7c21
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42740521405463
    """
    return f'{field} / ts_mean({field}, {d})'


def rank_transform_e92359cb(field, d=20):
    """
    时序平滑与加权
    逻辑 (Logic): 依次组合 rank、ts_mean；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank({field} / ts_mean({field}, 20))
    使用算子 (Operators Used): rank, ts_mean
    参数建议 (Parameter Recommendations): d 默认20，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.e92359cb9f4a9fc7
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank({field} / ts_mean({field}, {d}))'
