# Tier-A1（`92 → 100`）全量本地 SC、候选池 `N×N` 正交去重与只读终检审核包

> [!IMPORTANT]
> - **100% 只读审计边界**：全程仅调用 `GET /users/self/alphas?stage=OS`、`GET /alphas/{id}`、`GET /alphas/{id}/recordsets/pnl`、`GET /alphas/{id}/correlations/prod` 与 `GET /alphas/{id}/check`。**零回测、零 `PATCH`、零 `/submit`**。
> - **新版可移植本地 SC 缓存全量就绪**：[os_pnl_cache.db](file:///C:/Wq/WorldQuant%20Brain/data/sc_cache_v2/os_pnl_cache.db) 已 100% 同步全部 **92 / 92** 条已提交 OS Alpha（`USA: 29 [5 PPA]`, `GBR: 28 [1 PPA]`, `EUR: 18 [2 PPA]`, `GLB: 17 [15 PPA]`，`failed_pnl = 0`），彻底修复旧 `sc_engine.py` 缓存停留在 2026-09-09（仅 89 条）的严重盲区。
> - **平台实盘 `/correlations/prod` 与 `/check` 状态如实记录**：本次审计期间（`2026-11-25 16:15–16:28 CST`），平台对 `KPVlkqwE` 立即返回 `PC = 0.7742`（`PC_READY_HIGH`），其余 8 条均持续返回 `HTTP 200` + `Retry-After: 1.0` + 空响应体（异步计算排队中）。`wq_research_v2/pc_poller.py` **严格标记为 `PENDING_PC_COMPUTING` 而绝不伪造 `PC=0` 或误报通过**（同步暴露出 `cnhkmcp:check_correlation` 在空体下误返 `all_passed: true` 的隐患）。

---

## 1. 关键纠偏：新版 92-OS 缓存拦截 3 条过期 `Useful` 雷区 + 6 对池内互撞

### 1.1 被拦截的 3 条“过期 `Useful`”高 SC 候选（强烈建议切勿提交）

旧 `sc_engine.py` 因缺失近期提交的 **`1YWNm9eM`**（`GBR/D1/OTHER` OS），导致以下 3 条 10 月份标了 `Useful` 的候选在旧体系下显得 SC 仅 `0.42–0.47`；**新版全量 92-OS 实时复算显示它们与 `1YWNm9eM` 的相关性高达 `0.81–0.93`**：

| Alpha ID | 原标签 / 历史名称 | 新版全量 92-OS 实测 `SC_ALL` | 撞车 OS Peer | 处置建议 |
| --- | --- | :-: | :-: | --- |
| **`j287pqwO`** | `Useful` (`SC 0.423 PC 0.593`) | **`0.9254`** (`SC_READY_HIGH`) | `1YWNm9eM` | **拦截！** 确认后可用 `wq_research_v2 tag apply --alpha-ids j287pqwO,mL6vGEzE,omomd71E --tag SC_IS_HIGHT --confirm-apply` 自动剥离过期 `Useful` 并标 `SC_IS_HIGHT` |
| **`omomd71E`** | `Useful` (`SC 0.434 PC 0.607`) | **`0.8285`** (`SC_READY_HIGH`) | `1YWNm9eM` | **拦截！** 同上 |
| **`mL6vGEzE`** | `Useful` (`SC 0.470 PC 0.638`) | **`0.8115`** (`SC_READY_HIGH`) | `1YWNm9eM` | **拦截！** 同上 |

### 1.2 实盘高 PC 淘汰（1 条）

- **`KPVlkqwE`**（`GBR/D1/OTHER`, `tm_15_r1_r5_r10_rh_glb_d1_r5_q1`, `SC = 0.1843`）：实盘 `/correlations/prod` 立即返回 **`pc_max = 0.7742`（`PC_READY_HIGH`）**，不具备直提条件；其孪生变体 **`LL8VlGQ1`** 与其池内相关高达 **`0.9723`**，一并淘汰。

### 1.3 候选池 `N×N` 两两正交矩阵拦截（6 对，防“交一个挂一批”）

| 被剪枝候选 | 阻断它的高优候选 | 候选池两两相关 | 关键价值 |
| --- | --- | :-: | --- |
| `LL8VlGQ1` | `KPVlkqwE` | `0.9723` | `tm_15` 同集孪生字段 |
| `XgNmlLm5` | `2rG8ZR8Z` | `0.9791` | `imb5_score` (`ts_rank` vs `ts_zscore`) |
| `6XKVp8kP` | `leKO8qPA` | `0.8663` | 同式不同池（`TOP2000` vs `TOP3000`） |
| `kqgz1q5k` | `xAbJ6grw` | `0.7554` | 同源 `eur_aggregated_value_2` |
| `wpNKJgpQ` | `0mGOAaW8` | `0.7423` | 同源 `mdl177_rvm_rvm_eur_composite_alt` |
| **`e71knEaN`** | **`1YGknEYQ`** | **`0.7310`** | **高价值跨数据集撞车拦截！** `mdl38` 与 `mdl177` 表面分属两数据集，但日收益相关性达 `0.731`，两两矩阵提前防止连续提交失败 |

---

## 2. 净剩正交低 SC 人工复核清单（直接推进 **`92 → 100`**）

下表全部候选**全量 92-OS `SC < 0.54`** 且**同区域任意两条之间两两相关性严格 `< 0.59`**（安全低于 `0.68` 正交红线）：

| 建议顺序 | Alpha ID | Region / Uni | 金字塔贡献 | 当前标签 / 历史 PC | 实测 `SC_ALL` (Peer) | 同区池内最大互相关 | Sh / Fit / TO / Margin | 远程 PC/Check 实时状态 | 人工操作建议 |
| :-: | --- | --- | --- | --- | :-: | :-: | :-: | --- | --- |
| **1 (立即可审)** | **`bl8LnbA6`** | `GBR/TOP700` | **`GBR/D1/OTHER`** (**2→3, `1.6×`**) | **`Useful`** (`PC 0.538`) | **`0.1715`** (`mLgkbx5p`) | **`0.0954`** (vs `xAbJ6grw`) | `1.65 / 1.08 / 15.8% / 8.6bp` | `PENDING_PC_COMPUTING` *(已有历史 `PC 0.538` 验真)* | **首选第 1 条！** 已带 `Useful` 标签，网页端确认提交检查绿灯即可手工提交，直接点亮 `GBR/OTHER 2→3` |
| **2 (立即可审)** | **`xAbJ6grw`** | `GBR/TOP700` | **`GBR/D1/OTHER`** (**2→3, `1.6×`**) | **`Useful`** (`PC 0.625`) | **`0.5316`** (`1YWNm9eM`) | **`0.0954`** (vs `bl8LnbA6`) | `2.76 / 1.88 / 56.6% / 9.3bp` | `PENDING_PC_COMPUTING` *(已有历史 `PC 0.625` 验真)* | **首选第 2 条！** 已带 `Useful` 标签，与 `bl8LnbA6` 几乎完全正交（`0.095`），可双收冲 `94/100` |
| **3 (待 PC 落定)** | **`2rG8ZR8Z`** | `GBR/TOP700` | **`GBR/D1/IMBALANCE`** (**空白 0→1**) | 无标签 (`SC 0.187`) | **`0.1871`** (`j26qYaQo`) | `0.1734` (vs `0mGOAaW8`) | `1.96 / 1.40 / 16.6% / 10.3bp` | `PENDING_PC_COMPUTING` *(需复查实时 PC)* | **高优空白塔候选！** 待平台 PC 队列空闲执行 `pc check`，若 `<0.70` 即打 `Useful` 交网页手工提交 |
| **4 (待 PC 落定)** | **`1YGknEYQ`** | `GBR/TOP700` | `GBR/D1/MODEL` (`92→100` 凑量) | 无标签 (`SC 0.514`) | **`0.5138`** (`9qpbKkoo`) | `0.5898` (vs `0mGOAaW8`) | `2.38 / 2.29 / 14.4% / 18.4bp` | `PENDING_PC_COMPUTING` | 顶级 Fitness (`2.29`) 与 Margin (`18.4bp`)；待 PC `<0.70` 后打 `Useful` |
| **5 (待 PC 落定)** | **`0mGOAaW8`** | `GBR/TOP700` | `GBR/D1/MODEL` (`92→100` 凑量) | 无标签 (`SC 0.458`) | **`0.4580`** (`qMj18MnO`) | `0.5898` (vs `1YGknEYQ`) | `2.60 / 1.46 / 42.9% / 6.3bp` | `PENDING_PC_COMPUTING` | 2Y Sharpe `2.35`；与 `1YGknEYQ` 相关性 `0.5898 < 0.68` 可共存 |
| **6 (待核 `RA_CHILD`)** | **`leKO8qPA`** | `USA/TOP3000` | **`USA/D1/PV`** (**空白 0→1**) | 无标签 (`type=RA_CHILD`) | **`0.4878`** (`omYMxop5`) | 单条代表 | `2.73 / 1.57 / 38.8% / 6.6bp` | `PENDING_PC_COMPUTING` | 需核实 `RA_CHILD` 网页直提资格及实时 PC（若不可直提则改 `-rank(pv47_...)` 复现 1 次） |
| **7 (单步急救)** | **`LL8VRmX6`** | `GBR/TOP700` | `GBR/D1/ANALYST` (`1.6×`) | 临界 `PC 0.705` | **`0.2793`** (`vRkge0K3`) | `< 0.13` | `1.92 / 1.23 / 1.64 (2Y)` | `PENDING_PC_COMPUTING` | 仅超 PC 线 `0.005`，列入后续 1 步 `signed_power` 降 PC 候选 |
| **备选** | **`786bZAR5`** | `EUR/TOP2500` | `EUR/D1/PV` | 无标签 (`type=RA_CHILD`) | **`0.1405`** (`qMj63zwj`) | 单条代表 | `3.29 / 1.55 / 41.1% / 4.5bp` | `PENDING_PC_COMPUTING` | Margin `4.5bp` 偏低，仅作末位备选 |

---

## 3. 轻量 `Useful` 标签复查与运维指令（无 GUI，显式确认后执行）

```powershell
$env:PYTHONPATH = "wq_research_v2\src"

# 1. 待平台相关性队列空闲时，补测 4 条核心待定候选的只读远程 PC 与 /check（零写操作）
python -m wq_research_v2 pc check --alpha-ids 2rG8ZR8Z,1YGknEYQ,0mGOAaW8,leKO8qPA --region GBR

# 2. 若需清理已确认撞车 1YWNm9eM 的 3 条过期 Useful 标签（默认 dry-run 预览，加 --confirm-apply 才写标签）
python -m wq_research_v2 tag apply --alpha-ids j287pqwO,mL6vGEzE,omomd71E --tag SC_IS_HIGHT
# 确认无误后执行：
# python -m wq_research_v2 tag apply --alpha-ids j287pqwO,mL6vGEzE,omomd71E --tag SC_IS_HIGHT --confirm-apply

# 3. 待 2rG8ZR8Z 等 PC < 0.70 验证通过后，打上 Useful 标签供您在 BRAIN 网页端筛选并手工提交：
# python -m wq_research_v2 tag apply --alpha-ids 2rG8ZR8Z,1YGknEYQ --tag Useful --confirm-apply
```

最后审计时间：2026-11-25 16:28 CST。
