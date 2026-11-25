# Region Agnostic Alpha 全解析 + 老Alpha重跑ARC候选脚本 + ARC2026参赛攻略置顶的

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/43410200668823
- **作者**: KH94146
- **发布时间/热度**: 20天前, 得票: 59

## 帖子正文

**🌍 新因子形式来了：Region Agnostic Alpha + 老Alpha也能冲ARC2026！** 

一次模拟，同时覆盖 GLB / USA / ASI / EUR 四大区域——这就是 RAA。现在提交 RAA 或 RA Parent Alpha，还能参加官方 All Region Competition 2026 拿奖金。本帖合并了两篇内容：RAA 原理与玩法 + 社区分享的"把已提交老Alpha批量重跑成RA候选"脚本，一次看懂原理、怎么用新方法、也别忘了老因子还能再战一次。

**目录** ：
 [一、什么是 Region Agnostic Alpha](#what)  ｜
 [二、Parent / Child 结构](#structure)  ｜
 [三、模拟设置要点](#settings)  ｜
 [四、提交测试标准](#submission)  ｜
 [五、配额与统计口径](#quota)  ｜
 [六、成功小贴士](#tips)  ｜
 [七、老Alpha怎么重跑成ARC候选](#resim)  ｜
 [八、ARC2026 比赛怎么玩](#arc)

## 💡 一、什么是 Region Agnostic Alpha

Region Agnostic Alpha（RAA）是一种全新的研究方法： **一次模拟即可同时覆盖多个区域（GLB、USA、ASI、EUR）** ，表达式结构和普通 Fast Expression 完全一样，区别在于数据字段会被自动翻译成 GLB / USA / EUR / ASI 四个版本的 Alpha。

核心好处两点：

- 稳健性 如果一个信号在多个区域都有效，说明统计显著性更强、覆盖面更广，过拟合的可能性也更低。
- 灵活性 如果信号只在特定区域有效，也可以针对性调整，专攻那些区域。

提交门槛：只要在  **2 个或以上区域** 表现达标，就可以提交。

[↑ 返回顶部](#post-top)

## 🧩 二、Parent / Child 结构

一次 RA 模拟会产生  **1 个 RA Parent Alpha**  +  **最多 4 个 RA Child Alpha** （每个区域一个：USA / EUR / ASI / GLB）：

- Alpha 的属性（名称、描述等）保存在 Parent 层级；修改 Parent 的描述会同步更新所有 Child。
- 单个 RA Child Alpha 仍然可以像普通 Alpha 一样被克隆、继续研究。
- RA Child Alpha 可以用于 Super Alpha（和普通 Alpha 一样处理）。
- 官方建议：能用 RAA 提交就优先用 RAA，而不是把各区域拆开单独提交。

模拟入口：在 Simulation 页面点击「+」，选择  **「New Region-Agnostic Simulation」** 即可。

[↑ 返回顶部](#post-top)

## ⚙️ 三、模拟设置要点

**兼容性限制：**

- Delay：仅支持 D1。
- Universe：必须使用专属的 RA universe——SMALL / MEDIUM / LARGE（映射见下表）。
- Max-trade 与 Max-pos 不能同时开启：
  - 两者都 OFF → ASI 自动以 Max-trade ON 运行；
  - Max-trade ON、Max-pos OFF → ASI 保持 Max-trade ON；
  - Max-trade OFF、Max-pos ON → ASI 使用 Max-pos ON，Max-trade OFF。

**Universe 映射表：**

RA Universe
ASI
EUR
GLOBAL
USA

LARGE
MINVOL1M
TOP2500
MINVOL1M
TOP3000

MEDIUM
MINVOL10M
TOP1200
MINVOL10M
TOP2000

SMALL
TOP500
TOP800
TOPDIV3000
TOP1000

**数据字段规则：** 表达式中引用的字段区域覆盖不需要完全重合，模拟会取 **交集区域** 运行。例如  `abc_usa_asi * xyz_glb_eur`  无交集区域会直接失败； `abc_usa_asi * xyz_usa_eur`  交集只剩 USA 一个区域，同样不能作为 RA 运行（RA 要求交集区域数 > 1）。建议优先选择多区域都有覆盖的字段，且最好一次专注一个数据集。

[↑ 返回顶部](#post-top)

## ✅ 四、提交测试标准

需要至少  **2 个 RA Child Alpha**  同时通过以下全部测试：

- 标准 Sharpe 测试：Sharpe ≥ 1.58
- 标准 Fitness 测试：Fitness ≥ 1.0
- 2 年阶梯 Sharpe 测试：2Y ladder Sharpe ≥ 1.58
- 子universe Sharpe 测试
- 自相关测试
- ASI 专属：Max-trade 强制 ON

**Prod correlation 在 RA Parent 层级测试** ：假设已有 ≥2 个 RA Child 通过上述标准，若 **全部** 未通过 prod correlation，则整个 RA Parent 不可提交；否则所有通过的 RA Child 都会被提交。

Alpha 分类方面，RAA 既可以是  **Atom** ，也可以是  **Power Pool**  Alpha；不同 Child 在 IS ladder 测试上分类结果不同是正常现象。

[↑ 返回顶部](#post-top)

## 📊 五、配额与统计口径

**配额管理：**

配额类型
处理方式

提交配额
按 1 个普通 Alpha 计（只占用 RA Parent 的提交配额，不占 Child）

并发模拟配额
按各 RA Child 并发配额之和计算

每日模拟配额
按已模拟的 RA Child 数量计算

**Genius 统计口径：**

统计项
处理方式

Signals
计入 RA Child Alpha

Combined Alpha performance
计入已提交的 RA Child Alpha

每个 Alpha 的 operator/field 数
按 1 个 Alpha 计（只看 RA Parent）

Signal / pyramid 计数
只看已提交的 RA Child

Pyramid 每个已提交的 RA Child 都会计入其对应 pyramid 及 alpha distribution； **Pyramid 主题乘数取所有已提交 Child 中的最大值** ，记录在 Parent 上，同时每个 Child 自己的乘数也单独记录。普通主题乘数则是把所有已提交 Child 的乘数按公式  `(sum(乘数) - 乘数个数 + 1)`  合并计算，Pyramid 乘数会把 Child 中最大的那个也作为一项加入公式。

Osmosis Points 只适用于已提交的 RA Child，Parent 本身不能组成 Combo，所以不能分配积分。

[↑ 返回顶部](#post-top)

## 🎯 六、成功小贴士

- 做跨区域数据比较时要小心，注意货币单位、市值量级、股票面值等可能不一致，建议按各自量级归一化，或用时间序列比较算子来统一单位。
- 如果一个 RAA 很难同时满足 2 个以上区域的提交标准，针对单一区域优化仍然是可行方案。
- 在 GLB 区域发现的信号，往往是很好的起点。

[↑ 返回顶部](#post-top)

## ♻️ 七、老Alpha怎么重跑成ARC候选

除了从零开始做 RAA，社区还分享了一个思路：把你手头 **以前已经提交（OS）的 Regular Alpha**  批量按 ALL/D1 的 Region-Agnostic 设置重新回测一遍，看看有没有能达到多区域覆盖、直接具备提交 ARC 资格的"漏网之鱼"。整理自社区帖子： [【Region-Agnostic】一键批量将所有OS Regular Alpha 重跑为 ALL/D1 的脚本](../引用的关联帖L2/[L2] 【Region-Agnostic】一键批量将所有OS Regular Alpha 重跑为 ALLD1 的脚本论坛精选_43322521365143.md) （感谢原作者分享）。

**脚本核心逻辑：** 分页读取你账号里所有 OS 阶段的 REGULAR Alpha，把原表达式逐条按 ALL/D1 的 Region-Agnostic 设置重新提交模拟请求，每次请求后写入 checkpoint 方便断点续跑。

关键点 普通模拟请求只把  `region`  改成  `ALL`  是不会创建 RA 回测的，必须在 REST 请求里显式指定  `type="REGION_AGNOSTIC"` 。已验证可用的请求体大致如下：

```
{
  "type": "REGION_AGNOSTIC",
  "settings": {"instrumentType": "EQUITY", "region": "ALL", "universe": "LARGE",
    "delay": 1, "decay": 10, "neutralization": "STATISTICAL", "truncation": 0.08,
    "pasteurization": "ON", "unitHandling": "VERIFY", "nanHandling": "OFF",
    "language": "FASTEXPR", "visualization": false},
  "regular": expression
}
```

`ALL`  下可选 universe 为 LARGE / MEDIUM / SMALL，跑完之后模拟详情会显示  `RA_PARENT` 。

边界 这只是 IS/UNSUBMITTED 阶段的研究工具：只负责创建模拟、记录结果， **不会自动设置属性、也不会自动提交 Alpha** ，跑完之后该怎么处理由你自己决定。

**建议的三段式跑法：**

```
python resim_os_regular_as_region_agnostic.py --config brain-accounts.json --account YOUR_ID
python resim_os_regular_as_region_agnostic.py --config brain-accounts.json --account YOUR_ID --execute --max-items 5
python resim_os_regular_as_region_agnostic.py --config brain-accounts.json --account YOUR_ID --execute
```

- 第一条：只做盘点（inventory），不实际提交模拟。
- 第二条：小样本验证，先跑 5 条看看效果。
- 第三条：正式全量跑，会根据 checkpoint 自动跳过已经是终态（COMPLETE/ERROR/FAIL/CANCELLED）的记录，继续处理剩下的。

评论区建议 有热心顾问补充：在  `ALL`  下 LARGE / MEDIUM / SMALL 三个 universe 建议都各跑一遍，筛选面更大，代价只是模拟次数 ×3。

**常见报错怎么看：**

- `Region agnostic simulations must have more than one regions`  —— 说明这个字段本身不具备多区域覆盖，属于兼容性问题，重试没用，直接跳过。
- `CONCURRENT_SIMULATION_LIMIT_EXCEEDED`  或 HTTP 429 —— 临时的队列限流，读取  `Retry-After`  之后重试即可。
- `ERROR`  /  `FAIL`  —— 建议保留原表达式、源 Alpha ID、模拟地址和响应内容，方便之后分析是字段覆盖问题还是语法问题。
- `POST_ERROR`  —— 不要直接当成"已处理"，要先区分是临时性队列错误还是不可恢复的请求错误，避免续跑的时候漏掉本来该重发的请求（评论区也特别提醒把它单独标记，和 ERROR/FAIL 区分开）。

**注意：** RA 回测本质上是一次跨区域可用性筛选，不代表原来的 Regular Alpha 会保留原本的 Sharpe、Fitness 或提交资格。批量重跑完成后，仍然要独立走一遍相关性、稳定性和正式提交测试（对照第四节的标准），别看到 COMPLETE 就直接当成能交的 ARC。评论区也提醒： **如果用这个方法跑完一个能交的 ARC 都没有，可能说明手头信号质量偏低** ，值得当作自查信号。

[↑ 返回顶部](#post-top)

## 🏆 八、ARC2026 比赛怎么玩

All Region Competition 2026（ARC2026）正是围绕 RAA 展开的官方比赛， **只有 ARC Alpha 或 RA Parent Alpha 有参赛资格** ——不管是新做的 RAA，还是第七节里重跑出来的老 Alpha，只要符合条件都能报名。

**关键日期：**

- 提交开始：9 月 7 日 8AM EST
- 介绍 Webinar：9 月 15 日 8AM EST
- 提交截止：10 月 11 日 23:59 EST

**评分标准：** 最终分数 = 25% IS robustness + 75% OS robustness，每个区域的 robustness 分值范围 2-8（整数），按 Sharpe 分段给分（1.58-2 记1分，≥2 记2分）；并列时用已提交 alpha 的 Avg OS Fitness 作为 tie-breaker。 **OS 分数不会实时公布** ，只在最终榜单公布，避免过拟合、注意提交池的多样性。

**奖金设置** （总奖池 $25,000）：

名次
奖金

第1名
$3,000

第2名
$2,000

第3名
$1,000

4-10名
$700

11-25名
$350

26-50名
$150

另外每个国家前 3 名可额外获得 $100（不占全球 Top50 名额）。 **拿奖资格需要至少提交 10 个** 。

重要提示 比赛期间：所有 genius 等级均可参加、不允许组队、alpha 配额（4个）和 superalpha 配额（1个）不变、比赛开始日前提交的 alpha 不计入、base payment 和 quarterly payment 照常发放（与比赛奖池独立）。

[↑ 返回顶部](#post-top)

一次模拟、多区域覆盖，稳健性更强、配额更省；老因子也别浪费，花几分钟批量重跑说不定就多了一个 ARC 候选——现在就去 Simulation 页面试试「New Region-Agnostic Simulation」，或者跑一下第七节的重跑脚本，向 ARC2026 发起挑战吧！

---

## 讨论与评论 (49)

### 评论 #1 (作者: ML38868, 时间: 20天前)

====================================================================================

学习一下
可能容易被忽略的事项：
1.Max-trade 与 Max-pos 不能同时开启

2.提交配额按 1 个普通 Alpha 计（只占用 RA Parent 的提交配额，不占 Child）

Signal / pyramid 计数    只看已提交的 RA Child

(意味着：做atom的前提下，一天最多能点16次pyramid？)

====================================================================================

---

### 评论 #2 (作者: TT92977, 时间: 19天前)

关于第七节批量重跑老 Alpha 的部分，有两个操作上的点想进一步确认：

- 如果按评论区建议把 ALL 下 LARGE / MEDIUM / SMALL 三个 universe 都跑，模拟次数 ×3，而每日模拟配额按已模拟的 RA Child 数量计算，重跑前是否需要先核对账号当天剩余配额？脚本遇到每日配额限制是自动等待，还是需要手动改天再跑？
- 脚本只负责创建模拟和记录状态，不汇总哪些 RA Parent 有 ≥2 个 Child 通过提交测试。如果手头 OS 老 Alpha 数量多，手动逐个检查模拟详情会比较低效，有没有推荐的后续筛选方式，或者脚本是否能顺带输出每个 Parent 对应的 Child 达标情况？
- POST_ERROR 被提醒要单独标记，脚本现有的 checkpoint 逻辑里是否会把它视为待重试项？还是需要自己在代码里加一层判断，避免续跑时漏掉可恢复的请求？

---

### 评论 #3 (作者: TS96358, 时间: 19天前)

感谢整理，特别是第七节“把已提交 OS Regular Alpha 重跑成 RA 候选”的思路。结合帖子里“只改 region=ALL 不会创建 RA 回测，必须显式 type=REGION_AGNOSTIC”这点，想确认几个实操细节：

1. 批量重跑前，是否建议先按第三节的字段交集规则筛一遍原表达式？如果字段交集区域数 ≤1，按帖子说明会遇到 “Region agnostic simulations must have more than one regions”，这类在 inventory 阶段跳过更省模拟次数。
2. POST_ERROR 在 checkpoint 里是否单独标记？帖子里提醒不要把它直接当已处理，续跑时是默认重试，还是仍按终态跳过？想确认脚本实际逻辑。
3. 帖子里提到 ALL 下 LARGE / MEDIUM / SMALL 建议各跑一遍。是否先小样本 5 条分别验证，再决定是否全量 ×3？

另外，重跑出 COMPLETE 后仍要按第四节标准独立检查提交测试和相关性，不能直接当作可交 ARC，这点很关键。

---

### 评论 #4 (作者: MZ45384, 时间: 19天前)

太详细了！！！这是我见过最具体的RAA回测教程和ARC比赛事项！已经在回测仓库里的老古董了，希望出货！

======================================================================================
知难上，戒骄狂，常自省，穷途明。“寻找可以重复数千次的东西。”——吉姆·西蒙斯（量化投资之王、文艺复兴科技创始人）
# Alpha∞ Engine Status: ONLINE [♦♦♦♦♦♦♦♦♦♦] 100%
# sys.setrecursionlimit(α∞) 
# PnL = ∑(Robustness * Creativity)
#无限探索、鲁棒性优先，创新性增值 
#Where there is a will, there is a way. 路漫漫其修远兮，吾将上下而求索。
======================================================================================

---

### 评论 #5 (作者: RL84586, 时间: 18天前)

很有帮助 非常感谢！！！

---

### 评论 #6 (作者: XC50098, 时间: 18天前)

楼主这篇把 RAA 模拟、老 Alpha 重跑和 ARC2026 串起来了，我想针对第七节批量重跑脚本确认几个实操点：

1. 全量跑之前，ALL 下 LARGE / MEDIUM / SMALL 是否建议各跑一遍？帖子里提到这样筛选面更大、代价是模拟次数 ×3；如果并发或每日模拟配额有限，优先跑哪种 universe 更合适？
2. POST_ERROR 单独标记后，续跑时是否先重试 POST_ERROR，再处理 checkpoint 里未终态的请求？帖子里提醒不能把它当“已处理”，这个容易漏。
3. 重跑完成显示 COMPLETE 后，仍要按第四节独立检查：至少 2 个 RA Child 同时通过 Sharpe / Fitness / 2Y ladder Sharpe / 子 universe / 自相关，且 prod correlation 在 RA Parent 层级判断。若只有 1 个 Child 达标，是否只能作为单区域研究，不能算 ARC 候选？
4. 比赛开始日前提交的 alpha 不计入；如果重跑在 9/7 前完成、提交在 9/7 后，是否按提交时间计入？这个点想确认下。

帖子里建议的三段式跑法里，先跑 5 条小样本验证再全量，确实能少踩不少坑。

---

### 评论 #7 (作者: FF45555, 时间: 18天前)

感谢楼主把 RAA 原理、重跑脚本、ARC 攻略合并成一篇，第四节那张「提交测试标准」和第五节的配额/统计口径表尤其有用，官方文档里散着的口径这一篇基本收齐了。

补一个重跑流程里容易被忽略的最后一道闸。按第四节的口径，Prod correlation 是在 RA Parent 层级测的：假设已有 ≥2 个 Child 过了标准测试，若全部未过 PC，整个 Parent 一样不可提交。批量重跑老 Alpha 时，前面的 Sharpe、Fitness、2Y ladder 都过了，最后卡在 Parent 层 PC 的概率不低——老 Alpha 之间本来就同族，重跑出来的 RA Child 互相像、也容易跟池子里已有的像。所以跑完脚本别急着逐个提交，先把同族候选分好组、每组挑互不相关的代表去走验收，省得名额和测试轮次都耗在注定撞车的兄弟身上。

另外第五节那笔配额账值得在开工前算清楚：提交配额只按 1 个 Parent 计，但并发和每日模拟配额是按 Child 数算的——第七节评论区建议的「LARGE / MEDIUM / SMALL 三个 universe 各跑一遍」，成本正好 ×3 落在模拟配额上。批量重跑前先估一下自己每天的模拟额度，把三 universe 全跑留给最值得的第一批，其余先跑 LARGE 单档过一遍筛。

---

### 评论 #8 (作者: WZ36417, 时间: 18天前)

这好像很难

---

### 评论 #9 (作者: SD17531, 时间: 18天前)

非常实用的 RAA 综述，特别是第七节的批量重跑思路。补几点实际跑模拟时容易踩的坑，供大家参考：

1. RA 的 universe 映射有个隐性成本：同一表达式在 USA 用 TOP3000、在 ASI 用 MINVOL1M，池子口径完全不同。即便 IS 各区域都过了 Sharpe 门槛，跨区域的真实可比性仍然要打折扣——所以建议单独记录每个 Child 的区域归属，看它到底是被哪个区域拉动达标的，避免"2 个区域达标"其实是同一类小市值/低流动性股票在两个区域的重复。

2. 字段用向量类（VECTOR/event）时，Region-Agnostic 下必须先 vec_avg / vec_choose 抽成标量再回填，否则不同区域的数据覆盖时点不一致，交集区域数经常只有 1，直接就报"must have more than one regions"。这不是重试能解决的，属于字段兼容性问题，要在选字段阶段就过滤。

3. 第三节提到规格差异，还有一个容易忽略的：neutralization 用 STATISTICAL 还是 INDUSTRY 对跨区域可移植性影响很大。统计中性在小市值池里更容易吃区域特性，industry 中性在不同区域里行业构成差异也大。建议重跑老 Alpha 时至少跑两组中性化设置，而不是只跑配置里那一套。

4. 评论区说的 LARGE/MEDIUM/SMALL 都跑一遍确实更全，但代价不光是模拟次数 ×3，还有判断负担：同一个表达式三个池子结果经常打架。我自己的习惯是先 LARGE 看方向是否成立，再 MEDIUM/SMALL 作为备选，而不是平铺三项直接收结果。

5. 第七节脚本只做跨区域可用性筛选，跑出 COMPLETE 不代表能交。ARC2026 评分是 25% IS + 75% OS，OS 又只在最终榜公布——所以筛选时宁可少而精，挑方向稳、换手低、四区域相关性不高的候选重点看，也比海量重跑更能控制后期过拟合。

---

### 评论 #10 (作者: SD17531, 时间: 18天前)

继续补一个 ARC2026 参赛策略视角，给这篇做点补充。比赛评分是 25% IS + 75% OS，而且 OS 分数只在最终榜单公布，意味着"靠在线反馈迭代"这条路基本走不通，更重要的是赛前设计：

1. 建议按"独立经济机制"来规划参赛池，而不是按"同一表达式换参数"来凑数量。两个参数很接近的变体在 OS 期大概率高度相关，等于同一个 bet 提交了两次，既浪费配额也不会在鲁棒性评分上叠加。

2. tie-breaker 是 Avg OS Fitness，所以在满足提交门槛的前提下，margin 更优的候选在并列时更占优。我自己会优先挑"换手低、margin 高的结构"，而不是 Sharpe 最高的那个。

3. RA Parent 级的 prod correlation 门槛意味着：你手头已经交过的 OS alpha 如果和某个 RA Child 相关性偏高，会影响整个 Parent 的可提交性。提交前把 RA 候选与已提交池做一次相关扫描，比提交后才发现不合格要省事得多。

4. 每个国家前 3 名额外 $100 这条，对顾问密度低的国家性价比更高。如果你所在区域竞争不激烈，本土冲刺的实际期望收益可能高于挤全球 Top50，值得先盘一下再定策略。

---

### 评论 #11 (作者: XG31364, 时间: 18天前)

感谢分享！Region Agnostic Alpha 确实能提升跨区域稳健性。我想补充一点：在进行 RA 回测时，建议先在单个区域（如 EUR）跑出基础因子，再检查其字段在其他区域的覆盖率；这样能更快定位哪些字段具备多区域潜力，减少无效模拟次数。此外，注意 RA universe 的选择会影响子universe Sharpe 测试，建议优先使用 MEDIUM universe 进行初步筛选，因为它在覆盖面和计算成本之间取得了良好平衡。祝大家在 ARC2026 中好运！

---

### 评论 #12 (作者: ML42552, 时间: 18天前)

这篇把 Region Agnostic Alpha 的机制、Parent 和 Child 的关系，以及不同区域的设置限制都整理得很清楚。以前我看到跨区域回测时，最容易忽略的就是字段覆盖和 Universe 映射，结果表达式本身没问题，模拟却因为交集不足直接失败。你把这些注意事项放在前面很有帮助，尤其是 Delay、Universe 和区域字段规则。后面如果能再补一个从普通 Alpha 改成 RA 候选的完整例子，大家会更容易照着操作。

---

### 评论 #13 (作者: ZH34713, 时间: 17天前)

顺着第四节那份提交标准清单，贴一组我这边的平台 checks 实际返回值做个对照。先说明样本：不是 RA，是 12 条普通的 TWN / TOP500 / delay 1 REGULAR alpha，表达式主体都是  `ts_median(-winsorize(fnd28_value_08631q, std=N), W)` ，或外面再套一层  `signed_power(..., 1.1)` ，中性化用 INDUSTRY 或 REVERSION_AND_MOMENTUM，decay 3 / 6，truncation 0.04 / 0.08 / 0.15，目前都在 IS 阶段、UNSUBMITTED。

- 标准 Sharpe 测试（ `LOW_SHARPE` ，limit 1.58）：2 条 PASS ——  `qMWpjV71`  1.76、 `j23JjOa5`  1.73；其余 10 条返回的是  **WARNING**  而不是 FAIL，value 在 1.42 ~ 1.55。
- 标准 Fitness 测试（ `LOW_FITNESS` ，limit 1.0）：12 条全 PASS，value 1.36 ~ 1.91。
- 2 年阶梯 Sharpe（ `LOW_2Y_SHARPE` ，limit 1.58）：12 条全 PASS，value 2.19 ~ 2.46，而且每一条的 2 年值都高于它自己的全周期 Sharpe。
- 子宇宙 Sharpe（ `LOW_SUB_UNIVERSE_SHARPE` ）：limit 不是固定值，在 0.82 ~ 1.02 之间；value 1.06 ~ 1.35，12 条全 PASS。
- 自相关（ `SELF_CORRELATION` ）：12 条全部是 PENDING。

另外把这批里  `CONCENTRATED_WEIGHT`  一项按 truncation 分组贴一下，因为它是这批里唯一跟着 truncation 分档变化的项：truncation 0.04 的 2 条（ `2rOxpng8` 、 `GrdNG3jZ` ）是 PASS；truncation 0.08 的 6 条 INDUSTRY 中性化是 WARNING，value 0.1037 ~ 0.1139（limit 0.1），而同样 truncation 0.08 的 2 条 REVERSION_AND_MOMENTUM 中性化是 PASS；truncation 0.15 的 2 条是 WARNING， `1YxRz0RK`  value 0.1479、 `vRkbvPbr`  value 0.1743。

---

### 评论 #14 (作者: PZ64174, 时间: 16天前)

这篇文章对新推出的跨区域因子机制和比赛规则梳理得非常清晰到位。在实际尝试多区域回测时，最容易遇到的卡点就是数据字段在不同市场的覆盖范围差异，很多在单一市场表现亮眼的小数据集在跨区域时往往因为覆盖缺失而直接报错。因此优先选用覆盖广泛的分析师预期、量价或全球基础财务字段，配合较为稳健的中性化处理，往往更容易在两个以上区域同时达标。此外批量重跑已通过的存量因子确实能节省大量试错成本，非常适合作为备战这次全区域比赛的基础起手式。

---

### 评论 #15 (作者: XG43628, 时间: 16天前)

跨区域全天候因子架构对于提升组合的全球泛化能力具有关键意义在实际将历史存量因子转化为RAA候选时不仅需要考察各子区域的夏普与适应度表现更要重点防范不同市场微观结构差异带来的符号反转效应建议在批量重跑过程中结合统计中性化与分位数截断算子对极端异常值进行平滑处理从而在满足ARC竞赛多区域严格合规门槛的同时实现更持久的稳健超额收益

---

### 评论 #16 (作者: GY85447, 时间: 16天前)

看完第七节，老 Alpha 重跑成 ARC 候选这个思路很具体。想确认几个落地边界：

1. 批量重跑后筛选时，是先看模拟详情里是否变成 RA_PARENT，还是先看是否有 ≥2 个 RA Child 通过第四节的 Sharpe / Fitness / 2Y ladder 等测试？如果只跑 ALL/D1/LARGE，是否值得按评论区建议再补跑 MEDIUM / SMALL，还是先等 LARGE 出候选再补更省模拟次数？

2. POST_ERROR 在 checkpoint 里目前怎么处理？帖子提醒它不能直接当“已处理”，要和 ERROR/FAIL 区分。如果脚本默认把它当终态跳过，续跑前是否需要单独导出这些记录并重新入队，避免漏掉本该重发的请求？

3. 重跑得到 RA_PARENT 后，到 ARC 报名前是否仍必须走 RAA 的正式提交测试和 Parent 提交，而不能沿用原 Regular Alpha 的 OS 状态？如果 inventory 输出能直接标出“至少 2 个区域覆盖”的字段，筛选会方便很多。

---

### 评论 #17 (作者: BW14163, 时间: 15天前)

楼主把 RAA 的 Parent/Child、ALL/D1 请求和 ARC 流程梳理得很完整。我补一个实际筛选时容易忽略的对照：我在 2026-09-14 的平台 OS Regular 记录里有三条 KOR/D1/TOP600 样本，om6b7YmE 的 IS Sharpe=1.90、Self Corr=0.6761、Prod Corr=0.7975；rK5qrMnd 为 1.63、0.4195、0.6215；E5vja7eG 为 1.86、0.1469、0.5448，且 E5vja7eG 的 2Y Sharpe=2.14。三例中的 IS Sharpe 与 Prod Corr 排序并不一致；这些是单区域 Regular/OS 样本，不是 RAA Child，不能替代跨区域结果。因此在本次 RA 重跑核对中，我不会把 COMPLETE 或单区 Sharpe 当成唯一筛选条件，而会逐 Child 记录区域覆盖数、IS/2Y/Ladder Sharpe、Self/Prod Corr、turnover 和失败原因。若目标是至少两个区域，字段交集不足两区时先标记待复核；若响应确实提供 Retry-After，则把它和状态、请求参数一起保存，帮助判断是否需要等待重试并复核字段/参数。请问大家有没有比较过同一表达式在 LARGE、MEDIUM、SMALL 三档的 Child 相关性差异？

---

### 评论 #18 (作者: ZJ47333, 时间: 15天前)

感谢分享，先收藏了。

---

### 评论 #19 (作者: LK39823, 时间: 14天前)

补一个实战细节：RA 模拟的 neutralization 可选项和单区域不完全一样，直接套用单区域常用设置可能会报错，建议先小批量试跑确认设置合法后再放量。另外 child alpha 可以单独克隆出来继续调，对表现分化明显的区域单独改 decay 或 neutralization，往往能把一个区域的 Sharpe 救回来。

---

### 评论 #20 (作者: FX25214, 时间: 14天前)

佬把 RAA 的 Parent/Child 结构、专属 universe 映射以及字段交集规则放在一起解释，对第一次接触 ALL/D1 的人非常实用。尤其是“两个字段各自覆盖多个区域，但最终交集必须大于一个区域”这一点，比只告诉大家脚本怎么批量重跑更重要，因为语法能跑通不代表它真的具备 Region-Agnostic 的研究意义。我想补充一个筛选老 Alpha 的标准：不应该只看原来某一个区域 Sharpe 高不高，而要先判断字段在 USA、EUR、ASI、GLB 中是否具有一致的数据定义、更新时间和覆盖结构。同名翻译字段如果在各区含义或供应商口径不同，Parent 表面共用一个表达式，Child 实际上可能在交易不同信号。建议脚本输出每个 Child 的 Sharpe、turnover、margin、有效起始年份以及区域间方向一致性，再决定是否提交 Parent。这样“老 Alpha 再战一次”才是跨区域稳健性验证，而不是简单把旧表达式换一个模拟入口。 ------------------------------------来自传奇耐打王的补充------------------------------------

---

### 评论 #21 (作者: JR57542, 时间: 11天前)

楼主把 Parent/Child、universe 映射和配额口径梳理得很全。补三个我们 2026-09-08 首批 RAA 探针（2 个 parent、8 个 child）里直接观测到的读法陷阱，都是帖子里没展开的：

**1）MATCHES_COMPETITION 在两层语义不同。** 实测 parent 层是 PASS、四个 child 全是 WARNING——同一个 check，parent 才是「是否入围 ARC2026」的判读层。看到 child 一排 WARNING 就断定没入围，是把 WARNING 当 FAIL 用了。

**2）两条流传的「RAA 专属豁免」被实测推翻。** 一是「ASI child 免 LOW_ASI_JPN_SHARPE」：该 check 实际在场且会 FAIL；二是「GLB child 免区域 Sharpe」：AMER/EMEA/APAC 三条全在，该 FAIL 的照样 FAIL。RAA 没有任何专属 check 豁免，按普通 alpha 的 checks 预期去核对就行。

**3）结果表里 parent 行的 margin 类指标恒为 NA 是平台行为，不是数据缺失。** 我们本地账本处理时对 parent 直接标 RAA_PARENT_W4_NA / RAA_PARENT_MARGIN_NA，绝不用 child 的 max/mean 冒充 parent 读数；margin 判定落在 child 层、各取各区地板。另确认一点楼主表格的行为：ASI child 的 maxTrade 由平台强制 ON（parent 传 OFF 也会被改）。

这些是单批 2 parent / 8 child 的直接观测，样本不大，欢迎有更多 RAA 实测的朋友补充对照。

---

### 评论 #22 (作者: TZ69297, 时间: 10天前)

楼主把 RAA 的 Parent/Child、ALL/D1 请求和 ARC 流程拆得很清楚；评论里问到 LARGE/MEDIUM/SMALL 三档 Child 相关性差异，我也在补这块，但目前没有可验证的三档对照，所以先列几个我会优先核对的点：

1. 先按区域对齐再比相关性。帖子映射表里同一 RA universe 档在各区域对应的 universe 不同，例如 USA 的 LARGE/MEDIUM/SMALL 分别是 TOP3000/TOP2000/TOP1000，EUR 是 TOP2500/TOP1200/TOP800。比较时拆成“USA 三档”“EUR 三档”等分别看，避免把区域差异和 universe 档位差异混在一起。
2. 每个 Child 记录区域覆盖数、IS/2Y/ladder Sharpe、Self/Prod Corr、turnover 和失败原因。COMPLETE 不等于可提交 ARC，帖子也提醒过重跑只是 IS/UNSUBMITTED 研究工具，不自动设属性或提交。
3. 失败原因分开处理：字段交集不足两区直接跳过；429/并发限制按 Retry-After 重试；POST_ERROR 单独标记，不要当已处理。
4. 如果三档都跑，筛选面更大但模拟次数×3；可以先按评论区建议跑 5 条小样本，再靠 checkpoint 续跑。

如果大家有同一表达式在三档、同一区域的 Child 相关性对照，希望能分享，我也想学习怎么判断差异主要来自 universe 档位还是区域本身。

---

### 评论 #23 (作者: JX84394, 时间: 10天前)

同问三档 universe 的 Child 相关性差异。看完帖子和补充，我的感受是：RA 重跑更像筛选，不能只看 COMPLETE 或单区 Sharpe。

- LARGE/MEDIUM/SMALL 都跑时，是先比各档 Child 相关性，还是先看区域覆盖数？
- 字段交集刚好两区时，会先换字段还是标记待复核？

---

### 评论 #24 (作者: SY86571, 时间: 9天前)

楼主第七节把老 Alpha 重跑定位成跨区域可用性筛选，COMPLETE 不等于可交 ARC；评论区还卡在「三档 universe 都跑时，先比 Child 相关性还是先看区域覆盖数」「字段交集刚好两区时先换字段还是先标记」。从目前信息看，筛选顺序可以先定，不必等三档对照齐了再动手。

1. 先看区域覆盖数。第三节要求交集区域数 > 1，第四节提交至少要 2 个 Child 同时过测；覆盖不足两区的，按评论里的做法标记待复核或直接跳过，这类报错重试无效。
2. 覆盖够了再逐 Child 记 IS / 2Y / ladder Sharpe、Self / Prod Corr、turnover 和失败原因，不要只用 COMPLETE 或单区 Sharpe。
3. 比三档相关性时先按区域对齐：同一 RA universe 档对应的各区 universe 不同（USA：TOP3000 / TOP2000 / TOP1000，EUR：TOP2500 / TOP1200 / TOP800），拆成「USA 三档」「EUR 三档」再比，避免把区域差和档位差混在一起。
4. 配额上提交只占 Parent，并发和每日模拟按 Child 计；三档全跑是模拟次数 ×3。评论里有人建议先 5 条小样本，或先 LARGE 看方向，MEDIUM / SMALL 作备选。

字段交集刚好两区：按帖子口径已满足 RA 运行和提交门槛的下限，建议先标记待复核，等 Child 测试和 Parent 层 prod correlation 出结果，再决定要不要换字段。

目前评论里还没有同一表达式、同一区域、三档 Child 的可验证相关性对照。有跑过的话，希望能贴一下同一区域三档的 Self / Prod Corr，方便判断差异主要来自 universe 档位还是区域本身。

---

### 评论 #25 (作者: XY78410, 时间: 9天前)

牛啊，不用盲目的，没有目标的乱跑了，这真是站在巨人的肩膀上了。

---

### 评论 #26 (作者: XX88140, 时间: 8天前)

非常实用的RAA讲解，先收藏下了~ 等点完塔试一下提交RAA因子。

======================================

DAY DAY UP!

=====================================

---

### 评论 #27 (作者: WZ92324, 时间: 8天前)

顺着上面几位问的三档 universe，说一点我的体会：我觉得这三档不太适合平铺着跑。USA 的 TOP3000/2000/1000、EUR 的 TOP2500/1200/800，本来就是同一个池子一层层收窄，跑出来三份 Child 天生就长得像；

---

### 评论 #28 (作者: LB34773, 时间: 8天前)

感谢分享，虽然能提交的只有一两个，但是意外的收获了很多不错的child，丢给AI优化居然还出来几个RA，官方加强版金字塔👍

=============一朝得成master，始知我命不由天。然回首来时路，步步皆由抉择生，非独命运之锁，亦系吾心之向。故虽知天命，仍行吾道，不负此心。==============

---

### 评论 #29 (作者: HC14446, 时间: 8天前)

这篇把 RAA 的机制和 ARC 流程串得很完整，评论里补的实战细节也很值得对照。我顺着已有信息补充几个筛查时容易忽略的点：

1. 三档 universe 的 Child 相关性差异目前评论区还没有可验证的对照数据。比较时建议先按区域对齐再比相关性——同一 RA universe 档在不同区域的池子并不同（比如 USA 的 LARGE 是 TOP3000、EUR 是 TOP2500），直接跨区域比三档容易把区域差异和档位差异混在一起。

1. 重跑脚本产出的 RA_PARENT 只是 IS/UNSUBMITTED 阶段的研究结果，不自动提交也不沿用原 Regular 的 OS 状态，要走正式提交测试和 Parent 层 prod correlation 判断后才能作为 ARC 候选。评论里提到的「MATCHES_COMPETITION 在 parent 层和 child 层语义不同」这点值得留意，但目前只是一批 2 parent / 8 child 的观测，样本不大，建议有更多实测的朋友补充对照。

1. POST_ERROR 的 checkpoint 处理逻辑只有脚本作者能确认，帖子里建议单独标记而不是当终态跳过。如果手头 OS 老 Alpha 数量多，可以先小样本跑 5 条验证，确认脚本对 POST_ERROR 和 429 的重试行为符合预期，再决定是否全量 ×3 跑。

---

### 评论 #30 (作者: XY59450, 时间: 7天前)

已提交的老因子可以通过脚本批量按全区域重跑为候选，关键在于请求体必须显式指定区域无关类型，仅仅修改区域并不会触发跨区域回测。跑完之后仍然要独立核验提交标准，不能看到完成状态就直接当成可以提交，还需要检查相关性稳定性以及正式提交测试等要求。

---

### 评论 #31 (作者: YJ75326, 时间: 7天前)

这篇文章把 RAA 机制、Parent/Child 逻辑以及老 Alpha 重跑脚本串得非常透彻，配额和测试口径整理得太及时了！老 Alpha 往往出自几套相似的表达式骨架，批量重跑出来的 RAA 极其容易在 Parent 层级因 Prod Correlation 超标被整组拦截。可以在跑完 COMPLETE 后，先做一次账号内部候选池的自相关阵聚类，每组只选跨区域残差最显著的代表走正式提交，避免白白消耗时间。再次感谢楼主的无私分享！

---

### 评论 #32 (作者: YL61874, 时间: 7天前)

MATCHES_COMPETITION 在 parent 层 PASS、child 层全 WARNING 这个读法陷阱很关键。补两条配额口径上的经验：

1）PC 检查在当日提交配额满时不会计算（返回 EMPTY/PENDING），这时既不能当 FAIL 也不能当 PASS。要区分两件事：「平台算不算」只看提交配额，配额满就不算，等次日重置；「算得多快」有时段规律，白天容易撞超时，可以延后到晚上或改单条跑。

2）parent/child 两层的 universe 映射不一致，比较相关性前一定先按区域对齐，否则同一档在不同区域对应的池子不同，结论会互相矛盾。

---

### 评论 #33 (作者: WW78189, 时间: 6天前)

非常详细，感谢分享，有一些地方确实没考虑到，也感谢分享的脚本，

---

### 评论 #34 (作者: LZ90942, 时间: 6天前)

补一个时间线：文中第四节那套子可交清单是开赛时的版本，后面平台改过几次，我这边看到的是这样。

9/11 之前有些子带 PP 宽松档，LOW_FITNESS、LOW_2Y 没过只算 WARNING，我最早交成的几条里有子 fitness 0.5 也交上了；9/11 晚上这一档从所有子上消失了。9/12 起 LOW_2Y_SHARPE 是硬门，我当时重拉 211 个子，171 个挂在它上面。9/23 上午（香港时间 11:10 到 11:26 之间）之后新模拟的子不再有 LOW_2Y_SHARPE，换成了 IS_LADDER_SHARPE，没过也只是 WARNING，我 9/23 晚上交成的一条就有两个子 IS_LADDER 是 WARNING。

老模拟不是一刀切换过来的：9/14、9/15、9/19 模拟的几条已经变成 IS_LADDER，9/8、9/17、9/22 的还挂着 LOW_2Y，翻老候选的时候先看一眼子 checks 里现在是哪一项。

另外子页面上的 checks 不是最终口径，完整的逐子判决在 precheck 之后  `GET /alphas/{parent}/submit`  的  `is.subregions`  里，这个结果过一阵会变成 404，要及时读。

---

### 评论 #35 (作者: JB71859, 时间: 5天前)

谢谢楼主分享，也想听听其他朋友的看法。我平时看论坛，除了关注结论，也比较好奇背后是怎么考虑的，有没有遇到过和预期不一样的情况。有时候一个不起眼的细节，恰好就能解开之前没想明白的问题。大家有相关经验也可以补充几句，不一定非要是成功的做法，试过但没走通的路同样值得聊。不同情况放在一起看，也方便我理解哪些地方可以参考，哪些还需要自己再琢磨一下。

---

### 评论 #36 (作者: YH25030, 时间: 3天前)

今天终于把ARC2026的比赛规则吃透了，整理了一下思路。

1.把以前已经提交的RA因子做一下梳理，看看哪些数据集和字段总容易出Parent 和Child RA。

2. 制作ARC2026比赛专用模板，随机跑一些数据字段。

3.让AI做检查，优化并且提交。

---

### 评论 #37 (作者: LO84823, 时间: 3天前)

第七节这个“老 Alpha 重跑成 ARC 候选”的思路，结合评论区关于三档 universe、POST_ERROR 和 Parent 层 PC 的讨论，我建议把重跑后的处理拆成四步：

1. inventory 阶段先按第三节字段交集规则过滤。交集 ≤1 的表达式直接跳过，不要进执行队列；帖子里提到的 “Region agnostic simulations must have more than one regions” 属于字段兼容性问题，重试没有意义。

1. LARGE / MEDIUM / SMALL 是否都跑，先算配额再决定。第五节说每日模拟配额按已模拟的 RA Child 数计算，评论区建议三档各跑一遍等于次数 ×3；如果额度有限，可以先 LARGE 跑一轮，再只对少量候选补 MEDIUM / SMALL，而不是全量平铺。

1. POST_ERROR 在 checkpoint 里不要当终态。评论区多次提醒它要和 ERROR/FAIL 分开；续跑前建议单独导出 POST_ERROR，结合响应内容判断是队列临时错误还是请求错误，再决定是否重入队。

1. COMPLETE 之后按第四节独立验收，不要用原 Regular Alpha 的 OS 状态或单区 Sharpe 替代。至少看是否有 ≥2 个 RA Child 通过 Sharpe / Fitness / 2Y ladder / 子 universe / 自相关；Prod correlation 在 RA Parent 层级判断。同族老 Alpha 重跑出来的 Child 容易互相像，评论区建议先分组挑互不相关代表，这在批量场景下能省不少测试轮次。

另外，评论区问到同一表达式在 LARGE/MEDIUM/SMALL 三档的 Child 相关性差异，目前上下文里还没有可验证的三档对照。如果要比较，评论区有人建议先按区域拆开，例如 USA 三档、EUR 三档分别看，避免把 universe 档位差异和区域差异混在一起。这个点如果有跑过的朋友能补一组对照，会很有参考价值。

---

### 评论 #38 (作者: HY14686, 时间: 3天前)

补一个跑RA的体感：机制在两个以上区域真的成立这个门槛比想象中高。我跑下来发现很多表达式其实是靠某一个区域的市场结构才赚钱的，转成RA之后其他区域的child就是纯陪跑，最后凑不齐两个达标child，白烧模拟额度。所以选字段阶段就优先看多区域覆盖的均衡性，别被单一区域的强字段带跑。另外老alpha重跑党注意评论区说的parent层级PC，同机制的老腿转完互相关不低，重跑前先按机制分组、一组挑一条代表，比无脑全量跑的出货率高。

---

### 评论 #39 (作者: ER48854, 时间: 3天前)

看贴后，以前8*10框架的多并发模拟好像不行了，就算改了settings好像还是不行。

---

### 评论 #40 (作者: ZW26474, 时间: 3天前)

楼主第七节把老 Alpha 批量重跑成 ARC 候选的思路很具体，我想接着评论区反复问的点，补一下重跑后的筛选顺序：

1. 先做 inventory 字段交集预筛。帖子第三节和评论区都提到，交集不足两区会直接报  `Region agnostic simulations must have more than one regions` ，这种重试没用；先筛掉比全量跑完再人工看更省模拟次数。

1. 重跑出 COMPLETE 后，不直接当提交资格。按第四节标准，至少 2 个 RA Child 同时过 Sharpe / Fitness / 2Y ladder / 子 universe / 自相关，再在 RA Parent 层看 prod correlation；评论里也提醒 Parent 层 PC 全部不过时整个 Parent 不可提交。逐 Child 记录区域覆盖数、IS/2Y/ladder Sharpe、Self/Prod Corr、turnover 和失败原因会更稳妥。

1. LARGE / MEDIUM / SMALL 三档是否都跑：帖子里评论区建议各跑一遍，代价是模拟次数 ×3；评论里也有人指出同一档在 USA / EUR / ASI 映射的 universe 不同，比较 Child 相关性时建议按区域拆开，否则区域差异和档位差异容易混在一起。目前上下文里没有可验证的三档对照，我会先用 5 条小样本验证，再决定是否全量补 MEDIUM / SMALL。

另外，POST_ERROR 这块如果脚本默认把它当终态跳过，续跑前建议单独导出这些记录重新入队；这点最好用小样本确认 checkpoint 行为，避免全量跑完才发现漏发。

如果只跑 ALL/D1/LARGE 出了 RA_PARENT，大家会先补 MEDIUM / SMALL，还是先按 Parent 层 PC 筛一轮再补？

---

### 评论 #41 (作者: DW35234, 时间: 3天前)

很有帮助 非常感谢！！！

---

### 评论 #42 (作者: XS55765, 时间: 3天前)

十分感谢，新的知识，学习中！

---

### 评论 #43 (作者: LY33035, 时间: 3天前)

楼主第七节的三段式跑法很实用，评论区反复问的 LARGE / MEDIUM / SMALL 三档和 POST_ERROR 处理，也正好是重跑时最容易卡住的两个点。按帖子现有信息，我会这样排筛选顺序：

1. 先跑 inventory，按字段交集规则过滤。交集区域数 ≤1 的表达式会直接遇到 “more than one regions”，这类在正式重跑前跳过，比跑完再筛省模拟次数。
2. 三档不必一开始全量。全跑等于模拟次数 ×3，而每日模拟配额按已模拟的 RA Child 数量计算；可以先跑 5 条小样本，优先看 LARGE 方向是否成立，再决定是否补 MEDIUM / SMALL。
3. POST_ERROR 建议单独标记，不要和 ERROR / FAIL 一起当终态跳过，否则 checkpoint 续跑可能漏掉可重发的请求。429 或并发限制按 Retry-After 处理。
4. 跑出 COMPLETE 不等于可交 ARC。仍要逐 Child 记录区域覆盖数、IS / 2Y / ladder Sharpe、Self / Prod Corr、turnover 和失败原因，并确认至少 2 个 RA Child 通过第四节标准；Prod correlation 在 RA Parent 层判断。
5. 比较三档结果时，先按区域拆开看：同一 RA universe 档在 USA、EUR 等区域对应的实际 universe 不同，避免把区域差异和档位差异混在一起。

如果三档结果互相打架，我会先看区域覆盖数和 Child 相关性，再决定是否保留；只有 1 个 Child 达标的，先按单区域研究处理。你们跑三档时是先看 LARGE 出候选再补，还是直接平铺三档？

---

### 评论 #44 (作者: HW35272, 时间: 2天前)

这篇帖子简直是WorldQuant BRAIN社区的“圣经”级教程啊！必须给楼主点个大大的赞，这哪里是分享，简直是在做慈善！

说实话，Region Agnostic Alpha（全区域Alpha）一直是很多新手的噩梦，我也在这个坑里摔过无数次。每次看到那些复杂的Universe定义、Delay设置，还有让人头秃的Sub-universe处理逻辑，真的想直接放弃。但楼主这篇教程太细致了，从最基础的原理拆解，到具体的代码实现，甚至连“坑”都帮你标得清清楚楚。特别是关于如何处理不同区域数据差异的那部分，简直是醍醐灌顶，以前我总是在这里卡壳，导致回测结果一塌糊涂。

最让我感动的是，楼主不仅给了“鱼”，还给了“渔”。那个关于如何验证Alpha稳健性的思路，比代码本身更值钱。这种毫无保留的分享精神，在现在的社区里真的太稀缺了。看完这篇帖子，我感觉自己之前的摸索都像是在盲人摸象，现在终于有人把灯打开了。

真心希望楼主能多出一些这种深度的实战教程，哪怕是用爱发电我们也愿意看！这种干货满满的帖子，建议直接置顶，让所有还在Region Agnostic门口徘徊的兄弟们都能少走弯路。再次感谢大佬的无私分享。

---

### 评论 #45 (作者: ZL85711, 时间: 2天前)

感谢整理，特别是第七节“把已提交 OS Regular Alpha 重跑成 RA 候选”的思路。很有帮助 非常感谢！！！

---

### 评论 #46 (作者: TJ83049, 时间: 2天前)

楼主把 Parent/Child、ALL/D1 请求体和 ARC 流程串得很清楚，第七节“重跑只是 IS/UNSUBMITTED 筛选、不自动设属性/提交”这个边界尤其关键。针对评论区反复问到的三档 universe、POST_ERROR 和跑完后的筛选，我会按这个顺序核对：

1. 先在 inventory 阶段筛字段交集和区域覆盖。按第三节，RA 要求交集区域数 >1；只改  `region=ALL`  不会创建 RA 回测，必须显式  `type="REGION_AGNOSTIC"` 。交集不足两区的表达式直接跳过，比跑完再报 “must have more than one regions” 省模拟次数。
2. 小样本验证设置后再放量。有评论提到 RA 的 neutralization 可选项与单区域不完全一样，先跑 5 条确认合法；三档 LARGE/MEDIUM/SMALL 都跑会让模拟次数 ×3，而每日/并发配额按 Child 数算，先核对当天剩余额度。可以先 LARGE 看方向，再补 MEDIUM/SMALL。
3. POST_ERROR 不要当终态。帖子和评论都提醒它要和 ERROR/FAIL/CANCELLED 区分；如果 checkpoint 默认跳过，续跑前最好单独导出并重入队，避免漏掉可恢复请求。
4. COMPLETE 不等于可提交。仍要按第四节看至少 2 个 RA Child 同时过 Sharpe/Fitness/2Y ladder/子 universe/自相关，且 prod correlation 在 Parent 层判断。有实测评论提到 MATCHES_COMPETITION 在 Parent 层才是入围判读层，child 层 WARNING 不一定等于没入围，这个可以单独核对。
5. 三档 Child 相关性目前评论区还没有可验证对照。建议按区域拆开记录（例如 USA 三档、EUR 三档），每个 Child 记区域覆盖数、IS/2Y/ladder Sharpe、Self/Prod Corr、turnover 和失败原因，再判断差异主要来自 universe 档位还是区域本身。

如果脚本 inventory 能直接标出“至少 2 个区域覆盖”的字段和每个 Parent 下 Child 达标数，筛选会省不少手工。

---

### 评论 #47 (作者: HY88570, 时间: 2天前)

@SD17531 大佬好，我是 HY88570，最近一直在主攻 KOR/TOP600/D1 的 INSIDERS 方向。看到您在 KOR/D1/INSIDERS 上有三笔提交（sharpe 1.50 / 1.50 / 1.03，互相 self-corr 只有 0.42 / 0.29 / 0.05，非常正交），非常佩服——这基本是这个类别在 KOR 上的天花板了。我自己在 KOR INSIDERS 上系统遍历了很多轮（insd5 的日期腿/内容字段 × 各类伙伴数据集 × 多种统计量结构），始终卡在强度和正交互斥这一关。想冒昧请教一下：这三笔 INSIDERS 大概是用什么思路做的？比如是 insiders5 的哪类字段（事件日期类还是持股/金额类）、单数据集还是跨数据集组合？不求具体表达式，能给个方向性的提示就感激不尽！也欢迎回帖或私信，谢谢！

---

### 评论 #48 (作者: LT20707, 时间: 2天前)

感谢整理，已经使用跑起来了，要在ALL这个region里的字段才可以用于ARC跑脚本

---

### 评论 #49 (作者: RL25317, 时间: 2天前)

补充两个容易被忽略的点。第一，平台刚公告上线"All regions/D1 Power Pool Oct'26"主题，和 ARC 2026 完全同构：都是 ALL regions/D1 的 Region-Agnostic 提交，同一批 RA Parent 可以同时计入 ARC 参赛资格和主题 multiplier，等于一份回测吃两份收益——如果这个主题里有你未点亮的 Region+Dataset 格子，优先拿对应字段组去重跑老 Alpha，命中率与收入双收。第二，平台同步更新了 ARC 模拟容量：RA/ARC 回测现在走独立并发池，不再挤占普通 8 卡槽，所以 LARGE/MEDIUM/SMALL 三档可以放心并行跑，但每日模拟配额仍按 Child 数扣，开工前务必查当天剩余额度。最后提醒：平台 9 月把 LOW_2Y_SHARPE 换成了 IS_LADDER_SHARPE，且老模拟不是一刀切换，翻旧候选时先看子 checks 现在是哪一项，别拿新口径套老结果。

---

