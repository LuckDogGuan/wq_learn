"""
sim/validator.py
Alpha 提交前的深度验证工具集。

计算职责分离（不可混用）：
  - get_sc_check()   : 自相关性 SC —— 参考池在本地计算；目标 Alpha 详情/PnL 只读平台。
                       缓存为空返回 "no_cache"，目标 PnL 不可用返回 "pnl_unavailable"。
  - get_pc_check()   : 生产相关性 PC —— 优先专用 /correlations/prod 接口，
                       未取得数值时仅用 /check 降级一次。
                       不走本地 PPAC，两者严格独立。
  - get_ppac_check() : Power Pool Correlation —— 只本地计算（sc_engine）。
                       缓存为空时返回 "no_cache"，不 fallback 平台。
  - get_alpha_extended_details(): Alpha 扩展指标（IS/Train/Test 全阶段）。
  - is_ppa()         : 判断 Alpha 是否属于 PPA。
"""
from Core.api.sim_api import get_alpha_check, get_prod_correlation
from Core.sim.sc_engine import (
    load_data, load_ppac_data, calc_self_corr, calc_ppac,
    DEFAULT_CACHE_DIR, PnlUnavailableError,
)

import time
import threading
import pandas as pd


# ─────────────────────────────────────────────────────────────────
# 模块级缓存（线程安全，进程内单例）
# ─────────────────────────────────────────────────────────────────
_cache_lock = threading.Lock()

# SC 缓存（非 PPA OS Alpha）
_sc_ids    = None
_sc_rets   = None
_sc_loaded = False

# PPAC 缓存（PPA OS Alpha）
_ppac_ids    = None
_ppac_rets   = None
_ppac_loaded = False


def _ensure_sc_cache(client=None):
    """加载 SC 磁盘缓存；不触发网络请求。"""
    global _sc_ids, _sc_rets, _sc_loaded
    if _sc_loaded:
        return
    with _cache_lock:
        if _sc_loaded:
            return
        _sc_ids, _sc_rets = load_data(DEFAULT_CACHE_DIR, tag='SelfCorr')
        _sc_loaded = True


def _ensure_ppac_cache(client=None):
    """加载 PPAC 缓存（仅磁盘加载，不触发网络请求）。"""
    global _ppac_ids, _ppac_rets, _ppac_loaded
    if _ppac_loaded:
        return
    with _cache_lock:
        if _ppac_loaded:
            return
        _ppac_ids, _ppac_rets = load_ppac_data(DEFAULT_CACHE_DIR)
        _ppac_loaded = True


def invalidate_cache():
    """手动使 SC + PPAC 缓存失效（download_data 更新后调用）。"""
    global _sc_loaded, _ppac_loaded
    with _cache_lock:
        _sc_loaded   = False
        _ppac_loaded = False


# ─────────────────────────────────────────────────────────────────
# SC —— 只本地计算
# ─────────────────────────────────────────────────────────────────

def get_sc_check(client, alpha_id: str,
                 cache_pnl_below: float | None = None,
                 alpha_result: dict | None = None) -> float | str:
    """
    计算指定 Alpha 的自相关性 (Self-Correlation)。

    数据来源：参考 OS Alpha 使用本地 sc_engine 缓存；目标 Alpha 详情/PnL 从平台只读获取。
    若本地缓存为空、目标 PnL 不可用或计算失败，分别返回
    "no_cache" / "pnl_unavailable" / "error"。

    参数:
        client    : BrainClient 实例，仅用于读取目标 Alpha；不会刷新参考缓存。
        alpha_id  : Alpha ID 字符串。
        alpha_result: 已有 Alpha 详情；传入后不再重复请求详情接口。

    返回:
        float     — SC 值（0.0 ~ 1.0）
        "no_cache"— 本地缓存尚未下载
        "pnl_unavailable"— 平台未返回目标 Alpha 的 PnL，属于待定而不是失败
        "error"   — 其它计算过程异常
    """
    _ensure_sc_cache(client)

    if _sc_rets is None or (isinstance(_sc_rets, pd.DataFrame) and _sc_rets.empty):
        print(f"[validator] SC 缓存不可用，请先调用 download_data()。alpha_id={alpha_id}")
        return "no_cache"

    try:
        sc_val = calc_self_corr(
            client, alpha_id, _sc_rets, _sc_ids,
            alpha_result=alpha_result,
            cache_pnl_below=cache_pnl_below,
        )
        return float(sc_val)
    except PnlUnavailableError as e:
        print(f"[validator] 目标PnL暂不可观察: {e}")
        return "pnl_unavailable"
    except Exception as e:
        print(f"[validator] SC 计算异常: {e}")
        return "error"


# ─────────────────────────────────────────────────────────────────
# PPAC —— 只本地计算
# ─────────────────────────────────────────────────────────────────

def get_ppac_check(client, alpha_id: str) -> float | str:
    """
    计算指定 Alpha 与所有 PPA Alpha 的最大相关性（PPAC）。

    数据来源：只使用本地 sc_engine 缓存，不发任何平台请求。
    若本地缓存为空返回 "no_cache"；当前 Region 无 PPA Alpha 时返回 0.0；
    参考收益无有效重叠时返回 float('nan')。

    参数:
        client    : BrainClient 实例（仅在缓存为空时用于触发首次下载）。
        alpha_id  : Alpha ID 字符串。

    返回:
        float     — PPAC 值（0.0 ~ 1.0）
        0.0       — 当前 Region 无 PPA Alpha 数据
        float nan — PPA 参考数据存在但无有效收益重叠
        "no_cache"— 本地缓存尚未下载
        "error"   — 计算过程异常
    """
    _ensure_ppac_cache(client)

    if _ppac_rets is None or (isinstance(_ppac_rets, pd.DataFrame) and _ppac_rets.empty):
        print(f"[validator] PPAC 缓存不可用，请先调用 download_data()。alpha_id={alpha_id}")
        return "no_cache"

    try:
        ppac_val = calc_ppac(client, alpha_id, _ppac_rets, _ppac_ids)
        return float(ppac_val)   # 可能为 nan（参考数据无有效重叠）
    except Exception as e:
        print(f"[validator] PPAC 计算异常: {e}")
        return "error"


# ─────────────────────────────────────────────────────────────────
# PC —— 只远端平台计算
# ─────────────────────────────────────────────────────────────────

def get_pc_check(client, alpha_id: str, max_attempts: int = 1,
                 wait_seconds: float = 30, should_stop=None) -> float | str:
    """
    优先从专用接口获取生产相关性，全部尝试未取得数值时仅调用一次 /check。

    主接口为 GET /alphas/{id}/correlations/prod；/check 仅作为兼容降级，
    避免日常 PC 查询触发完整提交检查。不涉及任何本地计算。

    参数:
        client    : BrainClient 实例。
        alpha_id  : Alpha ID 字符串。
        max_attempts: 专用接口最大查询次数，默认只查一次。
        wait_seconds: 多次查询之间的等待秒数。
        should_stop: 可选停止回调，返回 True 时立即中止。

    返回:
        float     — PROD_CORRELATION 值
        float nan — 平台尚未返回该字段（检查未完成）
        "sleep"   — Session 已过期（is=0）
        "interrupted" — 外部请求停止
        "error"   — 接口异常或解析失败
    """
    max_attempts = max(1, int(max_attempts))
    for attempt in range(max_attempts):
        if should_stop and should_stop():
            return "interrupted"
        value = get_prod_correlation(client, alpha_id)
        if value is not None:
            return value
        if attempt + 1 < max_attempts:
            end = time.time() + max(0.0, float(wait_seconds))
            while time.time() < end:
                if should_stop and should_stop():
                    return "interrupted"
                time.sleep(min(0.25, max(0.0, end - time.time())))

    if should_stop and should_stop():
        return "interrupted"
    check = get_alpha_check(client, alpha_id, wait_for_result=False)
    if not check:
        return "error"
    if check.get("is", 0) == 0:
        return "sleep"
    try:
        checks_df = pd.DataFrame(check["is"]["checks"])
        pc_rows   = checks_df[checks_df.name == "PROD_CORRELATION"]["value"].values
        if len(pc_rows):
            return float(pc_rows[0]) if not pd.isna(pc_rows[0]) else float("nan")
        return float("nan")   # 平台尚未返回 PROD_CORRELATION
    except Exception as e:
        print(f"[validator] PC 解析异常: {e}")
        return "error"


# ─────────────────────────────────────────────────────────────────
# 扩展指标详情
# ─────────────────────────────────────────────────────────────────

def get_alpha_extended_details(client, alpha_id: str) -> dict:
    """
    查询 Alpha 的扩展指标（IS/Train/Test 各阶段 Sharpe、Fitness、Drawdown 等）。

    参数:
        client   : BrainClient 实例。
        alpha_id : Alpha ID 字符串。

    返回:
        dict: 包含各阶段指标的嵌套字典；请求失败返回 {}。
    """
    while True:
        resp = client.get(f"/alphas/{alpha_id}")
        if not resp or not resp.ok:
            print(f"[validator] 获取 {alpha_id} 扩展详情失败")
            return {}
        if "retry-after" in resp.headers:
            time.sleep(float(resp.headers["Retry-After"]))
        else:
            break

    metrics = resp.json()
    details = {}

    for phase in ["is", "train", "test"]:
        if phase in metrics and metrics[phase]:
            pd_data = metrics[phase]
            details[phase] = {k: pd_data.get(k) for k in
                              ("sharpe", "fitness", "turnover", "returns", "drawdown", "margin")}
            inv = pd_data.get("investabilityConstrained")
            if inv:
                details[f"{phase}_investability"] = {
                    k: inv.get(k) for k in
                    ("sharpe", "fitness", "turnover", "returns", "drawdown", "margin")
                }

    if "is" in metrics and "checks" in metrics["is"]:
        counts      = {"PASS": 0, "WARNING": 0, "PENDING": 0, "ERROR": 0, "FAIL": 0}
        fail_names  = []
        for chk in metrics["is"]["checks"]:
            res = chk.get("result", "UNKNOWN")
            counts[res] = counts.get(res, 0) + 1
            if res == "FAIL":
                fail_names.append(chk.get("name", "UNKNOWN"))
        details["is_testing_status"] = counts
        if fail_names:
            details["fail_reasons"] = fail_names

    return details


# ─────────────────────────────────────────────────────────────────
# 辅助判断
# ─────────────────────────────────────────────────────────────────

def is_ppa(alpha_info: dict) -> bool:
    """
    判断该 Alpha 是否属于 PPA (Power Pool Alpha)。

    参数:
        alpha_info (dict): 从 API 获取的 Alpha 数据字典。

    返回:
        bool
    """
    checks = alpha_info.get("is", {}).get("checks", [])
    return any(c.get("name") == "POWER_POOL_CORRELATION" for c in checks)
