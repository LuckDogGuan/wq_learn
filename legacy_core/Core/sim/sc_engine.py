"""
sim/sc_engine.py
本地自相关性 (Self-Correlation) 快速计算引擎。

直接内嵌计算逻辑，不依赖 cnhkmcp 包的动态 import。
核心来源：brain-calculate-alpha-selfcorrQuick/scripts/skill.py (已适配 BrainClient)

主要 API：
  - download_data(client, cache_dir)  : 增量下载 OS Alpha PnL 数据到本地缓存
  - load_data(cache_dir, tag)         : 从缓存加载 OS Alpha 收益序列
  - calc_self_corr(client, alpha_id, os_alpha_rets, os_alpha_ids) : 计算单个 Alpha 的 SC 值
"""

import pickle
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Tuple, Dict, List

import numpy as np
import pandas as pd
from Core.data.runtime_paths import SC_PPA_CACHE_DIR

# SC/PPA 运行时缓存统一放在 Core/runtime_data/sc_ppa/。
DEFAULT_CACHE_DIR = SC_PPA_CACHE_DIR
TARGET_PNL_CACHE_DIRNAME = 'target_pnls'


class PnlUnavailableError(RuntimeError):
    """平台暂时或永久没有返回目标 Alpha 的可用 PnL。"""


# ─────────────────────────────────────────────────────────────────
# 持久化工具
# ─────────────────────────────────────────────────────────────────

def _save_obj(obj: object, path: Path) -> None:
    """将对象序列化为 pickle 文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path) + '.pickle', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def _load_obj(path: Path) -> object:
    """从 pickle 文件反序列化对象。"""
    with open(str(path) + '.pickle', 'rb') as f:
        return pickle.load(f)


def _target_pnl_cache_path(alpha_id: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    """返回单个目标 Alpha 的 PnL 缓存路径，并拒绝路径型 ID。"""
    alpha_id = str(alpha_id or '').strip()
    if not alpha_id or any(char not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for char in alpha_id):
        raise ValueError('alpha_id 只能包含字母、数字、下划线和连字符')
    return Path(cache_dir) / TARGET_PNL_CACHE_DIRNAME / alpha_id


def load_target_pnl_cache(alpha_id: str, cache_dir: Path = DEFAULT_CACHE_DIR):
    """读取已通过 SC 的目标 Alpha PnL；不存在或损坏时返回空 DataFrame。"""
    try:
        value = _load_obj(_target_pnl_cache_path(alpha_id, cache_dir))
        if isinstance(value, pd.DataFrame) and alpha_id in value.columns:
            return value
    except (FileNotFoundError, EOFError, pickle.UnpicklingError, ValueError, OSError):
        pass
    return pd.DataFrame()


def save_target_pnl_cache(alpha_id: str, alpha_pnls: pd.DataFrame,
                          cache_dir: Path = DEFAULT_CACHE_DIR) -> None:
    """保存 SC 通过项的目标 PnL，不把它加入 OS 参考池。"""
    if not isinstance(alpha_pnls, pd.DataFrame) or alpha_id not in alpha_pnls.columns:
        raise ValueError(f'目标PnL缺少列: {alpha_id}')
    _save_obj(alpha_pnls[[alpha_id]], _target_pnl_cache_path(alpha_id, cache_dir))


def delete_target_pnl_cache(alpha_id: str,
                            cache_dir: Path = DEFAULT_CACHE_DIR) -> bool:
    """删除 SC 未通过项的本地目标 PnL；不存在时视为已清理。"""
    path = Path(str(_target_pnl_cache_path(alpha_id, cache_dir)) + '.pickle')
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False


# ─────────────────────────────────────────────────────────────────
# OS Alpha PnL 拉取
# ─────────────────────────────────────────────────────────────────

def _get_alpha_pnl(client, alpha_id: str) -> pd.DataFrame:
    """
    拉取单个 Alpha 的 PnL 序列（日频）。

    参数:
        client: BrainClient 实例。
        alpha_id (str): Alpha ID。

    返回:
        pd.DataFrame: 列为 [Date, <alpha_id>] 的 PnL 数据帧。
    """
    url = f"/alphas/{alpha_id}/recordsets/pnl"
    for attempt in range(3):
        resp = client.get(url)
        if not resp or resp.status_code != 200:
            raise PnlUnavailableError(
                f"Failed to fetch PnL for {alpha_id}: "
                f"{resp.status_code if resp else 'No response'}"
            )
        if not resp.text.strip():
            # gzip 解压后偶发空 body，等待后重试
            time.sleep(1)
            continue
        pnl = resp.json()
        cols = [item['name'] for item in pnl['schema']['properties']]
        df = pd.DataFrame(pnl['records'], columns=cols)
        df = df.rename(columns={'date': 'Date', 'pnl': alpha_id})
        return df[['Date', alpha_id]]
    raise PnlUnavailableError(f"PnL body empty after 3 retries for {alpha_id}")


def get_alpha_pnls(
    client,
    alphas: List[dict],
    alpha_pnls: Optional[pd.DataFrame] = None,
    alpha_ids: Optional[Dict[str, list]] = None,
    max_workers: int = 10,
) -> Tuple[Dict[str, list], pd.DataFrame]:
    """
    批量下载 Alpha PnL，增量合并到已有数据帧中（跳过已有的列）。

    参数:
        client: BrainClient 实例。
        alphas (list[dict]): Alpha 信息字典列表（需包含 'id' 和 'settings.region'）。
        alpha_pnls (pd.DataFrame, optional): 已有的 PnL 数据帧（按 Date 索引）。
        alpha_ids (dict, optional): 已有的 {region: [alpha_id, ...]} 映射。
        max_workers (int): 并行下载线程数（默认 10）。

    返回:
        tuple: (alpha_ids_dict, alpha_pnls_df)
    """
    if alpha_ids is None:
        alpha_ids = defaultdict(list)
    if alpha_pnls is None:
        alpha_pnls = pd.DataFrame()

    new_alphas = [a for a in alphas if a['id'] not in alpha_pnls.columns]
    if not new_alphas:
        return alpha_ids, alpha_pnls

    # requests.Session 非线程安全，改为顺序下载
    results = []
    for a in new_alphas:
        try:
            pnl = _get_alpha_pnl(client, a['id']).set_index('Date')
            results.append(pnl)
            region = a.get('settings', {}).get('region', 'UNKNOWN')
            region_ids = alpha_ids.setdefault(region, [])
            if a['id'] not in region_ids:
                region_ids.append(a['id'])
        except Exception as e:
            print(f"[sc_engine] PnL 下载失败 {a['id']}: {e}")

    if results:
        alpha_pnls = pd.concat([alpha_pnls] + results, axis=1)
        alpha_pnls.sort_index(inplace=True)

    return alpha_ids, alpha_pnls


def _get_os_alphas_result(client, limit: int = 100,
                          get_first: bool = False,
                          stop_at_ids=None, must_find_ids=None) -> Tuple[List[dict], bool]:
    """返回 ``(Alpha列表, 是否完整可观察)``，供刷新调度区分空结果与请求失败。"""
    from Core.api.pagination import iter_alpha_pages, AlphaPageUnavailable
    fetched = []
    required_ids = set(must_find_ids or ())
    cached_ids = set(stop_at_ids or ())
    found_required_ids = set()
    boundary_seen = False

    def load_page(offset):
        response = client.get(
            f"/users/self/alphas?stage=OS&limit={limit}&offset={offset}&order=-dateSubmitted"
        )
        if response is None or response.status_code != 200:
            return None
        try:
            return response.json()
        except (ValueError, TypeError):
            return None

    try:
        for page in iter_alpha_pages(load_page, page_size=limit):
            for item in page["results"]:
                alpha_id = item["id"]
                if alpha_id in required_ids:
                    found_required_ids.add(alpha_id)
                if alpha_id in cached_ids:
                    boundary_seen = True
                else:
                    fetched.append(item)
            # Finish the current page, including uncached items after the boundary.
            if get_first or (boundary_seen and required_ids.issubset(found_required_ids)):
                break
    except AlphaPageUnavailable as exc:
        print(f"[sc_engine] PARTIAL/PENDING: {exc}")
        return fetched, False
    return fetched, True


def get_os_alphas(client, limit: int = 100, get_first: bool = False) -> List[dict]:
    """
    拉取平台上当前账户的 OS (Out-of-Sample) 阶段 Alpha 列表。

    参数:
        client: BrainClient 实例。
        limit (int): 每次请求的条数（默认 100）。
        get_first (bool): 若为 True 只拉取第一页（用于增量刷新）。

    返回:
        list[dict]: Alpha 信息字典列表。
    """
    alphas, _ = _get_os_alphas_result(client, limit=limit, get_first=get_first)
    return alphas


# ─────────────────────────────────────────────────────────────────
# 数据持久化（下载 + 本地缓存）
# ─────────────────────────────────────────────────────────────────

def download_data_with_report(client, cache_dir: Path = DEFAULT_CACHE_DIR,
                              flag_increment: bool = True,
                              retry_alpha_ids=None) -> dict:
    """
    增量下载 OS Alpha PnL 数据并持久化到本地缓存（pickle）。

    参数:
        client: BrainClient 实例。
        cache_dir (Path): 本地缓存目录（默认 Core/runtime_data/sc_ppa/）。
        flag_increment (bool): 若为 True 则增量更新（保留旧数据），否则全量重下。

    返回带可观察状态和新增/失败 ID 的字典；旧 ``download_data`` 仍保持二元返回。
    """
    cache_dir = Path(cache_dir)
    os_alpha_ids = None
    os_alpha_pnls = None
    exist_alpha = []
    ppac_alpha_ids = []

    if flag_increment:
        try:
            os_alpha_ids  = _load_obj(cache_dir / 'os_alpha_ids')
            os_alpha_pnls = _load_obj(cache_dir / 'os_alpha_pnls')
            ppac_alpha_ids = _load_obj(cache_dir / 'ppac_alpha_ids')
            exist_alpha = [alpha for ids in os_alpha_ids.values() for alpha in ids]
            print(f"[sc_engine] 已加载本地缓存，共 {len(exist_alpha)} 个 Alpha")
        except (FileNotFoundError, EOFError, pickle.UnpicklingError):
            print("[sc_engine] 首次运行，全量下载...")
            os_alpha_ids, os_alpha_pnls, ppac_alpha_ids = None, None, []
        except Exception as e:
            print(f"[sc_engine] 缓存加载异常，重新下载: {str(e)[:80]}")
            os_alpha_ids, os_alpha_pnls, ppac_alpha_ids = None, None, []

    cached_before = set(
        os_alpha_pnls.columns if isinstance(os_alpha_pnls, pd.DataFrame) else []
    )

    # 拉取当前 OS Alpha 列表。请求失败时不覆盖任何旧缓存。
    if os_alpha_ids is None:
        print("[sc_engine] 拉取完整 OS Alpha 列表...")
        alphas, list_observed = _get_os_alphas_result(
            client, limit=100, get_first=False
        )
    else:
        # 按提交时间倒序逐页读取，遇到任一已缓存 Alpha 即停止。这样在两次刷新
        # 之间新增超过一页时也不会漏项，同时避免每次都扫描完整 OS 历史。
        alphas, list_observed = _get_os_alphas_result(
            client, limit=100, get_first=False, stop_at_ids=cached_before,
            must_find_ids=retry_alpha_ids,
        )

    if not list_observed:
        return {
            'status': 'PENDING', 'reason': 'OS Alpha列表不可观察',
            'alpha_ids': os_alpha_ids or defaultdict(list),
            'alpha_pnls': os_alpha_pnls if isinstance(os_alpha_pnls, pd.DataFrame) else pd.DataFrame(),
            'observed_new_os_alpha_ids': [], 'cached_new_os_alpha_ids': [],
            'failed_pnl_alpha_ids': [], 'cached_os_count': len(cached_before),
            'cache_changed': False,
        }

    # 以实际 PnL 列为准；旧 ID 列表可能残留没有成功下载的 Alpha。
    alphas = [a for a in alphas if a.get('id') not in cached_before]
    observed_new_ids = [a.get('id') for a in alphas if a.get('id')]

    os_alpha_ids, os_alpha_pnls = get_alpha_pnls(
        client, alphas,
        alpha_pnls=os_alpha_pnls,
        alpha_ids=os_alpha_ids,
    )

    cached_columns = set(os_alpha_pnls.columns) if isinstance(os_alpha_pnls, pd.DataFrame) else set()
    successful_new_ids = {a['id'] for a in alphas if a.get('id') in cached_columns}
    retry_alpha_ids = list(dict.fromkeys(retry_alpha_ids or []))
    failed_pnl_ids = [
        alpha_id for alpha_id in dict.fromkeys(observed_new_ids + retry_alpha_ids)
        if alpha_id not in cached_columns
    ]
    ppac_alpha_ids.extend(
        a['id'] for a in alphas
        if a['id'] in successful_new_ids
        and any(cls.get('name') == 'Power Pool Alpha' for cls in a.get('classifications', []))
    )
    ppac_alpha_ids = list(dict.fromkeys(a for a in ppac_alpha_ids if a in cached_columns))
    os_alpha_ids = {
        region: list(dict.fromkeys(a for a in ids if a in cached_columns))
        for region, ids in os_alpha_ids.items()
    }

    cache_changed = bool(successful_new_ids)
    if cache_changed:
        try:
            _save_obj(os_alpha_ids,   cache_dir / 'os_alpha_ids')
            _save_obj(os_alpha_pnls,  cache_dir / 'os_alpha_pnls')
            _save_obj(ppac_alpha_ids, cache_dir / 'ppac_alpha_ids')
            print(f"[sc_engine] 缓存已更新，新增 {len(successful_new_ids)} 个 Alpha")
        except Exception as e:
            print(f"[sc_engine] 写入缓存失败: {str(e)[:80]}")
            return {
                'status': 'PENDING', 'reason': f'写入SC缓存失败: {str(e)[:80]}',
                'alpha_ids': os_alpha_ids, 'alpha_pnls': os_alpha_pnls,
                'observed_new_os_alpha_ids': observed_new_ids,
                'cached_new_os_alpha_ids': sorted(successful_new_ids),
                'failed_pnl_alpha_ids': failed_pnl_ids,
                'cached_os_count': len(cached_before), 'cache_changed': False,
            }

    status = 'PARTIAL' if failed_pnl_ids else ('REFRESHED' if cache_changed else 'NO_CHANGE')
    return {
        'status': status, 'reason': '',
        'alpha_ids': os_alpha_ids, 'alpha_pnls': os_alpha_pnls,
        'observed_new_os_alpha_ids': observed_new_ids,
        'cached_new_os_alpha_ids': sorted(successful_new_ids),
        'failed_pnl_alpha_ids': failed_pnl_ids,
        'cached_os_count': len(cached_columns), 'cache_changed': cache_changed,
    }


def download_data(client, cache_dir: Path = DEFAULT_CACHE_DIR,
                  flag_increment: bool = True):
    """兼容旧接口，返回 ``(os_alpha_ids, os_alpha_pnls)``。"""
    report = download_data_with_report(
        client, cache_dir=cache_dir, flag_increment=flag_increment
    )
    return report['alpha_ids'], report['alpha_pnls']


def load_data(
    cache_dir: Path = DEFAULT_CACHE_DIR,
    tag: str = 'SelfCorr',
) -> Tuple[Dict[str, list], pd.DataFrame]:
    """
    从本地缓存加载 OS Alpha 收益序列（日频），根据 tag 过滤 PPA/非 PPA。

    参数:
        cache_dir (Path): 缓存目录（默认 Core/runtime_data/sc_ppa/）。
        tag (str): 过滤模式
            - 'SelfCorr' : 排除 PPA Alpha（仅用于自相关计算）
            - 'PPAC'     : 仅保留 PPA Alpha（用于 PPAC 计算）
            - 其他       : 不过滤

    返回:
        tuple: (os_alpha_ids_dict, os_alpha_rets_df)
               os_alpha_rets_df 是日收益率（相邻差分后的 PnL），最近 4 年窗口。
               若加载失败返回 ({}, pd.DataFrame())。
    """
    cache_dir = Path(cache_dir)
    try:
        os_alpha_ids   = _load_obj(cache_dir / 'os_alpha_ids')
        os_alpha_pnls  = _load_obj(cache_dir / 'os_alpha_pnls')
        ppac_alpha_ids = _load_obj(cache_dir / 'ppac_alpha_ids')

        if not os_alpha_ids or (hasattr(os_alpha_pnls, 'empty') and os_alpha_pnls.empty):
            raise ValueError("缓存文件为空或无效")
    except (FileNotFoundError, EOFError, pickle.UnpicklingError, ValueError) as e:
        print(f"[sc_engine] 无法加载本地缓存: {str(e)[:80]}")
        return {}, pd.DataFrame()
    except Exception as e:
        print(f"[sc_engine] 加载异常: {str(e)[:80]}")
        return {}, pd.DataFrame()

    # 缓存可能因历史下载中断而出现 ID/列不一致；只使用实际存在的列。
    available_columns = set(os_alpha_pnls.columns)
    ppac_alpha_ids = set(ppac_alpha_ids) & available_columns
    os_alpha_ids = {
        region: list(dict.fromkeys(a for a in ids if a in available_columns))
        for region, ids in os_alpha_ids.items()
    }

    # 按 tag 过滤
    if tag == 'PPAC':
        for r in os_alpha_ids:
            os_alpha_ids[r] = [a for a in os_alpha_ids[r] if a in ppac_alpha_ids]
    elif tag == 'SelfCorr':
        for r in os_alpha_ids:
            os_alpha_ids[r] = [a for a in os_alpha_ids[r] if a not in ppac_alpha_ids]

    exist_alpha = [a for ids in os_alpha_ids.values() for a in ids]
    if not exist_alpha:
        print("[sc_engine] 过滤后无可用 Alpha，请先调用 download_data() 更新缓存")
        return os_alpha_ids, pd.DataFrame()

    # 计算日收益率，取最近 4 年
    os_alpha_pnls = os_alpha_pnls[exist_alpha]
    os_alpha_rets = os_alpha_pnls - os_alpha_pnls.ffill().shift(1)
    cutoff = pd.to_datetime(os_alpha_rets.index).max() - pd.DateOffset(years=4)
    os_alpha_rets = os_alpha_rets[pd.to_datetime(os_alpha_rets.index) > cutoff]

    return os_alpha_ids, os_alpha_rets


# ─────────────────────────────────────────────────────────────────
# 核心计算：自相关性 (Self-Correlation)
# ─────────────────────────────────────────────────────────────────

def calc_self_corr(
    client,
    alpha_id: str,
    os_alpha_rets: pd.DataFrame,
    os_alpha_ids: Dict[str, list],
    alpha_result: Optional[dict] = None,
    alpha_pnls: Optional[pd.DataFrame] = None,
    cache_pnl_below: Optional[float] = None,
    cache_dir: Path = DEFAULT_CACHE_DIR,
) -> float:
    """
    计算单个 Alpha 与所有 OS Alpha 之间的最大相关性（自相关性 SC）。

    算法：
        1. 若未提供 alpha_result，先从平台拉取 Alpha 详情（含 region）。
        2. 若未提供 alpha_pnls，拉取该 Alpha 的 PnL 序列。
        3. 将 PnL 差分为日收益率，取最近 4 年。
        4. 与同 region 所有 OS Alpha 收益率做 corrwith，取 max。
        5. NaN 一律视为 0（无相关性）。

    参数:
        client: BrainClient 实例。
        alpha_id (str): 目标 Alpha ID。
        os_alpha_rets (pd.DataFrame): 已加载的 OS Alpha 日收益率矩阵（load_data 返回值）。
        os_alpha_ids (dict): {region: [alpha_id, ...]} 映射（load_data 返回值）。
        alpha_result (dict, optional): 已有的 Alpha 详情字典（可传入以避免重复请求）。
        alpha_pnls (pd.DataFrame, optional): 已有的该 Alpha PnL DataFrame。

    返回:
        float: SC 值（0 ~ 1），越小越好。NaN 情形返回 0.0。
    """
    # 1. 获取 Alpha 详情
    if alpha_result is None:
        resp = client.get(f"/alphas/{alpha_id}")
        if not resp or not resp.ok:
            raise RuntimeError(f"Failed to fetch alpha details for {alpha_id}")
        alpha_result = resp.json()

    if cache_pnl_below is not None and (
        isinstance(cache_pnl_below, bool)
        or not isinstance(cache_pnl_below, (int, float))
    ):
        raise ValueError('cache_pnl_below 必须是数值或 None')

    # 2. 获取目标 Alpha 的 PnL；开启通过项缓存时优先读取本地。
    pnl_from_cache = False
    if alpha_pnls is None or (isinstance(alpha_pnls, pd.DataFrame) and alpha_pnls.empty):
        if cache_pnl_below is not None:
            alpha_pnls = load_target_pnl_cache(alpha_id, cache_dir)
            pnl_from_cache = not alpha_pnls.empty
            if pnl_from_cache:
                print(f'[sc_engine] 使用本地目标PnL缓存 {alpha_id}')
        if alpha_pnls is None or alpha_pnls.empty:
            # 单目标计算需要保留 PnL 获取失败的真实原因，不能由批量接口吞掉后变成 KeyError。
            alpha_pnls = _get_alpha_pnl(client, alpha_id).set_index('Date')

    if alpha_id not in alpha_pnls.columns:
        raise KeyError(f"Alpha {alpha_id} not found in alpha_pnls")

    # 3. 转为日收益率，最近 4 年
    pnl_series = alpha_pnls[alpha_id]
    alpha_rets  = pnl_series - pnl_series.ffill().shift(1)
    cutoff = pd.to_datetime(alpha_rets.index).max() - pd.DateOffset(years=4)
    alpha_rets  = alpha_rets[pd.to_datetime(alpha_rets.index) > cutoff]

    # 4. 与同 region OS Alpha 计算 corrwith
    region     = alpha_result.get('settings', {}).get('region', '')
    peer_ids   = os_alpha_ids.get(region, [])
    if not peer_ids:
        result = 0.0
    else:
        peer_rets = os_alpha_rets[peer_ids]
        self_corr = peer_rets.corrwith(alpha_rets).max()
        result = 0.0 if np.isnan(self_corr) else float(self_corr)

    # 5. 只保留严格通过阈值的目标 PnL；达到阈值立即删除。
    if cache_pnl_below is not None:
        try:
            if result < float(cache_pnl_below):
                if not pnl_from_cache:
                    save_target_pnl_cache(alpha_id, alpha_pnls, cache_dir)
                    print(f'[sc_engine] 已保存SC通过项目标PnL {alpha_id}')
            else:
                removed = delete_target_pnl_cache(alpha_id, cache_dir)
                if removed:
                    print(f'[sc_engine] 已删除SC未通过项目标PnL {alpha_id}')
        except OSError as exc:
            print(f'[sc_engine] 目标PnL缓存更新失败 {alpha_id}: {exc}')
    return result


# ─────────────────────────────────────────────────────────────────
# PPAC (Power Pool Alpha Correlation) 本地计算
# ─────────────────────────────────────────────────────────────────

def load_ppac_data(cache_dir=None):
    """
    从本地缓存加载 PPA Alpha 收益序列，用于 PPAC 计算。
    等价于 load_data(tag='PPAC')，提供更直观的命名。

    返回:
        tuple: (ppac_alpha_ids_dict, ppac_alpha_rets_df)
    """
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR
    return load_data(cache_dir=cache_dir, tag='PPAC')


def refresh_ppac_data(client, cache_dir=None, flag_increment=True, return_report=False):
    """增量刷新缓存；可选同时返回刷新报告。"""
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR
    report = download_data_with_report(
        client, cache_dir=cache_dir, flag_increment=flag_increment
    )
    ppac_data = load_ppac_data(cache_dir=cache_dir)
    if return_report:
        return *ppac_data, report
    return ppac_data


def calc_ppac(client, alpha_id, ppac_alpha_rets, ppac_alpha_ids,
              alpha_result=None, alpha_pnls=None):
    """
    计算单个 Alpha 与所有 PPA (Power Pool Alpha) 的最大相关性（PPAC）。

    算法与 calc_self_corr() 完全相同，区别仅在比较对象是 PPA Alpha 子集：
      ppac_alpha_ids / ppac_alpha_rets 由 load_data(tag='PPAC') 产生。

    参数:
        client         : BrainClient 实例。
        alpha_id (str) : 目标 Alpha ID。
        ppac_alpha_rets: PPA Alpha 日收益率矩阵（load_ppac_data 返回值）。
        ppac_alpha_ids : {region: [ppa_alpha_id, ...]} 映射。
        alpha_result   : 已有 Alpha 详情字典（可选，避免重复请求）。
        alpha_pnls     : 已有该 Alpha PnL DataFrame（可选）。

    返回:
        float: PPAC 值（0.0~1.0）。
               当前 Region 没有任何 PPA 参考 Alpha 时返回 0.0；
               参考序列存在但无有效重叠时返回 float('nan')。
    """
    # 1. 获取 Alpha 详情
    if alpha_result is None:
        resp = client.get(f"/alphas/{alpha_id}")
        if not resp or not resp.ok:
            raise RuntimeError(f"Failed to fetch alpha details for {alpha_id}")
        alpha_result = resp.json()

    # Region 没有任何 PPA 参考 Alpha 时，PPAC 定义为 0，且无需下载目标 PnL。
    region = alpha_result.get('settings', {}).get('region', '')
    peer_ids = [
        peer_id for peer_id in ppac_alpha_ids.get(region, [])
        if peer_id != alpha_id and peer_id in ppac_alpha_rets.columns
    ]
    if not peer_ids:
        print(f"[sc_engine] Region '{region}' 无 PPA Alpha 数据，PPAC 返回 0.0")
        return 0.0

    # 2. 获取 PnL
    if alpha_pnls is None or (hasattr(alpha_pnls, 'empty') and alpha_pnls.empty):
        _, alpha_pnls = get_alpha_pnls(client, [alpha_result])

    if alpha_id not in alpha_pnls.columns:
        raise KeyError(f"Alpha {alpha_id} not found in alpha_pnls")

    # 3. 日收益率，最近 4 年
    pnl_series = alpha_pnls[alpha_id]
    alpha_rets = pnl_series - pnl_series.ffill().shift(1)
    cutoff = pd.to_datetime(alpha_rets.index).max() - pd.DateOffset(years=4)
    alpha_rets = alpha_rets[pd.to_datetime(alpha_rets.index) > cutoff]

    # 4. 与同 Region PPA Alpha 做 corrwith
    peer_rets = ppac_alpha_rets[peer_ids]
    correlations = peer_rets.corrwith(alpha_rets).dropna()
    if correlations.empty:
        print(f"[sc_engine] Alpha {alpha_id} 与 PPA 参考集无有效重叠，PPAC 无法计算")
        return float('nan')

    return float(correlations.max())
