# FASTEXPR 编译器与自愈语法纠错机制

> **归档位置**：`src/多臂老虎机总结/05_FASTEXPR编译器与自愈语法纠错.md`  
> **研究对象**：`generation_two/core/template_validator.py` 与 `expression_compiler.py`  
> **核心主题**：AST 编译管线、规则库正则清洗、错误自愈修复、仿真报错反哺学习库

---

## 1. 六阶段全编译流水线 (Expression Compiler Pipeline)

Generation Two 构建了一套专门面向 WorldQuant Brain FASTEXPR 语法的轻量级编译管线：

```
原始表达式 (Raw String)
   │
   ▼
[Stage 1: 词法分析 (Lexical Analysis)] ──── 提取 Token 序列 (IDENTIFIER, OPERATOR, NUMBER, LPAREN, RPAREN, COMMA)
   │
   ▼
[Stage 2: 语法分析 (AST Parsing)] ──────── 构建抽象语法树 (AST Tree)
   │
   ▼
[Stage 3: 语义分析 (Semantic Analysis)] ── 核查算子签名、入参数量合法性、字段存在性、时序/截面类型对齐
   │
   ▼
[Stage 4: 中间表示 (IR Generation)] ────── 生成标准化三地址码或平铺树结构
   │
   ▼
[Stage 5: 优化 Pass (Optimization)] ────── 消除死算子 (如 rank(rank(x)) 简化为 rank(x))
   │
   ▼
[Stage 6: 目标代码生成 (Code Generation)] ── 产出标准纯净 FASTEXPR 仿真载荷
```

---

## 2. 启发式正则清洗与静态纠错 (`_cleanup_template`)

大语言模型（如 Ollama / DeepSeek）生成的表达式通常伴随特定语法幻觉。系统在进入编译期前执行 8 重启发式正则净化：

### 2.1 地区前缀剔除 (Region Prefix Removal)
- **幻觉现象**：LLM 误将地区作为对象命名空间，输出 `USA.close` 或 `EUR.anl10_eps`；
- **修复规则**：
  ```python
  re.sub(r'\b(USA|EUR|CHN|ASI|GLB|IND)\.([a-z][a-z0-9_]+)\b', r'\2', text, flags=re.IGNORECASE)
  ```

### 2.2 非法一元正负号清理 (Leading Signs)
- **幻觉现象**：括号内多余的正号 `(+field)` 或 `(+ts_mean(`；
- **修复规则**：强制剔除紧随左括号后的冗余 `+` 号。

### 2.3 遗漏逗号修复 (Missing Parameter Commas)
- **幻觉现象**：时序算子常将参数写为 `ts_rank(field 20)` 或 `ts_delta(field) 10`；
- **修复规则**：
  ```python
  cleaned = re.sub(r'\)\s+(\d+)', r'), \1', cleaned)
  ```

### 2.4 重复算子合并 (Duplicated Operators)
- **幻觉现象**：生成 `rankrank(x)` 或 `ts_meants_mean(x, 20)`；
- **修复规则**：利用正则捕捉相邻同词重复并压平为单算子。

### 2.5 括号对称平衡 (Parentheses Balancing)
- **自愈逻辑**：计算左括号 `(` 与右括号 `)` 计数差；若右括号缺失则尾部补全，若右括号多余则自右向左安全剥离。

---

## 3. 基于 SQLite 的报错学习与自愈记忆库 (Error Learning)

为实现“不踩同一块石头两次”，Gen 2 将静态校验器与仿真运行时报错紧密结合：

```
                ┌──────────────────────────────────────────┐
                │ 平台仿真报错回传 (Simulation Error JSON) │
                └────────────────────┬─────────────────────┘
                                     │
                                     ▼
                ┌──────────────────────────────────────────┐
                │   错误模式分类器 (Error Classifier)      │
                └────────────────────┬─────────────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
   [unknown_variable]         [invalid_field]          [type_incompatible]
   字段在当前大区不存在       字段不支持当前 Delay 0      时序与截面算子入参倒置
           │                         │                         │
           └─────────────────────────┼─────────────────────────┘
                                     │
                                     ▼
                ┌──────────────────────────────────────────┐
                │ 写入 SQLite: generation_two_backtests.db │
                │ 1. 字段禁用黑名单 (Blacklist)            │
                │ 2. 算子参数约束规则库 (Param Constraints)│
                │ 3. 错误拓扑纠正映射表 (Correction Maps)  │
                └──────────────────────────────────────────┘
```

### 3.1 核心错误模式匹配映射
- **`unknown_variable` / `invalid_field`**：自动将该字段加入当前 `(region, delay, universe)` 维度的**黑名单拦截池**，后续生成直接过滤；
- **`type_error`**：识别出事件型（Event）字段不能直接送入普通连续型差分算子，自动外层注入 `ts_backfill` 或 `group_rank`；
- **`missing_lookback`**：对时序算子缺失的周期参数，根据该算子在本地配置中的基准值（默认 20 或 5）自动补足。
