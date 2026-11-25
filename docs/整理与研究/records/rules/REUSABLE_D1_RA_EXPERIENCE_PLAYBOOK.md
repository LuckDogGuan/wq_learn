# WorldQuant BRAIN D1 RA 可复用筛选、提效与降 PC 经验手册

> [!IMPORTANT]
> 本手册是自动化研究与每 2 小时定时复盘的**标准可执行规则真源**，其机器可读版本同步保存在 [reusable_experience_rules.json](../../../../wq_research_v2/config/reusable_experience_rules.json)。
> **固定硬门槛（永不放松）**：`Delay = 1` · Decision #3（禁 `+`/`*`/`add`/`multiply`/`trade_when`）· RA 与 PPA 严格分离 · 绝不自动 `/submit` · `COMPLETED_FULL` 记录永不覆盖。
> **可调软参数（允许多轮小幅微调）**：`decay ∈ {0,1,2,3,4,5,6}`、`truncation ∈ {0.04,0.06,0.08}`、平滑窗口 `{5,8,10,15,22,66,126}`、`adv20` 门控分位 `{0.35..0.55}`、相似种子剪枝参数（`--prune-jaccard` / `--prune-max-per-field` / `--prune-max-per-dataset`）、二三阶段晋级阈值。

---

## 1. 8:2 查资料与决策优先级法则（已写入 `AGENTS.md`）

1. **80% 首选核心知识栈（遇到任何瓶颈必须先查这三处）**：
   - **王哥 Skill**（[worldquant-brain-cyber-game-king](file:///C:/Users/31186/.gemini/config/skills/worldquant-brain-cyber-game-king/SKILL.md)）：ATLAS L1→L6、Decay `[0,1,3,5,10,20]` 防断崖扫频、9 维度中性化扫频、本地 SC `0.68` 安全缓冲线、控算子数防过拟合。
   - **Top 100 黄金顾问团**（[wq-top-advisors-skill](file:///C:/Users/31186/.gemini/antigravity/skills/wq-top-advisors-skill/SKILL.md) & [04_分方向优化与模板.md](../../04_分方向优化与模板.md)）：`SZ83096 #47` 五步晋级链（2Y 先行 → 嵌套分组 `country*industry` → `signed_power` 降 PC）、`JR23144 #12` 同向极值对齐 + 候选池 `N×N` 正交剪枝、`JX79797 #15` 禁 `lambda_max>1`、`ZH87224 #51` 冗余算子剥离。
   - **管理员原创发帖**（`WL13229` + `KH94146` 254 篇验证原创）：`min(rank(A), rank(B))` 双支融合、禁 `ts_decay_linear(rank(x), d)` 无 `dense=true`、禁插噪声降 PC、单数据集 ATOM 免 `IS_LADDER_SHARPE`。
2. **20% 兜底资料库**：**仅当前述 80% 体系无法解决当前卡点时**，才翻查普通中文论坛帖子（`brain-forum-browse` / `brain-alpha-judge` 语料）寻找补充思路。

---

## 2. 渐进四阶段漏斗筛选与标记规则

| 阶段 | 目标与软门槛（可小幅微调） | 过滤与剪枝机制 | 状态标记 |
| :-: | --- | --- | :-: |
| **一阶段（宽筛）** | 选高覆盖/低拥挤新数据集，跑 `v4` 4 组正反对称模板；**正向 `Sharpe ≥ 0.80`** 入 `POOL_B` | 正向早停（满 `48` 条且 `Sh≥0.80` 命中 `<2%` 且无 `≥1.25` 即停，免疫 CHN 融券双负假象） | `POOL_B` |
| **二阶段（轻参提效）** | 围绕 `POOL_B` 种子小步微调（`decay/truncation/neut/window` + 双支），冲 **`Sharpe 1.25–1.45+`** 入 `POOL_A` | 非破坏性相似种子剪枝（`jaccard ≤ 0.78`、`ΔSh≤0.06 & ΔTO≤0.02`、同字段限 2、同集限 6） | `POOL_A` |
| **三阶段（单轴攻坚）** | **每次仅改 1 个轴**对症解救瓶颈，冲 **`Sharpe ≥ 1.58 & Fitness ≥ 1.0 & 2Y ≥ 2.02 & 0 FAIL`** 入 `POOL_S` | 严格禁止同时改 3 个轴（防复现 `S3-r2-USA-PSD` 1.51→0.77 教训） | `POOL_S` |
| **四阶段（相关性与交付）** | 1) 本地 92-OS SC **`< 0.65`**；2) 池内两两正交 `< 0.68`（同簇冲突优先留 **`Margin` 更高者**）；3) 异步 `pc_poller.py` 远程 PC `< 0.70` | **凡过 RA 硬检且 SC `< 0.65` 统一写别名 `SC 0.xxx PC 0.xxx`**；全通过打 **`Useful`**（按 `Margin` 降序）；仅 PC 未过打 **`SC_PASS`** 入专项降 PC 队列 | `SC_PASS` / `Useful` |

---

## 3. 经实盘验证的四大提效与降 PC 规则（含成败复盘）

1. **规则 `IMP-01`（解救 `LOW_SUB_UNIVERSE_SHARPE`）**：
   - **成功复现**：留在宽宇宙 `EUR/TOP2500`，用 `if_else(rank(adv20) > 0.35..0.55, expr, 0)` 或单集 ATOM 总资产 `mdl25_bsv421_5v` 门控，一次产出 **20+ 条 `0-FAIL` `POOL_S`**（如 `6XG8AOVP Sh=2.49`）。
   - **失败避坑**：绝不盲缩宇宙（`EUR/TOP1200` 把 `3.16` 直接摔成 `1.26`）；且**不要**在未知市值分布的新信号（如 `USA/price_signal_dl`）上直接硬切 `adv20 > 0.35`。
2. **规则 `IMP-02`（`SC_PASS` 专项压 PC 四连击 —— 今日实盘把 `PC` 从 `0.946` 砍穿至 `0.615`！）**：
   - 杠杆 ① 嵌套分组 `group_cartesian_product(country, industry)`（单招砍 `-0.153 PC`）；
   - 杠杆 ② Decision #3 双支融合 `min(rank(A), rank(B))` 配低拥挤字段如 `mdl25_8v` 应计项 / `op_eff`（砍 `-0.166 PC`）；
   - 杠杆 ③ 风险模型中性化：**`CROWDING`**（快且稳，`RR53xm10 PC = 0.6599`）与 **`STATISTICAL`**（强压 PC，`vRYqEALz PC = 0.6218`、`9qGvelwo PC = 0.6146`，须配 `poll_timeout_sec = 900s` 防超时！）与 **`REVERSION_AND_MOMENTUM`**（`vRYqEZja PC = 0.6688`）；**严禁在 `EUR/TOP2500` 批量使用 `FAST` / `SLOW_AND_FAST`**（实测易 600s 超时并引发后续槽位 429）；
   - 杠杆 ④ 非线性尾重塑 `signed_power(x, 2 / 0.5)`（`SZ83096 #47`）或 `vector_neut(x, rank(ts_mean(returns, 22)))`（`9qGvelwo PC = 0.6146`）。
3. **规则 `IMP-03`（单变量迭代铁律）**：
   - **坏批次复盘**：`S3-r2-USA-PSD` 同时修改了平滑窗口（`5→15/22`）+ `adv20` 门控 + `decay (0→4/6)` 三个轴，导致 `xAl6rxYw` 从 `Sh=1.51 / 2Y=2.89 / PC=0.749` 暴跌至 `0.77`。已在 `S3-r3-USA-PSD-SINGLEAXIS` 纠偏为严格单轴微调。
4. **规则 `IMP-04`（数据集第一 + 地区独立验真）**：
   - **实证对比**：新集 `model238`（SmartHoldings）在 `EUR/TOP2500` 首波即打出 `kq87w6vO Sh=1.50, PC=0.6349`，但在 `USA/TOP3000` 跑满 `48` 条 `0` 命中（`max=0.61`）被自动早停。说明**数据集决定天花板，且同一数据集在不同地区必须独立测试、独立止损**！

---

## 4. 现役标准模板显式说明表（严格 5:5 归属）

| 模板 ID | 归属与作者 | 精确表达式骨架 | 经济含义与适用场景 |
| --- | --- | --- | --- |
| `RA-ADM-01/02` | `ADMIN_ORIGINAL` (`WL13229`) | `(reverse) group_zscore(ts_mean({x}, 22), subindustry)` | 22 日月度平滑细分行业标准分，低换手保 Margin，适合基本面/慢模型 |
| `RA-ADM-03/04` | `ADMIN_ORIGINAL` (`WL13229`) | `(reverse) group_rank(ts_decay_linear({x}, 10), subindustry)` | 10 日线性衰减前置（规避 `dense=false` 拉偏），适合中频量价/持仓 |
| `RA-TOP-01/02` | `TOP100_2026Q4` (`SZ83096 #47`) | `(reverse) group_rank(ts_zscore(ts_mean({x}, 5), 66), subindustry)` | 5 日去噪 + 66 日时序 Z 值冲击，`USA/price_signal_dl` `Sh=1.51/2Y=2.89` 冠军骨架 |
| `RA-TOP-03/04` | `TOP100_2026Q4` (`LD22811 #13`) | `(reverse) group_zscore({x}, industry)` | 1 算子原汁行业标准分，`EUR/model25` `Sh=3.16–3.33` 冠军骨架 |
| `S3PC-DUAL-ACC-CI` | `TOP100 + ADMIN` (`ZS59763 + WL13229`) | `if_else(rank(adv20)>{cut}, group_zscore(min(rank(A), rank(B)), group_cartesian_product(country, industry)), 0)` | 降 PC + 救 Sub-Uni 联合冠军（`RR53xm10 PC=0.6599`, `vRYqEZja PC=0.6688`） |
| `S3PC-SP2-CI` | `TOP100_2026Q4` (`SZ83096 #47`) | `if_else(rank(adv20)>{cut}, signed_power(group_zscore(A, group_cartesian_product(country, industry)), 2), 0)` | 非线性分布重塑压 PC 冠军（`vRYqEALz Sh=2.24, PC=0.6218`, `pwWX2xNb PC=0.6806`） |
| `S3PC-VNEUT-CI` | `ADMIN + TOP100` (`WL13229 + ZS59763`) | `if_else(rank(adv20)>{cut}, vector_neut(group_zscore(A, group_cartesian_product(country, industry)), rank(B)), 0)` | 剔除拥挤/动量暴露压 PC 冠军（`9qGvelwo PC=0.6146`, `gJrA5OlJ Sh=2.21, PC=0.6433`） |

---

## 5. 每日可跑规模与工程防踩坑记录

- **官方平台吞吐与 4,500/天 连续流水线架构**：
  - 官方 `GET /users/self/activities/simulations` 与 `POST /simulations` 响应头实证：Gold 账号日上限 **`5,000`** 次（`Alphas=0` 免额字段不扣减此额度），单次 Multi-Sim 上限 **`8` 条子表达式**。
  - **为何旧版仅跑 `1,300/天`（四大瓶颈已根治）**：① 波次屏障等待最慢任务导致其余槽位空等；② 同地区 4 线程同毫秒抢发 `POST` 触发突发 `429` 且直接丢弃未建任务；③ 跑完后串行拉取 16 次子结果期间未释放槽位；④ 旧上限设 `3,000`。
  - **新版连续滚动跨地区流水线（`sim_runner.py` + `daemon_ra_runner.py`）**：① **跨地区并行混跑**（`--slots 4 --max-per-region 2`：`2` 线程 `EUR` + `2` 线程 `USA` = `4` 线程 × `8` 槽常驻满载）；② **零波次屏障**（任一线程完成即秒补下一批）；③ **全局 `2.0s` `POST` 错峰锁 + 创建前 `429` 冷却重试（最多 2 次）**；④ **模拟完成即秒释槽位 + 4 线程并行拉取子结果**；⑤ 目标提升至 **`--daily-target 4500`**（并在 `X-RateLimit-Remaining <= 80` 自动安全停泊）。按实测延迟（`USA 140s`, `EUR 177s`）稳定吞吐 **`~450–650 FULL/小时`**，可在 **~7–8 小时内稳健跑满 `4,500/天`**。
- **三大逻辑/平台 Bug 实录与永久根治**：
  1. **重启 `DEDUP_SKIPPED` 覆盖 `COMPLETED_FULL` Bug（已根治）**：旧版 `upsert_sim_task` 使用 `INSERT OR REPLACE`，服务重启跑同 `batch_id` 时将已完成的 `COMPLETED_FULL` 行覆盖成 `DEDUP_SKIPPED`（Alpha 仍在 BRAIN 平台完好保存，但本地台账统计变小）。现已在 `ledger_store.py` 与 `sim_runner.py` 加入不可变保护并配单测，永不再发。
  2. **`EUR/TOP2500` 批量 `STATISTICAL`/`FAST`/`SLOW_AND_FAST` 600s 超时引发 429 Bug（已根治）**：Stage-1 宽筛停用 `STATISTICAL/FAST/SLOW_AND_FAST`，主力降 PC 优先使用高效且不超时的 **`CROWDING` + `REVERSION_AND_MOMENTUM`**。
  3. **BRAIN 后端僵尸仿真（卡死 `progress=0.15/0.90` 长达 45–80 分钟）占槽引发 `POST 429` Bug（Audit #2 根治）**：实测发现在高并发下 BRAIN 偶发将某些 `EUR` 批次永久卡在 `progress=0.15` 或 `0.90`，旧版苦等 `900s` 且不撤单，导致僵尸持续占满服务端并发槽并把小时吞吐从 `~500` 拖垮至 `~180`。现已在 `auth_session.py` + `sim_runner.py` 实装 **`stall_timeout_sec=240s` 进度停滞早退 + 只读对账 1 次未完成即调用官方 `DELETE /simulations/{id}` 撤单释槽 + 子查询 429 重试 + `max_post_429_retries=4`**（已实测 `DELETE` 返回 `HTTP 200` 秒删 5 个旧僵尸）。
  4. **Stage-4 异步 PC 体检必须严格“逐条串行轮询”**：并发短间隔轮询 6–8 条 `/correlations/prod` 会导致 BRAIN 单用户异步 PC 队列饥饿与 `/check` 429；改为逐条串行遵守 `Retry-After` 后，实测 11/11 条候选均在 2–6 次内稳定返回真实远程 PC。
  5. **真正正交必须跨主信号/跨数据集**：实测 14 条 `model25` 含 `value_momentum_region_percentile` 的变体（含 `signed_power(1.5/2)` / `vector_neut` / `accruals`）与 `RR5QjWYz` 两两相关性仍达 `0.707–0.9997`；而 **`EUR / model238`（`88G9Kk9o`, `Sh=1.76, SC=0.188, PC=0.608`）与 `RR5QjWYz` 相关性仅 `0.2054`**！
  6. **分地区非对称槽位配额（`--region-caps EUR:1,USA:3`）与空体僵尸 `DELETE`**：Audit #3 实证 `EUR` 2 并发 + `VECTOR` 集易引发 `58%` 后端 `Sim ERROR`/停滞，而 `USA` 纯 `MATRIX` 零 `Sim ERROR` 且完成率 `88–100%`；拆分为 `EUR:1 + USA:3` 共 4 槽，并修复 `GET` 返回空体 `HTTP 200` 时跳过 `DELETE` 的边界 Bug，实现 `0 次 429` 且逼近 `4,500 FULL/天`。
  7. **慎用跨数据集硬切 `adv20 > 0.40`**：`adv20 > 0.40` 仅适用于 `EUR/model25` `val_mom` 等大中盘强信号；对 `USA/price_signal_dl`、`EUR/model238`（`xAl8adOn 1.58→0.69`）、`EUR/model25` `op_eff`（`1.85→0.74`）直接硬切 `adv20 > 0.40` 会腰斩 Sharpe，应改用**软门控（`0.20/0.30`）、`hump`、轻衰减或原生子宇宙 `TOP1200/TOP800` 单轴测试**。
  8. **机构基本面/盈利预测大集远胜冷门舆情/新奇集（Audit #4 实证）**：`EUR/model77`（S&P Capital IQ）首波 48 条即出 `1YGbzOlz (Sh=1.80, 2Y=2.49, Fit=1.25, Mgn=19.3bp, corr=0.583)` 与 `gJrO9RbK (Sh=1.66, PC=0.698, corr=0.135)`，而冷门集 `EUR/other455 (max=0.36)`、`USA/other580 (max=0.56)`、`USA/model68 (max=0.82)` 均低效早停；因此 `USA` 3 槽已全面换装机构级 StarMine 三大王牌（`model28` 全免额信用违约、`model31` 盈利质量、`model30` SmartEstimate 预期差）。
