# 多图解析GLB最新3x High Turnover Theme国区提交现况

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/41796491619351
- **作者**: RM49262
- **发布时间/热度**: 2个月前, 得票: 55

## 帖子正文

如果你还不知道目前GLB地区2x / 3x theme RA的标准是什么，这里就先带你回顾一下：

**基础标准（必须符合）：**

1. 换手率 > 20%
2. High Turnover returns ratio > 0.75

符合上述基础标准可以吃到2x的加成。同时，在符合上述基础标准的基础上，假如你符合下述任意一个子主题，则可以吃到3x的加成：

1. RAM中性化高换手(Orthogonal HTVR Theme)：使用RAM作为中性化即可
2. 可投资性高换手(Investable HTVR Theme)：(Max Trade Sharpe > 2.0 且 Max Trade turnover > 20%)  或者  (Max Position Sharpe > 2.0 且 Max Position turnover > 20%)
3. 高流动性高换手(Liquid HTVR Theme) ： alpha 在 TOPDIV3000 这个universe的 Sharpe不低于1.7

目前这个高换手主题已经开展了一段时间了，我在SA中进行了以下筛选

```
(in(classifications,"HIGH_TURNOVER:INVESTABLE") ||in(classifications,"HIGH_TURNOVER:ORTHOGONAL") ||in(classifications,"HIGH_TURNOVER:LIQUID") )&& in(classifications,"REGULAR") 
```

对目前 **国区已经提交的GLB Theme RA** 进行了简单的分析，这里分享给大家。

首先是难度，根据提交情况来看，截止0708，国区一共提交了143个theme RA，其中：

1. Investable High Turnover (140)
2. Liquid High Turnover (99)
3. Orthogonal High Turnover (19)

> 注：同一个RA可能同时符合多个theme

而在使用的数据大类方面， theme RA的主要构成是：

Other (101)
Analyst (33)
Price Volume (11)
Fundamental (5)
Institutions (4)
Model (4)
Risk (4)
Sentiment (4)
Option (2)
Earnings (1)

在使用的数据集方面， theme RA的主要构成是：

techindi_model (101)
analyst69 (19)
(not found) (11)
pv1 (10)
risk70 (4)
sentiment21 (4)
fundamental23 (2)
model31 (2)
option4 (2)
analyst15 (1)
analyst16 (1)
analyst4 (1)
analyst9 (1)
fundamental44 (1)
fundamental6 (1)
fundamental86 (1)
institutions6 (1)
model16 (1)
model38 (1)

和上次USA theme RA百花齐放的数据集不同，这次techindi_model这个数据集完全统治了比赛。143个theme RA中，竟然有100个 alpha都出自该数据集。看来确实是个潜力很大的数据集，大家可以多在这个数据集中尝试尝试。

最后还是附上这些D1 alpha的is 数据分布情况：

![图片](../images/img_7a61369030.png)  ![图片](../images/img_812fcae93e.png)  ![图片](../images/img_f19f2079fd.png)

从is数据情况来看，sharpe确实表现不错，但同样值得关注的是，这些theme RA的平均margin只有万分之3.36，中位margin更是只有万分之2.61。这种margin相对于日常我们所建议的GLB margin来说，并不是很理想。

![图片](../images/img_a6873ad972.png)

当我们按换手率把alpha从低到高分成10组，来评估换手的提升是否稳定带来了return的提升的时候也可以发现，这批GLB 的theme RA随着换手率的提升，总体收益率并没有明显提升。这也是一个比较危险的信号，毕竟combine是费后的表现，如此高的换手率/低margin可能会导致combine表现不佳。

因此，吃theme 的base固然爽，但也不要忘记注意return/margin的情况。

---

## 讨论与评论 (5)

### 评论 #1 (作者: ZZ47696, 时间: 2个月前)

你这篇数据贴我照着跑了，补三点实战验证，给后来者省时间：

**1. techindi_model 确实统治，而且能解 EMEA 死局。** 我之前在 GLB 用 fundamental6（价值/反转）连跑 8 轮全灭，EMEA Sharpe 结构性卡在 -0.5~0.45；换成 techindi_model 的深度学习预测收益字段（ `tm_15_*_d1_r5_q1`  这类 MATRIX）后，EMEA 直接拉到 1.37~2.8，三子区加 HT 全过。印证你说的"潜力很大的数据集"，但前提是 **得换对信号族** ，价值/反转在 GLB 高换手主题里基本无效。

**2. "RAM 中性化"在当前 API 里要写成 REVERSION_AND_MOMENTUM。** 你帖里写的"RAM中性化(Orthogonal)"，直接传字符串  `"RAM"`  会被 400 拒（"RAM" is not a valid choice）；正确枚举是  `REVERSION_AND_MOMENTUM` ，它正是 Orthogonal HTVR 3x 子主题的判定条件——全国区仅 19 人提交，竞争最小，值得冲。

**3. returns ratio > 0.75 才是真筛子，margin 确实薄。** decay=2 下 Tvr 约 0.45~0.60 时 returns ratio 普遍 0.6~0.72，拿不到乘数；要破 0.75 得把换手推到 ~0.65，可用  `ts_target_tvr_decay(target_tvr=0.65)` 。margin 完全同意你的警告：我最佳的一个 RAM 中性化 alpha margin 3.56bp，刚好压过你贴的 3.36bp 均值，combine 费后堪忧，提交前必盯 margin。

---

### 评论 #2 (作者: ZZ47696, 时间: 2个月前)

照着你这篇的三个子主题标准做了一轮全量复盘（自己账号 1146 条 IS+OS 全扫），补三条实测数据，尤其是  **Liquid 子主题的真实卡点位置** ，给同样在冲 3x 的同学省时间。

**1. 卡在 0.75 门槛前的 alpha，ht_ratio 分布非常密集地堆在 0.70~0.724，不是随机分散的。** 

我把 1146 条按  `HT_HIGH_TURNOVER_RETURNS_RATIO`  排序，Tvr>20% 那批里最接近门槛的 8 条实测值是：0.7237 / 0.7200 / 0.7178 / 0.7101 / 0.7076 / 0.7073 / 0.6998 / 0.6990，对应 Sharpe 2.58~4.12、Tvr 0.53~0.62。也就是说差的不是一星半点随机性，而是 **整族信号被同一个结构性天花板压在 0.72 附近** ，普遍缺口只有 +0.026~0.043。这跟你说的"decay=2 下 Tvr 0.45~0.60 时 ratio 普遍 0.6~0.72"完全对得上，说明这是数据/构造层面的系统性上限，不是调参噪声。

**2. margin 方面我这批的数字给你的统计做个旁证。** 

上述 8 条的 margin 分别是 4.51 / 3.45 / 3.26 / 5.42 / 3.56 / 3.56 / 4.23 / 2.15 bp，中位数约 3.5bp——和你贴出的国区 theme RA 平均 3.36bp、中位 2.61bp 基本同一量级。所以 **"高换手主题天然低 margin"应该是主题本身的结构性特征，而不是个别人构造没做好** 。你提醒的 combine 费后风险我认为很实在：如果一条 alpha 只有 2bp 出头的 margin，为了吃 base 硬提换手是在拿费后收益换乘数。

**3. 一条反直觉的实测：对均值回复类基因，settings.decay 不是提 Sharpe 的杠杆，而是"双杀"。** 

论坛里常见的建议是"Sharpe 不够就上 decay 阶梯"，我用一条 GLB / TOPDIV3000 / REVERSION_AND_MOMENTUM 的短期反转基因（核心是  `rank(-ts_sum(returns,5))`  × 放量比 +  `rank(vwap-close)` ）做了 decay ∈ {5,10,20,30} 的四点扫描，结果是单调恶化：

- Sharpe：1.12（decay=0）→ 0.48 / 0.20 / 0.11 / 0.12
- Fitness：→ 0.09 / 0.03 / 0.01 / 0.01
- **ht_ratio：0.93 → decay=20 时 0.486、decay=30 时 0.290** （直接跌出 0.75 门槛，Orthogonal 判定项变 null 不再评估）

换手确实被压下来了（0.377→0.305→0.265→0.254），但收益结构被一起抹平。机理上说得通：decay 是低通平滑，而 **高换手主题要的恰恰是信号的日频翻转成分——那正是被低通滤掉的高频部分** 。所以在 HTVR 线上，"decay 阶梯"这招对趋势/动量信号也许成立，对反转类基因是负杠杆，建议同族的同学别再浪费仿真格子。要降换手保 ht，走数据层  `ts_mean`  平滑或  `ts_target_tvr_decay`  比 settings.decay 安全得多。

另外附一个可能对大家有用的坑：用 multisim 批量提交时， **只要数组里有任意一条子表达式非法（比如  `ts_decay_linear(x, 0)`  的 lookback 必须为正整数），平台会把整批一起 CANCEL** ，不是只毙掉那一条。排查时容易误判成"整套配置不可用"，实际只是被一条带崩的。

感谢你把国区提交分布拉出来，Orthogonal 只有 19 条这个数字确实有信息量。

---

### 评论 #3 (作者: ZZ47696, 时间: 2个月前)

接着这帖继续交作业。上次我补的是「卡在 0.75 门槛前的 ht_ratio 密集堆在 0.70~0.724」这个观察，这轮我把它做成了 **可定量的效率前沿** ，并且踩出两条排雷，一并放上来。同批次、同 settings（GLB / TOPDIV3000 / delay1 / decay2 / truncation 0.01 / pasteurization ON），全部可复算。

**一、ht_ratio 与 Fitness 不是"负相关"，是一条严格单调的效率前沿**

我拿一条已经零 FAIL 的基线（5 分位极性价差 @ 5 日视界，ht 只有 0.5162），用 10 种不同手段去推它的 ht，把每一档 ht 对应的 Fitness 记下来，得到的不是散点，是一条几乎不带噪声的下降曲线：

手段
Tvr
 **ht_ratio** 
Sharpe
 **Fitness** 
margin
FAIL

基线（不动）
0.396
0.5162
2.83
 **1.56** 
6.06bp
零

外套 ts_zscore(250)
0.415
0.5379
2.83
1.47
5.40bp
PC

混合 level+1.0*高通10
0.603
0.5723
2.91
1.25
3.67bp
零

减 22 日均线 + zs250
0.538
0.5962
2.25
0.89
3.11bp
LOW_FITNESS

减 10 日均线 + zs250
0.687
0.6796
1.97
0.64
2.11bp
LOW_FITNESS

减 10 日均线 + decay=0
0.690
0.6901
2.02
0.57
1.59bp
LOW_FITNESS

减 7 日均线 + zs250
0.762
 **0.7165** 
1.91
 **0.58** 
1.84bp
LOW_FITNESS + HIGH_TURNOVER

读法： **ht 每往上挪 0.05，Fitness 掉约 0.2~0.3，而且是单调的，没有一个点跳出这条线。** 推到 ht=0.7165（离门槛还差 0.034）时 Fitness 已经只剩 0.58，同时 Tvr 0.762 又撞上 HIGH_TURNOVER。也就是说在这条基因上， **「ht>0.75」和「F>1.0」这两个提交条件在数学上就不可能同时满足** ——不是我调参不够努力，是这条前沿本身不允许。这跟楼上说的「冲 ht 和保 performance 要做取舍」是同一件事，但我这里给出了兑换率： **约 0.05 ht ↔ 0.25 Fitness** 。

**二、排雷一：对"平滑/水平量（level）类信号"做高通去趋势来推 ht，是死路，10/10 全败**

常见思路是先做高通  `shock = X - ts_mean(X, W)`  再  `ts_zscore(rank(shock), 250)` ，让信号被迫日频翻转。这招在 techindi_model 这种 shock 型基因上确实能把 ht 打到 0.81~0.97（我之前验过）， **但对"预测概率/分位价差"这种 level 型信号完全失效** ：W 从 7 / 10 / 22 / 250 全扫了一遍，ht 最高只到 0.7165，一条都没过 0.75，而 Fitness 全部塌到 1.0 以下。

我的理解是：ht_ratio 要求收益来自「当天翻转」，高通只能把 **已有** 的日频成分放大，如果原信号的收益本来就 100% 来自「持有多天的水平差」，那高通只是在放大噪声——放大出来的换手是真的，收益却不是。 **所以 ht 是信号的先天体质，不是后处理能改的。** 这和楼上「ts_target_tvr_decay 会把 ht 从 0.80 砸到 0.59~0.74」正好是一枚硬币的两面：后处理只能 **降**  ht，不能 **升**  ht。要 ht>0.75，只能在建仓之前就去挑天然日频翻转的字段。

**三、排雷二：想靠"掺一条低 PC 的腿"顺手把 PC 也降下来，方向是反的**

同一批里我做了  `zscore(主腿) + w*zscore(高通腿)` ，w=0.5 和 w=1.0 两档。结果 ht 确实从 0.5162 抬到 0.5498 / 0.5723， **但 PC 同步从 0.6895 抬到 0.7139 / 0.6980，两档都是升的** 。写成闭式就清楚了：两腿近似正交时  `PC_c = (a + w·b)/sqrt(1 + w²)` ，它在  `w* = b/a`  处取的是 **极大值** ，所以温和稀释（w=0.5~1）必然把 PC 往上抬；真要降 PC 得  `w > 2ab/(a²-b²)` ，可那个量级的 w 会把 margin 和 Fitness 直接打崩。 **结论：掺腿救 PC 只有在副腿 PC 极低（≤0.3）且 margin 至少有主腿一半时才成立，否则纯属倒贴。**

**四、一个容易吃暗亏的平台口径差异（这条建议所有写批量脚本的同学都看一眼）**

`GET /alphas/{id}`  返回体里  `is.checks`  的判定，和  `GET /alphas/{id}/check`  的判定 **不是同一套阈值** 。同一批里我实测到：PROD_CORRELATION =  **0.7545 在 is.checks 里被判 PASS** ，同批另一条 0.7649 才被判 FAIL——而两边返回的  `limit`  字段写的都是 0.7。

也就是说， **批量脚本里那句  `if not fails: 标记为可提交候选` ，如果读的是 is.checks，会把一批 PC 在 0.70~0.76 之间的 alpha 误判成"零 FAIL"** 。我之前就这么误标过一批，直到逐条打 /check 才发现。建议：筛选阶段用 is.checks 快速过滤没问题，但 **凡是要进"可提交清单"的，必须逐条打 /check 复核，并且要轮询到 PENDING 全部清空为止** （刚跑完的 alpha 打 /check 经常整片 PENDING + value 全 null，直接读会得到一张空表）。

**五、顺带给楼主的 margin 统计做个佐证**

我这批 42 条达标候选的 margin 分布是 2.46~5.42bp，中位数约 3.6bp，和你贴的国区 theme 平均 3.36bp / 中位 2.61bp 完全同一量级。 **所以"高换手主题 margin 上 10bp"这个目标基本可以放弃了** ，它不是构造问题是主题的结构性特征；真正卡住 Base Payment 的还是 ProdCorr<0.7 那一关。

下一轮我打算换个思路：既然 ht 是先天体质、后处理只能往下不能往上，那就 **先按 ht 体质筛字段（我手上已经扫到几个裸跑 ht 就有 0.78~0.98 的字段），再在这些字段上做提 Sharpe 的构造** ，而不是反过来拿高 Sharpe 的构造去硬推 ht。跑完继续回来贴数据。

---

### 评论 #4 (作者: ZZ47696, 时间: 2个月前)

补一组  **GLB / High Turnover 3x**  的硬实测，专门回答「Fitness 差一点、能不能靠掺腿或加 decay 补上」这个所有人都会踩的问题。结论比较反直觉： **在同一个 kernel 内，Fitness 闸门和 Prod-Corr 闸门的可行区间根本不相交** 。

**1) 权重 w 细扫（8 条同族 sim，只改混合权重）** 

母式是 GLB / D1 / TOP3000 / RAM 中性化 / decay2 的「短反转×放量」kernel，辅腿是另一数据集的极性价差腿，形式  `zscore(main) + w*zscore(leg)` ：

w
Sharpe
Fitness
Turnover
ht_ratio
PROD_CORR

0.60
2.89
 **1.01** 
0.623
0.8135
 **0.8379** 

0.75
2.89
0.99
0.630
0.8164
未算

0.85
2.88
0.98
0.635
0.8193
未算

1.00
2.85
0.96
0.636
0.8208
未算

Fitness 对 w  **严格单调递减** ，ht_ratio 对 w  **严格单调递增** ——两个目标天然对冲。唯一能把 F 顶过 1.0 的点是 w=0.60，而恰恰是这一点 PROD_CORR 飙到 0.8379，比 **不掺腿的母式（0.8243）还高** 。也就是说， **稀释不但没降相关，反而抬了相关** 。这个我一共做了 4 组不同辅腿的对照，方向全一致，可以当定论用： **PROD_CORR 是主腿血脉决定的，掺腿救不了，只能换主腿/换数据集。**

**2) 「加大 decay 抬 margin」是伪杠杆** 

很多人（包括我）会想：Fitness ≈ Sharpe × √margin，那把 decay 调大压 turnover、抬 margin，Fitness 不就上去了？实测打脸：

decay
Turnover
margin
Sharpe
Fitness
额外后果

2
0.636
2.25bp
2.85
0.96
—

3
0.529
2.46bp
2.59
0.91
IS_LADDER_SHARPE FAIL

4
0.459
2.64bp
2.42
0.88
IS_LADDER_SHARPE FAIL

margin 只从 2.25 涨到 2.64bp（+17%，√后仅 +8%），Sharpe 却从 2.85 掉到 2.42（−15%）。 **净效应是 Fitness 单调下降** ，还顺带把 IS ladder 打 FAIL。同批 truncation 从 0.01 放到 0.02 也一样：Fitness 纹丝不动（0.96），只有 ht_ratio 涨到 0.8208（全族最高）。 **对高换手 alpha，低通类旋钮是分子分母一起砍，别指望它救 Fitness。**

**3) 一个省时间的机制小坑** 

平台 **不会为基础闸 FAIL（尤其 LOW_FITNESS）的 alpha 计算相关性** 。上表 F=0.96/0.98/0.99 那三条，PROD_CORR 挂了 2 小时还是 PENDING；F=1.01 那条秒出。所以想读 PC， **必须先把 Fitness 顶过 1.0** ，否则你等再久也等不到数。做 w 网格的时候，请把 F>1.0 的点排在前面跑。

**4) 中性化才是 ht_ratio 的主旋钮，不是 decay** 

同一信号只改 neutralization 的六点曲线（ht_ratio / Sharpe）：RAM 0.8989/0.80 > COUNTRY 0.8647/1.01 > MARKET 0.8141/1.06 > SECTOR 0.7612/1.32 > INDUSTRY 0.7528/1.47 > SUBINDUSTRY 0.7226/1.73。 **ht_ratio 与 Sharpe 严格反向** ，且这条曲线的跨度（0.72→0.90）远大于 decay 能挪动的幅度（±0.01）。要卡 ht>0.75 这条 HTVR 硬门，先在中性化上选点，再拿 decay 做微调，顺序反了会白跑很多批。

顺带更正一个流传较广的误解： **Liquid 3x 的门槛是  `HT_LIQUID_TOPDIV3000_SHARPE ≥ 1.7` ，这个指标是在 TOPDIV3000 子域上重算的，和你 alpha 自身的 universe 无关** ——TOP3000 的 alpha 一样能拿 Liquid 3x，不需要为了这个去换 universe。门槛值都是从  `GET /alphas/{id}/check`  返回的  `limit`  字段直接读出来的，比猜靠谱。

---

### 评论 #5 (作者: ZZ47696, 时间: 2个月前)

接着这帖再交一次作业。你在文末给的那个警告——「theme RA 平均 margin 只有万分之 3.36、中位 2.61，combine 费后堪忧」——我这轮正好把它撞穿了，顺便把我自己上一条评论里「decay 是伪杠杆」的结论修正成一个统一判据。四条实测，全部同一族基因、单变量对照、可复算。

### 一、margin 薄不是主题的宿命，是 universe 选错了：换 MINVOL1M，margin 从 2.37bp 抬到 4.96bp

你统计的 143 条 theme RA 里 techindi_model 占 101 条，我这族也是 techindi_model。同一条表达式一个字不改， **只换 universe** ：

universe
成分数
Sharpe
Fitness
margin(bp)
2Y Sharpe

TOPDIV3000
~3000
3.05
1.05
2.37
2.04

MINVOL10M
—
3.45
1.26
2.65
2.13

 **MINVOL1M** 
~8913
 **4.59** 
 **1.87** 
 **3.32** 
 **2.74** 

六项指标同时改善、没有任何交换代价。机理我理解是横截面从 3000 拓到 8900，特质风险被平均掉（Sharpe 升）同时 rank 的尾部更极端（单位换手赚得更多，margin 升），而 F=S·√(505·margin) 是乘性的，所以 F 超线性地涨。再叠上后面第二条的 decay，这一族现在 margin 稳定在  **4.4~5.0bp** ，是你贴的国区中位数 2.61bp 的 1.7~1.9 倍。

**最关键的一点、也是我一开始不敢换池子的原因：换 universe 会不会丢 Liquid 子主题资格？实测不会。**   `HT_LIQUID_TOPDIV3000_SHARPE`  这项 check 是平台 **固定在 TOPDIV3000 子集上重算** 的，跟你 settings 里填的 universe 无关。我这批 MINVOL1M 的 alpha，该项实测值 2.90~3.19，远高于 1.7 的闸。所以「想吃 Liquid 就必须在 TOPDIV3000 上跑」是个误解，白白吃了薄 margin。

### 二、「decay 是伪杠杆」需要修正：它是净赚还是净亏，有一个可判定的临界斜率

我上一条评论里贴过一组 decay 2→4 让 Fitness 从 0.96 掉到 0.88 的数据，当时下了「伪杠杆」的结论。这轮在 MINVOL1M 上重做，方向完全反过来（GLB / delay1 / RAM 中性化 / trunc0.01，权重 21:16 锁死， **只动 decay** ）：

decay
Sharpe
Fitness
Turnover
margin(bp)
ht_ratio
PROD_CORR

2
5.09
2.24
0.6446
3.88
0.7700
0.6978

3
4.86
2.30
0.5324
4.49
0.7602
0.7082

4
4.68
 **2.33** 
0.4596
 **4.96** 
0.7518
0.7062

margin +28%，Sharpe 只掉 8%，Fitness 反而从 2.24 涨到 2.33。两组数据看着矛盾，其实用  `F = S·√(505·margin)`  一算就统一了（这个恒等式我在两组数据上误差都 <1%）：

**decay 净赚 ⟺ √(margin 倍数) × (Sharpe 保留率) > 1 ⟺ dlnS/dln(margin) > −0.5**

- 我这组：margin ×1.278（√ ×1.131），Sharpe ×0.919 ⇒ 乘积 1.039，实测 F 比 2.33/2.24=1.040 ✓  **斜率 −0.34 > −0.5，净赚**
- 我上一组：margin ×1.173（√ ×1.083），Sharpe ×0.849 ⇒ 乘积 0.920，实测 F 比 0.88/0.96=0.917 ✓  **斜率 −1.02 < −0.5，净亏**

所以不用再争「decay 到底有没有用」—— **跑两个 decay 点、算一下这个斜率就知道该不该继续加** 。经验上：底层信号越强、universe 越宽，Sharpe 对压换手越不敏感，decay 就越容易落在净赚区。

### 三、Orthogonal 子主题（19 条）是三个 3x 里最空的坑，而拿它几乎零成本

你的统计是 Investable 140 / Liquid 99 /  **Orthogonal 仅 19** 。我做了个直接对照：同一条表达式、同一权重，只把中性化在 CROWDING 和 REVERSION_AND_MOMENTUM 之间切：

- CROWDING 版：S 4.86 / F 2.28 / margin 4.40bp， `MATCHES_CLASSIFICATION`  = [High Turnover, Investable, Liquid] ——  **3 类**
- RAM 版：S 5.09 / F 2.24 / margin 3.88bp， `MATCHES_CLASSIFICATION`  = [High Turnover, Investable, Liquid,  **Orthogonal** ] ——  **4 类**

Fitness 差 1.8%，换来最稀缺的那个子主题标签。所以只要你的基因对中性化不敏感， **默认就该用 RAM，没有理由用别的** 。补一个 API 上的坑（我踩过）：枚举值必须写  `REVERSION_AND_MOMENTUM` ，直接传  `"RAM"`  会被 400 拒。

### 四、一个会坑死所有自动化脚本的陷阱：IS 阶段的 fails=[] 是假的

这条跟策略无关，但凡是自己写批量筛选/自动提交脚本的都值得看一眼。 `GET /alphas/{id}`  拿到的 check 列表里， `PROD_CORRELATION`  /  `SELF_CORRELATION`  /  `DATA_DIVERSITY`  在 IS 阶段 **恒为 PENDING** ，不是 FAIL。如果你的脚本按「fails 为空」判达标，这三项等于被无视了。

我这轮全库扫了 1150 条 IS+OS，按 IS 口径「零 FAIL + Tvr>0.2 + ht>0.75 + Liquid Sharpe 达标」筛出  **114 条** ；逐条跑  `GET /alphas/{id}/check`  并等 PENDING 消失后拿到实测 PROD_CORR，真正全过闸的只剩  **40 条** —— **假阳性率 64.9%** 。里面甚至有 PROD_CORR 高到 0.95 的被判成"达标"。正确姿势是轮询 check 接口直到 PENDING 清空再判；顺手加个 12 小时 TTL 的本地缓存，我这边把全库复查从 1 小时 43 分压到了几分钟。

**目前还没解的：** 这一族 decay4 那条 F 已经到 2.33（全族最高、且四个分类全中），其余 26 项 check 全 PASS， **只卡在 PROD_CORR = 0.7062，超闸 0.0062** 。有意思的是 PC 对 decay  **不单调** （.6978 → .7082 → .7062），看着是饱和了，说明 decay 不是压 PC 的旋钮。我现在在用两个已标定的压缩器去啃这 0.0062：权重轴（dPC/dp ≈ −0.74）和 B 腿混合去相关（每压 0.01 PC 约赔 0.02 F，且不动 ht）。有结果继续来交作业。

---

