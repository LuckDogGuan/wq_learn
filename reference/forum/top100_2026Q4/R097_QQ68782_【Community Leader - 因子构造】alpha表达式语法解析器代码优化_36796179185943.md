# 【Community Leader - 因子构造】alpha表达式语法解析器代码优化

- **链接**: https://support.worldquantbrain.com/hc/zh-cn/community/posts/36796179185943
- **作者**: QQ68782
- **发布时间/热度**: 10个月前, 得票: 67

## 帖子正文

在AI生成alpha的过程中, 表达式的解析、校验越来越重要;

论坛已有正则表达式、ast解析表达式的方法, 但是有些局限性:

- 正则表达式难以处理复杂表达式, 难以覆盖所有情况

- python ast依赖正则表达式预处理为python代码, 同样存在上面的问题, 且无法区分reverse、subtract等

本文使用表达式解析器lark定义语法, 实现alpha表达式解析, 语法简洁, 逐步完善可以实现完备的解析能力

**## 使用示例**

```python

code = '''

g = industry;

-group_normalize(ts_mean(vec_choose(nws18_sse, nth=-1), 66), densify(g))

'''

# 假设您想调用的是 parse_fast_exp

result = parse_fast_exp(code)

print(result)

```

输出示例

```

{

"ops": [ //操作符

"densify",

"group_normalize",

"reverse",

"ts_mean",

"vec_choose"

],

"ops_count": 5,

"fields": [ //字段

"industry",

"nws18_sse"

],

"fields_count": 2,

"defined_vars": { //定义的中间变量

"g"

}

}

```

**## 代码定义**

```python

from lark import Lark, Transformer

# 语法定义

grammar = r"""

start: (assignment | expr_with_semicolon)*

assignment: NAME EQUAL expr SEMICOLON

expr_with_semicolon: expr SEMICOLON?

?expr: expr PLUS expr     -> binary_expr

| expr MINUS expr    -> binary_expr

| expr STAR expr     -> binary_expr

| expr SLASH expr    -> binary_expr

| expr EQEQ expr     -> binary_expr

| expr NEQ expr      -> binary_expr

| expr LESSTHAN expr -> binary_expr

| expr MORETHAN expr -> binary_expr

| expr LEQ expr      -> binary_expr

| expr GEQ expr      -> binary_expr

| term

| LPAR expr RPAR     -> paren_expr

term: NUMBER               -> number

| NAME                 -> variable

| STRING               -> string

| BOOL                 -> boolean

| MINUS term           -> reverse  # 处理 -1 和 -x

| function_call

function_call: NAME LPAR [arg_list] RPAR

arg_list: arg (COMMA arg)*

?arg: expr                 -> positional_arg

| NAME EQUAL expr      -> keyword_arg

// 词法规则

BOOL: "true" | "false"

NAME: /[a-zA-Z_][a-zA-Z0-9_]*/

NUMBER: /\d+(\.\d+)?/   # <-- 保持修复后的版本

STRING: /"[^"]*"|'[^']*'/

// 标点符号

EQUAL: "="

SEMICOLON: ";"

LPAR: "("

RPAR: ")"

COMMA: ","

PLUS: "+"

MINUS: "-"

STAR: "*"

SLASH: "/"

EQEQ: "=="

NEQ: "!="

LESSTHAN: "<"

MORETHAN: ">"

LEQ: "<="

GEQ: ">="

COMMENT: /#.*|\/\*.*?\*\//

%ignore COMMENT

%ignore /[ \t\r\n]+/

"""

# 操作列表 (保持不变)

OPERATIONS_LIST = [

'add', 'exp', 'multiply', 'sign', 'subtract', 'pasteurize', 'log', 'purify',

'arc_tan', 'max', 'arc_sin', 'to_nan', 'abs', 'round_down', 'sigmoid', 'divide',

'min', 'nan_mask', 'arc_cos', 'tanh', 'nan_out', 'signed_power', 'inverse',

'round', 'sqrt', 's_log_1p', 'reverse', 'replace', 'log_diff', 'power', 'densify',

'fraction', 'floor', 'ceiling', 'or', 'and', 'not', 'is_not_finite', 'negate',

'is_nan', 'is_not_nan', 'less', 'equal', 'greater', 'is_finite', 'if_else',

'not_equal', 'less_equal', 'greater_equal', 'ts_corr', 'ts_zscore', 'ts_returns',

'ts_product', 'ts_std_dev', 'ts_triple_corr', 'ts_backfill', 'days_from_last_change',

'last_diff_value', 'ts_scale', 'ts_entropy', 'ts_vector_neut', 'ts_percentage',

'ts_step', 'ts_sum', 'ts_co_kurtosis', 'ts_partial_corr', 'inst_tvr',

'ts_decay_exp_window', 'ts_av_diff', 'ts_rank_gmean_amean_diff', 'ts_kurtosis',

'ts_mean', 'ts_min_max_diff', 'ts_arg_max', 'ts_max', 'ts_min_max_cps', 'ts_rank',

'ts_ir', 'ts_delay', 'ts_theilsen', 'hump_decay', 'ts_weighted_decay', 'ts_quantile',

'ts_min', 'ts_count_nans', 'ts_covariance', 'ts_co_skewness', 'ts_min_diff',

'ts_decay_linear', 'jump_decay', 'ts_moment', 'ts_arg_min', 'ts_regression',

'ts_skewness', 'ts_max_diff', 'kth_element', 'hump', 'ts_median', 'ts_delta',

'ts_poly_regression', 'ts_vector_proj', 'ts_target_tvr_decay', 'ts_target_tvr_delta_limit',

'ts_target_tvr_hump', 'ts_delta_limit', 'winsorize', 'rank', 'regression_proj',

'vector_neut', 'regression_neut', 'zscore', 'scale_down', 'truncate', 'scale',

'rank_by_side', 'normalize', 'generalized_rank', 'one_side', 'rank_gmean_amean_diff',

'quantile', 'vector_proj', 'multi_regression', 'vec_norm', 'vec_percentage',

'vec_kurtosis', 'vec_ir', 'vec_min', 'vec_count', 'vec_sum', 'vec_skewness',

'vec_max', 'vec_powersum', 'vec_avg', 'vec_stddev', 'vec_range', 'vec_choose',

'vec_filter', 'right_tail', 'bucket', 'tail', 'filter', 'clamp', 'keep',

'left_tail', 'trade_when', 'group_min', 'group_mean', 'group_median', 'group_max',

'group_percentage', 'group_vector_neut', 'group_rank', 'group_vector_proj',

'group_normalize', 'group_coalesce', 'group_extra', 'group_backfill', 'group_scale',

'group_count', 'group_zscore', 'group_std_dev', 'group_sum', 'group_neutralize',

'group_multi_regression', 'group_cartesian_product', 'convert', 'inst_pnl'

]

OPERATIONS = set(OPERATIONS_LIST)

class FastExpParser(Transformer):

def __init__(self):

super().__init__()

self.operations_found = []

self.defined_vars = set()

self.used_vars = set()

def assignment(self, items):

var_name = str(items[0])

self.defined_vars.add(var_name)

return var_name

def variable(self, items):

var_name = str(items[0])

self.used_vars.add(var_name)

return var_name

def function_call(self, items):

func_name = str(items[0])

if func_name in OPERATIONS:

self.operations_found.append(func_name)

return func_name

def number(self, items):

# 显式返回 float，以便 reverse 方法检查类型

return float(items[0])

def string(self, items):

return str(items[0])

def boolean(self, items):

return items[0].lower() == "true"

def binary_expr(self, items):

op_token = items[1]

op_char = op_token.value

op_mapping = {

'+': 'add',

'-': 'subtract',

'*': 'multiply',

'/': 'divide',

'<': 'less',

'>': 'greater',

'<=': 'less_equal',

'>=': 'greater_equal',

'==': 'equal',

'!=': 'not_equal'

}

if op_char in op_mapping:

self.operations_found.append(op_mapping[op_char])

return op_char

def reverse(self, items):

"""处理一元负号 (unary minus)"""

# items[0] 是 MINUS token

# items[1] 是 'term' 规则被 transform 后的结果

term_value = items[1]

# 检查 'term' 是否是一个数字字面量

if isinstance(term_value, (int, float)):

# 这是 -1, -10.5 等情况。

# 这不是一个 'reverse' 操作，只是一个负数。

# 我们返回负值，并且 *不* 记录 'reverse' 操作。

return -term_value

else:

# 这是 -my_field, -func(x) 等情况。

# 这 *是* 一个 'reverse' 操作。

self.operations_found.append('reverse')

return term_value # 返回 'term' 的值

# 添加这些是为了确保 Transformer 正确传播

def start(self, items):

return items

def expr_with_semicolon(self, items):

return items[0] if items else None

def paren_expr(self, items):

return items[0]

# 使用 LALR 和 缓存

parser = Lark(grammar, start="start", parser="lalr", cache=True)

def parse_fast_exp(code):

"""从代码中提取所有使用的操作和字段"""

try:

tree = parser.parse(code)

extractor = FastExpParser()

extractor.transform(tree)

global_vars = extractor.used_vars - extractor.defined_vars

# 返回去重和排序后的结果，以匹配测试

ops_set = extractor.operations_found

return {

'ops': sorted(list(ops_set)),

'ops_count': len(ops_set),

'fields': sorted(global_vars),

'fields_count': len(global_vars),

'defined_vars': extractor.defined_vars

}

except Exception as e:

print(f"Error parsing code: {code} \n{e}")

raise e

if __name__ == "__main__":

code = '''

g = industry;

-group_normalize(ts_mean(vec_choose(nws18_sse, nth=-1), 66), densify(g))

'''

# 假设您想调用的是 parse_fast_exp

result = parse_fast_exp(code)

print(result)

# {'ops': ['densify', 'group_normalize', 'reverse', 'ts_mean', 'vec_choose'], 'ops_count': 5, 'fields': ['industry', 'nws18_sse'], 'fields_count': 2, 'defined_vars': {'g'}}

```

**## 待改进**

- 覆盖更多测试用例

- 目前只支持RA

---

## 讨论与评论 (5)

### 评论 #1 (作者: JZ74499, 时间: 9个月前)

功能很全，本来想发一个我自己纯靠正则实现的，但是看来你已经把我的活包揽了

---

### 评论 #2 (作者: XB37939, 时间: 9个月前)

试了下 貌似没啥用？希望是可以输入表达式 判断表达式是否合法就好了 合法就回测 不合法就跳过~

---

### 评论 #3 (作者: ZX72144, 时间: 9个月前)

不错，要是有语法检查功能就完美了

---

### 评论 #4 (作者: YQ84572, 时间: 9个月前)

挺全的功能，应该是很方便的功能，拿来用了感谢分享
========================================================================================================================================================================

---

### 评论 #5 (作者: LL40122, 时间: 9个月前)

慢慢学习大佬的技术，感谢~

---

