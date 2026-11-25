"""可直接调用的模板本体；未验证不代表有效，差表现由disabled_templates.py排除。"""

def cross_sectional_rank(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 比较输入值在当前截面中的排名。
    模板 (Template): rank({field})
    使用算子 (Operators Used): rank
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.acc17dcc23d62536
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/36183099180823
    """
    return f'rank({field})'


def scale_transform_c16b9551(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 scale、quantile；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): scale(quantile({field}))
    使用算子 (Operators Used): scale, quantile
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.c16b95512285c994
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/24957813446167
    """
    return f'scale(quantile({field}))'


def rank_transform_0a43374f(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): 0.65 * rank(-{field})
    使用算子 (Operators Used): rank
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.0a43374f428eab4f
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39441605621911
    """
    return f'0.65 * rank(-{field})'


def ts_max_diff_transform(field, d=252):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 ts_max_diff、scale；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ts_max_diff(scale({field},longscale=1,shortscale=0),252)
    使用算子 (Operators Used): ts_max_diff, scale
    参数建议 (Parameter Recommendations): d 默认252，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.6aaf4730f3d51ae1
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/23807105368215
    """
    return f'ts_max_diff(scale({field}, longscale=1, shortscale=0), {d})'


def last_diff_value(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): last_diff_value({field}, 5)
    使用算子 (Operators Used): last_diff_value
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.7d8a8a9d4aeabdb6
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/19831590714135
    """
    return f'last_diff_value({field}, 5)'


def ts_delay_transform(field, d=5):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): {field} / ts_delay({field}, 5)
    使用算子 (Operators Used): ts_delay
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.bde7ba8d9e2e5a46
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/20284582494359
    """
    return f'{field} / ts_delay({field}, {d})'


def quantile(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): quantile({field})
    使用算子 (Operators Used): quantile
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.40e0fc605dcb3147
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/35026706128279
    """
    return f'quantile({field})'


def ts_delay_transform_42429575(field, d=1):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): {field} /ts_delay({field},1)-1
    使用算子 (Operators Used): ts_delay
    参数建议 (Parameter Recommendations): d 默认1，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.42429575fc80b0cc
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/35490617356823
    """
    return f'{field} / ts_delay({field}, {d}) - 1'


def sqrt(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): sqrt({field})
    使用算子 (Operators Used): sqrt
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.4b1b453de0d0a55c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/34208186164631
    """
    return f'sqrt({field})'


def pasteurize(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): pasteurize({field})
    使用算子 (Operators Used): pasteurize
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.5b135c7d5d658d4b
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/40732429672343
    """
    return f'pasteurize({field})'


def rank_transform_5bdde2b0(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank({field})>0.7
    使用算子 (Operators Used): rank
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.5bdde2b0901f5468
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/33169668224919
    """
    return f'rank({field}) > 0.7'


def zscore(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): zscore({field})
    使用算子 (Operators Used): zscore
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.75007fe58e0a4369
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/40732429672343
    """
    return f'zscore({field})'


def rank_transform_7d899f43(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank({field}) < 0.4
    使用算子 (Operators Used): rank
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.7d899f431dc53345
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/22752141318167
    """
    return f'rank({field}) < 0.4'


def inverse(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): inverse({field})
    使用算子 (Operators Used): inverse
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.969db6e6eb9293fc
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/34208186164631
    """
    return f'inverse({field})'


def scale(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): scale({field}, scale=1, longscale=1, shortscale=1)
    使用算子 (Operators Used): scale
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.dce17f367c5f5b92
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/34208186164631
    """
    return f'scale({field}, scale=1, longscale=1, shortscale=1)'


def ts_delay_transform_df9ee724(field, d=1):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): {field} - ts_delay({field},1)
    使用算子 (Operators Used): ts_delay
    参数建议 (Parameter Recommendations): d 默认1，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.df9ee72494dfaeb1
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/20278408956439
    """
    return f'{field} - ts_delay({field}, {d})'


def scale_ec2678d1(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): scale({field})
    使用算子 (Operators Used): scale
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.ec2678d1000f0c08
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/40732429672343
    """
    return f'scale({field})'


def rank_transform_f2d4e34d(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): (rank({field})-0.5)*2
    使用算子 (Operators Used): rank
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.f2d4e34d895ab905
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/26671942422295
    """
    return f'(rank({field}) - 0.5) * 2'


def rank_transform_10569464(field, d=5):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 rank、ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(ts_delay({field},5))
    使用算子 (Operators Used): rank, ts_delay
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.10569464d0e52df0
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39225718749591
    """
    return f'rank(ts_delay({field}, {d}))'


def rank_transform_3cdaafd7(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 rank；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): (-1 * rank({field}))
    使用算子 (Operators Used): rank
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.3cdaafd796ded422
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'-1 * rank({field})'


def normalize(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): normalize({field})
    使用算子 (Operators Used): normalize
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.3e65a29dc86086a0
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/41076241014423
    """
    return f'normalize({field})'


def cross_sectional_rank_4a4fadf3(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 比较输入值在当前截面中的排名。
    模板 (Template): rank(-{field})
    使用算子 (Operators Used): rank
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.4a4fadf37fbf3e80
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(-{field})'


def abs(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): abs({field})
    使用算子 (Operators Used): abs
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.5ee09e6396309acf
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/43529216017047
    """
    return f'abs({field})'


def rank_transform_63e3248b(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 rank、abs；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank(abs({field}))
    使用算子 (Operators Used): rank, abs
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.63e3248bd40188aa
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank(abs({field}))'


def abs_transform_64b9570e(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 abs；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): abs({field})>=0.1
    使用算子 (Operators Used): abs
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.64b9570ebabe0382
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/15227024028311
    """
    return f'abs({field}) >= 0.1'


def max_transform(field, d1=1, d2=2, d3=3, d4=4):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 max、ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): max({field}, ts_delay({field}, 1), ts_delay({field}, 2), ts_delay({field}, 3), ts_delay({field}, 4))
    使用算子 (Operators Used): max, ts_delay
    参数建议 (Parameter Recommendations): d1 默认1，窗口可比较20或60（必须重新验证）, d2 默认2，窗口可比较20或60（必须重新验证）, d3 默认3，窗口可比较20或60（必须重新验证）, d4 默认4，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.6bd9f132540bc052
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/43179860065303
    """
    return f'max({field}, ts_delay({field}, {d1}), ts_delay({field}, {d2}), ts_delay({field}, {d3}), ts_delay({field}, {d4}))'


def rank_transform_7902a722(field, d=1):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 rank、ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank({field} - ts_delay({field}, 1))
    使用算子 (Operators Used): rank, ts_delay
    参数建议 (Parameter Recommendations): d 默认1，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.7902a72244bb0c48
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank({field} - ts_delay({field}, {d}))'


def rank_transform_83bdfe90(field, d=1):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 rank、ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): rank({field}) - rank(ts_delay({field}, 1))
    使用算子 (Operators Used): rank, ts_delay
    参数建议 (Parameter Recommendations): d 默认1，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.83bdfe902b5071d7
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39411791834647
    """
    return f'rank({field}) - rank(ts_delay({field}, {d}))'


def sign_transform(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 sign；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): -sign({field})
    使用算子 (Operators Used): sign
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.8cf6da5eaca76386
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/43151729306647
    """
    return f'-sign({field})'


def ts_delay_transform_916baf05(field, d=1):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): ({field} == ts_delay({field},1))
    使用算子 (Operators Used): ts_delay
    参数建议 (Parameter Recommendations): d 默认1，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.916baf05aac2cbee
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/15390538468887
    """
    return f'{field} == ts_delay({field}, {d})'


def abs_transform_9fc2b549(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 abs；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): abs({field}) > 1
    使用算子 (Operators Used): abs
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.9fc2b549dbd45fc7
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39225718749591
    """
    return f'abs({field}) > 1'


def ts_delay_transform_a4a84157(field, d=5):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): -({field}-ts_delay({field},5))/{field}
    使用算子 (Operators Used): ts_delay
    参数建议 (Parameter Recommendations): d 默认5，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.a4a84157b0fe7d1c
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/19353819839639
    """
    return f'-({field} - ts_delay({field}, {d})) / {field}'


def ts_delay(field, d=200):
    """
    截面排序与非线性变换
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): ts_delay({field}, 200)
    使用算子 (Operators Used): ts_delay
    参数建议 (Parameter Recommendations): d 默认200，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.c7b708fdc921fcd2
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/17647293721239
    """
    return f'ts_delay({field}, {d})'


def log(field):
    """
    截面排序与非线性变换
    逻辑 (Logic): 按下列公式对单一输入字段进行统计变换。
    模板 (Template): log({field})
    使用算子 (Operators Used): log
    参数建议 (Parameter Recommendations): 无窗口参数；替换field即可。
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.da7c4db8c65ffaae
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/31280678526615
    """
    return f'log({field})'


def ts_delay_transform_dd0ab192(field, d=1):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): (1-{field})*ts_delay(1-{field},1)
    使用算子 (Operators Used): ts_delay
    参数建议 (Parameter Recommendations): d 默认1，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.dd0ab1924189ab82
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/15763503067543
    """
    return f'(1 - {field}) * ts_delay(1 - {field}, {d})'


def log_transform_e4c1d3e4(field, d=1):
    """
    截面排序与非线性变换
    逻辑 (Logic): 依次组合 log、ts_delay；变换方向以模板公式为准，收益尚未验证。
    模板 (Template): log({field}/ts_delay({field},1))
    使用算子 (Operators Used): log, ts_delay
    参数建议 (Parameter Recommendations): d 默认1，窗口可比较20或60（必须重新验证）
    验证状态: UNVALIDATED；仅本地合规通过，不能当作有效或过拟合已通过。
    模板ID: admin.catalog.e4c1d3e42b4a1bec
    来源帖子: https://support.worldquantbrain.com/hc/zh-cn/community/posts/20238317296791
    """
    return f'log({field} / ts_delay({field}, {d}))'
