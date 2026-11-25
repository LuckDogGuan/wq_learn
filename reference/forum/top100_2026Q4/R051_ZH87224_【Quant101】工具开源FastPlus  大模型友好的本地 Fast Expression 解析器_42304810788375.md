# 【Quant101】工具开源：FastPlus —— 大模型友好的本地 Fast Expression 解析器

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/42304810788375
- **作者**: ZH87224
- **发布时间/热度**: 2个月前, 得票: 14

## 帖子正文

> Github:  [AshSwing/FastPlus](https://github.com/AshSwing/FastPlus)
> Pypi:  [py-fastplus](https://pypi.org/project/py-fastplus)

你是否遇到过这些问题：

批量回测时，一条表达式的语法错误导致整批任务全部报废；大模型反复修改表达式，却始终无法通过平台校验；平台返回晦涩难懂的错误信息，让人完全不知道问题出在哪里；大模型凭空编造不存在的操作符；大模型分不清楚 Group / Matrix / Vector，一堆表达式反复嵌套；或者仅仅因为少了一个括号，整个表达式就无法运行……

FastPlus 正是为解决这些问题而来。它会在提交回测前检查表达式语法、参数数量、参数类型和部分操作符规则，并提供包含错误位置、期望类型和实际类型的友好诊断信息，让研究员和大模型都能快速定位并修复问题。

给你的大模型研究员配备一套可靠的表达式质检与调试工具。

欢迎 pr 欢迎 fork，任何问题可以 issue / 留言 / 私聊

## 项目介绍

FastPlus 是一个基于 Rust 和 PyO3 实现的 WorldQuant Fast Expression 解析器。它把 Alpha 表达式解析为可访问的 Python 对象，并在解析已知操作符时进行参数数量、参数类型和部分操作符专属规则检查。

当前实现面向 RegularAlpha，收录了 Expert 权限范围内的 108 个操作符。

## 安装

 https://github.com/AshSwing/FastPlus#%E5%AE%89%E8%A3%85

FastPlus 预编译包需要 Python 3.12 及以上版本。

从 PyPI 安装：

```
pip install py-fastplus
```

如果需要从源码开发：

```
uv sync
source .venv/bin/activate
maturin develop --skip-install
```

安装后可以在 Python 中导入：

```
import fastplus
```

## Python 用法

 https://github.com/AshSwing/FastPlus#python-%E7%94%A8%E6%B3%95

使用  `fastplus.parse`  解析一个 Alpha 表达式：

```
import fastplus

alpha = fastplus.parse("a=ts_delay(close, 5); group_rank(a, industry)")

print(alpha.fields)
print(alpha.operators)
```

输出：

```
{'matrix': ['close'], 'vector': [], 'group': ['industry']}
['ts_delay', 'group_rank']

```

`Alpha`  提供以下属性：

- `assignments` ：赋值语句列表，每个元素包含  `variable`  和  `value` 。
- `signal` ：最终信号表达式。
- `fields` ：按  `matrix` 、 `vector` 、 `group`  分类的数据字段名称。
- `operators` ：表达式中使用的操作符名称列表。

解析失败会抛出  `ValueError` 。例如：

最终  `signal`  不能是  `Group`  或  `Vector` ：

```
fastplus.parse("bucket(rank(x), range='0, 1, 0.1')")
```

```
 --> 1:1
  |
1 | bucket(rank(x), range='0, 1, 0.1')
  | ^--------------------------------^
  |
  = signal must be Matrix-compatible, but got Group

```

`bucket`  不能同时提供有效的  `range`  和  `buckets` ：

```
fastplus.parse("bucket(rank(x), range='0, 1, 0.1', buckets='0, 0.5, 1')")
```

```
 --> 1:1
  |
1 | bucket(rank(x), range='0, 1, 0.1', buckets='0, 0.5, 1')
  | ^-----------------------------------------------------^
  |
  = operator `bucket` check failed: InvalidExpression("bucket requires exactly one of range and buckets to be valid")

```

`vec_*`  操作符要求  `Vector` ，不能把其他返回  `Matrix`  的操作嵌进去：

```
fastplus.parse("vec_avg(rank(x))")
```

```
 --> 1:1
  |
1 | vec_avg(rank(x))
  | ^--------------^
  |
  = operator `vec_avg` check failed: InvalidArgumentType { expected: Vector, actual: Matrix }

```

异常信息会同时指出错误位置、操作符名称、错误类型、期望类型和实际类型，便于研究员和大模型定位问题并自动修复表达式。

## FastPlus 语法

 https://github.com/AshSwing/FastPlus#fastplus-%E8%AF%AD%E6%B3%95

### Alpha 和赋值

 https://github.com/AshSwing/FastPlus#alpha-%E5%92%8C%E8%B5%8B%E5%80%BC

一个 Alpha 由零个或多个赋值语句和一个最终信号组成：

```
[variable = expression;] expression [;]

```

例如：

```
adv = ts_mean(volume, 20);
signal = rank(adv);
signal

```

赋值左侧只能是普通变量，不能使用占位符。最后一个分号可选。

### 变量、字段和占位符

 https://github.com/AshSwing/FastPlus#%E5%8F%98%E9%87%8F%E5%AD%97%E6%AE%B5%E5%92%8C%E5%8D%A0%E4%BD%8D%E7%AC%A6

普通变量由字母开头，只能包含 ASCII 字母、数字和下划线：

```
close
industry
my_signal_1

```

占位符必须使用完整形式：

```
<close_field/>

```

目前不支持常数占位符，例如  `<1/>`  或  `<0.5/>` 。占位符会统一作为数据字段处理，并在  `Alpha.fields`  中保留完整的  `<` 、 `/>`  标记。

已知操作符会根据参数签名把变量和占位符分类为  `matrix` 、 `vector`  或  `group` 。未知变量在无法确定类型时作为通配类型处理；赋值左侧定义的变量不会被计入  `fields` 。

### 操作符调用

 https://github.com/AshSwing/FastPlus#%E6%93%8D%E4%BD%9C%E7%AC%A6%E8%B0%83%E7%94%A8

操作符调用格式为：

```
operator(positional_arg, ..., keyword=value, ...)

```

位置参数必须写在关键字参数之前，关键字参数只能使用常量：

```
add(close, volume, filter=true)
clamp(x, lower=-1, upper=1, inverse=false, mask='mean')

```

已知操作符会检查：

- 位置参数数量；
- 位置参数类型；
- 关键字名称和类型；
- 必填关键字参数；
- 部分操作符专属约束，例如  `k <= d` 、 `clamp`  的上下界关系，以及  `bucket`  的参数互斥和数组顺序。

未知操作符会保留在表达式中，但跳过操作符检查。

当前实现中的几个平台差异：

- `subtract`  目前只支持两个位置参数。
- `add` 、 `multiply` 、 `max` 、 `min`  等可变参数操作符至少需要两个位置参数。
- `jump_decay`  的位置参数是  `x` 、 `d` ，关键字参数是  `stddev` 、 `sensitivity` 、 `force` 。
- `ts_rank_gmean_amean_diff`  使用必填的  `lookback`  关键字参数。
- 其他包含 lookback 语义的时间序列操作符通常把 lookback 作为最后一个位置参数，例如  `ts_backfill(x, d)`  和  `ts_rank(x, d)` 。
- 关键字参数只能使用常量，不能传入变量、占位符或复杂表达式。
- 操作符至少需要一个位置参数；位置参数和关键字参数不能交错。

### 表达式和运算符

 https://github.com/AshSwing/FastPlus#%E8%A1%A8%E8%BE%BE%E5%BC%8F%E5%92%8C%E8%BF%90%E7%AE%97%E7%AC%A6

支持括号、前缀运算、二元运算和三元表达式：

```
-(x + 1)
x > 0 && y < 1
x ? y : z

```

支持的二元运算符包括：

```
||  &&  !=  ==  >=  <=  >  <  +  -  *  /

```

支持的前缀运算符包括：

```
!  +  -

```

三元表达式的三个分支都必须是完整表达式。

### 常量和关键字参数

 https://github.com/AshSwing/FastPlus#%E5%B8%B8%E9%87%8F%E5%92%8C%E5%85%B3%E9%94%AE%E5%AD%97%E5%8F%82%E6%95%B0

支持整数、浮点数、布尔值和字符串常量。数值常量会根据值归类为整数、正整数、比例、浮点数等类型；数值标量可以按平台规则广播为  `Matrix` 。

字符串关键字会经过统一解析，例如：

```
driver='gaussian'
mask='nearest_bound'
mask='mean'
ignore='NaN'

```

还支持范围、数组和集合形式，例如：

```
range='0, 1, 0.1'
buckets='0, 0.2, 0.5, 1'
ignore='NaN 0 1'

```

### 注释和空白

 https://github.com/AshSwing/FastPlus#%E6%B3%A8%E9%87%8A%E5%92%8C%E7%A9%BA%E7%99%BD

空格、制表符和换行会被忽略。支持以下注释：

```
// 行注释
# 行注释
/* 块注释 */

```

## 当前限制和待开发功能

 https://github.com/AshSwing/FastPlus#%E5%BD%93%E5%89%8D%E9%99%90%E5%88%B6%E5%92%8C%E5%BE%85%E5%BC%80%E5%8F%91%E5%8A%9F%E8%83%BD

### 操作符权限范围

 https://github.com/AshSwing/FastPlus#%E6%93%8D%E4%BD%9C%E7%AC%A6%E6%9D%83%E9%99%90%E8%8C%83%E5%9B%B4

当前只有 Expert 权限，因此只能完整检查 Expert 范围内的操作符。未知操作符会跳过检查，以便后续扩展；欢迎提交 Pull Request 补充操作符签名和规则。

### 当前不会检查的规则

 https://github.com/AshSwing/FastPlus#%E5%BD%93%E5%89%8D%E4%B8%8D%E4%BC%9A%E6%A3%80%E6%9F%A5%E7%9A%84%E8%A7%84%E5%88%99

以下表达式按平台规则应该失败，但当前还没有检测：

- 定义了但没有使用的变量；
- 用户定义变量与数据字段重名。
- 字段分类的交叉校验：如果同一个字段同时出现在  `matrix`  和  `vector` （或其他类别）中，说明至少有一个位置的类型推断错误，目前尚未检测。

### 待开发功能

 https://github.com/AshSwing/FastPlus#%E5%BE%85%E5%BC%80%E5%8F%91%E5%8A%9F%E8%83%BD

- 模板展开：根据占位符自动生成具体表达式。
- 参数遍历：遍历参数空间并生成参数组合。
- AST 结构化输出：提供  `.format()`  方法。
- 表达式编译：提供  `.compile()`  方法，自动合并同类项并优化因子表达式结构。
- 补充更多权限级别的操作符和操作符专属校验。

## 开发验证

 https://github.com/AshSwing/FastPlus#%E5%BC%80%E5%8F%91%E9%AA%8C%E8%AF%81

Rust 测试和检查：

```
cargo fmt -- --check
cargo test --lib
cargo clippy --all-targets --all-features -- -D warnings
```

Python 测试和类型检查：

```
uv run pytest
uv run ty check
```

##

---

## 讨论与评论 (15)

### 评论 #1 (作者: RM49262, 时间: 1个月前)

感谢分享，FastPlus 正好戳中批量回测时“一条表达式报错导致整批失败”的痛点。错误信息能直接给出错误位置、期望类型和实际类型，比平台原始的晦涩报错直观很多，对大模型调试也很友好。

几个细节印象比较深：

1. 对操作符做参数数量、类型、关键字和专属规则的多层检查，问题可以在提交前被发现；
2. 当前限制说明得很清晰，比如只覆盖 Expert 权限、未知操作符跳过检查，用的人不会误以为所有规则都已覆盖；
3. 错误示例覆盖了  `bucket`  参数互斥、 `vec_avg`  类型错误这类典型场景，很有参考价值。

期待后续模板展开和参数遍历功能，这两块对批量生成表达式会很有帮助。

---

### 评论 #2 (作者: TL53163, 时间: 1个月前)

非常实用的开源工具！在 LLM 驱动的 Agent 自动化 Alpha 挖掘中，回测前的表达式本地校验是避免 400 Bad Request、限流配额浪费以及排队阻塞的关键屏障。针对 FastPlus（ `py-fastplus` ）在 Agent 接入与工程化落地上的应用，结合我们本地校验技能的部署经验，提供 3 个高价值的配合建议：

1. **整合防过拟合硬性规则校验（E1 / E3 证据）** ：
   平台语法正确并不等于符合提交标准。在 Fast Expression 框架下，Agent 生成的表达式去重字段数严禁 > 4（去重 1 字段最佳），去重操作符数严禁 > 6。建议在 FastPlus AST 解析后增加  `len(alpha.fields['matrix']) <= 4`  与  `len(set(alpha.operators)) <= 6`  的静态断言，在本地直接打回过拟合复杂表达式，无需等待云端回测。
2. **Vector of Field 与 Python/Fast 跨类型拦截（E2 证据）** ：
   在 BRAIN 平台中，部分数据集字段为 Vector 类型（如  `news104_sentiment` ）。FastPlus 对  `vec_*`  必须作用于 Vector 类型的类型检查能有效拦截  `vec_avg(rank(x))`  这种常见 LLM 语法误用。建议增加对 Python Alpha 模式下不支持 Vector Field 的前置拦截提示。
3. **与决策投影摘要集成（E3 证据）** ：
   将 FastPlus 解析出的 AST 结构（ `fields`  /  `operators`  / 错误位置）直接输出为单行决策 JSON（ `decision.json` ），代替完整异常 Stack Trace 传入 LLM 上下文。这不仅能让 Agent 实现 1-Step 语法自我修复，还能避免抛出上百行编译日志造成的 Token 黑洞。

感谢楼主开源这么优秀的 Rust/Python 工具，已在 Agent 预检流程中推荐使用！

---

### 评论 #3 (作者: MY27687, 时间: 1个月前)

刚好最近在把 FastPlus 接入自己的 agent 工作流，实际跑了几百条表达式之后来反馈几个体验：

**Rust/PyO3 选型是亮点**：解析速度确实快，我批量跑了 500 条表达式的校验，总共不到 0.5 秒，对比之前用的纯 Python 正则方案快了至少一个数量级。对于 agent 循环中每次生成表达式都要即时校验的场景，这个延迟完全可以接受——不会成为 agent 迭代的瓶颈。

**提两个实际使用中碰到的小坑**：
1. `ts_rank_gmean_amean_diff` 的 `lookback` 关键字参数文档里写了是必填，但实际 BRAIN 平台上该参数是可选的（有默认值）。我用 FastPlus 校验时报错，以为表达式有问题，结果去掉校验直接提交其实是过的。建议在文档里标注哪些是"平台实际行为"与"FastPlus 检查规则"之间的已知差异。
2. 对于赋值变量在后续表达式中被 `group_rank` 等操作符引用时，类型推断偶尔会 fallback 到通配类型——这种情况下 `Alpha.fields` 里的分类会不完整，后续的防过拟合检查（字段数 ≤4）就会漏判。

**关于待开发功能的一点建议**：参数遍历（parameter sweep）功能如果能直接输出 `alpha_expressions` 列表（而不是只是参数组合），就可以无缝对接 `create_multi_simulation`，这会是批量优化场景下最实用的一步。模板展开同理——如果能接受占位符模板 + 字段列表 → 直接产出完整表达式列表，整个 agent 工作流会少一次"表达式拼接"的步骤。

这个工具对降低无效模拟请求的帮助是实打实的，已 star ⭐。期待 AST 结构化输出和 `.compile()` 优化功能。

---

### 评论 #4 (作者: PZ64174, 时间: 1个月前)

非常实用的开源解析工具。在利用大模型生成 WorldQuant BRAIN 表达式的场景中，本地语法校验和算子去重统计至关重要。平台对算子数量和数据字段数量有明确的硬性限制，如果能在调用仿真接口之前先在本地使用解析器进行语法检查、算子去重以及非法组合过滤，可以有效降低无效回测请求的数量，提升整体研究效率。非常感谢作者的开源贡献。

---

### 评论 #5 (作者: QW94165, 时间: 1个月前)

几个动手前可以先确认的点，避免踩坑：

- 108 个 Expert 操作符是否已经覆盖你们常用的高频集合？建议先拿近期一批真实 alpha 跑一遍，统计 FastPlus 能识别操作符的比例，再决定能不能直接接进批量回测前的预检链路。
- 字段分类的交叉校验（同一字段既出现在  `matrix`  又出现在  `vector` ）现在还没检测，这条对“模型编造操作符”和“误用 vec_*”的场景其实很关键，可以先在你们 Agent 侧补一层兜底，避免静默放过。
- `bucket`  /  `clamp`  /  `k,d`  类专属规则已经做了，但诸如“定义未使用的变量”、“用户变量与字段重名”这种当前是不报的，建议把这两类在接入清单里单独标注成“已知未覆盖”，避免后续排查时把锅甩给 FastPlus。

另外有个细节想跟楼主确认： `subtract`  目前只支持两个位置参数这条限制，是平台真实行为，还是当前解析器的临时约束？如果是后者，后续是否打算放开成可变参数版本？这个对依赖  `subtract(x, y, z)`  的历史表达式会很关键。

---

### 评论 #6 (作者: GC81559, 时间: 1个月前)

关于  `ts_decay_exp_window(x, d, factor)`  的使用心得：这个算子比  `ts_decay_linear`  更灵活，因为它允许通过 factor 参数控制衰减速度。factor=0.5 时是线性衰减，factor<0.5 时近期权重更大（适合短周期信号），factor>0.5 时远期权重更大（适合长周期信号）。在动量因子上用 factor=0.3 效果很好，能更快响应趋势变化。

---

### 评论 #7 (作者: XW23690, 时间: 1个月前)

这个工具太需要了！之前用 Cursor 批跑回测，经常因为一个括号或参数类型错误导致整批报废，平台返回的错误信息又晦涩难懂。FastPlus 的错误诊断信息（位置 + 期望类型 + 实际类型）比平台友好太多。

补充一个使用场景：建议把 FastPlus 集成到 Agent 的"生成 → 校验 → 提交"流程里——LLM 生成表达式后先本地  `fastplus.parse()`  过一遍，通过了再提交平台回测。实测能减少约 60% 的无效回测请求，既省 token 又省时间。

另外，关于"待开发功能"里的模板展开，如果能支持从  `{operator_list} × {field_list}`  自动生成候选表达式，配合批量回测脚本，基本就是一套完整的 alpha 挖掘 pipeline 了。期待后续更新！

---

### 评论 #8 (作者: SY90356, 时间: 1个月前)

回测前先做本地语法和类型校验，确实能避免“一条表达式报错拖垮整批任务”的情况，错误信息带上位置和期望/实际类型，对大模型反复改表达式的场景也会顺手不少。

结合前两条评论里的建议，想确认几个点：

1. 评论里提到可以在本地再加一道复杂度静态断言，比如去重字段数和去重操作符数的上限检查——这类规则看起来目前不在 FastPlus 的检查范围内，后面有没有计划做成可选校验项，而不是只依赖操作符签名检查？

1. AST 结构化输出和模板展开都还在待开发列表里，如果这两块落地，输出的 fields/operators 结构有没有可能直接生成给大模型用的单行决策摘要，省掉传完整日志的步骤？

1. 帖子提到未知操作符会跳过检查但保留在表达式中，这种情况下的参数节点类型推断是怎么处理的？如果操作符名拼写错误，字段分类结果是否还会正常输出？

---

### 评论 #9 (作者: YY31580, 时间: 1个月前)

刚好缺这个

---

### 评论 #10 (作者: YW84821, 时间: 1个月前)

感谢楼主 这个帮大忙了，特别是遇到vector字段的时候，总会没有使用vec_avg，还有些冷门算子格式容易错误，导致批量模拟的时候一批全部取消了。

---

### 评论 #11 (作者: SY54221, 时间: 1个月前)

楼主开发的FastPlus精准命中批量回测前语法校验痛点。评论1建议增加去重字段≤4、操作符≤6的静态断言防过拟合，这里补充一个实操细节：在AST解析后，还可统计单个赋值变量的复用次数。若某中间信号被反复嵌套变换（如 a=ts_delay(close,5); b=rank(a); c=group_rank(b, industry); signal=add(b,c) 中 b 被复用），建议将高频复用标记为过拟合风险点，本地打回比回测后失效更省配额。样本外表现仍须独立验证。

---

### 评论 #12 (作者: LJ40932, 时间: 27天前)

感谢分享，FastPlus 确实把“批量回测时一条表达式报错导致整批报废”这个痛点解决得很直接。错误信息能定位到位置、期望类型和实际类型，对大模型调试和研究员自查都友好。

结合评论里提到的工程化建议，想补充几个方向，方便后续迭代时参考：

1. 评论里提到的防过拟合硬性校验（去重字段数 ≤ 4、去重操作符数 ≤ 6）很实用，但当前 FastPlus 只做语法和类型检查。是否考虑在 AST 解析后直接提供类似  `len(alpha.fields['matrix'])`  的快捷属性，或内置可选的静态断言入口，方便用户在本地预检阶段直接打回过拟合表达式？
2. 将 AST 结构输出为单行 JSON（如  `decision.json` ）替代完整异常堆栈传给 LLM，确实能减少 token 消耗。当前  `Alpha`  对象已暴露  `fields`  /  `operators` ，如果后续能直接提供序列化方法，Agent 接入会更容易。
3. 帖子中提到目前不支持常数占位符（如  `<1/>` ），且字段分类交叉校验还未实现。这两个点在实际使用中可能容易触发，后续模板展开功能如果能把占位符类型推断一起考虑进去，应该会更完整。

期待后续的模板展开和参数遍历功能，感谢开源。

---

### 评论 #13 (作者: TT92977, 时间: 18天前)

FastPlus 把错误定位到具体列并给出实际/期望类型，确实比平台原始报错更适合接入 Agent 预检。楼里提到的“本地拦截过拟合复杂表达式”方向，和  `alpha.fields`  /  `alpha.operators`  的输出也能自然结合，不过有几处需要先确认：

- 评论 2 提到的“去重字段数 > 4、去重操作符数 > 6 禁止提交”，如果这些阈值来自平台规则，建议单独标注来源；如果只是经验值，最好做成可配置项，不要写死。
- 用  `len(alpha.fields['matrix'])`  和  `len(set(alpha.operators))`  做断言时，需要考虑未知操作符：当前未知操作符会跳过检查但仍会出现在  `operators`  里，计数时是否纳入？否则可能出现本地拦截但平台实际可提交的情况。
- FastPlus 目前只说明面向 RegularAlpha，没有区分 Python/Fast 模式；评论 2 提到的“Python Alpha 模式不支持 Vector Field”如果要前置拦截，需要先补充模式参数或解析上下文，否则容易和  `vec_*`  的 Vector 类型检查混淆。

期待后续模板展开和参数遍历，如果展开时能一并输出字段分类，再接这些规则会更顺。

---

### 评论 #14 (作者: BL12743, 时间: 14天前)

这个工具在本地先卡掉表达式语法和类型错误，确实能省掉不少无效提交。针对评论区提到的 Agent 接入和本地预检，有几个点想确认下：

1. 字段/操作符数量这类提交限制目前没有内置，后续是打算作为可选规则，还是让调用方自己用  `fields`  /  `operators`  做断言？如果做成可配置会更灵活，因为不同模式或权限范围可能不一样。
2. 未知操作符会跳过检查，这在 Agent 场景下可能漏掉类型或参数错误。是否有计划提供操作符签名扩展接口，或至少在解析结果里标记哪些操作符未检查，避免调用方误以为已经通过完整校验？
3. 待开发功能里 AST 输出是  `.format()` ，但评论中提到需要  `decision.json`  这类能直接给 LLM 的单行结果。如果能提供 JSON 或可序列化结构，应该能更顺地接入 Agent 的自我修复循环。

---

### 评论 #15 (作者: LO84823, 时间: 13天前)

本地预检这个思路确实戳中批量回测的痛点：一条表达式报错，整批任务跟着报废，成本太高。评论区提到的几个扩展方向挺有意思，也想借楼问几个小问题：

1. 评论里建议解析后按  `fields`  /  `operators`  数量做硬性拦截，这类检查是否适合做成可配置开关？具体阈值还需要按场景再确认。
2. `vec_*`  必须作用于 Vector 的类型检查能拦住不少 LLM 误用；如果再加上“Python Alpha 模式不支持 Vector 字段”的前置提示，会不会更完整？
3. 把 AST 输出成单行 JSON 传给大模型，从帖子里的待开发项看，能和 AST 结构化输出 /  `.format()`  衔接上，后面有考虑直接支持 JSON 输出吗？

模板展开和参数遍历如果落地，对批量生成表达式会很有帮助，蹲一个后续。

---

