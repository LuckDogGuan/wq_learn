# Machine Alpha 基础知识6：模板的拓展——数据处理的重要性，继续以CAPM模型的思路为例

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/25526497127959
- **作者**: WL13229
- **发布时间/热度**: 2年前, 得票: 17

## 帖子正文

在前一篇系列文章👉 [Machine Alpha 基础知识5：模板的拓展——以CAPM模型的思路为例](Machine Alpha 基础知识5模板的拓展以CAPM模型的思路为例_25329078901911.md) 中，我们介绍了如何以CAPM模型的思路拓展模板。本文今天的讨论重点是将焦点转向 Beta 系数及数据处理（Beta 衡量的是股票相对于其群组的波动性，提供了其相较于同行的相对风险的信息）。

承接本系列前文，Brain 表达中的 CAPM Beta：

```
ts_regression(returns, group_mean(returns, ts_mean(cap, 21), 252, rettype=2))
```

通过将  `rettype`  设置为2，您将得到回归方程的斜率。

实现和扩展： 为了进一步应用这个想法，请在模板框架内进行:

1. 数据准备：与任何数据科学实验一样，干净和准确的数据非常重要。首先进行数据预处理步骤，例如：

```
target_data = winsorize(ts_backfill(<target_data>, 63), std=4.0);
market_data = winsorize(ts_backfill(<market_data>, 63), std=4.0);
```

1. 计算分组 Beta：这次，不是看残差，而是比较群组之间的斜率/Beta（例如，行业或产业）以得出不同的市场洞见：

```
target_beta = ts_regression(target_data, group_mean(market_data, log(ts_mean(cap, 21)), sector), 252, rettype=2);
```

完整的模板形式如下：

```
target_data = winsorize(ts_backfill(<target_data>, 63), std=4.0);
market_data = winsorize(ts_backfill(<market_data>, 63), std=4.0);
target_beta = ts_regression(target_data, group_mean(market_data, log(ts_mean(cap, 21)), sector), 252, rettype=2);
target_beta
```

该模板捕捉了个别股票与其相应群组之间的联动。请在下方分享您认为在此模板下效果最佳的数据集！期待您的想法和发现。

---

## 讨论与评论 (3)

### 评论 #1 (作者: LL81909, 时间: 10个月前)

如果我在2个不同类型数据集都能提交不少regular alpha 并且sharp 能去到2到3，fitness 大于2。 是说明这个模版泛化能力比较强，还只是我运气比较好？

---

### 评论 #2 (作者: ZZ26913, 时间: 9个月前)

```
ts_regression(<data_fields>, group_mean(market_data, log(ts_mean(cap, 21)), sector), 252, rettype=2)
```

该模板与上篇文章中模板的关键区别在于：该模板求得的是回归模型的beta系数（β）。该系数表达的是 X 每增加一个单位，Y 的预期变化幅度。这是单个股票的该数据字段与其所在板块或行业中按市值为权重的均值之间的斜率。

其中，市值做了21天的平滑。板块或行业可切换下范围。回归的追溯日期可根据所用数据字段的特性调整为：21，63，126等区间。

最终得到的斜率越大，代表该股票在该字段上有着越大的变化幅度，根据字段本身的特性，这可能会体现出某种Alpha信号。

---

### 评论 #3 (作者: WC64477, 时间: 8个月前)

现在在group_mean里使用log(ts_mean(cap, 21))这种权重都会报平台困难，

- WorldQuant BRAIN is experiencing some difficulties. Please contact  [support](/hc)  if this problem persists.

---

