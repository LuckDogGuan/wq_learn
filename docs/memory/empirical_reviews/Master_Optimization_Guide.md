# 平台 Alpha 挖掘与优化方向指南 (Master Optimization Guide)

本文档综合了 2026年8月2日-8月4日 期间两百多份批量模拟日志（涵盖 GLB 和 GBR 市场以及 PC 优化测试）的实证结果。
在后续的 Alpha 挖掘中，请严格遵守以下被验证过的“正确方向”和“失效边界”。

---

## 1. 降低 PC (Production Correlation) 的有效方向与代价

降低 PC 往往以牺牲因子质量为代价，必须在以下范围内仔细权衡：

### ✅ 有效且推荐的方向
*   **分组中性化 (`group_neutralize`)**：
    *   **原理**：在 EUR 和 GLB 市场中，利用 `industry`, `sector` 或 `subindustry` 进行中性化对降低 PC 有稳定的改善作用。
    *   **适用范围**：建议配合较长的平滑窗口（如 `d=768` 或 `1024`），这样可以在降低 PC 的同时保护基础质量（Sharpe / IS Ladder）。
    *   **风险防范**：单纯叠加中性化可能导致 Margin 被压低至 `<10bp`，需随时监控双边换手与利润空间。

### ⚠️ 有效但需谨慎的方向
*   **平滑函数 (`ts_mean`, `ts_decay_linear`)**：
    *   **原理**：外层叠加短窗口平滑能单调降低 PC，并改善换手率和 Margin。
    *   **适用范围**：只能用于微调，短窗口（如 `d=3` 到 `d=10`）。
    *   **风险防范**：窗口变长会**严重损失** Fitness 和 IS Ladder。**不要盲目沿同一平滑窗口方向死扫长周期**。当短窗口平滑无法降 PC 至阈值时，应转向替换核心因子逻辑。

### ❌ 明确失效或反作用的方向 (请勿继续尝试)
*   **截面排序/分位数作为第二腿 (`ts_quantile`, `ts_zscore`)**：
    *   虽然能显著降低 PC，但极易造成 Sub-universe 覆盖率失败，或将收益质量摧毁，属于“PC降了但质量毁了”的无效方向。
*   **`group_scale`**：
    *   不会降低 PC，反而会推高 PC 至接近 1，并导致单边化（Short Count=0）。
*   **`ts_av_diff`**：
    *   虽然具有强烈的去相关作用，但会把 Alpha 质量（Sharpe/Fitness）降至零附近。

---

## 2. 市场别挖掘策略指导

### GLB (Global) 市场
*   **成功骨架**：“实际基本面 (Actual Fundamentals) + 分析师预期 (Analyst Estimates)”双轮驱动，结合细粒度 `subindustry` 中性化。
*   **成功案例**：`ebitda_quarterly`, `mdl30_smartestimate_fy2_eps`, `anl10_cpsfy1_smart_ests_v2_6267` 等字段表现优异，并已成功产出 `Sharpe > 1.25`, `PC < 0.70` 的 Golden Alphas。
*   **后续指导**：
    *   当一个数据集或字段家族被**穷尽测试**且无法通过硬门槛时，应**果断停止**在同一模板上叠加操作符。
    *   优先切换到**未点亮**（未使用过）的**高覆盖率数据集**（例如 `fundamental44`, `earnings_sent_matrix`）。

### GBR (UK) 市场 (当前面临瓶颈)
*   **实证现状**：在 `analyst_earnings_ibes`, `model264`, `news18`, `shortinterest3`, `risk88` 等多个数据集、超过上百批次的测试中，通过率几乎为 0。
*   **核心矛盾**：
    *   收益强度好的变体（如 `ts_delta`）换手率通常过高（`>30%`）。
    *   满足换手率要求的变体（如 `ts_rank`, `ts_decay`）在风险中性化（RN Sharpe/Fitness）和 2Y Sharpe 稳定性上严重不足。
*   **后续指导**：
    *   当前 GBR 市场的模板骨架已明确被验证为**失效**，必须停止继续套用同一类算子组合。
    *   必须引入全新的多字段组合理念、跨期交叉逻辑，或者暂停对 GBR 市场的死磕，将算力转移回具有优势的 GLB 或其他市场。

---

## 3. 基础准则复述 (Safety & Boundaries)

1. **先过硬门槛**：只有当 Sharpe、Fitness、2Y Sharpe、Margin、Turnover 基础门槛和风险中性化门槛**全部明确通过**时，才允许进行后续的 robust、严格过拟合、生产相关性和属性设置测试。
2. **及时止损**：如果 `platform status` 为 `RESULTS_RECONCILED/BASIC_GATES_FAILED`，或者生产相关性返回结果为 `>0.7` 或未返回，均不可进入提交流程候选池。
