# 【QUANT101】什么是 Non-Compensated Alpha? 如何筛选 Compensated Alpha？

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/39354351739415
- **作者**: ZH87224
- **发布时间/热度**: 6个月前, 得票: 6

## 帖子正文

最近在优化 OsmosisPoints，用代码给因子打分的时候突然遇到接口报错：BadRequestError: {'message': {'osmosisPoints': ['Cannot update Osmosis points for non-compensated alpha.']}}

在中文区、国际区、文档&帮助检索之后，大概意思就是这个因子是未计费的，回忆了一下这个因子当时提交时应该是超出了每天 4 个的限额，这种因子是没有收益的，并且不能分配 OsmosisPoints的，虽然在我的评估体系里这个是个优质因子，但很遗憾还是要跳过。

那么我们应该如何跳过这类因子呢？打开这个因子页面，发现如下 WARNING：

![图片](../images/img_25b50bba04.png)

既然出现在 WARNING 区，那就好办了，我们从接口回传的因子原始数据中可以定位到：

```
'os': {'checks': [{'name': 'SUB_UNIVERSE_SHARPE', 'result': 'PENDING'}, {'name': 'NEW_HIGH', 'result': 'PENDING'}, {'name': 'SUPER_UNIVERSE_SHARPE', 'result': 'PENDING'}, {'name': 'SHARPE', 'result': 'PENDING'}, {'name': 'IS_SHARPE', 'result': 'PENDING'}, {'name': 'PROD_CORRELATION', 'result': 'PENDING'}, {'name': 'CONCENTRATED_WEIGHT', 'result': 'PENDING'}, {'name': 'COMPENSATED_ALPHA', 'result': 'WARNING'}, ...
```

那个 COMPENSATED_ALPHA 就是这类因子的警告标签，跟因子提交检测时常用的那些 Check 不同，那些都是在 IS.Checks 里，这个只有在 OS.Checks 里才会出现，所以可能会被忽略。

由于接口返回的checks信息是个List，不太好操作，我们先执行如下变换，然后检查COMPENSATED_ALPHA：

```
os_checks = {
    check_["name"]: {k: v for k, v in check_.items() if k != "name"}
    for check_ in _alpha.record_raw["os"]["checks"]
}

"COMPENSATED_ALPHA" in os_checks and os_checks["COMPENSATED_ALPHA"][
    "result"
] == "WARNING"

```

之前确实没注意到 OS-Checks，只处理了IS-Checks，后续可以将OS-Checks也加到本地因子库中。

> 因子库搭建可以参考： [【QUANT101】手把手教你搭建本地因子库]([L2] 【Quant101】手把手教你搭建本地因子库 ①经验分享_39213565539095.md)

---

## 讨论与评论 (5)

### 评论 #1 (作者: MP35172, 时间: 5个月前)

原来超出每日4个限额的Alpha没法分配OsmosisPoints，哪怕因子本身质量不错也不行！之前我也遇到过类似报错，查了半天文档没搞懂，看完你的排查过程终于明白了。看来提交时得优先把高置信度的因子放进计费名额里，新手真的容易踩这个坑，感谢分享避坑经验！

---

### 评论 #2 (作者: BW14163, 时间: 5个月前)

感谢分享，还从来没遇到过这种情况，学到了

---

### 评论 #3 (作者: XX81632, 时间: 4个月前)

感谢分享，得到了解决方案

---

### 评论 #4 (作者: MY27687, 时间: 2个月前)

这篇文章解决了实际开发中的一个痛点——我之前也遇到过类似的 OsmosisPoints 报错，查了半天没找到原因。你的排查思路很清晰：从接口报错信息定位到 COMPENSATED_ALPHA 这个 OS-level check，然后给出代码层面的过滤方法。

补充一个实操建议：如果你在做批量因子评估时，可以在提交前先用 `get_submission_check` API 跑一遍目标 alpha 的检查结果，提前筛掉 COMPENSATED_ALPHA = WARNING 的因子，避免浪费提交额度。另外，超出每日限额的因子虽然不能分配 OsmosisPoints，但如果信号质量确实好，可以考虑换个 universe 或者调整 neutralization 参数重新提交——有时候换一个区域（比如从 USA 切到 GLB）就能避开限额问题，同时因子逻辑依然成立。

最后，把 OS.Checks 也纳入本地因子库是个很好的做法，很多开发者只关注 IS.Checks，忽略了 OS 层面的补偿状态，后续排查问题时容易踩坑。

---

### 评论 #5 (作者: QQ38141, 时间: 6天前)

楼主从 OS.Checks 捞 COMPENSATED_ALPHA 这步我踩过同类坑：超额提交的因子进入 non-compensated，IS 质量再高也拿不到 OsmosisPoints。我的处理是把计费状态当硬门槛而非过滤项——本地因子库每天先查 COMPENSATED_ALPHA 再排提交优先级，把额度留给可计费因子。另外你提到 IS.Checks 与 OS.Checks 分开，我这边是每天批量对账两者，IS 达标但 OS 未决的因子一律不进组合。

---

