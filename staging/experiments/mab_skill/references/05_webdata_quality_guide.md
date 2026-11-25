# WebDataScope 离线质量先验与金字塔点亮指南

> **归档位置**：`doc/多臂老虎机_挖掘总结Skill/references/05_webdata_quality_guide.md`  
> **数据工具源**：`doc/多臂老虎机_挖掘总结Skill/scripts/webdata_quality`  
> **核心任务**：预先锁定高质量（T1/T2）、非过载（5 ≤ Count < 500）的未点亮金字塔冷门数据集

---

## 1. 为什么必须先进行离线数据质量审计？

在 WorldQuant BRAIN 平台上，超过 60% 的新进研究员失败于**“在错误的数据集上做徒劳的公式微调”**：
- **物理稀疏陷阱**：部分冷门数据集在 EUR 市场的覆盖度不足 20%，且长期无更新。任何数学算子都无法弥补底层数据的物理缺失，必然引发 `CONCENTRATED_WEIGHT` 或 `LOW_SUB_UNIVERSE_SHARPE`。
- **过载拥挤陷阱**：如 `fundamental6` 或 `analyst4` 的某些热门字段，全平台已有上万个 Alpha 提交，即便夏普达到 3.0，也会在终审时因 `MATCHES_THEMES` 或 `PROD_CORRELATION > 0.70` 被硬性拒审。
- **WebDataScope 先验工具**：通过离线快照，以零网络成本在秒级时间内完成全大区、全宇宙、全数据集的“覆盖度、稳定性、偏度、单边性、社区挖掘热度”体检。

---

## 2. 字段分档 (Field Tiers) 判别标准

依据 `scripts/webdata_quality/tier_rules.json`，字段健康度划分为四档：

| 档位 | 覆盖率均值 (Recent Mean) | 最低覆盖率 (Recent Min) | 绝对偏度 (Abs Skew) | 建议处理策略 |
|:---:|:---:|:---:|:---:|:---|
| **T1 (顶级健康)** | $\ge 90\%$ | $\ge 80\%$ | $\le 0.50$ | **优先选用**，分布近似对称高斯，天然免疫集中度报警 |
| **T2 (优质稳健)** | $\ge 80\%$ | $\ge 50\%$ | $\le 1.00$ | **完全可用**，建议外层搭配轻度线性平滑 (`ts_decay_linear`) |
| **T3 (中度稀疏)** | $\ge 50\%$ | $< 50\%$ | $> 1.00$ | **谨慎使用**，必须搭配 `winsorize` 且严禁裸相加 |
| **T4 / RED** | $< 50\%$ | 极低 | 极端偏态 | **坚决废弃**，强行挖掘必然触发平台硬拦截 |

---

## 3. 金字塔冷门数据集优选准则 (Unlit Pyramid Sourcing)

为了高效点亮未点亮金字塔（Unlit Pyramid），筛选规则必须严格遵循：

1. **Count 过滤走廊 (`5 ≤ Count < 500`)**：
   - $\text{Count} < 5$：几乎无人涉足或数据存在断点缺陷，盲目探索沉没成本极高；
   - $\text{Count} \ge 500$：已被平台数百人深入挖掘，主题冲突与生产相关性超标风险极大；
   - **$5 \le \text{Count} < 500$**：**黄金淘金走廊**！既保证了数据的有效可用性，又保留了极高的蓝海独创性空间。
2. **数据集深耕纪律 (No Frequent Hopping)**：
   - 锁定 1 个未点亮的优质数据集后，**严禁频繁切换**！
   - 在该数据集内，运用不同的策略风格（动量衰减、组内标准化、反转、比率）持续深挖；
   - 唯有在模板多样性已彻底穷尽且查阅论坛仍无突破时，方可按计划平移至下一个候选数据集。

---

## 4. 离线质量导出实操命令

在终端中执行以下命令，导出 EUR 区域未点亮金字塔的候选特征库：

```powershell
python "doc\多臂老虎机_挖掘总结Skill\scripts\webdata_quality\webdata_quality.py" `
  --region EUR `
  --delay 1 `
  --universe TOPCS1600 `
  --field-tiers "T1,T2" `
  --count-min 5 `
  --count-max 500 `
  --sharpe-min 1.0 `
  --fitness-min 0.8 `
  --output "doc\多臂老虎机_挖掘总结Skill\scripts\webdata_quality\output\EUR_TOPCS1600"
```

该工具将自动生成标准 XLSX 报表与字段清单，供老虎机挖掘引擎作为高质量特征输入。
