# Stage-0 D1 数据集与字段初筛报告（WebDataScope-1.0.6 + 华子哥 4 差距 + 管理员推荐）

> [!IMPORTANT]
> - **严格 D1-Only 锁定**：本次筛选由 `wq_research_v2` 离线执行（`python -m wq_research_v2 screen fields --region GLB,ASI,CHN,DEU,GBR --top 20 --export`），全流程强制锁定 **`delay = 1`**，零平台回测消耗，零 D0 污染。
> - **结构化输出产物**：完整机读队列已导出至 [stage0_d1_queue_v1.json](file:///C:/Wq/WorldQuant%20Brain/data/exports/stage0_d1_queue_v1.json)（Schema: `stage0_d1_queue_v1`）。
> - **关键时效红线**：`Alphas=0` 免每日额度窗口于 **`2026-12-06`** 冻结截止（剩余 11 天）；实盘跑批前须叠加 `FLD-P1`~`FLD-P4` 的实时 `dateCoverage ≥ 0.60`（5 年覆盖）与非数值陷阱字段拦截。

---

## 1. 方法论与四重差距规则（复用现有工具零重写）

本流水线通过 [wds_adapter.py](file:///C:/Wq/WorldQuant%20Brain/wq_research_v2/src/wq_research_v2/wds_adapter.py) 与 [field_screener.py](file:///C:/Wq/WorldQuant%20Brain/wq_research_v2/src/wq_research_v2/field_screener.py) 直接复用 `legacy_core/Core/tools/webdata_quality/webdata_quality.py` 与 `scripts/tools/webdata_unexploited_analytics.py`，在 `WebDataScope-1.0.6/data`（`info_data.bin` 截至 `2026-02-19`、`osis_data.bin` 截至 `2025-10-19`、145 个有效 D1 精确字段 `.bin` 归档）上融合以下规则：

1. **OS/IS Sharpe 差距与 Sweet-Spot**：筛选 `sharpe_ratio > region_mean_sharpe`（`GREEN`）且处于 `100 ≤ info_count ≤ 3000 & sharpe ≥ 1.1 × mean` 的高产蓝海甜区。
2. **产率差距（`production_rate = osis_count / info_count`）**：识别社区 Sharpe 高但 OS 产率 `< 10%` 的低拥挤蓝海（`WDS_BLUE_OCEAN_GAP`）。
3. **中性化拥挤度差距**：避开单一垄断中性化，直接给出 `n ≥ 20` 且社区 Sharpe 最高的 Top-2/3 非垄断中性化建议，供第一关免盲扫直达高胜率配置。
4. **精确 `.bin` 字段健康分级 + 黑名单与伪 VECTOR 守卫**：
   - 自动剔除 `JX79797` 全局黑名单（`earnings5`, `model194`, `option1`）与 `JX14975` 近 2 年缺失黑名单（本次自动拦截 `GLB` 4 个、`ASI` 9 个）；
   - 自动标注 `known_fake_vector_dataset`（`behavioral_signals`, `model135`, `model109`, `earnings4`），强制只测 `vec_avg` 节省 80% 额度；
   - **显式盲区兜底**：`WebDataScope-1.0.6/data` 快照明确不含 `DEU_1` 与 `GBR_1`，引擎输出 `REGION_NOT_IN_SNAPSHOT` 而不编造数据，直接衔接实时 `cnhkmcp` 与已沉淀的 [FLD-P1](FLD-P1-2to3-QuickWin.md) / [FLD-P2](FLD-P2-DEU-TOP500-D1.md) 字段卡。

---

## 2. 分区域 Stage-0 D1 优选榜单（可直接衔接下一批 `Alphas=0` 探针）

### 2.1 `GLB / TOP3000 / D1`（区域均值 Sharpe=`0.4394` · 拦截黑名单 `4` 个 · 主攻 `GLB/analyst` & `GLB/fundamental` 2→3）

| 档位 | Dataset ID | 命中来源 | 社区 Sh (Gap) | 产率 (`osis/info`) | 精确 `.bin` T1/T2 | 优先非垄断中性化 (Sh / 占比) | 实战落点建议 |
| :-: | --- | --- | :-: | :-: | :-: | --- | --- |
| **P0** | **`analyst15`** | 管理员推荐 + `.bin` T1 | `0.4765` (`+0.0372`) | `16.3%` (`4813/29474`) | **65 / 29** | `REVERSION_AND_MOMENTUM` (`0.774`, 5.3%) · `INDUSTRY` (`0.578`, 3.3%) | **直攻 `GLB/D1/ANALYST` 2→3！** 样例 T1：`anl15_gr_12_m_1m_chg` 等，避开 `STATISTICAL` 拥挤区直走 `RAM` |
| **P0** | **`analyst10`** | WDS 蓝海 + 管理员推荐 | `0.4669` (`+0.0275`) | **`0.0%`** (`0/2646`) | 0 / 0 | `FAST` (`0.730`, 3.4%) · `REVERSION_AND_MOMENTUM` (`0.701`, 7.7%) | **直攻 `GLB/D1/ANALYST` 2→3！** 配合 [FLD-P1](FLD-P1-2to3-QuickWin.md) 精选字段 |
| **P0** | **`model239`** | WDS 蓝海 + Sweet-Spot | **`0.7629`** (`+0.3236`) | `6.65%` (`25/376`) | 0 / 0 | **`COUNTRY` (`1.117`, 8.7%)** · `SUBINDUSTRY` (`0.706`, 16.4%) | 社区均值差距全区第一梯队，`COUNTRY` 中性化优势极大 |
| **P0** | **`sentiment26`** | WDS 蓝海 + Sweet-Spot | **`0.7389`** (`+0.2995`) | **`0.0%`** (`0/795`) | 0 / 0 | `SUBINDUSTRY` (`0.808`, 4.4%) · `STATISTICAL` (`0.785`, 54.8%) | 与用户截图经典范式 `snt26_top50pctranking` 同源！低拥挤高 Sharpe |
| **P0** | **`model31`** | WDS 蓝海 + Sweet-Spot | `0.5813` (`+0.1419`) | **`0.0%`** (`0/362`) | 0 / 0 | `CROWDING` (`0.634`, 3.9%) · `STATISTICAL` (`0.571`, 76.4%) | `CROWDING` 反拥挤切入 |
| **P0** | **`model252`** | WDS 蓝海 + Sweet-Spot | `0.5510` (`+0.1116`) | `4.68%` (`13/278`) | 0 / 0 | `CROWDING` (`0.726`, 11.8%) · `COUNTRY` (`0.574`, 7.1%) | GLB & ASI 跨区同时入围 P0 |
| **P0** | **`institutions6`** | WDS 蓝海 + Sweet-Spot | `0.4961` (`+0.0567`) | **`0.0%`** (`0/1053`) | 0 / 0 | `REVERSION_AND_MOMENTUM` (`0.786`, 15.1%) · `SUBINDUSTRY` (`0.709`, 4.7%) | 零 OS 产率高潜力机构类空白塔备选 |
| **P0** | **`global_seasonal_model`** / **`insider_agg_matrix`** | 管理员推荐 (新于 02-19 快照) | 实时查 | 实时查 | — | 见 [FLD-P1](FLD-P1-2to3-QuickWin.md) | 2026 年下半年新增集，极低拥挤，优先查 `Alphas=0` 字段 |

### 2.2 `ASI / MINVOL1M / D1`（区域均值 Sharpe=`0.4793` · 自动拦截 `9` 个 2Y 缺失黑名单 · 唯一活跃 D1 Theme 至 `12-20`）

| 档位 | Dataset ID | 命中来源 | 社区 Sh (Gap) | 产率 (`osis/info`) | 优先非垄断中性化 (Sh / 占比) | 实战与 Theme 注意事项 |
| :-: | --- | --- | :-: | :-: | --- | --- |
| **P0** | **`fundamental4`** | 管理员推荐 + Sweet-Spot | **`0.7751`** (`+0.2958`) | `22.9%` (`25/109`) | **`COUNTRY` (`0.935`, 63.9%)** · `MARKET` (`0.449`, 18.5%) | ASI Theme 10 推荐集之一；开启 `maxTrade=ON` + 控 Fundamental ≤30% |
| **P0** | **`model252`** | WDS 蓝海 + Sweet-Spot | `0.6924` (`+0.2131`) | **`6.47%`** (`11/170`) | `STATISTICAL` (`0.896`, 31.9%) · `SUBINDUSTRY` (`0.696`, 25.3%) | ASI 蓝海 + 甜区双命中最优非 Theme 补充集 |
| **P0** | **`ai_news_scores`** / **`corporate_news_index`** / **`mmp_nlp_sentiment`** / **`price_signal_dl`** / **`sentiment7`** | 管理员 Theme 推荐 (新于快照) | 实时查 | 实时查 | 建议先试 `COUNTRY` / `group_cartesian_product(country, sector)` | 全部在 [FLD-P3](FLD-P3-ASI-MINVOL1M-D1.md) 验真有权限，走 **`PPA + ATOM`（免日 1/月 10 配额）** |
| **P0** | **`behavioral_signals`** | 管理员 Theme 推荐 | 实时查 | 实时查 | 同上 | **`known_fake_vector_dataset=True`**：强制只跑 `vec_avg` 省 80% 额度 |
| **P1** | **`risk59`** / **`model243`** / **`news59`** / **`model207`** | WDS Sweet-Spot / 管理员 | `0.69–0.82` (`+0.21~+0.34`) | `17%–43%` | `risk59`: `CROWDING`/`COUNTRY` (`>1.04`) · `news59`: `COUNTRY` (`1.235`) | 极高 `COUNTRY` 社区 Sharpe，配合 `maxTrade=ON` & Robust ≥ 90% |

### 2.3 `CHN / TOP2000U / D1`（区域均值 Sharpe=`0.3492` · 主攻 `1.9×/1.8×` 空白金字塔）

| 档位 | Dataset ID | 命中来源 | 社区 Sh (Gap) | 产率 (`osis/info`) | 精确 `.bin` T1/T2 | 优先非垄断中性化 (Sh / 占比) | 实战落点建议 |
| :-: | --- | --- | :-: | :-: | :-: | --- | --- |
| **P0** | **`other561`** | WDS 蓝海 + Sweet-Spot | **`1.1345`** (**`+0.7853`**) | **`0.0%`** (`0/165`) | 0 / 0 | **`REVERSION_AND_MOMENTUM` (`1.581`, 28.3%)** · `CROWDING` (`0.992`, 34.3%) | **全场差距之王！** 直击 `CHN/D1/OTHER` **`1.9×`** 空白金字塔，先核实时 `dateCoverage` 与 `Alphas=0` |
| **P0** | **`macro61`** | WDS 蓝海 + Sweet-Spot | **`0.9333`** (`+0.5841`) | **`0.0%`** (`0/149`) | 0 / 0 | `REVERSION_AND_MOMENTUM` (`1.105`, 14.8%) · `CROWDING` (`0.998`, 25.5%) | 极低拥挤高 Sharpe 宏观蓝海 |
| **P0** | **`other551`** | WDS 蓝海 + Sweet-Spot | `0.7168` (`+0.3676`) | **`0.0%`** (`0/111`) | 0 / 0 | `CROWDING` (`0.691`, 48.2%) | `CHN/D1/OTHER 1.9×` 第二梯队蓝海 |
| **P0** | **`risk88`** / **`analyst45`** | WDS 蓝海 / 管理员新集 | `0.4145` / 实时查 | `9.5%` / 实时查 | 0 / 0 | `SLOW` (`0.541`) · `INDUSTRY` (`0.501`) | `analyst45` 已入 [FLD-P4](FLD-P4-CHN-TOP2000U-D1.md) 清洗卡 |
| **P1** | **`model135`** | 精确 `.bin` T1 | `0.4370` (`+0.0879`) | `95.9%` (`70/73`) | **129 / 1** | `SLOW` (`0.553`) | **`known_fake_vector_dataset=True`**，仅作高覆盖 T1 基线参考（`mdl135_d01_bb/fmc/icc`） |

### 2.4 `DEU / TOP500 / D1` 与 `GBR / TOP700 / D1`（`REGION_NOT_IN_SNAPSHOT` 显式实时兜底）

- **`DEU / TOP500 / D1`（6 个 `1.8×` 永久空白金字塔）**：因不在 02-19 快照中，自动路由至实时 API 与 [FLD-P2-DEU-TOP500-D1.md](FLD-P2-DEU-TOP500-D1.md) 全部 **8 个 P0 种子集**（`model264`, `analyst93`, `other250`, `other455`, `fundamental6`, `fundamental72`, `fundamental89`, `fundamental93`），已备好 **119 个清洗后 `Alphas=0` 字段**（均过非数值陷阱拦截与 `cov>0` 核验）。
- **`GBR / TOP700 / D1`（`GBR/OTHER` 2→3 速赢 + `GBR/IMBALANCE` 0→1）**：路由至实时 API 与 [FLD-P1-2to3-QuickWin.md](FLD-P1-2to3-QuickWin.md) **5 个 P0 种子集**（`dl_riskfree_returns`, `other250`, `other455`, `other47`, `other696`），同时优先消化近 60 天未提交池中的现成 Tier-A1 候选。

---

## 3. 下一步衔接口令（待用户批准 T0 校准批后触发）

```powershell
# 查看单字段 5:5 平衡 Stage-0 探针计划（离线零发单）
$env:PYTHONPATH="wq_research_v2\src"
python -m wq_research_v2 plan batch --region DEU --universe TOP500 --dataset model264 --field mdl264_1l_fmc --queue UNUSED_ALPHA0
```

最后生成时间：2026-11-25。
