# Python alpha官方webinar视频代码补档：ACO + Online alphas

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42061123738903
- **作者**: RM49262
- **发布时间/热度**: 2个月前, 得票: 55

## 帖子正文

## **Part 1：Ant Colony Optimization**

ACO，全称 Ant Colony Optimization，蚁群优化，是一种启发式全局优化算法。它的核心思想是：在离散参数空间中，通过“信息素”机制不断调整搜索概率，使搜索过程逐步从随机探索转向对高收益区域的集中利用。

这里的 “蚁群” 不是交易策略本身，而是一个参数搜索器。它在帮你回答这种问题：

> 均值反转 Alpha 里， `lookback`  用 5、10、21、63 还是 126？
> winsorize 的上下界用  `0.01/0.99`  还是  `0.05/0.95` ？
> 哪些组合在 Brain 回测里表现更好？

它的流程大概是：

1. **定义参数空间**

```
param_grid = {
    'lookback': [5, 10, 21, 42, 63, 126],
    'win_lo': [0.01, 0.02, 0.05],
    'win_hi': [0.95, 0.98, 0.99],
}
```

这些就是要搜索的候选参数。

1. **给每个参数值初始化“信息素”**
   比如一开始：

```
lookback=5      pheromone=1.0
lookback=10     pheromone=1.0
lookback=21     pheromone=1.0
...
```

信息素越高，后面被抽中的概率越大。

1. **每一代生成多个“蚂蚁”**
   每只蚂蚁其实就是一个参数组合，比如：

```
{'lookback': 21, 'win_lo': 0.02, 'win_hi': 0.98}
```

代码用  `pheromone.sample()`  按信息素权重随机抽参数。

1. **拿这个参数组合跑一次 Brain 回测**
   核心在这里：

```
result = simulate_params(params)
```

`simulate_params`  会根据参数构造一个 alpha：

```
raw = -np.nanmean(data.returns, axis=0)
raw = pasteurize(raw, data.universe[-1])
raw = winsorize(raw, lo=wlo, hi=whi)
return scale(neutralize(raw)).astype(np.float32)
```

这其实是一个简单的 **均值反转 Alpha** ：最近收益越高，信号越偏空；最近收益越低，信号越偏多。

然后它跑回测，算：

```
sharpe
returns
drawdown
pnl
```

1. **根据表现更新信息素**
   每一代结束后，它找出 Sharpe 最高的几个参数组合：

```
top = sorted(results, key=lambda r: r['sharpe'], reverse=True)[:top_k]
```

然后给这些组合里用到的参数值增加信息素：

```
self.pheromone[(name, idx)] += score
```

表现越好的参数组合，会让它用到的参数值以后更容易被抽中。

同时所有信息素都会衰减：

```
self.pheromone[key] *= (1.0 - evaporation_rate)
```

这叫 evaporation，防止算法太早锁死在某个参数上。

最后它输出 top 参数组合和信息素分布。

所以一句话说：

**这段 ACO 代码是在用“表现好的参数会留下更多信息素”的机制，逐代偏向更可能产生高 Sharpe 的 Alpha 参数组合。**

它和遍历的区别在于： **遍历是把所有组合都试一遍；ACO 是边试边学习，把算力逐渐集中到更有希望的区域。**

官方视频中的代码如下：

```
import randomimport numpy as npimport numpy.typing as nptimport pandas as pdfrom brain import Brain, BrainCachefrom brain.alphas import alphafrom brain.simulation import SimulationSettingsclass PheromoneMatrix:    """Tracks pheromone levels for each parameter value."""    def __init__(self, param_grid: dict):        """        param_grid: {'lookback': [5, 10, 21, 63], 'win_lo': [0.01, 0.05]}        """        self.param_grid = param_grid        # Initialize pheromone uniformly        self.pheromone = {}        for name, values in param_grid.items():            for i in range(len(values)):                self.pheromone[(name, i)] = 1.0    def sample(self, alpha_weight=2.0) -> dict:        """Sample one parameter combination via pheromone-weighted roulette."""        params = {}        for name, values in self.param_grid.items():            weights = np.array([                self.pheromone[(name, i)] ** alpha_weight                for i in range(len(values))            ])            weights /= weights.sum()            idx = random.choices(range(len(values)), weights=weights, k=1)[0]            params[name] = values[idx]        return params    def update(self, results, evaporation_rate=0.3, deposit_weight=1.0, top_k=5):        """Evaporate all pheromone, then deposit for top-k results."""        # Evaporate        for key in self.pheromone:            self.pheromone[key] *= (1.0 - evaporation_rate)        # Deposit for top-k        top = sorted(results, key=lambda r: r['sharpe'], reverse=True)[:top_k]        for r in top:            score = max(0.0, r['sharpe']) * deposit_weight            for name, values in self.param_grid.items():                val = r['params'][name]                if val in values:                    idx = values.index(val)                    self.pheromone[(name, idx)] += score    def summary(self):        """Print pheromone levels for inspection."""        for name, values in self.param_grid.items():            print(f"\n{name}:")            levels = [(values[i], self.pheromone[(name, i)]) for i in range(len(values))]            for val, pher in sorted(levels, key=lambda x: -x[1]):                print(f"  {val}: {pher:.3f}")brain = Brain()cache = BrainCache(brain)def pasteurize(a, universe):    # Sets values outside universe to nan    passdef neutralize(a):    # Removes cross-sectional mean to make the signal market-neutral    passdef scale(a):    # Scales the signal to unit notional (L1 norm = 1)    passdef winsorize(a, lo=0.05, hi=0.95):    # Clips extreme values at specified percentiles to reduce outlier impact    passdef ts_mean(a, lb):    # Computes time-series mean over the last 'lb' periods    passparam_grid = {    'lookback': [5, 10, 21, 42, 63, 126],    'win_lo': [0.01, 0.02, 0.05],    'win_hi': [0.95, 0.98, 0.99],}aco_config = {    'generations': 10,    'population': 15,  # ants per generation    'evaporation_rate': 0.3,    'deposit_weight': 1.0,    'top_k': 5,    'alpha_weight': 2.0,  # higher = greedier selection}def simulate_params(params):    """Run one BrainLabs simulation with given parameters and return stats."""    lb = params['lookback']    wlo = params['win_lo']    whi = params['win_hi']    @alpha(data=["returns"], store=[])    def aco_alpha(data, store) -> npt.NDArray[np.float32]:        raw = -np.nanmean(data.returns, axis=0)        raw = pasteurize(raw, data.universe[-1])        raw = winsorize(raw, lo=wlo, hi=whi)        return scale(neutralize(raw)).astype(np.float32)    settings = SimulationSettings(        instrument_type='EQUITY', region='USA', delay=1,        universe='TOP3000', lookback=lb, visualization=False,    )    am = brain.generate_alpha_matrix(aco_alpha, settings, cache)    pos = brain.generate_alpha_positions(am, settings, cache)    pnl_arr = brain.generate_alpha_stats(pos, settings, cache)    pnl = pd.Series(np.asarray(pnl_arr).ravel())    std = pnl.std()    sharpe = pnl.mean() / std * 250**0.5 if std > 0 else 0    ret = pnl.mean() * 250 * 2    cumsum = pnl.cumsum()    dd = (cumsum.cummax() - cumsum).max() * 2    return {        'params': params,        'sharpe': sharpe,        'returns': ret,        'drawdown': dd,        'pnl': pnl,    }pheromone = PheromoneMatrix(param_grid)all_results = []for gen in range(aco_config['generations']):    gen_results = []    for _ in range(aco_config['population']):        params = pheromone.sample(alpha_weight=aco_config['alpha_weight'])        result = simulate_params(params)        gen_results.append(result)    # Update pheromone    pheromone.update(        gen_results,        evaporation_rate=aco_config['evaporation_rate'],        deposit_weight=aco_config['deposit_weight'],        top_k=aco_config['top_k'],    )    all_results.extend(gen_results)    # Log    scores = [r['sharpe'] for r in gen_results]    print(f"Gen {gen}: n={len(scores)} | mean={np.mean(scores):.3f} | top={max(scores):.3f}")# --- Inspect results ---print(f"\nTotal simulations: {len(all_results)}")top5 = sorted(all_results, key=lambda r: r['sharpe'], reverse=True)[:5]for r in top5:    print(f"  {r['params']} -> Sharpe={r['sharpe']:.3f}")print("\n=== Pheromone Summary ===")pheromone.summary()
```

## **Part 2：Online alphas**

Online Alpha 是一种在线自适应 Alpha 组合方法。它不是在回测开始前固定选择一个参数版本，而是在 Alpha 运行过程中，同时维护多个候选子策略，并根据这些子策略近期的实际表现动态调整权重。

它做的的是另一件事： **不是提前选一个固定参数，而是在回测运行过程中，动态决定“今天更信哪个参数版本”。**

它有点像一个小型 ensemble / 动态加权器。

比如视频里有几个 lookback：

```
LOOKBACKS = [5, 10, 21, 63]
```

它不是只选一个：

```
只用 lookback=21
```

而是每天同时生成 4 个 alpha 子信号：

```
lookback=5  的均值反转信号
lookback=10 的均值反转信号
lookback=21 的均值反转信号
lookback=63 的均值反转信号
```

然后根据这些子信号最近一段时间的表现，给它们分配权重：

```
最近 lookback=5 表现好  -> 权重提高
最近 lookback=63 表现差 -> 权重降低
```

最后把它们混合成一个最终持仓：

```
blended += store.weights[s] * positions[s]
```

核心流程是：

1. **保存昨天各个子策略的持仓**

```
store.prev_positions
```

1. **今天来了新的收益率以后，计算昨天持仓今天赚了多少**

```
day_pnl = np.nansum(store.prev_positions[s] * today_returns)
```

也就是给每个 lookback 子策略记一条每日 PnL。

1. **把最近 252 天 PnL 放进 buffer**

```
store.pnl_buffer
```

252 大概是一年交易日。

1. **每个子策略算 rolling Sharpe**

```
sharpes[s] = pnl_slice.mean() / std * 250**0.5
```

1. **Sharpe 越高，权重越高**

```
store.weights = sharpes / total
```

如果最近没有谁明显好，就平均分配。

1. **按权重混合今日信号**

```
blended += store.weights[s] * positions[s]
```

官方视频代码如下：

```
import numpy as npimport numpy.typing as nptfrom brain.alphas import alpha# Configuration: parameter sets to blendLOOKBACKS = [5, 10, 21, 63]N_SETS = len(LOOKBACKS)WINDOW = 252  # rolling window for Sharpe (1 year)@alpha(    data=["returns"],    store=["prev_positions", "pnl_buffer", "day_count", "weights"],)def online_alpha(data, store) -> npt.NDArray[np.float32]:    n_inst = data.returns.shape[1]    # --- Initialize store on first call ---    if getattr(store, 'day_count', None) is None:        store.prev_positions = np.zeros((N_SETS, n_inst), dtype=np.float32)        store.pnl_buffer = np.zeros((WINDOW, N_SETS), dtype=np.float32)        store.day_count = np.array([0], dtype=np.int64)        store.weights = np.ones(N_SETS, dtype=np.float32) / N_SETS    t = int(store.day_count[0])    today_returns = data.returns[-1]    # --- Track per-set PnL from yesterday's positions ---    if t > 0:        for s in range(N_SETS):            day_pnl = float(np.nansum(store.prev_positions[s] * today_returns))            store.pnl_buffer[t % WINDOW, s] = day_pnl    # --- Compute positions for each parameter set ---    positions = np.zeros((N_SETS, n_inst), dtype=np.float32)    for s, lb in enumerate(LOOKBACKS):        # Mean reversion with this lookback        # (data.returns may have fewer rows than lb in early days - handle gracefully)        actual_lb = min(lb, data.returns.shape[0])        raw = -np.nanmean(data.returns[-actual_lb:], axis=0)        raw[np.isnan(raw)] = 0.0        a0 = np.nan_to_num(raw, nan=0)        raw -= np.mean(a0)        norm = np.linalg.norm(a0, ord=1)        if norm > 0:            raw /= norm        positions[s] = raw    store.prev_positions = positions    # --- Update weights from rolling Sharpe ---    if t >= WINDOW:        sharpes = np.zeros(N_SETS)        for s in range(N_SETS):            pnl_slice = store.pnl_buffer[:, s]            std = pnl_slice.std()            if std > 0:                sharpes[s] = max(0.0, pnl_slice.mean() / std * 250**0.5)        total = sharpes.sum()        if total > 0:            store.weights = sharpes / total        else:            store.weights = np.ones(N_SETS, dtype=np.float32) / N_SETS    # --- Blend positions ---    blended = np.zeros(n_inst, dtype=np.float32)    for s in range(N_SETS):        blended += store.weights[s] * positions[s]    store.day_count[0] += 1    return blended.astype(np.float32)@alpha(    data=["returns"],    store=["prev_positions", "pnl_buffer", "day_count", "weights", "weight_log"],)def online_alpha_with_logging(data, store) -> npt.NDArray[np.float32]:    n_inst = data.returns.shape[1]    if getattr(store, 'day_count', None) is None:        store.prev_positions = np.zeros((N_SETS, n_inst), dtype=np.float32)        store.pnl_buffer = np.zeros((WINDOW, N_SETS), dtype=np.float32)        store.day_count = np.array([0], dtype=np.int64)        store.weights = np.ones(N_SETS, dtype=np.float32) / N_SETS        # Log weights at each step (pre-allocate for expected days)        store.weight_log = np.zeros((2000, N_SETS), dtype=np.float32)    t = int(store.day_count[0])    today_returns = data.returns[-1]    if t > 0:        for s in range(N_SETS):            day_pnl = float(np.nansum(store.prev_positions[s] * today_returns))            store.pnl_buffer[t % WINDOW, s] = day_pnl    positions = np.zeros((N_SETS, n_inst), dtype=np.float32)    for s, lb in enumerate(LOOKBACKS):        actual_lb = min(lb, data.returns.shape[0])        raw = -np.nanmean(data.returns[-actual_lb:], axis=0)        raw[np.isnan(raw)] = 0.0        a0 = np.nan_to_num(raw, nan=0)        raw -= np.mean(a0)        norm = np.linalg.norm(a0, ord=1)        if norm > 0:            raw /= norm        positions[s] = raw    store.prev_positions = positions    if t >= WINDOW:        sharpes = np.zeros(N_SETS)        for s in range(N_SETS):            pnl_slice = store.pnl_buffer[:, s]            std = pnl_slice.std()            if std > 0:                sharpes[s] = max(0.0, pnl_slice.mean() / std * 250**0.5)        total = sharpes.sum()        if total > 0:            store.weights = sharpes / total        else:            store.weights = np.ones(N_SETS, dtype=np.float32) / N_SETS    if t < store.weight_log.shape[0]:        store.weight_log[t] = store.weights    blended = np.zeros(n_inst, dtype=np.float32)    for s in range(N_SETS):        blended += store.weights[s] * positions[s]    store.day_count[0] += 1    return blended.astype(np.float32)def plot_weight_evolution(weight_log, n_days):    import matplotlib.pyplot as plt    # The Alpha matrix stores the final store state    # Access weight_log from the last call's store    # (Alternatively, save weight_log to a file during the run)    # For visualization, assuming you have weight_log as a numpy array:    fig, ax = plt.subplots(figsize=(12, 4))    for i, lb in enumerate(LOOKBACKS):        ax.plot(weight_log[:n_days, i], label=f'lb={lb}')    ax.axvline(x=WINDOW, color='gray', linestyle='--', label='Warm-up end')    ax.set_xlabel('Trading Day')    ax.set_ylabel('Weight')    ax.set_title('Online Alpha: Weight Evolution')    ax.legend()    plt.tight_layout()    plt.show()
```

---

## 讨论与评论 (10)

### 评论 #1 (作者: LA79055, 时间: 2个月前)

文章把 ACO 中的信息素更新、蒸发机制和参数搜索之间的关系解释得很清楚，也说明了它与穷举搜索的差别。对想把参数调整从手工试错变成有记录流程的人很有参考价值。若能补充如何留出独立验证集，会更有助于避免只在同一批回测上追逐高分。

---

### 评论 #2 (作者: ZY88181, 时间: 2个月前)

感谢大佬分享，先学为敬。

---

### 评论 #3 (作者: JG15244, 时间: 2个月前)

感谢分享这段很清晰的代码实现。对  `online_alpha`  部分有一点想确认：

- `prev_positions`  在当天 signal 生成后直接被覆盖为当天的 positions，然后下一交易日用  `prev_positions`  乘以  `today_returns`  来计算 PnL。这意味着持仓实际上是假设在当天收盘时建立，并在次一交易日以全天收益结算——如果回测框架用的是 bar-by-bar 的逐笔逻辑，这种交收方式需要和  `delay`  设置对齐。（代码中 ACO 部分用了  `delay=1` ，但 online alpha 的  `@alpha`  中没有设置 delay，可能默认为 0，这里时序可能需要额外确认。）

---

### 评论 #4 (作者: GC81559, 时间: 2个月前)

关于  **model109**  的  `gr_`  前缀字段：这些是增长率的 VECTOR 字段，coverage 约 0.83，crowding 低。推荐  `vec_max`  聚合（取最大增长率），配合  `-ts_sum(ts_zscore(x, 5), 120)`  构建中周期反转信号。这个组合在 GLB/TOPDIV3000 上 PC 约 0.6，比 analyst 类字段更低。

---

### 评论 #5 (作者: HH34943, 时间: 2个月前)

这硬核科普太及时了！看官方视频里的这之前那段代码，脑子里一团糊涂，楼主一句“ACO是离线超参数搜索器，在线是在线动态加权”简直醍醐灌顶。

实际上在平台上跑策略，最怕的就是无脑难度导致严重过批次，选出来的“最强参数”往往一到OS（样本外）就崩盘。审视这一思路彻底打开了：可以先用ACO跑代做前置降维，把筛出来的几组低性“精英参数”完全相关作为底仓，再喂给在线框架根据近期盈亏做动态权重分配。这种把全局寻优化和自适应的架构太完美了，马上拿去改我手头的均值焦点策略，感谢大佬喂饭级教学！

--------------------------------------------------感谢大佬分享-----------------------------------------------------------------------------

---

### 评论 #6 (作者: PZ64174, 时间: 2个月前)

感谢补档官方webinar的代码，ACO做参数搜索这个思路在BRAIN平台上很实用。我之前也尝试过用网格搜索来优化lookback和winsorize参数，但参数组合一多模拟次数就爆炸了，ACO的信息素机制确实比暴力搜索高效很多。分享一点我的实践经验：在实现ACO时，信息素的蒸发系数设置对搜索效率影响很大，我测试过0.3到0.9的范围，发现0.5左右在BRAIN平台上效果最好，太低容易陷入局部最优，太高则收敛太慢浪费模拟资源。另外建议在每轮蚂蚁评估时加入一个简单的预过滤，比如先检查参数组合是否满足基本的金融逻辑比如lookback不能大于数据窗口的一半，这样能减少无效模拟。关于Online alphas部分，实时更新参数的能力和store机制天然契合，用store保存历史信息素权重，每日增量更新，可以避免全量重算的开销。

---

### 评论 #7 (作者: JR57542, 时间: 2个月前)

ACO 当参数搜索器（信息素沉积/蒸发）比暴力 grid 高效，但参数搜索本身治标——真正决定 alpha 上限的是信号源（字段族）不是参数，ACO 找到的高 IS 参数区在 OS 常不迁移。Online alpha 的 store 状态机确实是 Python 区别于 FastExpr 的核心杠杆（跨日增量更新 FastExpr 写不出）。

但 LOOKBACKS=[5,10,21,63] 四子信号那个隐藏陷阱要特别强调：本质是同一 returns 序列的窗口变体，PnL 高度同源，加权混合几乎不降 PC/SC（BRAIN 相关性看近四年日度 PnL）。真正降相关必须换信号源（字段/数据集），不是同源参数加权——这条和我们量价 PC 墙的结论一致。

---

### 评论 #8 (作者: MY27687, 时间: 2个月前)

感谢补档，这两个主题放在一起其实有更深层的协同逻辑，补充一个视角：
ACO 产出的不是单一最优参数，而是一个「候选参数池 + 信息素分布」——这和 Part 2 的 Online alpha 天然对接。与其在 ACO 最后只取 top-1 参数去提交一个固定 alpha，不如把 ACO 收敛后的 top-N 参数组（比如 lookback ∈ {21, 42, 63}）直接作为 Online alpha 的 LOOKBACKS 候选集。这样 ACO 负责离线阶段筛选有潜力的参数区域，Online alpha 负责在线阶段根据近期市场状态动态切换权重，相当于把「参数搜索」和「参数自适应」串成一个 pipeline，避免 ACO 选出来的参数只在回测期好用的问题。实操上需要注意：ACO 的 top-N 之间信息素差异不宜过大（可通过调低 alpha_weight 或提高 evaporation_rate 来控制），否则收敛太集中，Online alpha 阶段退化成单信号，失去 ensemble 意义。

---

### 评论 #9 (作者: QW94165, 时间: 1个月前)

补档很及时，正好把 ACO 信息素机制和 Online Alpha 的 store 状态机这两块一起看，思路连得上。几个跟代码相关的点想确认一下：

1. ACO 的  `simulate_params`  里你直接拿  `pnl.mean() / std  250*0.5`  当 Sharpe，没做 annualized risk-free 或年化窗口对齐，用 0 附近的负 Sharpe 也会被  `max(0.0, sharpe)`  直接截掉。这块和官方给的指标口径一致吗，还是你这边自己换的？

1. Online Alpha 的  `pnl_buffer`  用的是环形写入（ `t % WINDOW` ），前  `WINDOW`  天里  `t >= WINDOW`  之前权重一直是均等的。如果想观察 warm-up 阶段权重是怎么从均匀过渡到 Sharpe 加权的， `online_alpha_with_logging`  里  `t < 2000`  这个判断是不是会丢掉前几天的 log？

1. 关于同一 returns 不同 lookback 的同源问题，评论里有人提了，我自己也踩过这个坑——4 个子信号相关性很高的时候， `max(0.0, sharpe)`  + 归一化基本给不出真正的分散收益。代码层面有没有考虑过加一个跨子信号的 decorrelation penalty，或者干脆让 LOOKBACKS 覆盖不同字段族？

另外 ACO 那段  `top_k=5` 、 `population=15`  在  `param_grid`  有 6×3×3=54 个组合时，gen 0 几乎是随机采样，确认下你的初始信息素都是 1.0 没有先验偏置吧？

---

### 评论 #10 (作者: SY54221, 时间: 1个月前)

针对楼主 ACO 搜 lookback/winsorize 的代码，原帖  `simulate_params`  里  `neutralize(raw)`  固定做截面去均值，参数空间未覆盖它。

结合评论提到的独立验证集思路，建议先确认：

1. 在留出数据上，固定 neutralize 配合 ACO 高分参数是否仍稳健，警惕评论中说的高 IS 不迁移。
2. 评论提到 Online alpha 的 LOOKBACKS 同源信号 PnL 高度同源，实操中建议先确认子策略日度 PnL 相关性再混合。

---

