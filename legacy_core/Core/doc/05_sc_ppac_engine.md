# 05 — `Core/sim/sc_engine.py` — 本地 SC/PPAC 计算引擎

## 背景

WorldQuant BRAIN 平台的自相关性 (SC) 和 PPA 相关性 (PPAC) 检查需要消耗平台 API 限额，且存在网络延迟。通过将 OS Alpha 的 PnL 序列缓存在本地，可以在**毫秒级**完成相关性计算，完全不依赖平台接口。

本模块直接内嵌了 `brain-calculate-alpha-selfcorrQuick` Skill 的核心算法，**不需要安装任何额外包，不使用动态 import**。

---

## 本地缓存结构

```
Core/runtime_data/sc_ppa/
    ├── os_alpha_ids.pickle      {region: [alpha_id, ...]}  所有 OS Alpha 按地区分组
    ├── os_alpha_pnls.pickle     pd.DataFrame  Date × alpha_id  完整 PnL 序列
    └── ppac_alpha_ids.pickle    [alpha_id, ...]  PPA Alpha ID 列表（用于区分 SC/PPAC）
```

- **SC 使用**：`os_alpha_ids` 中排除 `ppac_alpha_ids` 的子集（非 PPA OS Alpha）
- **PPAC 使用**：`os_alpha_ids` 中只保留 `ppac_alpha_ids` 的子集（PPA Alpha）

---

## 核心算法：相关性计算

SC 和 PPAC 使用**完全相同的计算流程**，区别仅在比较的参考 Alpha 集合：

```
目标 Alpha PnL
    ↓  差分
目标 Alpha 日收益率（近 4 年）
    ↓  corrwith
参考 Alpha 日收益率矩阵（同 Region）
    ↓  max()
最终相关性值（0.0 ~ 1.0）
```

**`corrwith()`** 是 pandas 的向量化相关系数计算，对矩阵中每列（每个参考 Alpha）分别计算 Pearson 相关系数，最终取 max。

**NaN 处理**：若 Region 没有任何 PPA 参考 Alpha，PPAC 返回 `0.0`；若参考序列存在但没有有效重叠，PPAC 返回 `float('nan')`，表示无法判断。

---

## 函数清单

### 数据下载

```python
def download_data(client, cache_dir=DEFAULT_CACHE_DIR, flag_increment=True)
```
- 拉取平台 OS 阶段 Alpha 列表（`get_os_alphas`）。
- 增量模式（`flag_increment=True`）：跳过已缓存 Alpha，只下载新增。
- 全量模式（`flag_increment=False`）：忽略旧缓存，全量重下。
- 并行下载 PnL（`ThreadPoolExecutor(max_workers=10)`）。
- 写入三个 pickle 文件。
- **调用时机**：首次使用前或需要更新缓存时手动调用。

### 数据加载

```python
def load_data(cache_dir=DEFAULT_CACHE_DIR, tag='SelfCorr') -> (dict, pd.DataFrame)
def load_ppac_data(cache_dir=DEFAULT_CACHE_DIR) -> (dict, pd.DataFrame)
def refresh_ppac_data(client, cache_dir=DEFAULT_CACHE_DIR,
                      flag_increment=True, return_report=False)
```
- 从磁盘加载 pickle → 按 `tag` 过滤 Alpha 集合 → 差分计算日收益率 → 截取近 4 年。
- `tag='SelfCorr'`：排除 PPA Alpha（用于 SC 计算）。
- `tag='PPAC'`：只保留 PPA Alpha（用于 PPAC 计算）。
- 失败返回 `({}, pd.DataFrame())`。
- `refresh_ppac_data()` 每次先增量刷新一次缓存，再返回 PPAC ID 映射和收益率矩阵，适合批量筛选入口复用。
- `return_report=True` 时额外返回刷新报告，其中包含平台发现但未缓存、成功新增、PnL 失败的 Alpha ID，以及刷新后的本地缓存总数。

### SC 计算

```python
def calc_self_corr(client, alpha_id, os_alpha_rets, os_alpha_ids,
                   alpha_result=None, alpha_pnls=None) -> float
```
- 拉取目标 Alpha PnL → 差分 → 与同 Region 非 PPA Alpha 做 corrwith → 取 max。
- 可传入 `alpha_result` 和 `alpha_pnls` 避免重复请求。

### SC 与 Pyramid 统一刷新

```python
from Core.sim.sc_pyramid_refresh import refresh_sc_pyramid_bundle

result = refresh_sc_pyramid_bundle(client, interval_hours=6)
result = refresh_sc_pyramid_bundle(client, interval_hours=6, force=True)  # 手动强制刷新
```

- 安全检查点调用；未到6小时不会访问平台。
- 自动模式仅在发现新增远端OS Alpha时刷新Pyramid；首次无快照时初始化一次。
- OS列表或塔响应不可观察时返回 `PENDING`，保留旧缓存并在5分钟后重试。
- 部分新Alpha缺PnL返回 `PARTIAL`，成功项进入参考池，失败ID只记录。
- 无实际新增时不重写pickle，避免SC缓存token变化造成无意义重筛。

### SC 通过项目标 PnL 缓存

爬山筛选调用 `get_sc_check(..., cache_pnl_below=0.5)`。SC 严格小于阈值时，
目标 PnL 保存到 `sc_ppa/target_pnls/<alpha_id>.pickle`，后续检查直接读取本地；
SC 达到或超过阈值时删除对应文件。目标 PnL 不会加入 OS SC 参考池。

6 小时周期只检查远端 OS 列表；没有新增 OS Alpha 时不写参考池、不失效
进程内 SC 缓存，也不刷新 Pyramid。

### PPAC 计算

```python
def calc_ppac(client, alpha_id, ppac_alpha_rets, ppac_alpha_ids,
              alpha_result=None, alpha_pnls=None) -> float
```
- 流程与 `calc_self_corr` 完全相同，比较对象换为 PPA Alpha 子集。
- 若当前 Region 无 PPA Alpha，返回 `0.0`；若参考列存在但收益序列无有效重叠，返回 `float('nan')`，上层必须保持待处理。

---

## 使用流程

```python
from Core.sim.sc_engine import download_data, load_data, load_ppac_data, calc_self_corr, calc_ppac
from Core.api import login

client = login()

# 1. 首次初始化（或定期更新）
download_data(client, flag_increment=True)

# 2. 加载 SC 数据
sc_ids, sc_rets = load_data(tag='SelfCorr')

# 3. 计算 SC
sc_val = calc_self_corr(client, "alpha_id_xxx", sc_rets, sc_ids)
print(f"SC = {sc_val:.4f}")

# 4. 加载 PPAC 数据
ppac_ids, ppac_rets = load_ppac_data()

# 5. 计算 PPAC
ppac_val = calc_ppac(client, "alpha_id_xxx", ppac_rets, ppac_ids)
print(f"PPAC = {ppac_val:.4f}")
```

---

## 性能特点

| 指标 | 说明 |
|---|---|
| 首次下载耗时 | ~5~30 分钟（取决于 OS Alpha 数量，并行 10 线程） |
| 增量更新耗时 | < 1 分钟（仅下载新 Alpha） |
| 单次 SC 计算 | < 50ms（纯 pandas corrwith 向量化） |
| 单次 PPAC 计算 | < 50ms（同上） |
| 平台 API 消耗 | 参考缓存增量刷新及目标 Alpha PnL 下载；不调用 Power Pool correlation 接口 |
