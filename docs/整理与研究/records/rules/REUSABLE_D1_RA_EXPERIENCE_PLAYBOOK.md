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
- **两大逻辑 Bug 实录与永久根治**：
  1. **重启 `DEDUP_SKIPPED` 覆盖 `COMPLETED_FULL` Bug（已根治）**：旧版 `upsert_sim_task` 使用 `INSERT OR REPLACE`，服务重启跑同 `batch_id` 时将已完成的 `COMPLETED_FULL` 行覆盖成 `DEDUP_SKIPPED`（Alpha 仍在 BRAIN 平台完好保存，但本地台账统计变小）。现已在 `ledger_store.py` 与 `sim_runner.py` 加入不可变保护并配单测，永不再发。
  2. **`EUR/TOP2500` 批量 `STATISTICAL`/`FAST`/`SLOW_AND_FAST` 600s 超时引发 429 Bug（已根治）**：Stage-1 宽筛停用 `STATISTICAL/FAST/SLOW_AND_FAST`，`poll_timeout_sec` 升至 `900s`，主力降 PC 优先使用高效且不超时的 **`CROWDING` + `REVERSION_AND_MOMENTUM`**。
