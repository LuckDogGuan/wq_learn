# WorldQuant BRAIN 地区（Region）与股票池/宇宙范围（Universe）完全指南（D1-Only 开发与排障真源）

> [!IMPORTANT]
> - **数据真源**：本指南的 `Region × Delay × Universe × Neutralization` 全部经 **`cnhkmcp:get_platform_setting_options`**、**`get_pyramid_multipliers`**、**`get_pyramid_alphas`** 于 **`2026-11-25`** 实时核验（18 组官方 EQUITY 组合），并结合官方术语表（[BRAIN_OFFICIAL_GLOSSARY.md](../../official_guides/BRAIN_OFFICIAL_GLOSSARY.md)）与账号 `JG81923`（Gold，92 OS，100% D1）实测约束整理。
> - **核心红线**：全工作区严格锁定 **`Delay = 1 (D1)`**；**每个地区必须独立建档、独立回测、独立对比、独立漏斗导出**，严禁跨地区混池平均或把 D0 参数带入 D1。

---

## 1. 先分清概念：Region vs Universe vs Neutralization（避免定位错层）

| 层级 | 官方定义 | 决定什么？ | 典型定位排障症状 |
| --- | --- | --- | --- |
| **Region（地区）** | 基于共同地理、交易时段与市场机制划分的股票集合（如 `USA`, `EUR`, `GLB`, `ASI`, `CHN`, `DEU`, `GBR`, `HKG`, `KOR`, `IND`, `AMR`） | ① **Base Weight（区域基础权重/资金容量）**<br>② **平台提交硬门槛**（如 CHN `Sh≥2.08`、ASI `maxTrade=ON & Robust≥90%`）<br>③ **金字塔倍率与本地 SC 池**（SC 只在同一 Region 内算）<br>④ **并发槽位权重**（`GLB = 2` 槽，其余单地区 `= 1` 槽） | • 报 `LOW_SHARPE` 但 Sharpe=1.80 → 检查是否跑在 **`CHN`**（门槛 `2.08`）<br>• 报 `LOW_ASI_JPN_SHARPE` → **`ASI`** 多国池未做 `COUNTRY` 中性化<br>• 并发速率减半 → **`GLB`** 单批占 2 槽<br>• 本地 SC 频繁撞车 → 该 Region 已有较多 OS（如 `GBR` 34 条、`EUR` 26 条） |
| **Universe（股票池/宇宙范围）** | 指定 Region 内按**市值或流动性（成交额）**筛选出的可交易股票子集（如 `TOP3000`, `TOP2500`, `MINVOL1M`, `TOP2000U`, `TOP500`） | ① **池内标的数与流动性底线**<br>② **Sub-Universe Sharpe 基准线**（由更小高流动性子池决定）<br>③ **数据集/字段可用性与拥挤度**（如 `GLB/TOP3000` 拥挤度远低于 `GLB/TOPDIV3000`）<br>④ **小盘/大盘风格与换手成本** | • `get_datafields` 返回 `0` → `Region + Universe + Delay` 组合不合法（如 `CHN` 只认 `TOP2000U`，不认 `TOP3000`）<br>• 报 `LOW_SUB_UNIVERSE_SHARPE` → 信号只在尾部小票有效、大中盘失效<br>• 报 `HIGH_CONCENTRATION / Weight > 10%` → 池子太小（如 `TOP200`/`TOP500`）或字段覆盖率太低 |
| **Neutralization（中性化）** | 在横截面对组合持仓做均值去中心化/风险因子正交化的分组范围 | 决定剥离哪些系统性风险（市场/国家/行业/风格因子） | • **多国区域**（`GLB`, `EUR`, `ASI`, `AMR`）有 `COUNTRY` 选项；**单一国家区域**（`USA`, `CHN`, `DEU`, `GBR`, `HKG`, `KOR`, `IND`）**没有 `COUNTRY` 选项**（传入会报错！） |

---

## 2. 全量 11 个 D1 合法地区总览（高 Base 优先排序 · 2026-11-25 实盘核验）

> **关于「高 Base 地区」的核心逻辑**：
> 在 BRAIN 的收益分配与组合容量体系中，**Base Weight（基础资金容量权重）**主要由市场总规模与机构流动性决定：
> - **Tier-1 高 Base 巨型流动性池（优先多跑！）**：**`USA`、`EUR`、`GLB`、`ASI`、`CHN`** —— 单条高质低 PC Alpha 的长期 Base 收益上限最高，也是全球主流机构池。
> - **Tier-2 高倍率/零包袱单国与特色市场（逐个试探，专攻高倍率空白塔！）**：**`DEU (1.8×)`、`GBR (1.7×)`、`HKG (1.7×)`、`KOR (1.6×)`、`IND (1.4×)`、`AMR (1.7×)`** —— 当前多数为 **0 条历史 OS（零本地自相关包袱）** 且金字塔倍率高达 `1.6×–1.8×`，极适合做 `Alphas=0`（12-06 截止）快速突破与多市场差异化试水。

| 梯队 | Region | 官方合法 D1 Universes（推荐主池加粗） | 并发槽 | 账号当前 OS | 最高/均金字塔倍率 (D1) | 支持 `COUNTRY` 中性化 | 区域专属硬门槛与关键避坑 | 独立作战档案 |
| :-: | :-: | --- | :-: | :-: | :-: | :-: | --- | --- |
| **T1 高 Base** | **`USA`** | **`TOP3000`**, `TOP2000`, `TOP1000`, `TOP500`, `TOP200`, `TOPSP500` | `1` | `14` | `1.5× / 1.19×` (`sentiment 1.5×`, `other 1.4×`) | ❌ | 常规 D1（`Sh>1.58, Fit>1.0, 2Y>1.58`, 经验 `M≥10bp`）；**极度拥挤**，历史证明严禁盲扫 `TOP1000` 情绪长衰减，主攻 `TOP3000` 新/低拥挤集（`price_signal_dl`, `news_sentiment_dl`, `other566`） | [USA_TOP3000_D1.md](USA_TOP3000_D1.md) |
| **T1 高 Base** | **`EUR`** | **`TOP2500`**, `TOP1200`, `TOP800`, `TOP400`, `TOPCS1600` | `1` | `26` | `1.5× / 1.21×` (`other 1.5×`, `news/sent 1.4×`, `model/anl 1.3×`) | ✅ | 常规 D1（经验 `M≥10bp`）；**广州历史实测均 Sharpe 全场最高（`2.018`）**！多国欧股须善用 `SUBINDUSTRY`/`COUNTRY`/`RAM`；`model`/`news`/`sentiment` 塔当前 `0` OS | [EUR_TOP2500_D1.md](EUR_TOP2500_D1.md) |
| **T1 高 Base** | **`GLB`** | **`TOP3000`**, `MINVOL1M`, `MINVOL10M`, `TOPDIV3000` | **`2`** | `20` | `1.4× / 1.17×` (`analyst/fnd 1.4×`, `model/news/sent 1.3×`) | ✅ | 常规 D1（经验 `M≥9bp`）；**单批占 2 并发槽**；**选 `TOP3000` 严避 `TOPDIV3000` 高拥挤**；`analyst (2/3)` 与 `fundamental (2/3)` 各差 1 条点亮达标塔 | [GLB_TOP3000_D1.md](GLB_TOP3000_D1.md) |
| **T1 高 Base** | **`ASI`** | **`MINVOL1M`**, `MINVOL10M`, `TOP500` | `1` | **`0`** | `1.5× / 1.18×` (`analyst 1.5×`, `sent 1.4×`, `model/news/other 1.3×`) | ✅ | **硬性 `maxTrade=ON` + `Robust ≥ 90%` + `LOW_ASI_JPN_SHARPE ≥ 1.0`**，经验 `M≥15bp`；必须用 `COUNTRY` 或 `group_cartesian_product(country, sector)`；**RA 与活跃 PPA Theme 严格分离** | [ASI_MINVOL1M_D1.md](ASI_MINVOL1M_D1.md) |
| **T1 高 Base** | **`CHN`** | **`TOP2000U`** *(唯一)* | `1` | **`0`** | **`1.9× / 1.61×`** (`other 1.9×`, `anl/fnd/macro 1.8×`) | ❌ | **全场最严门槛：`Sh≥2.08, Fit≥1.0, Ret≥8%, Robust≥40%`, 经验 `M≥20bp`**；T+1+散户高反转，优先低换手财报比率（`other496` `1.9×`）与机构推荐（`analyst45` `1.8×`） | [CHN_TOP2000U_D1.md](CHN_TOP2000U_D1.md) |
| **T2 高倍率** | **`DEU`** | **`TOP500`** *(唯一)* | `1` | **`0`** | **`1.8× / 1.61×`** (`6` 塔全 `1.8×` 全空白) | ❌ | 常规 D1 + `Cluster ≥ 1.0`, 经验 `M≥10bp`；单一欧元市场无多国杂音；**实盘验证 `model264` 单字段天花板低（0.71），已及时止损转攻 `analyst93`/`other250`/`fundamental6`** | [DEU_TOP500_D1.md](DEU_TOP500_D1.md) |
| **T2 高倍率** | **`GBR`** | **`TOP700`** *(唯一)* | `1` | `34` | `1.7× / 1.41×` (`sent 1.7×`, `other/anl/news 1.6×`) | ❌ | 常规 D1（经验 `M≥10bp`）；`MODEL` 塔已饱和（23 条 OS，禁再扫）；优先零回测收割 `OTHER 2→3` 存量 `Useful` + 试 `dl_riskfree_returns` | [GBR_TOP700_D1.md](GBR_TOP700_D1.md) |
| **T2 高倍率** | **`HKG`** | **`TOP800`**, `TOP500` | `1` | **`0`** | **`1.7× / 1.41×`** (`anl/model/other 1.7×`, `fnd/news/sent 1.6×`) | ❌ | 常规 D1（无多国汇率杂音）；0 OS 零 SC 撞车；优先 `TOP800` 扩大截面防集中度，`news_sentiment_dl` / `mmp_nlp_sentiment` 高覆盖低拥挤 | [HKG_TOP800_D1.md](HKG_TOP800_D1.md) |
| **T2 高倍率** | **`KOR`** | **`TOP600`** *(唯一)* | `1` | **`0`** | **`1.6× / 1.39×`** (`6` 塔全 `1.6×` 全空白) | ❌ | 常规 D1；韩国散户活跃度极高，行为金融（`behavioral_signals`）与论坛情绪（`equity_forum_data`）具有鲜明本地微观结构优势 | [KOR_TOP600_D1.md](KOR_TOP600_D1.md) |
| **T2 高倍率** | **`IND`** | **`TOP500`** *(唯一)* | `1` | **`0`** | `1.4× / 1.15×` (`analyst 1.4×`, `fnd/news/other 1.3×`) | ❌ | 常规 D1；印度高成长新兴市场、大市值龙头集中（注意 `Weight < 10%` 与 `truncation=0.04`）；0 OS 零 SC 撞车 | [IND_TOP500_D1.md](IND_TOP500_D1.md) |
| **T2 高倍率** | **`AMR`** | **`TOP600`** *(唯一)* | `1` | **`0`** | `1.7× / 1.55×` (`sentiment 1.7×`, `pv 1.4×` 仅 2 塔) | ✅ | **特别注意：AMR 仅支持 7 种中性化（不支持 `RAM`/`CROWDING`/`FAST`/`SLOW`/`SLOW_AND_FAST`！）**，代码传入不支持的中性化会直接报错！且仅 2 个金字塔类别 | [AMR_TOP600_D1.md](AMR_TOP600_D1.md) |

*(注：平台另存在跨区虚拟项 `ALL` [`LARGE`/`MEDIUM`/`SMALL`]，一般仅用于全市场研究对比，非标准地区金字塔主战场。)*

---

## 3. 全量宇宙范围（Universe）精确定义与选池策略

| Universe 名称 | 适用 Region | 股票筛选逻辑（含义） | 标的数量级 | 开发与选池建议（防踩坑） |
| --- | --- | --- | :-: | --- |
| **`TOP3000`** | `USA`, `GLB` | 流动性/市值前 **3,000** 只股票（最宽广标准主池） | ~3,000 | **USA 与 GLB 首选主池**！截面最宽、分散度最高、单股权重不易超 10%，且 `GLB/TOP3000` 拥挤度远低于 `TOPDIV3000` |
| **`TOP2500`** | `EUR` | 欧洲多国流动性前 **2,500** 只股票 | ~2,500 | **EUR 首选主池**！覆盖泛欧大中小盘，历史回测平均 Sharpe 表现最强 |
| **`TOP2000U`** | `CHN` | 中国 A 股流动性前 **2,000** 只**可交易/非受限（Unrestricted）**股票 | ~2,000 | **CHN 唯一合法 D1 宇宙**（末尾 `U` 不可漏写，写 `TOP2000` 会报错！） |
| **`MINVOL1M`** | `ASI`, `GLB` | 日均成交额 **≥ 100 万美元**（Min Dollar Volume \$1M）的流动性池 | 动态 (~1,500–4,000+) | **ASI 首选主池**（亦为 ASI Theme 官方主池）；必须配合 `maxTrade=ON` 与 `Robust ≥ 90%`；警惕小盘股集中度，慎用 `hump` |
| **`MINVOL10M`** | `ASI`, `GLB` | 日均成交额 **≥ 1,000 万美元**的超高流动性池 | 动态 (大中盘) | 容量极大、交易成本更低，适合高换手信号或大盘低摩擦备选对照 |
| **`TOPDIV3000`** | `GLB` | 全球偏高股息/分红特征的 3,000 只池 | ~3,000 | **不作首轮主池**（实测同数据集拥挤度为 `TOP3000` 的 2–3 倍）；仅在 `TOP3000` 穷尽后作对照 |
| **`TOP2000` / `TOP1000`** | `USA` | 美股前 2,000 / 1,000 只中大盘股 | 2,000 / 1,000 | 中大盘测试用；注意广州历史实测 `USA/TOP1000` 情绪长衰减极易低夏普（均 `1.30`），非必要不从 `TOP1000` 起步 |
| **`TOP1200` / `TOP800` / `TOP400`** | `EUR` (`TOP800` 亦含 `HKG`) | 按流动性收缩的中大盘/核心蓝筹子池 | 1,200 / 800 / 400 | `HKG` 主选 **`TOP800`**（比 `TOP500` 截面更宽）；`EUR` 仅在大盘信号验证或 `Sub-Universe` 定位时切换 |
| **`TOPCS1600`** | `EUR` | 欧洲特定核心风格/行业平衡 1,600 只池 | ~1,600 | 欧洲备选池，标准研究仍以 `TOP2500` 为准 |
| **`TOP700` / `TOP600` / `TOP500`** | `GBR(700)`, `KOR/AMR(600)`, `DEU/IND/HKG/ASI/USA(500)` | 单一国家或精简核心市场的主池/蓝筹池 | 500–700 | `GBR`/`DEU`/`KOR`/`IND`/`AMR` 各自唯一主池；因标的数仅 500–700，**特别注意字段覆盖率须 ≥ 50%–60% 且用 `truncation=0.04` 严防单股权重超 10%** |
| **`TOP200` / `TOPSP500`** | `USA` | 美股超大盘前 200 / 标普 500 成分股池 | 200 / 500 | 机构定价极度有效、噪声小但超额难挖，仅适合极少数大盘宏观/分析师因子或对照测试 |

---

## 4. 中性化兼容性速查表（开发防 400 报错必看！）

- **通用 11 种中性化（除 `AMR` 外全部 10 个单一/多国区均支持）**：
  `NONE`, `MARKET`, `SECTOR`, `INDUSTRY`, `SUBINDUSTRY`, `REVERSION_AND_MOMENTUM`, `STATISTICAL`, `CROWDING`, `FAST`, `SLOW`, `SLOW_AND_FAST`
- **多国专属中性化 `COUNTRY`（仅以下 4 区合法！）**：
  ✅ **`GLB`、`EUR`、`ASI`、`AMR`**
  ❌ **`USA`, `CHN`, `DEU`, `GBR`, `HKG`, `KOR`, `IND`**（传入 `COUNTRY` 会直接报 `400 Bad Request`！）
- **`AMR` 特殊阉割列表（仅支持 7 种！）**：
  ✅ `NONE`, `STATISTICAL`, `MARKET`, `SECTOR`, `INDUSTRY`, `SUBINDUSTRY`, `COUNTRY`
  ❌ **严禁对 `AMR` 传入** `REVERSION_AND_MOMENTUM`, `CROWDING`, `FAST`, `SLOW`, `SLOW_AND_FAST`！

---

## 5. 按症状快速定位问题（开发排障对照表）

| 报错或异常现象 | 首先排查层级 | 常见根因与立即修正动作 |
| --- | --- | --- |
| `400 Bad Request` / 提交即 `SYNTAX_ERROR` | **Settings (`Region×Universe×Neut`)** | 检查：① 是否给单国区传了 `COUNTRY`；② 是否给 `AMR` 传了 `RAM`/`CROWDING`；③ `CHN` 是否漏写了 `U`（须 `TOP2000U`）；④ `ASI` 是否忘了 `maxTrade="ON"` |
| 单数据集连续 2 波（64 条）`max |Sharpe| < 0.80` | **Dataset / Field 方向错误** | **立即触发自动早停（`EARLY_STOP_DEMOTED`）**！例如 `DEU/model264` 实测 160 条最高仅 `0.71` → 保留最好低换手种子入库，不再浪费额度跑下一中性化，立刻切换下一个数据集或市场！ |
| `Sharpe` 全集中为 `-0.5 ~ -1.5` | **Template 符号方向** | 原始字段是负面含义（如下跌概率/应计项/排名越低越好）→ 统一只保留 `reverse(...)` 方向或走 `POOL_FLIP`，不要浪费 50% 额度测明知反号的模板 |
| `Sharpe` 尚可但 `Turnover > 70%` / `Margin < 10bp` | **Template 平滑不足** | 字段为高频日度信号 → 在 `rank`/`group_zscore` **之前**加 `ts_mean(x, 22)` 或 `ts_decay_linear(x, 10)`（T0 实证 `model264` TO 从 `67%→2.4%`, Margin 升至 `26bp`） |
| `LOW_2Y_SHARPE`（历史占比 49%） | **Signal 时效衰退 / 过拟合** | 阶段 3 第一优先修 `2Y > 1.58`：换 `subindustry` 分组算子、缩短回看窗或换用低拥挤新字段，不盲目调高 `decay` |
| `LOW_SUB_UNIVERSE_SHARPE` 或 `Weight > 10%` | **Universe 覆盖度 / 集中度** | 核查字段真实覆盖率是否 `< 50%`；在 `TOP500/600/700` 小池保持 `truncation=0.04`，避免使用仅覆盖单一子行业的稀疏字段 |
| `LOW_ASI_JPN_SHARPE` / `Robust < 90%` | **ASI 区域规则** | 切 `neutralization=COUNTRY` 或表达式内加 `group_neutralize(..., country)`，使用 `cov > 85%` 数据集（`price_signal_dl`, `behavioral_signals`, `mmp_nlp_sentiment`） |
| 报 `Prod Correlation FAIL` 但实测 PC 不高 | **PPA-First 平台路由陷阱** | 检查表达式是否触发了 PPA 自动优先检查（`≤8` 算子且 `≤3` 字段）并撞了 PPA 自相关池 `≥ 0.50`；RA 主线须先过完整 RA 门槛并保持与 PPA 隔离 |
