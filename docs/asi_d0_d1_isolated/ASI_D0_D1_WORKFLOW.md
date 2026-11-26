# ASI D0/D1 独立隔离探索标准操作流程（SOP）

> **设计目标**：沉淀一套**与现有 `wq_research_v2` D1-Only RA 主线完全硬隔离**的 ASI 探索闭环，吸收官方 Workshop 03（帖子 `45233242695703`）方法论与实盘核查结果，支持在账号高额度（`> 4,000/天`）或专题冲刺期按需手动启停，**绝不污染主线台账、主线标签、主线额度或主线 D1-Only 纪律**。  
> **配套配置模板**：[asi_isolated_config.json](file:///c:/Wq/WorldQuant%20Brain/docs/asi_d0_d1_isolated/asi_isolated_config.json)  
> **独立实验日志（1 对 1）**：[asi_experiment_log.md](file:///c:/Wq/WorldQuant%20Brain/docs/asi_d0_d1_isolated/asi_experiment_log.md)（前缀 `[TRACK:asi_isolated]`）  
> **三条路线总目录**：[TRACKS_AND_LOGS_GUIDE.md](file:///c:/Wq/WorldQuant%20Brain/docs/TRACKS_AND_LOGS_GUIDE.md)  
> **帖子调研依据**：[POST_45233242695703_ANALYSIS.md](file:///c:/Wq/WorldQuant%20Brain/docs/asi_d0_d1_isolated/POST_45233242695703_ANALYSIS.md)

---

## 一、硬隔离架构（与主线 `wq_research_v2` 的绝对边界）

| 隔离维度 | 现有主线（`wq_research_v2` · D1-Only RA） | 本独立流程 · `ASI-D1 兼容分支` | 本独立流程 · `ASI-D0 隔离实验分支` |
| :--- | :--- | :--- | :--- |
| **配置文件** | `wq_research_v2/config/`、`docs/agents/CORE_STATE.json` | `docs/asi_d0_d1_isolated/asi_isolated_config.json` (`branches.asi_d1`) | `docs/asi_d0_d1_isolated/asi_isolated_config.json` (`branches.asi_d0`) |
| **调度接入** | 主定时守护与批量调度器 | **默认不接入主调度器**（`attached_to_main_scheduler: false`，仅人工显式触发） | **双重硬锁**（平台当前无 ASI D0 + `allow_d0_override: false`） |
| **SQLite 台账** | `data/wq_v2_ledger.db`（严禁混写） | **`data/asi_isolated_ledger.db`**（独立 WAL 库，表字段带 `branch='ASI_D1'`） | **`data/asi_isolated_ledger.db`**（独立表/分区 `branch='ASI_D0'`） |
| **平台标签命名** | `Useful` / `SC_PASS` / `SC_IS_HIGHT` / `PC_IS_HIGHT` | 探索期：**`ASI_EXP_D1`**；PPA 达标确认后：**`PPA_Useful`**（仅 Hybrid 同时过 RA 且人工复核后方可评估归档，默认不混打 `Useful`） | **`ASI_EXP_D0`**（绝不与 `Useful` / `PPA_Useful` 混用） |
| **Delay 约束** | 全局硬锁 `settings.delay == 1` | 严格锁定 **`delay = 1`**（含平台以 D1 供给的 `*_4` D0-offset 变体字段） | `delay = 0`（**当前平台实测不支持**，仅当未来平台开放且人工双签解锁后可用） |
| **绝对共用红线** | 禁用 `+`/`*`/`trade_when`；绝不自动 `/submit`；只对账 1 次；`MemoryMax=512M` | **完全继承全部安全红线** | **完全继承全部安全红线** |

---

## 二、额度 > 4,000 触发机制与预算隔离边界

为防止 ASI 探索抢占主线 `wq_research_v2`（`DEU/CHN/GLB/GBR` RA 冲刺 `92 → 100 OS`）的回测额度与并发槽位，启用前必须通过以下 **4 级额度门禁**：

1. **实时额度预检（必做）**：启动前调用 `GET /users/self/activities/simulations`（只读）读取当日已消耗回测数与账号当前日额度上限。
2. **高额度触发阈值（`daily_quota > 4000`）**：
   - 仅当账号**当日总回测额度 `> 4,000`**（或主线当日预算已完成/明确划出溢出配额）时，允许开启 ASI 常规额度批次；
   - **主线保底预留**：固定为主线 `wq_research_v2` 预留至少 `3,200/天` 额度（或总日额度的 `80%`）；
   - **ASI 独立单日封顶**：普通付费/常规额度单日上限 **`max_daily_normal_sims = 400`**（单轮严格 `2–4` 条控制变量，单波不超过 `24` 条，避免大批量盲扫浪费）。
3. **免额度通道优先（`2026-12-06` 截止前）**：
   - `Alphas = 0` 字段回测不消耗普通日额度（冻结至 `2026-12-06`）；
   - 优先消耗已验真的 ASI/D1 `Alphas = 0` 队列（`model25` 高覆盖免费字段、`model26` 免费字段、`ai_news_scores *_2` 纯 ASI D1、`model307` 出海营收），即使在主线高负荷期也能以接近零成本完成前期探针（仍须错峰执行，避免触发 429 限流）。
4. **2 小时止损熔断**：若任意单个数据集连续 `24–32` 条有效 `FULL` 回测后，正向 `Sharpe ≥ 1.0` 且 `Robust ≥ 90%` 命中率为 `0%`，立即止损换数据集并记入独立复盘日志，严禁无上限爬山。

---

## 三、分支一：`ASI-D1 兼容分支`（`ASI_EXP_D1`）完整执行 SOP

本分支完全符合工作区 `D1-Only` 红线，服务两大清晰子目标：
- **子目标 1A（主题冲榜 · `PPA + ATOM`）**：冲刺 `2026-11-23 ~ 2026-12-20` 的 `ASI/D1 Power Pool` 主题（`$15,000` 奖池，需 `≥ 5` 条达标）并点亮 16 个空白 ASI D1 金字塔；严格单数据集（`ATOM`）+ `≤ 8` 算子 + `≤ 3` 字段。
- **子目标 1B（高质升级 · `Hybrid PPA + RA`）**：当 1A 候选同时跨过完整 RA 门槛（`Sh ≥ 1.58`, `2Y ≥ 1.58`, `Fit ≥ 1.0`, `SC < 0.65`, `PC < 0.70`）时，自动具备 Hybrid 免配额提交资格（不占 Pure PPA 日 1/月 10 配额），且同等条件下**严格优先保留 `Margin` 越高越好的因子**。

### Step 0 · 零回测预检（Preflight）
1. 核验配置：`attached_to_main_scheduler == false`、`branch == "ASI_D1"`、`settings.delay == 1`、`auto_submit == false`。
2. 调用只读 `get_platform_setting_options` 确认 `EQUITY / ASI / Delay=1` 与目标宇宙（默认 `MINVOL1M`）。
3. 检查额度与并发：确认当日总日额度 `> 4,000`（或本批全为 `Alphas=0` 免额字段）且当前主线无 429 告警。
4. 核查目标数据集权限与字段元信息（`get_datafields`）：
   - 拦截无权限集（如本账号无 `shortinterest3`、`model77`）；
   - 拦截低覆盖集（`cov < 0.65`，如 `analyst15` `0.39`、`earnings6` `0.46`）与非数值元数据字段（如 `model307` 4 个 ID）；
   - 核对字段类型：`VECTOR` 必须包 `vec_avg`（疑似单值伪 VECTOR 如 `behavioral_signals`/`model307` 禁止 `vec_sum`），且 `vec_*` 计入 `≤ 8` 算子上限。

### Step 1 · 选路径与构建紧凑基线（`2–4` 条/轮，强制 `FULL`）
- **Path A（跨区移植）**：挑 `≤ 3` 条已验证的紧凑 `GLB / JPN / KOR / TWN / HKG / USA` 表达式 → 核实全字段在 `ASI/D1/MINVOL1M` 覆盖 `≥ 0.65` → **公式一字不改**直接跑 ASI 基线。
- **Path B（ASI 原生新建）**：从以下两类高胜率数据集池择一（单轮只打 1 个数据集，保 `ATOM`）：
  - **低拥挤 Theme 主力（防 PPAC 首选）**：`price_signal_dl`（`cov=91.3%`, `1.3×`）、`behavioral_signals`（`cov=87.5%`, `1.3×`）、`mmp_nlp_sentiment`（`cov=77.4%`, `1.3×`）、`model25`/`model26` 高覆盖 `Alphas=0` 字段；
  - **官方经典高倍率集（高 JPN 覆盖首选）**：`analyst69`（`1.5×`）、`model138`（`1.3×`, `valScore=2.0`）、`model38`（`1.3×`）、`fundamental17` / `fundamental23`（`1.1×`, 仅宜做 PPA 慎做 RA）。
- **固定基线设置**：
  ```json
  {
    "instrumentType": "EQUITY",
    "region": "ASI",
    "universe": "MINVOL1M",
    "delay": 1,
    "neutralization": "SLOW",
    "decay": 4,
    "truncation": 0.08,
    "maxTrade": "ON",
    "pasteurization": "ON",
    "nanHandling": "OFF",
    "unitHandling": "VERIFY"
  }
  ```
  *(注：首次基线亦可用 `"COUNTRY"` 与 `"SLOW"` 做 2 条平行对照；严禁 `QUICK` 模式用于 ASI 终检，因 `QUICK` 会误判 `1.0 ≤ Sh < 1.58` 的合格 PPA 且丢失 `rn_sharpe`。)*
- **静态合规校验**：
  - 唯一算子/总算子数 `≤ 8`（仅豁免 `ts_backfill`、`group_backfill`，中间变量底层算子照计）；
  - 唯一非豁免字段数 `≤ 3`；
  - 严禁出现 `+`、`*`、`add`、`multiply`、`trade_when`；
  - 多币种财务项必做同币种比率（`ebit / assets`）或先做个股自身时序标准化（`ts_zscore`/`ts_rank`）。

### Step 2 · 单变量诊断精修（每轮只改 1 个轴，最多 `2–4` 变体）
回测落盘至 `data/asi_isolated_ledger.db` 后，读取完整 `is_tests`（重点看 `Sharpe`、`2Y Sharpe`、`Turnover`、`Margin`、`Sub-Universe`、`Robust Universe Sharpe/Returns Ratio`、`Japan Robustness Sharpe`、`Investability`），按单一最大瓶颈定向修复：

1. **若挂 `LOW_ROBUST_UNIVERSE_SHARPE / RETURNS (< 90%)`**：
   - 修复 A（中性化）：从 `STATISTICAL` 切 `SLOW` / `COUNTRY` / `INDUSTRY`（若 `SLOW` 触发 90% 陷阱，试 `INDUSTRY`/`SECTOR`；如测试 `STATISTICAL` 须额外验证 Returns 未跌超 20%–30%）；
   - 修复 B（内层标准化）：在时序算子之前插入 `group_zscore(ts_backfill(x, 252), country)`（Template 2 双国家 Z-Score）；
   - 修复 C（凸权重整形与截断）：用 `ts_covariance(x, x, 22)` 或 `signed_power(x, 1.5)` 配合收紧 `truncation`（`0.05` / `0.03` / `0.015`），打压低流动性小盘极端权重；
   - 禁区：严禁靠重度 `decay=60` 或小盘倾斜（`1 - rank(cap)`）硬刷 Headline Sharpe。
2. **若挂 `LOW_ASI_JPN_SHARPE (< 1.0)`**：
   - 修复 A（外层分组）：全局 `rank(...)` → `group_rank(..., country)` 或 `group_rank(..., market)`（或 `densify(group_cartesian_product(industry, country))`）；
   - 修复 B（中性化）：对比 `SLOW` vs `COUNTRY`；
   - 修复 C（覆盖与截断）：放宽过紧截断至 `winsorize(..., std=5)`；若某字段日本覆盖稀疏，直接换集。
3. **若高换手（`TO > 18%`，尤其 `> 30%`）或低 Margin（`< 15bp`）**：
   - **全流程通用换手率门控**：若 **`TO < 8%`（换手已偏低）直接跳过降换手步骤**（不额外加平滑或大 `decay`，防止稀释 Sharpe 或挂 `LOW_TURNOVER`）；
   - 当 `TO > 18%` 时：保持 `maxTrade = "ON"`；优先在 `rank` 之前加短窗 `ts_mean(x, 5/10/22)` 或 `ts_decay_linear(x, 5/10)`；单变量扫频 `decay ∈ {0, 5, 20}`（或 `{4, 6, 8, 10}`）；必要时试 `ts_target_tvr_decay(..., lambda_min=0, lambda_max=0.9, target_tvr=0.10..0.15)` 或对照 `MINVOL10M`；**`MINVOL1M` 慎用 `hump`，永久禁用 `trade_when`**。

### Step 3 · 本地相关性门禁（PPAC & SC & N×N 正交剪枝）
1. **PPA 路线门禁**：使用 `data/sc_cache_v2/os_pnl_cache.db`（只读加载！）计算与全部历史 PPA（含已移除 `PowerPoolSelected` 标签者）的本地 **`PPAC < 0.48`**（留 `0.02` 安全余量，低于平台 `0.50` 硬线）。
   - **铁律（评论区实证）**：若 `PPAC ≥ 0.50`（近似克隆常达 `0.59–0.99`），**直接止损换新想法/新数据集**，不要浪费额度微调 `decay`/`neutralization`！
2. **同批 N×N 正交剪枝**：本批 ASI 候选内部两两相关 `< 0.48`（PPA 线）或 `< 0.65`（Hybrid RA 线），按 **`Margin` 优先 + 稳健性均衡（避免过拟合拖累榜单 Merged PnL）** 保留最优代表。
3. **Hybrid RA 路线追加校验**：若同时达 RA 硬检 `0 FAIL`，再走本地全量 OS `SC < 0.65` 与 `pc_poller.py` 只读异步查 `PC < 0.70`（绝不轻信 `cnhkmcp:check_correlation` 空体假通过）。

### Step 4 · 描述补齐、独立打标与人工复核（永不自动提交）
1. **结构化英文描述（`≥ 100` 字符，Pure PPA/Theme 强制）**：包含三段标准要素——`Idea`（经济假设）、`Rationale for data`（为何选该亚洲数据集/覆盖与币种处理）、`Rationale for operators`（为何用 `country` 分组/平滑/截断）。
2. **标签与别名纪律（需显式 `--confirm-apply` 或人工确认后才执行 `PATCH /alphas/{id}`）**：
   - 探索期阶段性候选打 **`ASI_EXP_D1`**；
   - 通过全部 PPA + ASI 专属检查 + 本地 `PPAC < 0.48` + `≥ 100` 字英文描述后，打 **`PPA_Useful`**（可保留 `ASI_EXP_D1` 便于追溯）；
   - 若同时过完整 RA 硬检且 `SC < 0.65`：按工作区别名铁律写 `SC 0.xxx PC 0.xxx`（仅在人工复核后决定归档）。
3. **最终提交**：严格由用户在 BRAIN 网页端筛选 `PPA_Useful` / `ASI_EXP_D1` 人工复核官方 Check Submission（确认 `Robust Universe ≥ 90%` 与 `Japan Robustness ≥ 1.0`）并手工提交，**脚本永不调用 `POST /alphas/{id}/submit`**。

---

## 四、分支二：`ASI-D0 隔离实验分支`（`ASI_EXP_D0` · 当前双重锁定）

> [!CAUTION]
> **当前状态：不可运行（平台未开放 + 本地硬锁关闭）**
> 1. **平台事实锁（`2026-11-26` 实盘核验）**：WorldQuant BRAIN 平台目前**不提供 `EQUITY / ASI / Delay = 0`**（官方帖子 `45233242695703`、`get_platform_setting_options`、`get_datasets(ASI, delay=0)` 与 `get_pyramid_multipliers` 四方交叉验证均为 `0`）。
> 2. **工作区红线锁**：`AGENTS.md` 硬红线第 1 条要求全链路严格 `D1-Only`；未经用户显式书面放行，任何代理严禁尝试发起 D0 仿真。

### 未来仅当同时满足以下 4 项条件时，才可启用 `ASI_EXP_D0`：
1. **平台侧确认开放**：只读调用 `get_platform_setting_options` 返回存在 `Region == "ASI" && Delay == 0` 合法条目，且 `get_datasets(region="ASI", delay=0)` 返回非空数据集列表。
2. **人工显式双签解锁**：用户明确批准放行，手工将 [asi_isolated_config.json](file:///c:/Wq/WorldQuant%20Brain/docs/asi_d0_d1_isolated/asi_isolated_config.json) 中 `branches.asi_d0.allow_d0_override` 改为 `true`，且运行命令显式携带 `--confirm-d0-isolated`。
3. **完全物理隔离**：独立运行进程，只读写 `data/asi_isolated_ledger.db`（`branch='ASI_D0'`），平台标签固定 **`ASI_EXP_D0`**，额度严格受限于总日额 `> 4,000` 之后的独立实验上限（默认 `≤ 100 sims/天`），绝不写入 `data/wq_v2_ledger.db` 或主线任何配置。
4. **D0 专属风控核查（预设）**：未来若 ASI D0 开放，须优先核对日内时点截断（日本/澳新/韩台港不同收市时区错位导致的未来函数或执行延迟风险）、高换手成本对 Margin 的冲击（预计远高于 D1）、以及 D0 专属提交检查门槛与金字塔倍率。

---

## 五、启动前检查清单（Quick Checklist）

- [ ] 确认本次仅启动 **`ASI-D1 兼容分支`**（`ASI_EXP_D1`），`allow_d0_override` 保持 `false`；
- [ ] 确认未修改 `wq_research_v2/`、`docs/agents/`、`data/wq_v2_ledger.db`、`AGENTS.md` 任何文件；
- [ ] 通过只读 `GET /users/self/activities/simulations` 确认当日总日额度 `> 4,000`（或仅跑 `2026-12-06` 前的 `Alphas=0` 免费字段）；
- [ ] 单轮回测严格控制 `2–4` 条，强制 `FULL`、`delay=1`、`maxTrade="ON"`，每次只改 1 个变量；
- [ ] 检查结果必须覆盖 `Robust Universe ≥ 90%`、`Japan Robustness ≥ 1.0`、`Margin ≥ 15bp`、`PPAC < 0.48` 与 `≥ 100` 字符英文描述；
- [ ] 任何 `PATCH` 打标需显式确认，绝不自动提交。
