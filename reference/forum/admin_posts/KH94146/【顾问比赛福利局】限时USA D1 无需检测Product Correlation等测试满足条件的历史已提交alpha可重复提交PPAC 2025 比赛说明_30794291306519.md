# 【顾问比赛福利局】限时USA D1 无需检测Product Correlation等测试，满足条件的历史已提交alpha可重复提交。PPAC 2025 比赛说明

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/30794291306519
- **作者**: KH94146
- **发布时间/热度**: 1年前, 得票: 7

## 帖子正文

更多FAQ 请见 [https://support.worldquantbrain.com/hc/en-us/categories/30786312681239-Power-Pool-Alphas-Competition-PPAC-2025](/hc/en-us/categories/30786312681239-Power-Pool-Alphas-Competition-PPAC-2025)

## 比赛规则

### 1.1 关键日期：

- **24 Mar 2025:**  Alpha Submissions start
- **13 Apr 2025** : Cutoff for Mid Competition Semi OS snapshot score
- **15 Apr 2025** : Publish Mid Competition Semi OS snapshot scoring date
- **4 May 2025** : Alpha Submissions end
- **15 May 2025** : Final Results

### **1.2 比赛奖金**

**COMPETITION Final Rankings:
• 1st place – US$ 5,000
• 2nd place – US$ 3,000
• 3rd place – US$ 2,000
• 4th – 10th place – US$ 1200 each
• 11th – 25th place – US$ 700 each
• 26th – 50th place – US$ 300 each
• 51st – 100th place – US$200 each
• In addition, the top 3 consultants (excluding those who were in the Top 100 globally) from each eligible country or region may be eligible for – US$ 100 each**

### **1.3 什么Alpha 符合要求？**

- USA Delay 1
- use fewer than 8 operators （含8个）;
- use fewer than 3 datafields（含3个）;
- self correlation of less than 0.5 （Pool内）.
- Super Alpha 不符合比赛要求
- 符合参赛标准的alpha会在IS结果中展示标签

 **1.4 参加比赛的alpha是否符合base payment、quarterly payment、Genius Program? 是否会计入Value Factor**

是的、可以参加比赛的同时获得正常payment，并累计quarterly payment 天数和Genius Program, 提交的alpha也会影响Value Factor，符合条件的alpha也有可能进入Product

**1.5 评分标准**

从您选择的Power Pool阿尔法中，我们根据成分阿尔法的历史回报和波动性创建一个智能组合。这个阿尔法的夏普比率是adj_metairbc。 **当我们在这个阿尔法上应用交易成本和各种费用时，** 我们得到的是一个可实现的损益，其夏普比率是adj_metairac。我们将这两个比率都按这些数字的总体最小值和最大值缩放到0到1之间，并取平均值得到IS分数。对于您提交的每一个新的Power Pool阿尔法，分数将在不到4小时内更新。OS分数也是以类似的方式计算的，但您只能在中期竞赛OS揭晓（4月15日）时看到它。最终分数将是0.25×IS分数+0.75×OS分数。

![图片](../images/img_ebcd14057a.png)

**1.6  我如何知道alpha是否符合了alpha pool**

![图片](../images/img_7c5839b2e2.png)

**1.7 比赛分数显示？**

**排行榜每四小时刷新，当提交了超过10个pool内alpha后开始显示比赛分数。注意和以往比赛一样，排行榜仅显示IS分数，最终分数为IS*0.25 + OS*0.75**

**1.8 保持合理数量？**

在比赛初期无需考虑数量问题，但随着数量过多（148+） 会有更高的penalty。详情请见FAQ内

## **BeforeCost Penalty:**

- Formula: min(0.01 * ln(1 + alpha_count), 0.05)
- Minimum penalty: 0.024 (for 10 alphas)
- Mostly linear after 30 alphas, with a penalty of ~0.00013 IR (Sharpe of 0.0021) for each additional alpha
- Capped at 0.05

 **Alpha Count** 
 **BeforeCost Penalty** 

10
0.023979

30
0.03434

60
0.041109

100
0.046151

148+
0.05

## **AfterCost Penalty:**

- Formula: min(0.003 * ln(1 + alpha_count), 0.015)
- Minimum penalty: 0.007194
- Capped at 0.015

 **Alpha Count** 
 **AfterCost Penalty** 

10
0.007194

30
0.010302

60
0.012333

100
0.013845

148+ 0.015

**1.9每日提交上限是否还是4个？**

是的

**1.10 已提交alpha是否可以移除Pool内？**

符合条件的提交alpha会被打上Power Pool Selected的tag，移除tag即可。这在比赛后期调整自己的pool会起到至关重要的作用

---

## 讨论与评论 (4)

### 评论 #1 (作者: JL67084, 时间: 1年前)

在哪里移除tag

---

### 评论 #2 (作者: WS55742, 时间: 1年前)

![图片](../images/img_836455cf1a.png)

![图片](../images/img_53d904a980.png)

点击叉号就可以移除tag

[JL67084](/hc/en-us/profiles/28860513004567-JL67084)

---

### 评论 #3 (作者: JL67084, 时间: 1年前)

好的

---

### 评论 #4 (作者: ML42552, 时间: 1年前)

努力一下，提升自己的diversity，也能拿到更高的收入！

---

