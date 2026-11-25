# 【python alpha挑战赛】我的第一个python alpha经验分享

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/41505626370711
- **作者**: QQ68782
- **发布时间/热度**: 3个月前, 得票: 17

## 帖子正文

这是我的第一个的python alpha:

![图片](../images/img_dbd2101b62.png)

首先非常感谢这位大佬, 核心步骤都是按照这个来的:
【python alpha挑战赛】fast to python alpha skill
 [[L2] 【python alpha挑战赛】fast to python alpha skill经验分享_41449260982423.md]([L2] 【python alpha挑战赛】fast to python alpha skill经验分享_41449260982423.md)

下面分享下的我具体的操作过程

新建文件夹, 手动保存这几个网页:

- [https://platform.worldquantbrain.com/learn/documentation/consultant-information/getting-started-brain-python-alphas](https://platform.worldquantbrain.com/learn/documentation/consultant-information/getting-started-brain-python-alphas)
- [https://platform.worldquantbrain.com/learn/documentation/consultant-information/how-translate-fast-expression-alpha-python-alpha](https://platform.worldquantbrain.com/learn/documentation/consultant-information/how-translate-fast-expression-alpha-python-alpha)
- [[L2] Python alpha 提交经验分享经验分享_40734489248151.md]([L2] Python alpha 提交经验分享经验分享_40734489248151.md)
- [[L2] [Python Alpha 挑战赛] SKILL Regular to Python Alpha  稳定转写Python Alpha经验分享_41032955115927.md]([L2] [Python Alpha 挑战赛] SKILL Regular to Python Alpha  稳定转写Python Alpha经验分享_41032955115927.md)

手动保存是因为我的mcp上不了论坛 😂

我用的是claude code, 创建skills目录
.claude/skills/fast-to-python-alpha/SKILL.md, 粘贴原帖里的skill

mcp增加create_python_simulation方法, platform_functions.py 除了增加原帖里的代码, 还要增加个方法:

```
@mcp.tool()
async def create_python_simulation(
    python_code: str,
    region: str = "USA",
    universe: str = "TOP3000",
    neutralization: str = "INDUSTRY",
    lookback: int = 0,
) -> Dict[str, Any]:
    """
    🐍 Create a new Python simulation on BRAIN platform.

    Use this tool when you need to run a full Python alpha (not a FASTEXPR expression).
    Python alphas can include arbitrary logic, loops, data loading, etc.

    Args:
        python_code: Full Python alpha code to submit
        region: Market region (e.g., "USA")
        universe: Universe of stocks (e.g., "TOP3000")
        neutralization: Neutralization method (default "INDUSTRY")
        lookback: Lookback days for data (default 0)

    Returns:
        Simulation result with alpha details including id, sharpe, fitness, etc.
    """
    try:
        return await brain_client.create_python_simulation(
            python_code=python_code,
            region=region,
            universe=universe,
            neutralization=neutralization,
            lookback=lookback,
        )
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

```

打开claude code, 执行 /init, 让ai充分理解项目、掌握python alpha所有相关知识

挑选一个操作符少的alpha, 验证mcp能正常工作:

> 获取alpha详情, id=xxx

让ai改写:

> 使用fast-to-python-alpha, alpha_id = xxx

等待十几分钟, 可能转换失败, 换个alpha再次尝试, 经过几轮尝试, 终于转换成功

---

## 讨论与评论 (1)

### 评论 #1 (作者: FF45555, 时间: 2个月前)

第一个 python alpha 能跑通就赢一半了，你这套手动存文档 + claude code skill 绕开"MCP 上不了论坛"的操作很接地气（笑。你现在  **USA/TOP3000/INDUSTRY**  起步是最稳的选择，补两个我踩过的"第二步"坑，帮你少走弯路：

**第一，python alpha 最大的变化是 raw data 要自己洗。** fast 时代平台帮你处理了哨兵值，python 里你  `data.field[-1]`  直接拿到的可能混着 -1e20/NaN/Inf。量价字段先  `x[x<-1e20]=nan` ，比率字段要按分位数截断，不然一个脏值就能把整条截面算成 NaN。这个坑比调 region 更早暴雷。

**第二，别急着全 region 遍历，同字段跨 region 覆盖差很多。** 你 USA/TOP3000 覆盖高好上手，但换到 EUR 记得 universe 是  **TOP2500**  不是 TOP3000（我拿 TOP3000 查  `get_datafields`  直接 0 条）； `imbalance`  类在  **USA/TOP3000/D1**  覆盖 ~95%，到  **CHN**  只有 ~60%，裸搬会退化成只在六成票上成立。

**第三，delay 先 1 别碰 0。** delay0 是当天数据，坑多到劝退，先把 delay1、覆盖齐的 region 跑顺再谈花活。

接楼主：第一个跑通后，下一个就试试 python alpha 独有的  `store`  存昨天仓位来控换手——"今天维持昨天仓位"这种选项是 fast 给不了的杀器，也是你后面压 turnover 的最大依仗。加油（笑

---

