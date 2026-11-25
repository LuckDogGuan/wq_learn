# 分地区 D1 独立研究手册总目录（严禁跨地区混为一谈）

> [!IMPORTANT]
> **核心铁律**：
> 1. **概念严格分层**：`Dataset（数据集）≠ Data Field（数据字段）≠ Operator（算子）≠ Template（模板）≠ Expression（表达式）≠ Simulation Settings（设置）≠ Alpha`（官方术语表见 [BRAIN_OFFICIAL_GLOSSARY.md](../../official_guides/BRAIN_OFFICIAL_GLOSSARY.md)）。
> 2. **地区与宇宙范围完全说明**：全量 **11 个 D1 合法地区 × 18 组官方 Universe × 中性化兼容性 × 排障对照表** 已沉淀在 **[REGION_AND_UNIVERSE_GUIDE.md](REGION_AND_UNIVERSE_GUIDE.md)**。
> 3. **多市场全覆盖 + 高 Base 优先 + 30 分钟动态止损换向**：严格锁定 **`Delay = 1`**，优先放量 **高 Base 地区（`EUR`, `USA`, `GLB`, `ASI`, `CHN`）** 与 **高倍率空白区（`DEU`, `HKG`, `KOR`, `GBR`, `IND`, `AMR`）**；每个市场独立记录、独立导出 `<region>_ra_funnel_latest.json`，每 30 分钟复查实盘命中率，对低产数据集自动/手动早停换向！
> 4. **绝不丢弃好结果**：所有已完成 Alpha 全量永久保存于 SQLite，通过分层池（`POOL_S / POOL_A / POOL_B / POOL_FLIP / POOL_DROP`）过滤低夏普噪声自然拉升候选池整体质量。

---

## 全量 11 个 D1 市场独立作战档案（按高 Base + 高倍率执行顺序）

| 梯队 | 地区 / 主宇宙 / 延迟 | 并发槽 | 当前 OS | 最高倍率 | 核心门槛与市场特征摘要 | 独立作战档案 | 当前状态 |
| :-: | --- | :-: | :-: | :-: | --- | --- | --- |
| **T1 高 Base** | **`EUR / TOP2500 / D1`** | `1` | `26` | `1.5×` | 常规 D1 (`Sh>1.58, M≥10bp`)；广州历史均 Sh 第一（`2.018`），多国欧股善用 `SUBINDUSTRY`/`COUNTRY` | [EUR_TOP2500_D1.md](EUR_TOP2500_D1.md) | **🟢 即将首轮探针 (`news_sentiment_dl`, `price_signal_dl`)** |
| **T1 高 Base** | **`USA / TOP3000 / D1`** | `1` | `14` | `1.5×` | 常规 D1 (`Sh>1.58, M≥10bp`)；全场最高 Base 容量，主攻低拥挤/免费 `price_signal_dl` & `news_sentiment_dl` | [USA_TOP3000_D1.md](USA_TOP3000_D1.md) | **🟢 即将首轮探针 (`Alphas=0` MATRIX/VECTOR)** |
| **T1 高 Base** | **`GLB / TOP3000 / D1`** | **`2`** | `20` | `1.4×` | 常规 D1 (`M≥9bp`)；选 `TOP3000` 避 `TOPDIV3000`；`analyst`/`fundamental` 各差 1 条点亮 `2→3` | [GLB_TOP3000_D1.md](GLB_TOP3000_D1.md) | **🟢 纳入高 Base 轮巡 (`analyst10`, `fundamental44`)** |
| **T1 高 Base** | **`ASI / MINVOL1M / D1`** | `1` | `0` | `1.5×` | 强制 `maxTrade=ON` + `Robust≥90%` + `JPN` 子检 (`M≥15bp`)；RA 探针与 PPA 主题线严格隔离 | [ASI_MINVOL1M_D1.md](ASI_MINVOL1M_D1.md) | **🟢 纳入高 Base RA 探针 (`price_signal_dl`, `behavioral_signals`)** |
| **T1 高 Base** | **`CHN / TOP2000U / D1`** | `1` | `0` | **`1.9×`** | 全场最严（`Sh≥2.08, Ret≥8%, Robust≥40%, M≥20bp`）；主攻低换手免费 `other496 (1.9×)` & `analyst45 (1.8×)` | [CHN_TOP2000U_D1.md](CHN_TOP2000U_D1.md) | **🟢 纳入高 Base 轮巡 (`Alphas=0` 财报比率)** |
| **T2 高倍率** | **`DEU / TOP500 / D1`** | `1` | `0` | **`1.8×`** | 6 塔全 `1.8×` 零 OS；**17:22 实盘首查发现 `model264` 160 条最高 `0.71` → 已止损切换至 `analyst93`/`other250`/`fundamental6`** | [DEU_TOP500_D1.md](DEU_TOP500_D1.md) | **🟡 已纠偏换向（弃 `model264`，转 `analyst93`/`fnd6`）** |
| **T2 高倍率** | **`HKG / TOP800 / D1`** | `1` | `0` | **`1.7×`** | 常规 D1，0 OS 零撞车；港股高覆盖免费 `news_sentiment_dl (other 1.7×)` | [HKG_TOP800_D1.md](HKG_TOP800_D1.md) | **🟢 纳入全市场探针** |
| **T2 高倍率** | **`KOR / TOP600 / D1`** | `1` | `0` | **`1.6×`** | 常规 D1，0 OS；韩国散户主导，行为金融 `behavioral_signals` & 论坛 `equity_forum_data` 极契合 | [KOR_TOP600_D1.md](KOR_TOP600_D1.md) | **🟢 纳入全市场探针** |
| **T2 高倍率** | **`GBR / TOP700 / D1`** | `1` | `34` | `1.7×` | `MODEL` 塔饱和禁扫；优先零回测收割 `OTHER 2→3` 存量 + 试免费 `dl_riskfree_returns` | [GBR_TOP700_D1.md](GBR_TOP700_D1.md) | **🟢 存量收割 + `OTHER` 补塔探针** |
| **T2 高倍率** | **`AMR / TOP600 / D1`** | `1` | `0` | `1.7×` | 仅 2 塔且**只支持 7 种中性化（禁 `RAM`/`CROWDING`）**；试 `model239` 免费借券信号 | [AMR_TOP600_D1.md](AMR_TOP600_D1.md) | **🟢 纳入全市场轻探针** |
| **T2 高倍率** | **`IND / TOP500 / D1`** | `1` | `0` | `1.4×` | 常规 D1，0 OS；新兴高成长蓝筹集中市场，试 `quant_factor_lib` | [IND_TOP500_D1.md](IND_TOP500_D1.md) | **🟢 纳入全市场轻探针** |

---

## 动态早停、剪枝与 2 小时复查机制（专注 1–2 个高 Base 核心方向）

1. **当前严格专注的 2 个高 Base 主力方向**：
   - **主方向 ①：`EUR`（`TOP2500 / TOP1200 / TOP800`）· `model25`**（`model 1.3×`, `0 OS`）—— 已出 5 条 `POOL_S`（最高 `Sh=+3.16, 2Y=+2.27, Fit=+3.24`），当前全力跑 Stage-3 `Sub-Universe` 解救直取 `0 FAIL`！
   - **主方向 ②：`USA`（`TOP3000`）· `price_signal_dl` + `option_horizon_decomp`**（最高 Base，`Alphas=0` 免额 + `0 OS`）—— 已出 11 条正向 `POOL_B`（最高 `Sh=+1.10, 2Y=+1.99, Mgn=+33.4bp`），全力跑第 2 轮轻参数爬坡（目标 `1.3–1.4+`）→ 第 3 轮冲 `1.6+`！
2. **三阶晋级 + 相似种子剪枝 + 正向早停**：
   - 阶梯目标：`第 1 轮 ≥0.80 (POOL_B)` → `相似种子剪枝 (seed_pruner.py: jaccard≤0.78, max_per_field=2, max_per_dataset=6)` → `第 2 轮轻参数爬坡至 1.25–1.45+ (POOL_A)` → `第 3 轮单轴精修至 1.60+ 且 0 FAIL (POOL_S)` → `Stage-4 SC/PC → Useful`。
   - 正向早停：满 `48` 条且正向 `Sharpe ≥ 0.80` 命中率 `< 2%` 且无 `≥ 1.25` 自动早停（免疫 CHN 双负假象）。
3. **每 2 小时定时复查与逻辑修正（`0 */2 * * *`）**：每 2 小时复盘两主力方向晋级率、调整轻参数与剪枝参数；若出 `0 FAIL` `POOL_S` 立刻做 SC/PC 体检请用户确认打 `Useful`；若某方向枯竭则替换下一个验证过的高 Base 方向（如 `ASI/price_signal_dl` 或 `GLB/model239`），始终保持只专注 1–2 个方向！
