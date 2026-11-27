---
name: wq-d1-closed-loop
description: "WorldQuant BRAIN D1-Only RA 跨 AI 工具通用闭环技能（主 Agent 方向决策 + 子 Agent 控制变量优化 + 自动精简上下文）。在启动新一轮因子挖掘、2小时定时复盘、切换 AI 工具或执行 /compact 后调用。"
---

# WorldQuant BRAIN D1-Only 跨工具闭环技能 (`wq-d1-closed-loop`)

本技能将研究状态与对话历史彻底解耦，确保在 **Antigravity、Claude Code、Cursor、Codex** 等任何 AI 工具中均以 `< 8 KB` 极简上下文启动「采集 → Stage 1-2 快筛剪枝 → Stage 3 控制变量精修 → Stage 4 终检打标 → 有效/无效归因闭环」。

## 1. 启动第一步：只读加载轻量核心上下文（防上下文爆炸）

每次启动或 `/compact` 后，**只读以下 4 个轻量文件**（绝不扫描历史长对话）：
0. `goal/run_config.json` 与 `goal/START_HERE.md`（统一启动配置：自定义/默认 `Region`、`Universe`、`Category`、`Research Mode`、Stage 1-2 `QUICK` 模式、模板比例 `5:5 -> 8:2`、子代理默认 `dsh-opencode-go/deepseek-v4.1-flash`（先 probe，≤4 轮即弃））
1. `AGENTS.md`（硬红线：严格 `delay==1`、禁用 `+/*/trade_when`、精确 81 个 Gold 算子、零自动 `/submit`、Margin 优先、`Useful`/`SC_PASS` + `SC 0.xxx PC 0.xxx` 别名、8:2 查资料优先级）
2. `docs/agents/CORE_STATE.json`（当前专注的 1–2 个地区/数据集、现役 `Useful` 冠军、阶段 1–4 参数契约、Baseline v1.0 回退指针）
3. `docs/agents/OPTIMIZATION_LEDGER.json`（上轮哪些优化**有效 `[EFFECTIVE]`**、哪些**无效 `[INEFFECTIVE]`**）

> 若后续流程修改效果不如预期，随时对照或回退至冻结基准版：`docs/整理与研究/workflow/d1_ra_baseline_v1_frozen.json` 与 `docs/整理与研究/workflow/D1_RA_BASELINE_V1_MANUAL.md`。

## 2. 主 Agent + 子 Agent 闭环四步法

### Step A · 主 Agent 验真上轮结果并输出「有效 / 无效」归因
1. 查询 SQLite 台账（本地 `data/wq_v2_ledger.db` 或广州 `/root/worldquont/data/wq_v2_ledger.db`）最新完成批次。
2. 与母版基线（Parent Baseline）对比，必须明确归纳并追加写入 `docs/agents/OPTIMIZATION_LEDGER.json`：
   - **`[有效] xxx 的情况是有效的`**：写明在什么 Region/Dataset/母版上，单改了哪 1–2 个参数，使 Sharpe / 2Y / Fitness / Margin / PC 改善了多少；
   - **`[无效] yyy 的情况是无效的`**：写明什么改动导致指标劣化或超时，提取禁止重演规则。
3. 对任何新产出的 RA 硬检 `0-FAIL` 候选，立即按 Stage-4 规程执行：
   - 同步最新全量 OS（`LocalSCEngine.sync_os_alphas(client)`）算本地 SC `< 0.65`；
   - 按 **`Margin (bp)` 降序** 做池内两两正交剪枝（`< 0.68`）；
   - 串行查远程 PC（`pc_poller.py` 调用 `GET /alphas/{id}/correlations/prod` 解析 `records: [[min, max, alphas], ...]` 范围分布表）与官方 `/check`：
     - **严控 `PC < 0.70`**：仅当 `pc_max < 0.70`（且 RA 0-FAIL + SC < 0.65 + 池内正交最高 Margin）才打主力 **`Useful`** + 别名 `SC 0.xxx PC 0.xxx`；若 `PC >= 0.70` 即使触发 `+10%` Sharpe 官方豁免也建议少交（标记 `PC_EXEMPT_HIGH_PC_HOLD`）；
     - **PC 范围分布表定量判据（`parse_pc_histogram_records` · 已适当放宽多优化 1 轮）**：若 `0.70 <= pc_max <= 0.78` 且 `>= 0.70` 桶内生产因子总数 `alphas <= 10`、`>= 0.80` 桶 `alphas <= 2`，判定 `PC_RESCUE_NEAR_SPARSE`，值得回 Stage 3 专项优化 **`2–3` 轮（最多 3 轮）**；若 `>= 0.70` 区间数据很多（`alphas > 10`）或 `>= 0.80` 桶 `> 2` 或 `pc_max > 0.78` 或优化满 `3` 轮无改变，判定 `PC_ABANDON_CROWDED_OR_STALLED`，果断放弃继续压 PC，打 `SC_PASS` + 内部标记 `PC_STUCK_DORMANT` 休眠归档（严禁调 `/submit`）。

### Step B · 种子因子（Seed Factor）采集与 Stage 1–2 标准化快筛
1. **种子筛选固定规则**（`wq_research_v2/src/wq_research_v2/field_screener.py` · 融合华子哥四差距 + 顾问课堂 53 课 `worldquant-classroom-reference`）：
   - **选新集/低拥挤**：优先 `Alphas=0` 免额集（`2026-12-06` 截止）或 `aCnt <= 10` 或 WDS 产率 `osis/info < 10%` & `Sharpe > region_mean`；
   - **选有经济含义与高倍率塔**：先明确经济假设与预期正负方向，瞄准 `Value Factor > $1.5` 空白/高倍率金字塔；
   - **硬覆盖与类型门槛**：`coverage >= 0.75`（优选 `>= 0.80`）、`dateCoverage >= 0.60`（`>= 5–8` 年）、纯 `MATRIX` 优先（伪单值 `VECTOR` 只测 `vec_avg`），剔除元数据陷阱与黑名单；
   - **陌生字段 6 步探查**：必要时用 `build_datafield_inspection_probes()` 在 `Neutralization=NONE, Decay=0, testPeriod=P0Y0M` 下查真实非零覆盖与更新频率（`ts_std_dev(x, 5/22/66) != 0`）。
2. **Stage 1–2 标准化默认设置与 `FAST/QUICK` 模式**：
   - 默认固定 **`decay = 0`**、默认 **`neutralization = "SUBINDUSTRY"`**、**`testPeriod = "P0Y0M"`**、**`maxTrade = "OFF"`**（`2Y Test` 与全局 `maxTrade="ON"` 暂不开启，定于 **`2026-12-10`** 开启尝试）；
   - **阶段 1 与阶段 2 允许使用 `FAST/QUICK` 模式**（`simulationMode="QUICK", visualization=false`）加速初筛；
   - 满 48 条正向 `Sh >= 0.80` 命中率 `< 2%` 自动早停；晋级种子经 `seed_pruner.py`（`jaccard_max=0.78, max_per_field=2, max_per_dataset=6`）去重并做本地 SC `< 0.68` 初筛。

### Step C · 主 Agent 派发子 Agent 执行 Stage 3 控制变量优化（强制 `FULL` 模式）
1. 进入 Stage 3（`POOL_A` 种子 `Sh >= 1.25` 冲刺 `0-FAIL`）**严禁使用 `FAST/QUICK` 模式，强制锁定 `simulationMode="FULL"`**。
2. 主 Agent 向子 Agent（`invoke_subagent` 或同会话模块化调用）下达明确指令：
   - 冻结母版核心字段，**每轮只允许修改 1–2 个参数（控制变量法）**；
   - **标准参数轮询序列**：
     - 轴 1（Decay 轮询）：固定母版表达式与中性化，轮询 **`decay ∈ {0, 5, 20}`**（默认 `0` 起步，胜出点邻域再细扫 `{2, 4, 6}`）；
     - 轴 2（Neutralization 轮询）：固定最优 Decay，轮询 `SUBINDUSTRY` → `INDUSTRY` / `REVERSION_AND_MOMENTUM` / `CROWDING` / `STATISTICAL`；
     - 轴 3（单一短板手术 & **通用降换手规则**）：按 8:2 优先级（80% 王哥 + Top100 顾问 + 管理员/课堂53课）针对唯一 FAIL 项做单步改造；**所有流程必须检查换手率（`evaluate_turnover_action`）**：若 `TO > 18%` 则执行单变量降换手梯队（`decay ∈ {0, 5, 20}` → 前置/后置 `ts_decay_linear(10/22)`/`ts_mean(5/10/22)` → `ts_target_tvr_decay(lambda_max<=0.9)` → 仅无 `tail(newval=0)` 外壳时试 `hump(0.01)`，永久禁 `trade_when`）；**若 `TO < 8%`（换手偏低）则跳过降换手步骤**，避免稀释 Sharpe 或触发 `LOW_TURNOVER`。
   - **2–3 轮止损休眠铁律（`should_shelve_stalled_seed`）**：若某种子连续专一优化 **2–3 轮** 仍无有效提升，立刻停止消耗额度，打上 `STALLED_DORMANT_AFTER_3_ROUNDS` 标签连同瓶颈原因归档，留待未来找到新优化方法再定向唤醒。
    - **子代理默认配置**：默认 DSH，`dsh-opencode-go/deepseek-v4.1-flash`（tier=flash），启用前先 `dsh_worker_probe`（可用性未验证，probe 只证明 no-op 调用成功）；**每个子代理对一个任务负责完整闭环：提出意见 → 修改 → 结果（含自验证与回报），严禁把同一流程拆给多个代理接力**；**任务包按定时巡检间隔的 1.5 倍设计并留冗余**（3h 间隔 → 约 4.5h 工作量，超 2h 的拆成带检查点的段）；**每个子代理最多 4 轮对话，用满即丢弃换新**，状态靠 `docs/agents/TODO_20261127.md`、`.scratch/` 与账本文件传递；简报用 `docs/agents/SUBAGENT_BRIEF_TEMPLATE.md`，并禁止 commit/push/回测/submit；主 Agent 派单并以 `git diff` 与测试复核后写入有效/无效归因。其余见 `goal/run_config.json` → `subagent_profile`。
    - **证据分级**：结论一律标 `[V]` 已验证 / `[R]` 有报告未复核 / `[C]` 条件成立 / `[U]` 未验证，写账本时必须带标与适用坐标（见 `docs/agents/TODO_20261127.md` §0）。
    - **无新指令时**：按 `docs/agents/TODO_20261127.md` 自上而下执行第一个 `pending` 项，做完立即标记。
3. **嵌套层数治理**：
   - 调用 `compute_expression_nesting_metrics(expr)` 检查 `operator_count` 与 `nesting_depth`；
   - 优先保持 `operator_count <= 6`、`nesting_depth <= 4`；若 `nesting_depth >= 5` 或 `operator_count >= 7`，必须打上 `OVER_NESTED_TEMP_PC_FIX` 标签并完整记录每一层参数。

### Step D · 状态回写与上下文收敛
每轮结束时，更新 `docs/agents/CORE_STATE.json`、`docs/agents/OPTIMIZATION_LEDGER.json` 及对应地区档案（`docs/整理与研究/regions/*.md`），向用户汇报：
1. 上轮验证结论（**哪些有效 `[有效]`、哪些无效 `[无效]`**）；
2. 新增 `Useful`（按 Margin 降序）与 `SC_PASS` 清单；
3. 下轮主 Agent 锁定的 1–2 个控制变量优化方向。
