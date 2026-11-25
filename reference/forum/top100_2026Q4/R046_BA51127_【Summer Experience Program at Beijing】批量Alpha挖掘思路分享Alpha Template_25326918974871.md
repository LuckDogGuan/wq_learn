# 【Summer Experience Program at Beijing】批量Alpha挖掘思路分享Alpha Template

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/25326918974871
- **作者**: BA51127
- **发布时间/热度**: 2年前, 得票: 70

## 帖子正文

### **挖因子好比钻井，首先需要找到一个主信号。（这是最核心的）**

**当然如果找不到那也没关系，也不影响找到alpha。**

以下是一种找alpha的思路方式：

- 1、寻找论文或研报确定灵感————阅读并且采用gpt提取出关键词————将关键词输入到Datafield recommend *（自己编写或者详见前面的BRAIN API文档）* 寻找合适的field并且利用Data search *（也是自己编写的一个BRAIN API与Kimi相结合的一个小程序）* 工具搜索合适的datasets。

- 2、通过论文所给思路编写Template tree，如果编写不出来，则可以在论坛上或者其他途径上面找一找相关或者长得像的Template tree————将dataset代入Template tree利用Machine Alpha程序 *（一个自动化测试的程序代码，通过BRAIN平台的论坛内容和课程培训可以学习开发）* 进行测试————在平台上的unsubmitted上观察前几个结果sharp和turnovers，如果表现还可以则继续使用，如果表现不佳则更换表达式————直到主信号出现 *（如果尝试次数过多可以尝试放弃）* 。

- 3、将主信号导入MAPC结合不同的Datasets选出表现更好的alpha（ *测试之前，先提前将需要循环测试的alpha在平台上进行一下测试，通过之后再放入程序进行批量测试）* ————在平台上筛选出表现优秀的alpha————将alpha放入“GA遗传算法“ *（将遗传算法和Machine Alpha程序相结合的一个程序，通过BRAIN平台的论坛内容和课程培训可以学习开发）* 中进行测试优化————再选出优秀的Template tree————再结合datasets进行迭代————得出几个alpha。重复操作。

- 4、通过is/os脚本 *（一个筛选可提交alpha的工具）* ，检验is/os的ratio，一般这个值在1左右认为表现较好，选出表现最好的alpha。

**遇到的一些问题：“Correlation和IS ladder Sharpe指标”目前没有办法融入测试程序或者BRAIN 平台列表中，所以目前不太好批量筛选出这两个指标都通过的alpha，只能手动筛选，效率较低。可以开发满足需求的类似的应用程序。**

---

## 讨论与评论 (12)

### 评论 #1 (作者: WL13229, 时间: 2年前)

[BA51127](/hc/en-us/profiles/8958551180311-BA51127)

**IS ladder Sharpe在test会直接展示结果，在您通过API获得IS Performance之后，就可以直接看到这个test是否通过。**

**关于correlation，每天的请求是有限制的，有些test不通过的Alpha，建议不需要查看correlation**

---

### 评论 #2 (作者: MO34661, 时间: 1年前)

Hello I need someone who could help me intergrate the machine alpha program and genetic algorithm to get numerous alphas and introduce me to brain API

---

### 评论 #3 (作者: AZ37804, 时间: 1年前)

请问在哪里可以获取到api说明文档？

---

### 评论 #4 (作者: EO24865, 时间: 1年前)

You can get the Brain API under the learn section

---

### 评论 #5 (作者: WB30321, 时间: 1年前)

可以分享下 'Datafield recommend *（自己编写或者详见前面的BRAIN API文档）'这部分代码嘛，因为是user，看不到api文档，在根据文章找数据的时候不知道怎么去搜索*

---

### 评论 #6 (作者: CC85858, 时间: 1年前)

WB30321                                                                                                                                                                                    可以直接在平台的数据集出搜索英文关键词

---

### 评论 #7 (作者: YD77867, 时间: 1年前)

学习了

---

### 评论 #8 (作者: DX67257, 时间: 1年前)

大佬，能提供下 检验is/os的工具么

---

### 评论 #9 (作者: ZH24706, 时间: 1年前)

请问一下，主信号是什么？有什么特征？

---

### 评论 #10 (作者: ZL29846, 时间: 4个月前)

现在都被大数据给冲淡了

---

### 评论 #11 (作者: TH28301, 时间: 1个月前)

楼主提到的最后这个痛点——「Correlation 和 IS ladder Sharpe 目前没法融入批量测试程序，只能手动筛」——我在自己的批量流水线里刚好把这两项补进了自动化，分享一下我的做法。

我的流水线思路和楼主一致：模板 tree + dataset 代入 → 一阶回测 → 筛选剪枝 → 二阶 group 提升 → 三阶 trade_when 提升 → 提交。批量回测后进提交前检查，现在加了一道质量门禁：

- 平台 check 里只要  `LOW_SHARPE`  /  `LOW_2Y_SHARPE`  /  `LOW_FITNESS`  /  `IS_LADDER_SHARPE`  不是 PASS 就硬拦（在平台红线之外再收一道）；
- correlation 单独算：self-correlation > 0.7 硬拦、> 0.6 出黄线提醒，prod-correlation > 0.7 硬拦；
- 留了个  `force`  参数，个别需要人工判断的可以手动解锁。

中间踩过一个坑：脚本里读 correlation 的字段名写错（从  `is.selfCorrelation`  /  `prodCorrelation`  取），结果一直返回 None，门禁形同虚设；改成从 IS 明细里取之后才真正生效。

我自己的 OS alpha（USA/TOP3000/D1）self-corr 均值在 0.6 上下，最近 10 条里就有几条  `IS_LADDER_SHARPE` （2Y）只有 0.9–1.6，这正是我把这两项做成硬门禁的原因——批量出货时我不想再靠人眼一个个筛。

---

### 评论 #12 (作者: PZ64174, 时间: 22天前)

楼主分享的从研报提取主信号并结合模板树批量扩展的流程很清晰。在实际应用模板树时，还可以把关注点放在算子的正交替换上，比如在时序平滑阶段轮换使用线性衰减与指数衰减，或者在截面处理阶段尝试不同的分组方式。另外对于相关性筛选，可以在仿真前利用历史收益率矩阵进行离线相关性估计，这样能在提交前提前过滤掉大量高相关的冗余信号，大幅提升最终提交的有效率。

---

