# 【Community Leader - 因子回测🔍】简洁优雅的给Simulator设定每日限额的方法

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/36798780424983
- **作者**: JL11546
- **发布时间/热度**: 10个月前, 得票: 3

## 帖子正文

在每日限额上线后，我们的Simulator请求的响应头会增加三个键分别是"x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset".

我根据x-ratelimit-remaining的键值设计了一套到达每日限额后停止的方法，兼容绝大多数目前的主流回测框架。

首先，在wqb或者machine_lib等api代码中的回测器类中增加两个属性：

```
self.daily_limit_reached = asyncio.Event()# 我设定为每日保留手动回测限额1000次，各位可以根据自己需求修改self.daily_limit_threshold = 1000
```

然后，在api代码中的simulator方法中增加解析响应头的功能：

```
# 检查每日限额if remaining := resp.headers.get("x-ratelimit-remaining"):    if int(remaining) <= self.daily_limit_threshold:        self.daily_limit_reached.set()       self.logger.warning(f"⚠️ 每日限额即将耗尽，剩余 {remaining} 次，停止回测")
```

最后，在Simulator代码中开启回测前检查daily_limit_reached事件：

```
if simulator.daily_limit_reached.is_set():    # 更新日志并退出   return
```

这样就可以做到较小的改动下增加每日限额停止的功能，希望能帮助到大家。最后祝各位研究和投资顺利。

---

## 讨论与评论 (2)

### 评论 #1 (作者: JM34387, 时间: 8个月前)

很好的回测限流方案，这样就可以有计划的每日回测了。

---

### 评论 #2 (作者: HY20507, 时间: 8个月前)

很好的方案，现在只需要开启并限制数量即可，不需要定闹钟了。
另外问一个蠢问题，了解wq比较晚，machine_lib这个文件在哪啊？论坛也一直没找到，只找到了修改此代码的相关帖子

---

