# 【Alpha灵感】Forecasting Default with the KMV-Merton Model

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/29155767547543
- **作者**: JL11546
- **发布时间/热度**: 1年前, 得票: 28

## 帖子正文

本篇文章基于论文 [*Forecasting Default with the KMV-Merton Model*](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=637342) 的研究结果简化而成

1. Alpha核心思路：
   论文评估了基于KMV-Merton模型的企业违约概率预测能力，该模型以Merton(1974)的债券定价模型为基础。KMV-Merton模型假设企业的权益是对其总价值的看涨期权，其行权价格等于公司债务的面值。论文通过比较KMV-Merton模型与更简单的替代模型，发现后者在预测违约和样本外测试中表现略优。我将论文中的思路基于平台的operators和数据集做了相应的简化，最终表达为对违约概率数据进行排序，并对违约概率数据进行分桶化处理，基于分桶后的违约概率对数据进行中性化，最后排序得到最终因子。
2. Alpha Setting

- Region: USA
- Universe: TOP3000
- Neutralization: Subindustry
- Delay: 1
- Decay: 5
- Truncation: 0.08

3. Alpha Performance

![图片](../images/img_0b5a4ef9fd.png)

Alpha的表现符合Sharpe>1.3, turnover<50%, return>8%, fitness>0.7, pro-corr<0.65的要求，并且达到了可以提交的标准。

4. 增强Alpha的信号，以及其他不同的探索与尝试

我测试了不同的region和dataset，发现该表达式在其他的region和category上有交强的泛化性，具备模板化的价值。

5. 可提交的版本：同上图alpha。

6. Alpha的模板：

```
signal = ts_rank(winsorize(ts_backfill(<data>, 120), std=4), 60);credit_quality = bucket(rank(ts_delay(signal, 1), range='0.2, 1, 0.2')；final_signal = group_neutralize(ts_weighted_decay(signal, k=0.5), credit_quality);-rank(final_signal)
```

7. Alpha模板的产能：进行了大约1万次回测，产生了6个可提交的alpha，分布在USA，GLB，KOR等区域。

8. Alpha的稳健性检测：我调整了不同的region, universe, decay和truncation均可以产生较强信号。

9. 探索该Alpha遇到的困难与踩过的坑：平台上数据的关键字搜索给的范围比较广，数据找起来比较麻烦，未来数据字段信息也有必要进行本地服务器保存，不仅有利于数据搜索也为将来探索大模型挖掘alpha提供准备。

---

## 讨论与评论 (2)

### 评论 #1 (作者: JL11546, 时间: 1年前)

补充其他region因子表现;

![图片](../images/img_2e415d1dbf.png)

---

### 评论 #2 (作者: YW10763, 时间: 1年前)

```
signal = ts_rank(winsorize(ts_backfill(<data>, 120), std=4), 60);credit_quality = bucket(rank(ts_delay(signal, 1), rate = 0), range='0.2, 1, 0.2')；final_signal = group_neutralize(ts_weighted_decay(signal, k=0.5), credit_quality);-rank(final_signal)
```

部分错误已纠正 可以看一下这个

---

