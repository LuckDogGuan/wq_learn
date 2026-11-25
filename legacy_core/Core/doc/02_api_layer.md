# 02 — `Core/api/` HTTP 层详细设计

## 职责

`Core/api/` 是整个系统**唯一的 HTTP 通信出口**。所有网络请求必须通过本层发出。

## 文件清单

### `client.py` — BrainClient

```python
class BrainClient:
    session: requests.Session   # 持有已认证的 Session（含 Basic Auth Cookie）

    def request(method, url, **kwargs) -> Response | None
    def get(url, **kwargs)    -> Response | None
    def post(url, **kwargs)   -> Response | None
    def patch(url, **kwargs)  -> Response | None
    def delete(url, **kwargs) -> Response | None
    def options(url, **kwargs)-> Response | None
```

**`request()` 核心逻辑：**
1. URL 补全：相对路径（以 `/` 开头）自动拼接 `API_BASE_URL`。
2. **429 退避**：读取 `Retry-After` 响应头，等待对应秒数后重试（无上限）。
3. **5xx 指数退避**：最多重试 3 次，间隔 2^n 秒。
4. 网络异常时返回 `None`，**不抛出异常**，由调用方判断。

**常量：**
```python
API_BASE_URL  = "https://api.worldquantbrain.com"
PLATFORM_URL  = "https://platform.worldquantbrain.com"
```

---

### `auth.py` — 认证

```python
def load_config(config_path=None) -> dict
```
- 读取 `Password/config.yaml`，返回 `{username, password}` 字典。
- 自动从当前文件向上查找配置文件，支持任意嵌套深度的调用位置。

```python
def login(config_path=None) -> BrainClient
def login_hk(config_path=None) -> BrainClient
```
- 读取凭据 → 创建 `requests.Session` → 设置 Basic Auth → POST `/authentication`。
- 返回 `BrainClient(session=已认证的Session)`。
- `login_hk` 额外处理香港区域的 Persona Biometrics 流程。

---

### `platform.py` — 平台配置

```python
def get_day1_universe_map(client: BrainClient) -> dict[str, list[str]]
```
- 调用 `OPTIONS /simulations` 获取平台支持的 Region → Universe 映射。
- 返回格式：`{"USA": ["TOP3000", "TOP2000", ...], "CHN": [...], ...}`
- 失败（非 200）返回 `{}`。

```python
def get_all_valid_scopes(client: BrainClient) -> list[tuple[str, str]]
```
- 基于 `get_day1_universe_map` 展平为 `[(region, universe), ...]` 元组列表。

---

### `activity_api.py` — 用户活动与 Pyramid 分类

```python
def get_user_diversity(client: BrainClient) -> dict
```
- GET `/users/self/activities/diversity`，返回平台用户 diversity 原始字典。
- 失败、无效 JSON 或非对象响应返回 `{}`。

```python
def get_alpha_pyramid_pass_info(client: BrainClient, alpha_id: str) -> dict
```
- GET `/alphas/{alpha_id}`，读取 `is.checks[name="MATCHES_PYRAMID"]`。
- 从 `pyramids[].name` 提取一个或多个 Pyramid 范围作为 `categories`。
- 同时保留 `effective`、总 `multiplier` 和各 Pyramid multiplier。
- 响应不完整时返回 `status="PENDING"`，不能解释为无匹配。

```python
def evaluate_pyramid_coverage(diversity_payload: dict, pyramid_info: dict) -> dict
```
- 纯本地按 `Region + Delay + Category` 匹配 Alpha 关联塔与用户 diversity 快照。
- 返回 `ALL_PASS / HAS_GAP / PENDING`，同时列出全部范围和缺口范围。
- 忽略空 Category 汇总行，兼容 `pv / Price Volume`，不使用 `alphaCount` 自算比例。

详细返回结构和数据边界见 [`12_activity_api.md`](12_activity_api.md)。

---

### `data_api.py` — 数据集/字段

```python
def get_datasets(client, region="USA", universe="TOP3000", delay=1,
                 instrument_type="EQUITY") -> pd.DataFrame
```
- GET `/datasets?...` 拉取数据集列表，转换为 DataFrame。

```python
def get_datafields(client, dataset_id, instrument_type="EQUITY",
                   region="USA", delay=1, universe="TOP3000") -> pd.DataFrame
```
- GET `/datafields?dataset.id=...` 拉取字段列表。

```python
def get_vec_fields(fields: list) -> list[str]
```
- 纯本地：对每个字段生成 `vec_avg(field)` + `vec_sum(field)` 两个向量表达式。

```python
def process_datafields(df: pd.DataFrame) -> list[str]
```
- 纯本地：从 DataFrame 中提取 MATRIX/VECTOR 字段，应用 `winsorize(ts_backfill(...))` 预处理包装后返回表达式列表。

---

### `sim_api.py` — 模拟接口

```python
def set_alpha_properties(client, alpha_id, name, color, selection_desc, combo_desc, tags) -> Response
```
- PATCH `/alphas/{id}`，更新 Alpha 名称、颜色、标签等属性。
- **经过 BrainClient.request() 的重试保护**（之前是裸 `session.patch()`）。

```python
def locate_alpha(client, alpha_id) -> list
```
- GET `/alphas/{id}`，轮询直到无 `Retry-After`。
- 返回 `[alpha_id, exp, sharpe, turnover, fitness, margin, dateCreated, decay]`。

```python
def get_user_alphas(client, start_str, end_str, sharpe_th, fitness_th,
                    region, offset=0) -> list[dict]
```
- GET `/users/self/alphas?...` 批量拉取满足门槛的未提交 Alpha。

```python
def get_user_alphas_page(client, start_date, end_date, sharpe_min, fitness_min,
                         statuses=("UNSUBMITTED", "IS_FAIL"), offset=0, limit=100) -> dict | None
```
- 按自然日分页读取完整 REGULAR Alpha 字典，供调用方实现日期断点。
- 成功但无结果返回空 `results`；HTTP 或响应解析失败返回 `None`。
- 平台门槛用于缩小结果；严格大于判断仍由调用方本地完成。

```python
def post_simulation(client, simulation_data: dict) -> str | None
```
- POST `/simulations`（单条），成功返回 `Location` URL（progress endpoint）。

```python
def post_multi_simulation(client, sim_data_list: list) -> str | None
```
- POST `/simulations`（列表），成功返回 `Location` URL。

```python
def poll_simulation_progress(client, progress_url, timeout=600) -> dict
```
- 循环 GET progress URL，根据 `Retry-After` 等待。
- 当 `status` 为 `COMPLETE / WARNING / ERROR / FAILED` 时返回结果字典。
- 超时（默认 600 秒）返回 `{}`。

```python
def get_alpha_check(client, alpha_id, wait_for_result=True) -> dict
```
- GET `/alphas/{id}/check`。默认轮询直到无 `Retry-After`；传入
  `wait_for_result=False` 时只查询一次，供 PC 专用接口的末级兼容降级使用。

```python
def get_prod_correlation(client, alpha_id) -> float | None
```
- GET `/alphas/{id}/correlations/prod`，只读取生产相关性最大值。
- 未就绪、非 200、空响应或结构异常时返回 `None`，不会误判为 0。

```python
def get_ppc_value(client, alpha_id) -> tuple[float | None, float | None]
```
- GET `/alphas/{id}/correlations/power-pool`。
- 维护模块级限流计数器（`Ratelimit-Remaining`/`Ratelimit-Reset`）。
- 返回 `(max_corr, min_corr)`，失败返回 `(None, None)`。
- **注意**：Power Pool Correlation 与生产相关性 PC 含义不同，不能互相降级替代。

```python
def get_alpha_details(client, alpha_id: str, timeout=30) -> dict | None
```
- GET `/alphas/{id}`，带 429 Retry-After 限频保护，获取 Alpha 完整详情字典。

```python
def is_alpha_submitted(alpha_data: dict) -> bool
```
- 纯本地规则判定：基于 `dateSubmitted is not None or stage == 'OS' or os is not None` 返回布尔值。

```python
def check_alpha_submission_status(client, alpha_id: str) -> dict
```
- 结合 `get_alpha_details` 与 `is_alpha_submitted`，返回标准化的状态诊断摘要字典。

