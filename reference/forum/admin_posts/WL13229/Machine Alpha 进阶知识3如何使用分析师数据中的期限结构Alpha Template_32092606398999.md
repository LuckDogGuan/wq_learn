# Machine Alpha 进阶知识3：如何使用分析师数据中的期限结构Alpha Template

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/32092606398999
- **作者**: WL13229
- **发布时间/热度**: 1年前, 得票: 19

## 帖子正文

原文链接： [[Alpha Template] How do you utilize different periods of estimation – WorldQuant BRAIN](../引用的关联帖L2/[L2] [Alpha Template] How do you utilize different periods of estimationAlpha Template_27963407565975.md)  欢迎点击并查看更多讨论，或在本贴留言。

今天，我们将深入探讨如何利用常见分析师数据集中的期限结构来挖掘潜在的 Alpha 信号。当你查看诸如  `analyst14`  和  `analyst15`  之类的数据集时，会发现它们在多个字段中展现了期限结构。例如，当你研究  `anl14_mean_eps`  时，会发现多个字段共享相同的前缀，但在时间范围上有所不同，比如  `fp1` 、 `fp2` 、 `fy1` 、 `fy2`  等。

🔍  **理解时间范围：**

- **fp1** ：表示即将到来的季度。
- **fy1** ：表示即将到来的年度。

这些不同的后缀表示各自的时间范围，使你能够推导出多个时期的预估增长差异。

📊  **示例模板：**  一个潜在的模板可以是：

```
group_zscore(subtract(group_zscore(anl14_mean_eps_<period1>, industry), group_zscore(anl14_mean_eps_<period2>, industry)), industry)
```

此模板捕捉了第一时期和第二时期的平均估算值之间的行业标准化差异。基于之前的模板，你可以进一步扩展：

```
<group_compare_op_1>(<diff_op>(<group_compare_op_2>(anl14_mean_eps_<period1>, <group_2>), <group_compare_op_3>(anl14_mean_eps_<period2>, <group_3>)), <group_1>)
```

✨  **关键点：**

1. **保持前缀一致** ： `anl14_mean_eps_`  的前缀被保留，以确保比较在可比指标之间进行，避免 Alpha 搜索陷入随机比较。
2. **抽象化选择** ：所有操作符和分组数据都成为抽象化的选择，每一个都体现了原始选择背后的经济直觉。例如， `<group_compare_op_1>`  最初可能使用  `group_zscore` ，但其他有效选项还包括  `group_rank` ，它也可以将工具与其在  `<group_1>`  中的同行进行比较。

📂  **更多数据集信息：**  数据集还包括其他有价值的信息，例如估算数量、估算的标准差等。

💡  **讨论提示：**  你将如何系统地在模板中利用这些额外信息？欢迎分享你的想法和技巧！

祝大家研究顺利！🚀

---

## 讨论与评论 (3)

### 评论 #1 (作者: LL87164, 时间: 1年前)

多谢分享！今天刚好正在重温 ****[⭐如何自动化创建Alpha（Machine Alpha）合集内容 – WorldQuant BRAIN](如何自动化创建AlphaMachine Alpha合集内容Alpha Template_25329126761879.md)**  。** 没想到又有了最新更新，马上就有了尝试新模板的新鲜感和动力。

一个小问题：下面这些操作符和分组字段应该是一样的吧？这样才有可比性。2和3只是表示前后顺序。

```
<group_compare_op_2> == <group_compare_op_3> 
```

```
 <group_2> == <group_3>
```

---

### 评论 #2 (作者: LL87164, 时间: 1年前)

从分析师数据扩展到另类数据时，发现数据中的“中缀”可能也是一个具有经济学意义的参数。具体描述如下：

**ASI D1 Category:  [Other](https://platform.worldquantbrain.com/data/data-sets?category=other)  / AI/ML DATA 下：** 
三个字段 oth455_relation_roam_w1_pca_fact2_value、oth455_relation_roam_w2_pca_fact2_value 和 oth455_relation_roam_w5_pca_fact2_value 的描述均为“The 2nd eigenvalue of PCA, embedded using ROAM with relation data”，表明它们的核心含义一致：都是通过 ROAM 方法处理关系数据后，进行主成分分析（PCA），提取的第二主成分（PC2）对应的特征值（或相关值）。然而，它们的命名差异（w1、w2、w5）表明它们在某些方面存在不同。以下是可能的区别分析：

### 命名解析

字段名称的结构为 oth455_relation_roam_wX_pca_fact2_value，其中：

- relation：表示数据是关系型数据（例如，公司间竞争、合作或市场网络）。
- roam：指 ROAM 方法，用于嵌入或优化关系数据。
- wX：表示时间窗口（window），w1、w2、w5 分别对应不同的时间跨度（可能是 1 周、2 周、5 周）。
- pca_fact2：表示 PCA 的第二主成分（PC2），即第二特征值相关的值。
- value：表示该字段存储的是具体的值（可能是特征值、得分或其他量化结果）。

### 不同之处

基于命名和描述，三个字段的主要区别在于  **时间窗口（w1、w2、w5）** ，具体可能为：

- w1：可能表示 1 周（或 1 个时间单位）的数据窗口。例如，数据基于过去 1 周的关系数据进行 ROAM 嵌入和 PCA 分析。
- w2：可能表示 2 周的数据窗口，基于过去 2 周的关系数据。
- w5：可能表示 5 周的数据窗口，基于过去 5 周的关系数据。
- 时间窗口的不同会影响数据的平滑度和特征提取结果。较短的窗口（如 w1）可能更敏感于短期波动，而较长的窗口（如 w5）可能捕捉更稳定的长期模式。

验证：

用以下表达式通过遍历天数d，可以看出有明显信号的是22，因此判断w为周。

ts_delta(oth455_relation_roam_w5_pca_fact3_value, 22)

### 寻找信号

后续尝试套用之前的模版，进行不同时间窗口的行业标准化差异来寻找潜在的 Alpha 信号。

---

### 评论 #3 (作者: WL13229, 时间: 1年前)

[LL87164](/hc/en-us/profiles/28834270391959-LL87164)  这是我在这个系列里看到最有质量的评论

---

