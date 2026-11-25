# 【IQC 加油站】Alpha Examples  + New Dataset Available

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/23934004353687
- **作者**: KH94146
- **发布时间/热度**: 2年前, 得票: 5

## 帖子正文

**Alpha Example 1:网络依赖 Network Dependence**

**Alpha Idea**

在BRAIN的一个数据字段pv13_ustomergraphrank_hub_rank中，更高的hub score表示一家公司的客户拥有更多的关联联系，而较低的得分则表明合作伙伴集中度更高。如果一家公司的客户拥有较低的hub score，这意味着他们的合作伙伴较少，可能更依赖该公司。这对股票来说可能是正面的，因为它表明公司被替换的风险较低。因此，长期投资这类股票可能是个好主意。

**Implementation**

长期持有过去两年内Hub_Score得分低的公司的股票。

**Alpha Enhancement**

在表达式上使用一些横截面操作符(Cross-sectional operators)是否可以提高表现？

```
-ts_mean(pv13_ustomergraphrank_hub_rank,504)
```

延展阅读Cross Sectional Operators都有什么? 点击  [Operators | WorldQuant BRAIN](https://platform.worldquantbrain.com/learn/data-and-operators/operators#cross-sectional-operators)

**Settings:**

**![图片](../images/img_745cc0be42.png)**

**Alpha Example 2: 没有消息不是好消息**

**Alpha Idea**

如果一只股票的情绪长时间不变，这只股票在未来可能相对其他股票表现不佳。

**Implementation**

使用 'ts_std_dev' 来计算情绪随时间的波动。用过去一个季度的数据回填，以确保有足够的数据覆盖。

**Alpha Enhancement**

在表达式上使用一些横截面操作符(Cross-sectional operators)是否可以提高表现？

```
ts_std_dev(ts_backfill(snt_social_value,60),60)
```

**Setting**

![图片](../images/img_849a5e19e9.png)

**二、全新开放的数据集：Growth Valuation Model**

**数据集描述：**

- 增长估值模型数据集是一种股票排名模型，使用人工智能模型将多个估值比率组合成一个全面的相对估值度量。
- 每个比率都有权重，对于给定股票来说，最关键的比率对最终得分的影响最大。
- 数据集包括来自报告的实际数据和模型预测的信息。

**需要理解的关键概念：**

- 内在价值：基于历史财务表现和未来展望显示股票的实际价值。内在价值通常使用估值模型估算，并且，与市场价值一起，它可以提示股票的低估和高估。
- 稳态：在折现现金流（DCF）估值模型中代表增长率、股息支付比率等未发生变化的时期。在稳态期的无尽现金流（永续期）随后被捕获为终值。
- 折现率：用于将未来现金流折现至其现值的利率。

**示例Alpha**  **思路：**

- 对排名提高的股票采取多头头寸，对其他股票采取空头头寸，使用常见运算符如rank、zscore、ts_rank或ts_zscore。
- 对超出预测的股票采取多头头寸，对未达预测的股票采取空头头寸，使用ts_delay运算符。
- 通过结合内在价值和市场价值来识别低估和高估的股票。ts_corr和ts_covariance可以指示市场效率。

---

## 讨论与评论 (5)

### 评论 #1 (作者: MC63847, 时间: 2年前)

尝试-ts_mean(normalize(pv13_ustomergraphrank_hub_rank),504)，

-ts_mean(rank(pv13_ustomergraphrank_hub_rank),504)，

rank(-ts_mean(pv13_ustomergraphrank_hub_rank,504))，似乎效果并不好

---

### 评论 #2 (作者: KJ42842, 时间: 2年前)

可以继续尝试其他cross sectional ops

---

### 评论 #3 (作者: PZ64174, 时间: 2个月前)

感谢楼主关于 Alpha 逻辑与代码实现的深刻见解。在量化因子开发过程中，数据的预处理与异常值剔除对最终策略的夏普比率有着决定性影响。我们尝试过使用滑动窗口均值与指数衰减对高频噪声进行平滑，发现能够显著改善信号的连续性和多头集中度。非常具有启发性的文章，期待未来有更多深度探讨。

---

### 评论 #4 (作者: PZ64174, 时间: 2个月前)

感谢官方团队提供的案例与新数据集介绍。关于客户网络依赖度和中心度指标的逻辑非常有深度，节点公司的替换成本直接决定了其商业壁垒和盈利韧性。在使用这类图网络或关联度数据构建因子时，由于节点关系更新频率较低，极易出现数据稀疏或阶梯状突变。我们在实操中发现配合截面排序平滑以及与基础财务指标交叉验证，能显著提升逻辑在不同宇宙中的泛化性能。

---

### 评论 #5 (作者: GC81559, 时间: 1个月前)

SA 优化中一个关键但常被忽略的维度：组件的时间窗口多样性。如果所有组件都是 22 日窗口，组合后对市场regime变化很敏感。建议在 selection 阶段确保组件覆盖不同时间尺度：短周期(5-10日)、中周期(22-66日)、长周期(120-252日)各占1/3。

---

