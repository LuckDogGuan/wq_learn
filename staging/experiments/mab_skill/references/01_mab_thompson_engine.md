# 多臂老虎机 (MAB) 与贝叶斯汤普森采样原理手册

> **归档位置**：`doc/多臂老虎机_挖掘总结Skill/references/01_mab_thompson_engine.md`  
> **适用场景**：Alpha 因子挖掘中的策略选择、算子匹配、参数调优与探索/利用平衡

---

## 1. 为什么量化因子挖掘需要多臂老虎机？

在 WorldQuant BRAIN 平台上挖掘 Alpha 面临典型的**探索与利用困境 (Exploration-Exploitation Dilemma)**：
- **过度探索 (Over-Exploration)**：随机盲目尝试冷门算子或未接触字段，产生大量语法错误、低夏普或无意义噪音，浪费每日仿真额度；
- **过度利用 (Over-Exploitation)**：发现一个 Sharpe 1.8 的因子后，仅微调参数（如从 20 天调到 22 天），导致自相关性飙升至 0.85+，触发平台拒审；
- **多臂老虎机 (MAB)** 提供了一套严格的概率论框架，使系统能够在“深挖高收益模式”与“跳出局部最优寻找全新金字塔”之间达成动态数学平衡。

---

## 2. 贝叶斯汤普森采样 (Thompson Sampling) 数学原理

相比传统的 $\epsilon$-贪心与 UCB1 算法，**汤普森采样 (Thompson Sampling)** 具有渐进最优性（匹配 Lai-Robbins 理论下界），且在非平稳金融环境中收敛速度更快。

### 2.1 统计模型：Beta-Bernoulli 过程
对于每一个动作臂 $a_k \in \mathcal{A}$（如某个算子骨架或变异路由），其未知真实胜率 $\theta_k$ 的先验分布设定为 Beta 分布：
$$
P(\theta_k) = \frac{\theta_k^{\alpha_k - 1}(1 - \theta_k)^{\beta_k - 1}}{\text{B}(\alpha_k, \beta_k)}
$$
- $\alpha_k \ge 1$：表征该臂历史成功的等效虚拟观测次数；
- $\beta_k \ge 1$：表征该臂历史失败的等效虚拟观测次数；
- 初始无信息先验：$\alpha_k = 1.0, \beta_k = 1.0$（即 $[0, 1]$ 均匀分布）。

### 2.2 决策抽样 (Sampling)
在每次需要决策下一个回测候选方案时，对所有候选臂的后验分布进行蒙特卡洛独立抽样：
$$
\tilde{\theta}_k \sim \text{Beta}(\alpha_k, \beta_k), \quad \forall a_k \in \mathcal{A}
$$
选取抽取值最大的臂执行：
$$
a^* = \arg\max_{a_k \in \mathcal{A}} \tilde{\theta}_k
$$

### 2.3 连续奖励归一化与贝叶斯更新
平台仿真返回的实际收益由多目标硬指标决定（Sharpe, Fitness, Margin, Turnover, 门禁检查）。将综合评分 $R \in [-1, 1]$ 线性映射至 $[0, 1]$：
$$
\tilde{R} = \text{clip}\left(\frac{R + 1.0}{2.0}, 0.0, 1.0\right)
$$
执行贝叶斯后验参数更新：
$$
\alpha_k \leftarrow \alpha_k + \tilde{R}, \quad \beta_k \leftarrow \beta_k + (1.0 - \tilde{R})
$$

---

## 3. 分层上下文老虎机架构 (Hierarchical Contextual Bandit)

在 Alpha 工业级生产中，决策不是孤立的单一参数，而是一条完整的逻辑链路：

```
Level 1: Dataset Arm (数据集臂)
   │  └─ 锁定未点亮金字塔核心数据集 (如 analyst4, model16, news12)
   ▼
Level 2: Strategy Style Arm (策略风格臂)
   │  ├─ Momentum (反转动量 / 趋势跟踪)
   │  ├─ Fundamental Revision (分析师预期修订 / 盈利意外)
   │  ├─ Volatility / Liquidity (波动率极化 / 流动性拥挤)
   │  └─ Value / Quality (基本面估值偏离 / 质量安全边际)
   ▼
Level 3: Skeleton Template Arm (骨架模板臂)
   │  ├─ 时序线性衰减差分: ts_decay_linear(ts_delta(x, d), p)
   │  ├─ 组内相对标准化: group_zscore(x, subindustry)
   │  └─ 动态换手平滑: ts_target_tvr_decay(x, target_tvr)
   ▼
Level 4: Parameter Grid Arm (参数网格臂)
      └─ 窗口参数 d ∈ {5, 10, 20, 40}, 平滑参数 p ∈ {5, 10, 20}
```

### 反向传播更新规则：
当一个完整的 Alpha 批次产生回测指标后，系统计算综合奖励 $R$，并沿决策树路径自底向上加权反向更新所有涉及的节点，确保整条优质路径的 Beta 分布整体向右偏移。
