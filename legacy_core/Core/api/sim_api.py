"""
api/sim_api.py
封装所有与模拟 (simulation) 相关的平台 HTTP 请求。
业务编排逻辑 (并发、轮询、断点续传) 仍保留在 sim/ 中，本模块仅负责网络通信。
"""
import time
import pandas as pd
from datetime import date, datetime, timedelta
from requests.exceptions import HTTPError
from urllib.parse import quote
from zoneinfo import ZoneInfo
from Core.api.client import BrainClient


BEIJING_TZ = ZoneInfo("Asia/Shanghai")


def _inclusive_dates_to_half_open(start_date: str, end_date: str):
    start = date.fromisoformat(str(start_date))
    end = date.fromisoformat(str(end_date))
    if start > end:
        raise ValueError("start_date 不能晚于 end_date")
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=BEIJING_TZ)
    end_dt = datetime.combine(
        end + timedelta(days=1), datetime.min.time(), tzinfo=BEIJING_TZ
    )
    return (
        quote(f"dateCreated>={start_dt.isoformat()}", safe=""),
        quote(f"dateCreated<{end_dt.isoformat()}", safe=""),
    )


# === Alpha 属性管理 ===

def set_alpha_properties(client: BrainClient, alpha_id: str, name: str = None,
                         color: str = None, selection_desc: str = None,
                         combo_desc: str = None, tags: list = None):
    """只更新明确传入的 Alpha 属性，避免覆盖未相关字段。"""
    params = {}
    if name is not None:
        params["name"] = name
    if color is not None:
        params["color"] = color
    if tags is not None:
        params["tags"] = tags
    if selection_desc is not None:
        params["selection"] = {"description": selection_desc}
    if combo_desc is not None:
        params["combo"] = {"description": combo_desc}
    if not params:
        return None
    return client.patch(f"/alphas/{alpha_id}", json=params)



def get_alpha_details(client: BrainClient, alpha_id: str, timeout: int = 30,
                      raise_on_rejection: bool = False) -> dict | None:
    """按 Alpha ID 查询一次完整详情；传输重试由 BrainClient 统一处理。"""
    alpha_id = str(alpha_id or "").strip()
    if not alpha_id:
        return None
    resp = client.get(f"/alphas/{alpha_id}", timeout=timeout)
    if (raise_on_rejection and resp is not None
            and 400 <= resp.status_code < 500 and resp.status_code not in (401, 408, 429)):
        raise HTTPError(f"HTTP {resp.status_code}", response=resp)
    if resp is None or resp.status_code != 200:
        return None
    try:
        data = resp.json()
        return data if isinstance(data, dict) else None
    except (ValueError, TypeError):
        return None


def is_alpha_submitted(alpha_data: dict) -> bool:
    """纯本地判定 Alpha 是否已提交。

    必须有 dateSubmitted，并由 stage、os 或 status 至少一项交叉确认。
    """
    if not isinstance(alpha_data, dict):
        return False
    if not alpha_data.get("dateSubmitted"):
        return False
    if str(alpha_data.get("stage", "")).upper() == "OS":
        return True
    if isinstance(alpha_data.get("os"), dict) and bool(alpha_data.get("os")):
        return True
    status = str(alpha_data.get("status", "")).upper()
    if status in ("ACTIVE", "RETIRED", "SUBMITTED"):
        return True
    return False


def check_alpha_submission_status(client: BrainClient, alpha_id: str) -> dict:
    """检查指定 Alpha ID 的提交状态，返回结构化诊断字典。"""
    try:
        data = get_alpha_details(client, alpha_id, raise_on_rejection=True)
    except HTTPError as exc:
        return {"alpha_id": alpha_id, "is_submitted": None,
                "status": "ERROR", "error": str(exc)}
    if not data or data.get("id") != alpha_id:
        return {
            "alpha_id": alpha_id,
            "is_submitted": None,
            "stage": "UNKNOWN",
            "status": "QUERY_FAILED",
            "date_submitted": None,
            "date_created": None,
            "code": None,
            "region": None,
            "universe": None,
            "sharpe": None,
            "fitness": None,
            "turnover": None,
            "margin": None,
            "exists": False,
        }

    is_sub = is_alpha_submitted(data)
    error = data.get("error") or data.get("errors")
    if not is_sub and (error or str(data.get("status", "")).upper() in ("ERROR", "FAILED")):
        return {"alpha_id": alpha_id, "is_submitted": None,
                "status": "ERROR", "error": str(error or data.get("detail") or data["status"])}
    if not is_sub and not (
        str(data.get("status", "")).upper() in ("UNSUBMITTED", "IS_FAIL")
        and str(data.get("stage", "")).upper() == "IS"
    ):
        is_sub = None
    is_metrics = data.get("is") if isinstance(data.get("is"), dict) else {}
    settings = data.get("settings") if isinstance(data.get("settings"), dict) else {}
    regular = data.get("regular") if isinstance(data.get("regular"), dict) else {}

    return {
        "alpha_id": alpha_id,
        "is_submitted": is_sub,
        "stage": data.get("stage", "UNKNOWN"),
        "status": data.get("status"),
        "date_submitted": data.get("dateSubmitted"),
        "date_created": data.get("dateCreated"),
        "code": regular.get("code") or data.get("expression"),
        "region": settings.get("region"),
        "universe": settings.get("universe"),
        "sharpe": is_metrics.get("sharpe"),
        "fitness": is_metrics.get("fitness"),
        "turnover": is_metrics.get("turnover"),
        "margin": is_metrics.get("margin"),
        "exists": True,
    }


def locate_alpha(client: BrainClient, alpha_id: str) -> list:
    """查询指定 Alpha ID 的详细指标信息。"""
    while True:
        alpha = client.get(f"/alphas/{alpha_id}")
        if not alpha:
            return []
        if "retry-after" in alpha.headers:
            time.sleep(float(alpha.headers["Retry-After"]))
        else:
            break
    metrics = alpha.json()
    return [
        alpha_id,
        metrics.get('regular', {}).get('code'),
        metrics.get('is', {}).get('sharpe'),
        metrics.get('is', {}).get('turnover'),
        metrics.get('is', {}).get('fitness'),
        metrics.get('is', {}).get('margin'),
        metrics.get('dateCreated'),
        metrics.get('settings', {}).get('decay'),
    ]


def _get_user_alphas_page(client: BrainClient, start_str: str, end_str: str,
                          sharpe_th: float, fitness_th: float,
                          region: str, offset: int = 0, tag: str = None,
                          negative: bool = False):
    """拉取一页用户 Alpha；失败返回 None，成功保留 results/count。"""
    if tag is not None and not isinstance(tag, str):
        raise TypeError("tag 必须是字符串或 None")
    tag = tag.strip() if tag else None
    comparison = "%3C=-" if negative else "%3E="
    order = "is.sharpe" if negative else "-is.sharpe"
    q_start, q_end = _inclusive_dates_to_half_open(start_str, end_str)
    url = (
        f"/users/self/alphas?limit=100&offset={offset}"
        f"&status=UNSUBMITTED%1FIS_FAIL"
        f"&{q_start}&{q_end}"
        f"&is.fitness{comparison}{fitness_th}&is.sharpe{comparison}{sharpe_th}"
        f"&settings.region={region}&order={order}&hidden=false&type!=SUPER"
    )
    if tag:
        url += f"&tag={quote(tag, safe='')}"

    resp = client.get(url, timeout=30)
    if resp is None or resp.status_code != 200:
        return None
    try:
        payload = resp.json()
    except (TypeError, ValueError):
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        return None
    return {"results": payload["results"], "count": payload.get("count")}


def get_user_alphas_page(client: BrainClient, start_date: str, end_date: str,
                         sharpe_min: float, fitness_min: float,
                         statuses=("UNSUBMITTED", "IS_FAIL"),
                         offset: int = 0, limit: int = 100,
                         descending: bool = False) -> dict | None:
    """按创建日期读取一页 REGULAR Alpha；失败返回 ``None``。

    本函数面向需要自行编排日期断点的只读研究流程。成功但没有结果时返回
    ``{"results": [], "count": 0}``，从而与网络或响应解析失败明确区分。
    平台查询使用 ``>=`` 缩小返回范围；调用方若要求严格阈值，仍应在本地
    使用 ``>`` 再判断一次。
    """
    if not isinstance(statuses, (list, tuple)) or not statuses:
        raise ValueError("statuses 必须是非空列表或元组")
    normalized_statuses = []
    for status in statuses:
        value = str(status or "").strip().upper()
        if not value or not value.replace("_", "").isalnum():
            raise ValueError(f"非法 Alpha 状态: {status!r}")
        if value not in normalized_statuses:
            normalized_statuses.append(value)
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset 必须是非负整数")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit 必须是 1 到 100 的整数")
    if not isinstance(descending, bool):
        raise ValueError("descending 必须是布尔值")

    # 平台接受以 %1F 分隔的多状态查询；日期沿用现有 Core 的自然日边界。
    status_query = "%1F".join(normalized_statuses)
    order = "-dateCreated" if descending else "dateCreated"
    q_start, q_end = _inclusive_dates_to_half_open(start_date, end_date)
    url = (
        f"/users/self/alphas?limit={limit}&offset={offset}"
        f"&status={status_query}&type=REGULAR"
        f"&{q_start}&{q_end}"
        f"&is.fitness%3E={fitness_min}&is.sharpe%3E={sharpe_min}"
        f"&order={order}&hidden=false"
    )
    response = client.get(url, timeout=30)
    if response is None or response.status_code != 200:
        return None
    try:
        payload = response.json()
    except (TypeError, ValueError):
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        return None
    return {"results": payload["results"], "count": payload.get("count")}


def get_user_alphas(client: BrainClient, start_str: str, end_str: str,
                    sharpe_th: float, fitness_th: float,
                    region: str, offset: int = 0, tag: str = None) -> list:
    """按照条件拉取一页用户 Alpha；保留旧版列表返回值。"""
    page = _get_user_alphas_page(
        client, start_str, end_str, sharpe_th, fitness_th,
        region, offset, tag=tag,
    )
    if page is None:
        return []
    return page["results"]


def post_simulation(client: BrainClient, simulation_data: dict):
    """提交单条模拟请求，返回 progress URL。"""
    resp = client.post("/simulations", json=simulation_data)
    if resp and resp.status_code in (200, 201, 202):
        return resp.headers.get('Location')
    return None


def post_multi_simulation(client: BrainClient, sim_data_list: list,
                          return_metadata: bool = False, **request_kwargs):
    """提交 Multi-simulation；可选返回限频等可观察响应元数据。"""
    if not isinstance(sim_data_list, list) or not 2 <= len(sim_data_list) <= 8:
        raise ValueError("Multi-simulation 每批必须包含 2 到 8 条")
    resp = client.post("/simulations", json=sim_data_list, **request_kwargs)
    status_code = resp.status_code if resp is not None else None
    location = (
        resp.headers.get('Location')
        if status_code in (200, 201, 202) else None
    )
    if return_metadata:
        headers = resp.headers if resp is not None else {}
        return {
            'location': location,
            'status_code': status_code,
            'retry_after': headers.get('retry-after', headers.get('Retry-After')),
            'response_observed': resp is not None,
        }
    return location


def poll_simulation_progress(client: BrainClient, progress_url: str,
                              timeout: int = 600, should_stop=None) -> dict:
    """
    轮询一个 simulation progress URL 直至完成或超时。
    progress_url 可为完整 URL、/simulations/{id} 或裸 simulation ID。
    返回最终 JSON 结果；超时返回 {}，外部请求停止时返回 INTERRUPTED。
    """
    progress_url = str(progress_url or "").strip()
    if not progress_url:
        return {}
    if not progress_url.startswith(("http://", "https://", "/")):
        if progress_url.startswith("simulations/"):
            progress_url = f"/{progress_url}"
        else:
            progress_url = f"/simulations/{progress_url}"

    def wait_or_stop(seconds):
        """短间隔等待，使停止信号不必等完整 Retry-After。"""
        end = time.time() + max(0.0, float(seconds))
        while time.time() < end:
            if should_stop and should_stop():
                return False
            time.sleep(max(0.0, min(0.25, end - time.time())))
        return True

    start = time.time()
    while time.time() - start < timeout:
        if should_stop and should_stop():
            return {"status": "INTERRUPTED"}
        resp = client.get(progress_url)
        if not resp:
            if not wait_or_stop(5):
                return {"status": "INTERRUPTED"}
            continue
        retry_after = resp.headers.get("Retry-After", 0)
        if retry_after and float(retry_after) > 0:
            if not wait_or_stop(retry_after):
                return {"status": "INTERRUPTED"}
            continue
        result = resp.json()
        status = result.get("status", "")
        if status in ("COMPLETE", "COMPLETED", "WARNING", "ERROR", "FAILED", "CANCELLED"):
            return result
        if not wait_or_stop(3):
            return {"status": "INTERRUPTED"}
    return {}


# === 提交检查 (SC / PC / PPC) ===

def get_alpha_check(client: BrainClient, alpha_id: str,
                    wait_for_result: bool = True) -> dict:
    """获取 Alpha 的 check 原始结果；可关闭 Retry-After 轮询以只查询一次。"""
    while True:
        result = client.get(f"/alphas/{alpha_id}/check")
        if not result:
            return {}
        if wait_for_result and "retry-after" in result.headers:
            time.sleep(float(result.headers["Retry-After"]))
        else:
            break
    try:
        return result.json()
    except Exception:
        return {}


def get_prod_correlation(client: BrainClient, alpha_id: str) -> float | None:
    """通过专用接口读取生产相关性最大值；未就绪或响应异常返回 ``None``。"""
    response = client.get(f"/alphas/{alpha_id}/correlations/prod", timeout=15)
    if response is None or response.status_code != 200:
        return None
    try:
        value = response.json().get("max")
        return float(value) if value is not None else None
    except (AttributeError, TypeError, ValueError):
        return None


def get_ppc_value(client: BrainClient, alpha_id: str) -> tuple:
    """
    基本不使用，有本地计算 calc_ppac，差距非常小
    请求 /correlations/power-pool 接口，获取 PPC (max, min)。
    """
    url = f"/alphas/{alpha_id}/correlations/power-pool"
    empty_retries = 0
    while empty_retries < 10:
        resp = client.get(url, timeout=30)
        if resp is None or resp.status_code != 200:
            return None, None
        if not resp.content:
            time.sleep(min(20 * (2 ** empty_retries), 180))
            empty_retries += 1
            continue
        try:
            data = resp.json()
            maximum = data.get("max")
            minimum = data.get("min")
            if maximum is None or minimum is None:
                return None, None
            return float(maximum), float(minimum)
        except (AttributeError, TypeError, ValueError):
            return None, None
    return None, None
