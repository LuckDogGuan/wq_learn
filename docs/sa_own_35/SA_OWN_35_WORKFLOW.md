# 路线 ⑤：SuperAlpha 独立路线（SuperAlpha Own v1.0）

> **路线标识**：`super_alpha_own_v1` · 日志前缀 `[TRACK:super_alpha_own_v1]`
> **定位**：SuperAlpha（`type=SUPER`）独立回测线，**完全隔离于 RA 主线**（`data/wq_v2_ledger.db`）。只做 SuperAlpha 回测，**永不自动 `/submit`**。
> **构建基座**：继承路线④（`alphaforge_agy_dsh_v4`）的 P0 门禁 / 断点续传 / 日志隔离工程闭环；方法论文本源自王哥（ZS59763）+ 贺六浑（JR23144）+ 管理员（KH94146）。
> **配置文件**：[sa_own_config.json](sa_own_config.json) · **专属运行日志**：[sa_own_35_log.md](sa_own_35_log.md) · **五条路线总手册**：[TRACKS_AND_LOGS_GUIDE.md](../TRACKS_AND_LOGS_GUIDE.md)

---

## 一、额度预算（2026-11-28 用户拍板）

| 槽位 | 每日回测额度 | 说明 |
| --- | --- | --- |
| 常规 RA（路线①②④ 主线） | **4,200** | `daily_target / alpha0_switch_threshold` 已从 4,500 → 4,200 |
| SuperAlpha（本路线⑤） | **400** | `sa_daily_sim_budget = 400`，硬上限 |
| 安全垫 | 400 | 缓冲在途略超 / 429 / 人工手测 |
| **合计** | **4,600** | ≤ 平台 5,000/天 |

**关键澄清**：SuperAlpha 回测**共享**平台 5,000/天回测额度（Regular/Python/SuperAlpha 全走 `POST /simulations`）；SuperAlpha **提交配额独立**（1 条/天，不占 4 条 RA/天）。Gold 仅可组 `own`（自有池）。

---

## 二、运行方法（王哥 SELECTION v2 + 贺六浑 own 三五）

### Step 1 · 解锁检查（0 回测成本）
```powershell
$env:PYTHONPATH="wq_research_v2\src"
python -m wq_research_v2 sa status --region EUR
```
只读返回 `genius_level` + `submitted_regular_count`（≥100 即解锁 own SA）+ `super_alpha_count`。

### Step 2 · 盘点 own 弹药库（0 回测成本）
```powershell
python -m wq_research_v2 sa ammo --region EUR --limit 100
```
只读拉取已提交 D1 REGULAR，确认候选腿数 ≥10 才值得组（王哥+评论区硬约束）。

### Step 3 · 预览 payload（0 回测成本）
```powershell
python -m wq_research_v2 sa preview --spec docs/sa_own_35/sa_spec_example.json
```

### Step 4 · 正式回测（400/天上限，并发 3）
```powershell
python -m wq_research_v2 sa run --spec docs/sa_own_35/sa_spec_example.json --budget 400 --workers 3
```

### Step 5 · 断点续传
```powershell
python -m wq_research_v2 sa resume
```

### Selection 铁律（王哥 v2 十步法）
- `own && prod_correlation∈(0.1,0.6) && operator_count∈[2,8] && datafield_count<=3~4 && decay∈{0,1,3,5} && truncation<=0.1 && universe!='ILLIQUID_MINVOL1M'`
- 分层（turnover / long_count / datacategories）避免重复选取；**选择过细等于不选择，设置 selectLimit 不如多设条件**。

### Combo 铁律（王哥 + 韩国研究员 + 管理员共识）
- 等权 `1` 永远第一基准；进阶 `combo_a(alpha, mode='algo1')` / 风险平价；**combo 算子 ≤3，永不给因子负权重**。
- **定稿前必须切 `componentActivation=OS` 做 Reality Check**（官方 `superalpha-overview`），否则 OS/IS≥0.3 都难。

---

## 三、严禁事项（与工作区红线一致）

1. **严禁**任何形式的 SuperAlpha 自动 `/submit`（本模块无 submit 路径；1 条/天由用户网页端手动）。
2. **严禁**把 SA 的 selection/combo 送进 RA 的 `ExprValidator`（SA 方言含 `own/not(own)/in(...)/prod_correlation`，不是 FASTEXPR）。
3. **严禁**写 `data/wq_v2_ledger.db`（RA 主线库）；SA 台账唯一落点是 `data/sa_own_ledger.db`。
4. **严禁**突破 `SA_MAX_WORKERS=3` 与 `sa_daily_sim_budget` 硬上限。
5. **严禁**在 selection 用历史 Sharpe/Returns 排序（极端过拟合）。

---

## 四、红线继承

`delay=1` 全链路锁定；SA 提交也绝不自动；`reference/`、`legacy_core/Core/runtime_data/`、`Password/config.yaml` 只读；低内存 WAL Checkpoint；任务窗口 3–24 小时、最长 4 小时一次轻量巡检。
