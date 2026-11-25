# 多臂老虎机自主因子挖掘 Skill (独立自包含版)

> **位置**：`doc/多臂老虎机_挖掘总结Skill/`  
> **核心入口**：[SKILL.md](SKILL.md)  
> **协议规范**：[goal_protocol.md](goal_protocol.md)

---

## 概述

本 Skill 是一个基于**多臂老虎机（汤普森采样，Thompson Sampling）**与 **WorldQuant BRAIN 平台实战通关经验库**深度结合的自主量化因子挖掘流水线。

本模块为**完全独立且自包含（Self-Contained）的专属 Skill**，内嵌了完整的离线数据质量审计工具源、高阶算子拓扑库、严格门禁校验器、8 并发批量仿真调度器及每 10 轮多样性复盘报告生成器。

---

## 目录结构导航

```text
doc/多臂老虎机_挖掘总结Skill/
├── SKILL.md                                 # Skill 核心入口规范 (YAML frontmatter + SOP)
├── goal_protocol.md                         # /goal 触发指令专用交互协议与执行状态机
├── README.md                                # 本文档：快速概览与使用指南
│
├── references/                              # 理论手册与量化实证知识库
│   ├── 01_mab_thompson_engine.md            # 贝叶斯汤普森采样数学原理与分层老虎机推导
│   ├── 02_wqb_hard_rules_and_antipatterns.md# 生产十条铁律与全量门禁避坑指南
│   ├── 03_eur_market_mastery.md             # 欧洲市场深度复盘 (TOPCS1600 89.6%胜率秘诀)
│   ├── 04_gold_expression_templates.md      # 六大风格、小于8算子的殿堂级工业模板库
│   └── 05_webdata_quality_guide.md          # WebDataScope 离线质量先验与金字塔点亮指南
│
└── scripts/                                 # 独立执行脚本库
    ├── webdata_quality/                     # 因子数据源工具链 (完整自包含)
    │   ├── webdata_quality.py               # 离线质量主筛选程序
    │   ├── webdata_loader.py                # 离线快照加载器
    │   ├── webdata_classifier.py            # 字段档位与风险分类器
    │   ├── webdata_exporter.py              # XLSX 导出与校验器
    │   ├── tier_rules.json                  # T1-T4 质量分档规则
    │   └── WebData_20260219_V0.10.9.zip     # 离线数据快照底座
    │
    ├── mab_core.py                          # 汤普森采样臂、分层老虎机与严格门禁校验器
    ├── diversity_evaluator.py               # 每 10 轮多样性审计与扫盲分析生成器
    └── run_mab_miner.py                     # 自主挖掘总控编排器
```

---

## 快速使用说明

### 1. 触发方式
在与量化助手对话时，输入 `/goal` 指令（或配合定制参数）：
```text
/goal 挖掘region=eur 探索不同的universe delay=D1 max_trade=ON REGULAR类型的alpha sharpe>1.58 fitness>1 2ysharpe>1.6 margin>5bp，turnover>5%,turnover<30%，risk neutralization表现要好sharpe>1,fitness>0.7,margin>5bp，操作符数量<8，ra_failed_count=0，挑选未点亮的金字塔的1个数据集，不要频繁切换数据集除非alpha模板多样性已穷尽并且查阅论坛还是无计可施，使用1-2个字段，直到找到3个满足提交要求的不同数据集的完全不同策略风格的单数据集的未提交的alpha,这些alpha彼此之间的相关性<0.4，去点亮更多的金字塔,否则不要停下来，生产相关性结果没有出来或生产相关性>0.7的alpha不符合提交要求，不要提交，不要提交，记住了吗，我想自己手动提交。回测使用multi_create_simulate 8个并发，不要使用create_simulate，每找到一个就test robust和进行严格的过拟合测试,then pass帮我设置好属性。不要使用trade_when\add\multiply，不要创建自动化任务, 可以参考论坛模板与idea文章,每10轮回测进行alpha表达式多样性评估，包括操作符探索率，字段探索率，模板骨架多样性，风格多样性，预处理，收益来源归因，失效风险等进行总结和扫盲，中文回答
```

### 2. 独立脚本运行
可在项目根目录直接调用 Python 脚本执行离线测试：
```powershell
python "doc\多臂老虎机_挖掘总结Skill\scripts\run_mab_miner.py"
```
