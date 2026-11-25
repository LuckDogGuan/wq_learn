# `cnhkmcp` 平台工具链实战全景与辅助决策手册

> **归档位置**：`doc/多臂老虎机_挖掘总结Skill/references/06_cnhkmcp_tool_handbook.md`  
> **服务名称**：`cnhkmcp` (WorldQuant BRAIN MCP Server)  
> **核心使命**：为多臂老虎机（MAB）自主挖掘提供在线金字塔勘测、8并发回测提交、指标穿透审计、双重相关性验证、仿真报错诊断与论坛灵感检索全链路支撑。

---

## 1. `cnhkmcp` 工具链在挖掘工作流中的赋能全景图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            1. 金字塔与数据集勘测                            │
│  - get_pyramid_alphas: 扫描未点亮金字塔分类与盲区                           │
│  - get_pyramid_multipliers: 查询平台当前金字塔激励倍数 (1.2x ~ 2.0x)        │
│  - get_datasets: 检索 EUR/TOPCS1600 下线上可用数据集                        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 锁定未点亮金字塔数据源
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            2. 字段类型与配置核准                            │
│  - get_datafields: 在线拉取字段元数据，识别 MATRIX/VECTOR/GROUP 数据类型    │
│  - get_platform_setting_options: 校验 Universe/Neutralization 合法枚举值    │
│  - (结合 webdata_quality 离线预检: 过滤 T1/T2 且 5 ≤ Count < 500 字段)      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 产出 8 个通过硬规则检查的表达式
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            3. 8 并发原生批量回测                            │
│  - create_multi_simulation: 一次性提交 8 个 Alpha (8并发，等待8分钟完成)    │
│  - lookINTO_SimError_message: 若部分子任务报错，即时抓取原因反哺 MAB 修复   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 回测完成，提取指标
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            4. 门禁穿透与年度阶梯体检                        │
│  - get_alpha_details: 提取 Sharpe (>1.58), Fitness (>1.0), Margin (>5bp)   │
│  - get_alpha_yearly_stats: 审查各年度 PnL，核验 2Y Sharpe > 1.60            │
│  - get_submission_check: 穿透审查 CONCENTRATED_WEIGHT 与 0 Checks Fail      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 门禁全绿
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            5. 双重相关性与属性配置                          │
│  - check_correlation: 校验两两候选间相关性 < 0.40 及 生产相关性 < 0.70     │
│  - set_alpha_properties: 配置颜色、标签、金字塔属性说明                     │
│  - 【严防死守】: 严禁调用 submit_alpha，等待研究员在 Web 端手动点击提交     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 遇阻检索
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            6. 论坛经验检索与策略脱困                        │
│  - search_forum_posts / read_forum_post: 模板多样性穷尽时查阅核心顾问经验   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 核心工具调用规范与参数详解

### 2.1 金字塔状态洞察：`get_pyramid_alphas` & `get_pyramid_multipliers`
- **调用时机**：挖掘启动之初（第 0 步），确定优先点亮哪个金字塔分类。
- **调用示例**：
  ```python
  # 查看金字塔分布
  pyramid_info = call_mcp_tool(
      ServerName="cnhkmcp",
      ToolName="get_pyramid_alphas",
      Arguments={}
  )
  # 查询当前激励系数
  multipliers = call_mcp_tool(
      ServerName="cnhkmcp",
      ToolName="get_pyramid_multipliers",
      Arguments={}
  )
  ```
- **决策赋能**：对比各分类下已有点亮 Alpha 数量，锁定当前计数为 0 或乘数最高的未点亮金字塔。

---

### 2.2 线上数据源核查：`get_datasets` & `get_datafields`
- **调用时机**：在离线 `webdata_quality` 选定候选数据集后，做线上活性核验。
- **调用示例**：
  ```python
  fields = call_mcp_tool(
      ServerName="cnhkmcp",
      ToolName="get_datafields",
      Arguments={
          "region": "EUR",
          "universe": "TOPCS1600",
          "delay": 1,
          "dataset_id": "model16"
      }
  )
  ```
- **决策赋能**：核查字段的 `data_type`（矩阵/向量/群组），确保不会在标量差分算子中误入向量字段；核对字段在线更新状态。

---

### 2.3 8 并发批量仿真：`create_multi_simulation`
- **调用时机**：MAB 生成 8 个合法候选 Alpha 后的统一提交执行。
- **调用示例**：
  ```python
  sim_results = call_mcp_tool(
      ServerName="cnhkmcp",
      ToolName="create_multi_simulation",
      Arguments={
          "alpha_expressions": [
              "ts_decay_linear(ts_delta(mdl16_operating_income_est, 10), 10)",
              "group_zscore(ts_decay_linear(ts_zscore(mdl16_ebit_est, 20), 5), subindustry)",
              "-1.0 * ts_decay_linear(ts_rank(mdl16_cashflow_est, 22), 5)",
              "ts_decay_linear(winsorize(ts_delta(mdl16_revenue_est, 5), std=3.0), 10)",
              "ts_target_tvr_decay(ts_zscore(mdl16_operating_income_est, 20), target_tvr=0.10)",
              "ts_decay_linear(divide(mdl16_operating_income_est, abs(mdl16_total_assets) > 0.001 ? mdl16_total_assets : 0.001), 10)",
              "group_zscore(ts_decay_linear(ts_delta(mdl16_ebit_est, 15), 10), subindustry)",
              "-1.0 * ts_decay_linear(ts_zscore(mdl16_revenue_est, 30), 10)"
          ],
          "region": "EUR",
          "universe": "TOPCS1600",
          "delay": 1,
          "decay": 5,
          "neutralization": "SUBINDUSTRY",
          "truncation": 0.08,
          "max_trade": "ON",
          "pasteurization": "ON",
          "unit_handling": "VERIFY",
          "nan_handling": "OFF",
          "language": "FASTEXPR"
      }
  )
  ```
- **关键提醒**：该工具会同步挂起轮询直至 8 个 Alpha 全部完成（通常 8~10 分钟），输出各子任务的 `alpha_id`、`sharpe`、`fitness`、`turnover`、`margin`。

---

### 2.4 仿真报错深度诊断：`lookINTO_SimError_message`
- **调用时机**：当 `create_multi_simulation` 中某些任务状态为 `ERROR` 或未返回指标时。
- **调用示例**：
  ```python
  error_details = call_mcp_tool(
      ServerName="cnhkmcp",
      ToolName="lookINTO_SimError_message",
      Arguments={
          "locations": ["/simulations/sim-xxxxxx"]
      }
  )
  ```
- **决策赋能**：提取精确错误原因（如“Data field not available for Delay 1”、“Division by zero”），自动将错误模式注入 MAB 修复库，阻断同类错误。

---

### 2.5 门禁穿透与 2 年阶梯体检：`get_alpha_details`, `get_alpha_yearly_stats`, `get_submission_check`
- **调用时机**：对 Raw Sharpe > 1.58 的候选 Alpha 进行深度准入审查。
- **调用示例**：
  ```python
  # 1. 年度统计审查 (验证 2Y Sharpe > 1.6)
  yearly = call_mcp_tool(
      ServerName="cnhkmcp",
      ToolName="get_alpha_yearly_stats",
      Arguments={"alpha_id": "alpha-xxxxxx"}
  )
  
  # 2. 平台 pre-submission 硬门禁审查 (验证 0 checks fail)
  sub_check = call_mcp_tool(
      ServerName="cnhkmcp",
      ToolName="get_submission_check",
      Arguments={"alpha_id": "alpha-xxxxxx"}
  )
  ```
- **审查核心**：
  1. `CONCENTRATED_WEIGHT`: 必须为 `PASS`；
  2. `IS_LADDER_SHARPE`: 必须为 `PASS`（最近 2 年无断崖式衰减）；
  3. `SUB_UNIVERSE_SHARPE`: 必须为 `PASS`（子宇宙流动性良好）；
  4. `ra_failed_count == 0`：所有硬性门禁无任何警告。

---

### 2.6 双重相关性过滤：`check_correlation`
- **调用时机**：门禁全绿后，作为入选胜者池前的最后一道关卡。
- **调用示例**：
  ```python
  corr_result = call_mcp_tool(
      ServerName="cnhkmcp",
      ToolName="check_correlation",
      Arguments={
          "alpha_id": "alpha-xxxxxx",
          "correlation_type": "both",
          "threshold": 0.70
      }
  )
  ```
- **双重判据**：
  1. **生产相关性 (`PROD_CORRELATION`)**：必须 `< 0.70`；如果相关性任务在后台排队未出结果，**严禁提交，继续等待或保持只读对账**；
  2. **胜者两两自相关性 (`SELF_CORRELATION`)**：必须 `< 0.40`，保证 3 个 Alpha 来自不同数据集且风格高度正交。

---

### 2.7 属性配置（防自动提交保护罩）：`set_alpha_properties`
- **调用时机**：完全符合提交要求的 Alpha 归档入池。
- **调用示例**：
  ```python
  call_mcp_tool(
      ServerName="cnhkmcp",
      ToolName="set_alpha_properties",
      Arguments={
          "alpha_id": "alpha-xxxxxx",
          "name": "EUR_TOPCS1600_Model16_RevisionMomentum",
          "color": "GREEN",
          "tags": ["MAB_MINED", "EUR", "TOPCS1600", "SUBINDUSTRY", "UNLIT_PYRAMID"],
          "regular_desc": "MAB generated revision momentum with linear decay, passing all hard checks."
      }
  )
  ```
- **安全红线**：**配置完属性后，绝对禁止调用 `submit_alpha` 工具！** 任务终止并生成《人工提交审查清单》，由研究员在 Web 端做最终复核并手动点击提交。

---

### 2.8 论坛灵感探索与脱困：`search_forum_posts` & `read_forum_post`
- **调用时机**：当前数据集连续多轮无法突破夏普或换手率门禁（"alpha模板多样性已穷尽并且查阅论坛还是无计可施"）。
- **调用示例**：
  ```python
  posts = call_mcp_tool(
      ServerName="cnhkmcp",
      ToolName="search_forum_posts",
      Arguments={
          "search_query": "model16 decay TOPCS1600",
          "max_results": 10
      }
  )
  ```
- **赋能作用**：借鉴官方论坛顶级量化顾问（王哥、贺六浑、台湾第一等）对特定数据集的算子设计心得与微观结构建议，注入全新先验。
