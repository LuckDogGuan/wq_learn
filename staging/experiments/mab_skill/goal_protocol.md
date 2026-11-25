# `/goal` 触发指令专用交互协议与执行状态机

> **归档位置**：`doc/多臂老虎机_挖掘总结Skill/goal_protocol.md`  
> **指令源文**：`gaol_commd\test_goal.md:L3`  
> **核心作用**：定义 `/goal` 指令被触发时的全套解析规则、参数映射矩阵、执行状态机与停机准则

---

## 1. 原始指令原文与核心语义解构

### 1.1 触发指令原型
```text
/goal 挖掘region=eur 探索不同的universe delay=D1 max_trade=ON REGULAR类型的alpha sharpe>1.58 fitness>1 2ysharpe>1.6 margin>5bp，turnover>5%,turnover<30%，risk neutralization表现要好sharpe>1,fitness>0.7,margin>5bp，操作符数量<8，ra_failed_count=0，挑选未点亮的金字塔的1个数据集，不要频繁切换数据集除非alpha模板多样性已穷尽并且查阅论坛还是无计可施，使用1-2个字段，直到找到3个满足提交要求的不同数据集的完全不同策略风格的单数据集的未提交的alpha,这些alpha彼此之间的相关性<0.4，去点亮更多的金字塔,否则不要停下来，生产相关性结果没有出来或生产相关性>0.7的alpha不符合提交要求，不要提交，不要提交，记住了吗，我想自己手动提交。回测使用multi_create_simulate 8个并发，不要使用create_simulate，每找到一个就test robust和进行严格的过拟合测试,then pass帮我设置好属性。不要使用trade_when\add\multiply，不要创建自动化任务, 可以参考论坛模板与idea文章,每10轮回测进行alpha表达式多样性评估，包括操作符探索率，字段探索率，模板骨架多样性，风格多样性，预处理，收益来源归因，失效风险等进行总结和扫盲，中文回答
```

### 1.2 关键参数解析对照表

| 指令参数项 | 解析值 | 平台/系统映射规则 | 强制性等级 |
|:---|:---|:---|:---:|
| **`region`** | `EUR` | 设定为欧洲市场 | **强制** |
| **`universe`** | 探索不同宇宙 | 优先选用 `TOPCS1600`（通关率89.6%），备选 `TOP2500` | **强制** |
| **`delay`** | `D1` (Delay 1) | T+2 日撮合，排除微观高频白噪声 | **强制** |
| **`max_trade`** | `ON` | 平台仿真参数设置 `maxTrade: "ON"` | **强制** |
| **`type`** | `REGULAR` | 标准常规截面 Alpha | **强制** |
| **`sharpe`** | `> 1.58` | 全样本 In-Sample 夏普比率及格线 | **强制** |
| **`fitness`** | `> 1.00` | 全样本适应度及格线 | **强制** |
| **`2ysharpe`** | `> 1.60` | 最近 2 年夏普比率，杜绝阶梯夏普断崖 | **强制** |
| **`margin`** | `> 5 bp` | 单笔交易净利润率必须 $> 0.0005$ | **强制** |
| **`turnover`** | `5% ~ 30%` | 严格锁死换手率走廊 | **强制** |
| **`risk neutralization`** | RN Sharpe > 1.0, Fitness > 0.7, Margin > 5bp | 风险中性化（风格/行业对冲后）表现硬性指标 | **强制** |
| **`操作符数量`** | `< 8` | 算子总数严格限制在 7 个以内 | **强制** |
| **`ra_failed_count`** | `== 0` | 平台所有子项门禁零告警（全绿通关） | **强制** |
| **`禁用算子`** | 严禁 `trade_when`, `add`, `multiply` | AST 生成时直接前置拦截 | **绝对禁止** |
| **`数据源与金字塔`** | 挑选未点亮金字塔的 1 个数据集，使用 1~2 个字段，不频繁切换 | 使用 `scripts/webdata_quality` 预选 T1/T2 字段深耕 | **强制** |
| **`回测并发`** | 强制使用 `multi_create_simulate` (8 并发) | 严禁调用单任务 `create_simulate` | **强制** |
| **`提交策略`** | **严禁自动提交！** (`submit_alpha` 封禁) | 仅设置属性，由研究员在 Web 端手动点击提交 | **绝对禁止** |
| **`相关性标准`** | 内部两两相关性 `< 0.40`；生产相关性 `< 0.70` | 未出生产相关性结果一律禁止提交 | **强制** |
| **`多样性评估周期`** | 每 10 轮回测 | 调用 `diversity_evaluator.py` 生成完整中文报告 | **强制** |
| **`停机目标 (Goal)`** | **3 个不同数据集、完全不同策略风格、互相关性 < 0.4 的全绿未提交 Alpha** | 未达成前不得提前终止任务 | **核心目标** |

---

## 2. 执行状态机与流转图 (Execution State Machine)

```mermaid
stateDiagram-v2
    [*] --> S1_Init: 接收 /goal 指令
    S1_Init --> S2_PyramidScan: cnhkmcp: get_pyramid_alphas & multipliers
    S2_PyramidScan --> S3_DataPrior: webdata_quality 离线预检 + cnhkmcp: get_datasets, get_datafields
    S3_DataPrior --> S4_LockPyramid: 锁定 1 个未点亮金字塔单数据集 (深耕不频繁跳跃)
    
    S4_LockPyramid --> S5_MAB_Generate: MAB 多臂老虎机分层决策生成 8 候选
    note right of S5_MAB_Generate: 遇阻调用 cnhkmcp: search_forum_posts
    S5_MAB_Generate --> S6_HardRuleCheck: 严格硬规则审查 (<8算子, 禁trade_when/add/multiply)
    
    S6_HardRuleCheck --> S5_MAB_Generate: 违规重生成
    S6_HardRuleCheck --> S7_MultiSim: cnhkmcp: create_multi_simulation (8并发)
    note right of S7_MultiSim: 报错调用 cnhkmcp: lookINTO_SimError_message
    
    S7_MultiSim --> S8_MetricAudit: cnhkmcp: get_alpha_details, get_alpha_yearly_stats
    S8_MetricAudit --> S9_PreSubCheck: cnhkmcp: get_submission_check (0 Checks Fail)
    S9_PreSubCheck --> S10_MAB_Feedback: 更新 MAB 汤普森采样 Beta 奖励
    
    S10_MAB_Feedback --> S11_MilestoneCheck: 检查是否达到 10 轮整数倍？
    S11_MilestoneCheck --> S12_DiversityReport: diversity_evaluator.py (中文多维雷达与扫盲)
    S12_DiversityReport --> S13_WinningAudit
    S11_MilestoneCheck --> S13_WinningAudit: 未满 10 轮
    
    state S13_WinningAudit {
        [*] --> CheckCorr: cnhkmcp: check_correlation (内部<0.4 & 生产<0.7)
        CheckCorr --> SetProp: cnhkmcp: set_alpha_properties (配置标签色彩, 严禁自动提交!)
        SetProp --> RegisterWinner: 存入胜者池 (需来自完全不同数据集)
    }
    
    S13_WinningAudit --> S14_GoalDecision: 评估胜者池计数
    S14_GoalDecision --> S5_MAB_Generate: 胜者数 < 3 (继续挖掘，不准停下)
    S14_GoalDecision --> [*]: 胜者数 == 3 (圆满达成目标，输出 GOAL_COMPLETE)
```

---

## 3. `cnhkmcp` 工具链在各状态的调用清单

| 状态机节点 | 核心绑定的 `cnhkmcp` 工具 | 触发参数与关键入参 | 预期输出与系统决策 |
|:---|:---|:---|:---|
| **S2_PyramidScan** | `get_pyramid_alphas`<br>`get_pyramid_multipliers` | `{}` | 输出各金字塔分类的持仓 Alpha 数量与乘数，锁定为 0 的未点亮目标 |
| **S3_DataPrior** | `get_datasets`<br>`get_datafields` | `region="EUR"`, `universe="TOPCS1600"`, `delay=1`, `dataset_id="..."` | 校验线上字段活性与数据类型（`MATRIX`/`VECTOR`），防止类型不匹配 |
| **S5_MAB_Generate (遇阻)** | `search_forum_posts`<br>`read_forum_post` | `search_query="<dataset> TOPCS1600"`, `max_results=10` | 检索官方顾问在同类数据集上的构造经验与算子拓扑，突破探索瓶颈 |
| **S7_MultiSim** | `create_multi_simulation` | `alpha_expressions=[...8个...]`, `region="EUR"`, `universe="TOPCS1600"`, `neutralization="SUBINDUSTRY"`, `max_trade="ON"`, `decay=5`, `truncation=0.08` | 8 并发原生批量回测，同步等待 8+ 分钟直至全部完成 |
| **S7_MultiSim (排障)** | `lookINTO_SimError_message` | `locations=["/simulations/..."]` | 抓取子任务底层报错详情，更新 MAB 语法修复库 |
| **S8_MetricAudit** | `get_alpha_details`<br>`get_alpha_yearly_stats` | `alpha_id="..."` | 提取 Sharpe (>1.58), Fitness (>1.0), Margin (>5bp), 2Y Sharpe (>1.6) |
| **S9_PreSubCheck** | `get_submission_check` | `alpha_id="..."` | 穿透式核查 `CONCENTRATED_WEIGHT`, `IS_LADDER_SHARPE`, `ra_failed_count==0` |
| **S13_WinningAudit** | `check_correlation`<br>`set_alpha_properties` | `correlation_type="both"`, `threshold=0.70`<br>`color="GREEN"`, `tags=[...]` | 验证两两相关性 `<0.4` 与生产相关性 `<0.7`；设置因子标签与属性；**绝对封禁 `submit_alpha`** |

---

## 4. 跨轮次持久化与断点续传 (Checkpoint Recovery)

为了支持长时间（如跨夜）无监督自主运行，系统在 `tracking/` 目录下维护持久化检查点：
- **`tracking/mab_checkpoint.json`**：实时记录当前轮次、胜者列表、数据集分配、MAB 权重状态；
- **`tracking/alpha_goal_state.json`**：记录各候选 Alpha 的 ID、表达式、详细指标与两两相关系数矩阵；
- **自愈重连**：当发生网络偶发超时时，自动挂起 15 分钟并通过只读接口对账，绝不重发重复请求。
