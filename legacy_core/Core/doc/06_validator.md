# 06 — `Core/sim/validator.py` — 提交前验证逻辑

## 核心设计原则：严格职责分离

```
┌─────────────────────────────────────────────────────────────┐
│              检查函数         数据来源          fallback？  │
├─────────────────────────────────────────────────────────────┤
│  get_sc_check()    │ 本地参考池+目标PnL只读 │ 无（返回待定状态） │
│  get_ppac_check()  │  本地 sc_engine  │  无（返回 "no_cache"）│
│  get_pc_check()    │  /correlations/prod，/check 单次降级 │ 无（返回 float nan） │
└─────────────────────────────────────────────────────────────┘
```

**三个检查函数互相独立，禁止任何形式的 fallback 或混用。**

---

## 函数详解

### `get_sc_check(client, alpha_id, cache_pnl_below=None)` — 本地参考池计算

```
调用链：
  _ensure_sc_cache()
      └── load_data(tag='SelfCorr')  [磁盘读取]
              └── 若磁盘为空 + client 存在 → download_data() 触发一次下载
  calc_self_corr(client, alpha_id, _sc_rets, _sc_ids,
                 cache_pnl_below=cache_pnl_below)
```

**返回值：**
- `float` — SC 值（0.0 ~ 1.0），越小越好
- `"no_cache"` — 本地缓存为空，需先调用 `download_data()`
- `"pnl_unavailable"` — 平台连续三次没有返回目标 Alpha PnL，属于不可观察状态
- `"error"` — `calc_self_corr()` 的其它计算异常

**不发生的事：**
- ❌ 不调用 `get_alpha_check()`
- ❌ 不调用平台 `/check` 接口
- ✅ 始终只读请求目标 Alpha 详情；没有目标缓存时才请求 `/recordsets/pnl`
- ✅ 设置 `cache_pnl_below=0.5` 后，严格通过项保存目标 PnL，达到阈值则删除
- ✅ 目标 PnL 缓存与 OS SC 参考池分离

---

### `get_ppac_check(client, alpha_id)` — PPAC，只本地

```
调用链：
  _ensure_ppac_cache()
      └── load_ppac_data()  [= load_data(tag='PPAC')]  [磁盘读取]
              └── 若磁盘为空 + client 存在 → download_data() 触发一次下载
  calc_ppac(client, alpha_id, _ppac_rets, _ppac_ids)
```

**返回值：**
- `float` — PPAC 值（0.0 ~ 1.0）
- `0.0` — 该 Alpha 所在 Region 无 PPA Alpha 参考数据
- `float('nan')` — PPA 参考数据存在但没有有效收益重叠（上层需处理）
- `"no_cache"` — 本地缓存为空
- `"error"` — 计算异常

**不发生的事：**
- ❌ 不调用 `get_ppc_value()`（平台 power-pool 接口）
- ❌ 不调用 `get_alpha_check()`
- ❌ 不 fallback 到任何网络请求

---

### `get_pc_check(client, alpha_id, max_attempts=1, wait_seconds=30, should_stop=None)` — 生产相关性，只远端

```
调用链：
  优先 GET /alphas/{id}/correlations/prod
  未获得数值时单次 GET /alphas/{id}/check
  提取 checks 中 name=="PROD_CORRELATION" 的 value
```

**返回值：**
- `float` — `PROD_CORRELATION` 值
- `float('nan')` — 平台 checks 中无该字段（平台尚未完成检查）
- `"sleep"` — `is == 0`，Session 已过期，需重新 `login()`
- `"error"` — 接口返回空或 JSON 解析失败

**不发生的事：**
- ❌ 不调用 `calc_ppac()`（本地计算）
- ❌ 不调用 `get_ppc_value()`（power-pool 接口）
- ❌ 不使用任何本地缓存

---

## 模块级缓存机制

```python
# SC 缓存
_sc_ids    = None   # {region: [alpha_id, ...]}  非 PPA OS Alpha
_sc_rets   = None   # pd.DataFrame  日收益率矩阵
_sc_loaded = False

# PPAC 缓存
_ppac_ids    = None  # {region: [alpha_id, ...]}  PPA Alpha
_ppac_rets   = None  # pd.DataFrame
_ppac_loaded = False
```

- **单例模式**：模块首次 import 后，缓存在进程内全局有效。
- **线程安全**：使用 `threading.Lock()` 防止并发加载竞态。
- **惰性加载**：只在第一次调用 `get_sc_check()` 或 `get_ppac_check()` 时加载缓存。

### `invalidate_cache()`

```python
invalidate_cache()
```
- 同时重置 `_sc_loaded = False` 和 `_ppac_loaded = False`。
- 调用时机：执行 `download_data()` 更新缓存后，需要让 validator 重新读取新数据时调用。

---

## 其他工具函数

### `get_alpha_extended_details(client, alpha_id)` → `dict`

从 GET `/alphas/{id}` 提取 IS/Train/Test 三个阶段的详细指标：
- 每阶段：`sharpe / fitness / turnover / returns / drawdown / margin`
- 每阶段还有 `investabilityConstrained` 子集（同字段）
- `is_testing_status`：各检查项的 PASS/FAIL/WARNING 计数
- `fail_reasons`：所有 FAIL 的检查项名称列表

### `is_ppa(alpha_info)` → `bool`

判断 Alpha 是否属于 PPA：检查 `is.checks` 中是否存在 `name == "POWER_POOL_CORRELATION"` 的项。

---

## 典型调用场景

```python
from Core.sim.validator import get_sc_check, get_pc_check, get_ppac_check, invalidate_cache
from Core.sim.sc_engine import download_data
from Core.api import login

client = login()

# 首次或更新：下载 OS Alpha 数据
download_data(client, flag_increment=True)
invalidate_cache()   # 让 validator 重新加载新缓存

# 批量验证
for alpha_id in candidate_list:
    sc = get_sc_check(client, alpha_id)
    if sc == "no_cache":
        print("SC 缓存未初始化")
        break
    if isinstance(sc, float) and sc > 0.7:
        print(f"{alpha_id} SC={sc:.3f} 过高，跳过")
        continue

    ppac = get_ppac_check(client, alpha_id)
    if isinstance(ppac, float) and ppac != ppac:  # nan
        print(f"{alpha_id} 所在 Region 无 PPA Alpha，PPAC 按 0.0 处理")

    pc = get_pc_check(client, alpha_id)
    if pc == "sleep":
        client = login()
        pc = get_pc_check(client, alpha_id)
    if isinstance(pc, float) and pc > 0.7:
        print(f"{alpha_id} PC={pc:.3f} 生产相关性过高，跳过")
        continue

    print(f"{alpha_id} 通过验证 SC={sc:.3f} PPAC={ppac} PC={pc:.3f}")
```

持续运行脚本应优先调用 `Core.sim.sc_pyramid_refresh.refresh_sc_pyramid_bundle()`；
它会在SC缓存实际增加后自动调用 `invalidate_cache()`，并按新增OS Alpha决定是否刷新塔。
