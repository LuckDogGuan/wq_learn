# WorldQuant BRAIN D1-Only 统一启动指令中心 (`goal/START_HERE.md`)

> [!IMPORTANT]
> - **核心设计**：本目录（`goal/`）已保存在 Git 仓库并同步至 GitHub（`origin/main`）。无论在 **Antigravity（默认 Google Neon 模型）、ChatGPT / Codex、Claude Code 还是 Cursor** 中启动，或是在 `/compact` 清空上下文后重开，均从本文件复制对应启动指令即可。
> - **默认子代理策略**：默认主模型与子代理均为 **Google 模型（Neon）**，**子代理默认思考强度为 `中 (medium)`**（防止单轮 1–2 参数微调过度发散耗时）；也可在启动指令中一键指定切换为 ChatGPT 或指定任意 `Region / Universe / Category / 研究方式`。

---

## 1. 标准一键启动指令（使用 `goal/run_config.json` 默认配置）

当您开启新窗口、切换 AI 工具或执行 `/compact` 后，直接粘贴以下指令：

```text
请读取 goal/run_config.json、AGENTS.md、docs/agents/CORE_STATE.json 和 docs/agents/OPTIMIZATION_LEDGER.json，按 wq-d1-closed-loop 技能启动：
1. 先检查上轮回测结果，对照基线输出「[有效] xxx 情况有效 / [无效] yyy 情况无效」并更新 OPTIMIZATION_LEDGER.json；
2. 遵循「严进（华子哥+课堂53课选种子）-> 宽中（Stage 1-2 QUICK 快筛 + 5:5 成熟模板 + 剪枝）-> 专终（Stage 3-4 王哥/Top100 控制变量专一优化）」流程推进；
3. 对 0-FAIL 候选查本地 95-OS SC 与 GET /alphas/{id}/correlations/prod 的 PC 范围分布表（[min, max, alphas]）：严格优先 PC < 0.70（PC > 0.70 即使豁免也建议少交）；若 0.70<=PC<=0.75 且 >=0.7 区间因子数 <=5 则优化 1-2 轮，若数据很多或优化 1-2 轮无改善（或常规种子优化 2-3 轮无效果）则停止优化并打标休眠归档；
4. 子代理默认使用 Google Neon 模型、思考强度「中 (medium)」，每轮只做 1-2 个参数的控制变量优化。
```

---

## 2. 自定义方向启动指令模板（按需指定地区 / 宇宙 / 类别 / 研究方式 / 子代理模型）

如果您在开始时想指定特定方向（如单攻某个地区、宇宙、数据类别或切换子代理），复制并修改括号中的内容即可（未指定的项自动继承 [goal/run_config.json](file:///c:/Wq/WorldQuant%20Brain/goal/run_config.json) 的默认值）：

```text
请读取 goal/run_config.json、AGENTS.md、docs/agents/CORE_STATE.json 和 docs/agents/OPTIMIZATION_LEDGER.json，按以下自定义参数覆盖启动本轮研究：
- 目标地区 (Region)：【默认 USA,EUR | 可改如 ASI / GLB / DEU / CHN】
- 宇宙范围 (Universe)：【默认 USA=TOP3000, EUR=TOP2500 | 可改如 TOP1200 / MINVOL1M / TOP500】
- 数据集类别 (Category)：【默认 model,analyst,fundamental,other | 可改如仅跑 model 或 analyst】
- 研究方式 (Research Mode)：【默认 SEED_TO_USEFUL_CLOSED_LOOP | 可选 STAGE12_QUICK_SCREEN_ONLY / STAGE3_DEDICATED_OPT_ONLY / ADMIN_TEMPLATE_VALIDATION / DATAFIELD_6PROBE_EXPLORE】
- 模板比例 (Template Ratio)：【默认 5:5 (成熟模板) | 管理员模板验证扩充后可切 8:2】
- 子代理配置 (Sub-Agent)：【默认 Google Neon 模型，思考强度：中 (medium) | 可改如 ChatGPT OpenAI 思考强度：中】
请先汇报上轮「有效/无效」验真结论，再按该方向生成并执行本轮控制变量批次。
```

---

## 3. 命令行启动与广州下一轮切换 `Stage 1-2 QUICK` 模式命令

> **当前状态**：广州服务器当前批次保持 `FULL` 继续运行不中断；代码已升级支持 **`--stage12-mode QUICK`**（Stage 1–2 自动用 `QUICK` 快筛，Stage 3 `S3-*` 专一精修批次自动强制保持 `FULL`！）。

当广州当前批次跑完、准备在**下一轮**切换 Stage 1–2 为 `QUICK` 模式时，执行以下命令即可：

```powershell
# 本地测试 / 读取 goal/run_config.json 启动（Stage 1-2 用 QUICK，Stage 3 自动锁定 FULL）
cd "c:\Wq\WorldQuant Brain\wq_research_v2"
$env:PYTHONPATH="c:\Wq\WorldQuant Brain\wq_research_v2\src"
python -m wq_research_v2.daemon_ra_runner --goal-config "../goal/run_config.json" --stage12-mode QUICK --mode FULL --max-batches 4
```

```bash
# 广州服务器下一轮切换 Stage 1-2 为 QUICK 模式（Stage 3 仍强制 FULL）
/root/miniconda3/bin/python -u -m wq_research_v2.daemon_ra_runner \
  --goal-config /root/worldquont/goal/run_config.json \
  --region EUR,USA --slots 4 --max-per-region 2 --region-caps EUR:1,USA:3 \
  --batch-size 8 --post-stagger 2.0 \
  --stage12-mode QUICK --mode FULL \
  --daily-target 4500 --round-robin-waves 1 --early-stop-sims 48 \
  --prune-jaccard 0.78 --prune-max-per-field 2 --prune-max-per-dataset 6 --loop
```

---

## 4. 关键真源与 GitHub 保存清单

| 用途 | 仓库路径（已纳入 Git / GitHub） |
| --- | --- |
| **启动指令中心** | [goal/START_HERE.md](file:///c:/Wq/WorldQuant%20Brain/goal/START_HERE.md) |
| **可配置方向与子代理参数** | [goal/run_config.json](file:///c:/Wq/WorldQuant%20Brain/goal/run_config.json) |
| **动态演进流程图（严进 -> 宽中 -> 专终）** | [goal/PIPELINE_FLOWCHART.md](file:///c:/Wq/WorldQuant%20Brain/goal/PIPELINE_FLOWCHART.md) |
| **轻量核心脉搏（`< 4 KB`）** | [docs/agents/CORE_STATE.json](file:///c:/Wq/WorldQuant%20Brain/docs/agents/CORE_STATE.json) |
| **控制变量有效/无效归因账本** | [docs/agents/OPTIMIZATION_LEDGER.json](file:///c:/Wq/WorldQuant%20Brain/docs/agents/OPTIMIZATION_LEDGER.json) |
| **基础版 v1.0 冻结归档（一键回退真源）** | [docs/整理与研究/workflow/d1_ra_baseline_v1_frozen.json](file:///c:/Wq/WorldQuant%20Brain/docs/整理与研究/workflow/d1_ra_baseline_v1_frozen.json) |
| **PC 范围分布表解析与 1–2 轮止损器** | [wq_research_v2/src/wq_research_v2/pc_poller.py](file:///c:/Wq/WorldQuant%20Brain/wq_research_v2/src/wq_research_v2/pc_poller.py) |
