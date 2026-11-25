# [Python Alpha 挑战赛]一句话让AI批量生成Python Alpha经验分享

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/40790558975767
- **作者**: XJ80376
- **发布时间/热度**: 4个月前, 得票: 11

## 帖子正文

**1, Idea：**  **为了充分利用AI快速生成Python Alpha，分享在用的提示词和相关文件**

**2, 实现：**  **提示词和相关文件具体内容**

prompt = f"""请基于现有的{python_alpha}指导文件和{datafields_table}生成具有经济学/行为学意义的alpha,充分利用np python库构建独特函数,独特函数必须与{operators_table}中的运算符逻辑完全不同,这样才能体现python alpha的优势;函数不要和示例一致,示例只是让你知道用法,最少生成10个完整的python alpha 并提供生成的JSON文件。请删除除JSON文件外的任何不必要描述和字符,以便我能够轻松解析。每个alpha应尽可能使用不同的运算符。字段必须与原始数据集的id完全一致,不允许编造。

输出1: python_alpha:

"""

**相关输入文件如下:**

datafields_table是权限内的数据字段，operators_table是权限内的的运算符，大家可以自行下载权限内的字段和运算符输入。

python_alpha指导文件:

# BRAIN Python Alphas 入门指南

---

**Python Alpha** 是一项新功能，允许你使用 Python 编写 Alpha。借助 Python 丰富的开源生态，你可以构建比以往更精细、更灵活、更多样化的 Alpha。

---

## `@alpha` 装饰器

每个 Alpha 都是使用 `@alpha` 装饰的 Python 函数。装饰器声明要加载哪些数据字段以及哪些 store 变量需要跨时间步持久化。

```python

@alpha(

data=["returns"],

store=["my_state"],

)

def my_alpha(data, store) -> npt.NDArray[np.float32]:

# data.returns  — 形状 [lookback_window, n_instruments], float32

# data.universe — 形状 [lookback_window, n_instruments] (始终可用, int: 1 = 在池内, 0 = 不在)

#

# store.my_state — 初始化为 None, 跨时间步持久化

signal = -np.nanmean(data.returns, axis=0)

return signal.astype(np.float32)

```

### `data` — 声明输入字段

`data` 参数是一个数据字段名称列表。每个名称在 `data` 命名空间中变成一个 **二维 numpy 数组**，形状为 `[lookback_window, n_instruments]`：

```python

@alpha(data=["returns", "close"], store=[])

def my_alpha(data, store) -> npt.NDArray[np.float32]:

# data.returns  — [lookback_window, n_instruments], float32

# data.close    — [lookback_window, n_instruments], float32

# data.universe — [lookback_window, n_instruments] (始终可用，不要列入列表)

...

```

模拟引擎每个时间步调用一次你的 Alpha。在每一步，每个数据字段包含 `lookback + 1` 行历史数据。`lookback` 为 0 得到 1 行（仅今天），`lookback` 为 5 得到 6 行。最新数据位于最后一行：

```python

yesterday = data.returns[-1]          # 形状: [n_instruments]

two_days_ago = data.returns[-2]       # 形状: [n_instruments]

full_window = data.returns            # 形状: [lookback_window, n_instruments]

```

在最初几个时间步中，窗口仍在增长（少于 `lookback + 1` 行）。一旦窗口达到完整大小，它会向前滑动——底部新增一行，顶部移除最旧的一行。

特殊字段 `universe` 始终作为整数数组可用（1 = 在股票池内，0 = 不在）。**不要将 "universe" 包含在你的 data 列表中。**

**数据数组是只读的。** 引擎将它们标记为不可写——尝试原地修改会引发 `ValueError`。始终先 `.copy()` 再修改：

```python

# 错误 — 引发 ValueError: assignment destination is read-only

a = data.returns[-1]

a[a < 0] = 0

# 正确 — 先复制

a = data.returns[-1].copy()

a[a < 0] = 0

```

### `store` — 跨时间步持久化状态

`store` 参数是一个 store 声明列表。每个声明可以是**普通字符串**（无类型，预初始化为 `None`），也可以是声明变量形状及如何随股票池扩展的**类型化字典**：

```python

{"name": "my_arr", "dims": "i", "extend": np.float64(0)}

```

- **"name"**：变量名（必需）

- **"dims"**：轴字符字符串 — `"i"` = 股票轴（股票池扩展时自动扩展），`"x"` = 自由轴。`"xi"` 表示 2D `[any, n_instruments]`。

- **"extend"**：新增股票的填充值 — **必须与数组的 dtype 完全匹配**。即使默认值可能够用，也应始终显式指定——它能明确意图并避免意外。使用显式的 NumPy 标量构造函数：

- `np.float64(0)`、`np.float32(0)`、`np.float64(np.nan)`、`np.float32(np.nan)` 等

- **切勿**使用裸 `np.nan`——它是 Python 的 `float`，而非 `numpy.float64`，会导致类型检查失败

- **切勿**使用裸 Python 字面量如 `0` 或 `0.0`——它们可能不匹配数组的 dtype，会引发 `ValueError`：

`Store item 'name' extend value '0' has wrong type: <class 'int'> expected: <class 'numpy.float32'>`

- 若省略，填充值由类型决定（浮点数组为 NaN，整数数组为该类型的最小值），但**不推荐省略**

使用 `store.var is None` 来检测首次调用。对于类型化条目，模拟器在股票池增长时自动扩展 "i" 轴——无需手动填充。

```python

@alpha(data=["returns"], store=[{"name": "running_mean", "dims": "i", "extend": np.float64(0)}])

def smooth_alpha(data, store) -> npt.NDArray[np.float32]:

if store.running_mean is None:

store.running_mean = np.zeros(data.returns.shape[1], dtype=np.float64)

raw = -np.nanmean(data.returns, axis=0)   # float64

store.running_mean = 0.9 * store.running_mean + 0.1 * raw

return store.running_mean.astype(np.float32)

```

使用 `"dims": "xi"` 创建二维缓存，其中轴 0 是自由（时间）轴，轴 1 是股票轴。一个实用的场景是缓存超过 `lookback` 窗口天数的横截面排名。使用 `"extend": np.float64(np.nan)`，这样新增股票的历史条目为 NaN——`np.nanmean` 会自然排除它们直到股票积累足够的历史记录：

```python

RANK_DAYS = 20

@alpha(

data=["returns"],

store=[

{"name": "rank_cache", "dims": "xi", "extend": np.float64(np.nan)},  # [n_days_cached, n_instruments]

],

)

def mean_of_rank_alpha(data, store) -> npt.NDArray[np.float32]:

today = data.returns[-1]

# 今日收益的横截面排名

finite = np.where(np.isnan(today), -np.inf, today)

today_rank = np.argsort(np.argsort(finite)).astype(np.float64)

today_rank[np.isnan(today)] = np.nan

if store.rank_cache is None:

store.rank_cache = today_rank[np.newaxis, :]  # 形状: [1, n_instruments]

else:

new_cache = np.vstack([store.rank_cache, today_rank[np.newaxis, :]])

store.rank_cache = new_cache[-RANK_DAYS:]

mean_rank = np.nanmean(store.rank_cache, axis=0)

return (-mean_rank).astype(np.float32)

```

当股票池增长时，模拟器会自动向 `rank_cache` 追加一个新的 NaN 列——无需手动填充。

**无类型字符串条目的有效值**：

- `None`、标量（`int`、`float`、`bool`、`str`）、NumPy 标量

- `numpy.ndarray`

- 包含以上任何类型的列表和字典，包括嵌套数组、列表和字典

- 字典的键必须为字符串

**后备方案 — `_pad_store`（无类型条目）**：如果你使用普通字符串条目存储股票大小的数组，请手动扩展它再读取，否则在模拟中会出错：

```python

def _pad_store(arr, n_insts, fill_value):

"""当股票池增长时沿股票轴填充。"""

if arr.shape[-1] >= n_insts:

return arr

n_new = n_insts - arr.shape[-1]

if arr.ndim == 1:

return np.pad(arr, (0, n_new), mode='constant', constant_values=fill_value)

return np.pad(arr, ((0, 0), (0, n_new)), mode='constant', constant_values=fill_value)

n_insts = data.returns.shape[1]

store.running_sum = _pad_store(store.running_sum, n_insts, fill_value=0.0)

```

即使是二维情况如相关矩阵（对角线=1，非对角线=0），也可以使用类型化字典：使用 `"dims": "ii"` 配合 `"extend": np.float64(0)`。模拟器会用 0 填充新行和新列；在 Alpha 函数体中使用一个普通字符串 `"prev_n"` 来跟踪之前的股票池大小，以修正新增股票的对角线。

### 返回值

Alpha 必须返回一个形状为 `[n_instruments]` 的**一维 `float32` numpy 数组**。BRAIN 的数据字段通常是 `float32`，但许多 NumPy 操作会静默提升为 `float64`——例如 `np.nanmean`、`np.nanstd`、`np.nansum`，甚至与 Python 浮点数运算如 `0.9 * array`。**始终在返回时添加 `.astype(np.float32)` 作为安全措施**（如果数组已经是 `float32`，它是无操作的）：

```python

def my_alpha(data, store) -> npt.NDArray[np.float32]:

# np.nanmean 将 float32 输入提升为 float64 输出

signal = -np.nanmean(data.returns, axis=0)

return signal.astype(np.float32)

```

如果返回值不是 `float32`，模拟将报错：`Alpha vector is not float32`。

### 规则总结

1. 每个函数**恰好一个** `@alpha` 装饰器

2. 函数必须接受**恰好 2 个参数**（`data`、`store`）

3. 返回类型必须为形状 `[n_instruments]` 的 `float32` numpy 数组

4. **不要**将 `"universe"` 包含在 `data` 列表中——它始终可用

5. **不要**原地修改 `data` 数组——它们是只读的，先复制

---

## 完整示例

```python

from brain.alphas import alpha

import numpy as np

import numpy.typing as npt

def pasteurize(a, u):    ###pasteurize函数 只是示例，不要和这个一样，基于你的才能创建独特函数；

a = a.copy()

a[~u.astype(bool)] = np.nan

return a

def neutralize(a):       ###neutralize 只是示例，不要和这个一样，基于你的才能创建独特函数；

a0 = np.nan_to_num(a, nan=0, posinf=0, neginf=0)

return a - np.mean(a0)

def scale(a):             ###scale 只是示例，不要和这个一样，基于你的才能创建独特函数；

a0 = np.nan_to_num(a, nan=0, posinf=0, neginf=0)

norm = np.linalg.norm(a0, ord=1)

return a / norm if norm > 0 else a

@alpha(

data=["returns"],

store=[],

)

def mean_reversion(data, store) -> npt.NDArray[np.float32]:

a = -np.nanmean(data.returns, axis=0).astype(np.float32)

a = pasteurize(a, data.universe[-1])

a = scale(neutralize(a))

return a.astype(np.float32)

```

---

---

## 讨论与评论 (8)

### 评论 #1 (作者: ML38868, 时间: 4个月前)

====================================================================================

学习一下

我自己尝试用AI跑了几天都没什么好的

感谢分享

====================================================================================

---

### 评论 #2 (作者: LA79055, 时间: 4个月前)

这个流程很贴近实际痛点，尤其是把 datafields_table、operators_table 和 Python Alpha 指导文件一起输入，能减少字段编造和代码格式错误。官方 Python Alpha 文档对 @alpha、data、store、float32 输出都有明确要求，把这些规则放进提示词里，生成结果会更容易进入回测环节。

---

### 评论 #3 (作者: BW14163, 时间: 4个月前)

感谢分享，赶紧学习一下，和其他几个帖子做个交叉学习，看看能不能磨出点什么

---

### 评论 #4 (作者: HW93328, 时间: 4个月前)

正在认真学习python alpha，感谢大佬分享，希望后面也能开发出一套python alpha的自动生成方法～

===============================HW想评论====================================

---

### 评论 #5 (作者: ZZ10277, 时间: 3个月前)

非常实用的Prompt工程分享！这种“多表关联+规则约束”的提示词框架，通过引入字段表、算子表和官方指南，极大地降低了AI在生成Python Alpha时的“幻觉”风险，确保了字段真实性和代码合规性。特别是要求生成独特函数而非机械复刻示例的设定，真正挖掘出了Python的高自由度优势。感谢干货分享！

---

### 评论 #6 (作者: YQ84572, 时间: 3个月前)

很好的分享，能让ai快速理解python alpha的含义，转变为表达式，这样能快速生成有意义的alpha，能正确的进入回测保证不错误
====================================================================================

感谢大佬的分享，祝大佬base多多，vf高高

====================================================================================

---

### 评论 #7 (作者: SY90356, 时间: 3个月前)

非常实用的分享！这个 prompt 思路很清晰——把指导文件、字段表和运算符表一起喂给 AI，再要求生成独特函数而非照搬示例，确实能大幅提升批量生产效率。有几个可以进一步优化的方向供参考：一是建议在 prompt 中加入"经济逻辑验证"环节，让 AI 生成每个 alpha 时附带一段简短的经济学解释，这样后续筛选时可以按逻辑质量而非只看回测指标来过滤；二是可以加入"多样性约束"，要求生成的 alpha 之间字段重叠度不超过某个阈值，避免批量产出一堆同质化因子；三是考虑在输出 JSON 中增加"信号稀缺度"标签，标记每个 alpha 使用的字段组合在历史提交中的出现频率，帮助优先测试真正新颖的方向。期待后续分享实际回测效果！

---

### 评论 #8 (作者: PZ64174, 时间: 2个月前)

这个提示词模板很实用，特别是要求独特函数必须与operators_table中的运算符逻辑完全不同这一点，确实是发挥Python Alpha优势的关键。我之前用AI生成Python Alpha时也遇到过类似问题，AI倾向于直接把FASTEXPR算子翻译成numpy等价操作，这样写出来的Python Alpha和FASTEXPR版本没有本质区别，反而失去了Python自由编程的意义。我现在的做法是在提示词里明确要求使用numpy的线性代数操作比如np.linalg.svd或者np.percentile来做截面排序，这些是FASTEXPR算子无法直接实现的。另外提醒一点，AI生成的alpha一定要逐个检查datafield的id是否真实存在，我之前批量生成时有大概三成的alpha因为字段名编造导致回测报错。

---

