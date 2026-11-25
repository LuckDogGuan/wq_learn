"""通用 Alpha 提交 API：检查等待、单次提交及结果核验；不包含业务筛选规则。"""

import asyncio
import math
import time

from Core.api.auth import login
from Core.api.client import BrainClient
from Core.api.sim_api import check_alpha_submission_status


def submission_error(response):
    """无响应、限流和服务故障待确认；明确拒绝停止。"""
    if response is None:
        return None
    if response.status_code in (401, 408, 429) or response.status_code >= 500:
        return None
    try:
        data = response.json()
    except (ValueError, TypeError):
        data = None
    if isinstance(data, dict):
        for key in ("error", "errors"):
            if data.get(key):
                return str(data[key])
        if str(data.get("status", "")).upper() in ("ERROR", "FAIL", "FAILED"):
            return str(data.get("message") or data.get("detail") or data["status"])
    if 400 <= response.status_code < 500 and response.status_code not in (408, 429):
        return f"HTTP {response.status_code}"
    return None


def classify_submission_check(response):
    """将提交前检查归为 PASS、PENDING 或 ERROR。"""
    if response is None:
        return "PENDING", "check 无响应"
    error = submission_error(response)
    if error:
        return "ERROR", error
    if not 200 <= response.status_code < 300:
        return "PENDING", f"check HTTP {response.status_code}"
    try:
        data = response.json()
        checks = data.get("checks")
        if checks is None and isinstance(data.get("is"), dict):
            checks = data["is"].get("checks")
    except (ValueError, TypeError, AttributeError):
        checks = []
    if not isinstance(checks, list) or not checks:
        return "PENDING", "check 无检查项"
    failed = [
        f"{check.get('name', 'UNKNOWN')}={check.get('result', 'UNKNOWN')}"
        for check in checks
        if isinstance(check, dict) and check.get("result") == "FAIL"
    ]
    if failed:
        return "ERROR", f"check 失败：{', '.join(failed)}"
    if any(not isinstance(check, dict) or check.get("result") not in ("PASS", "WARNING")
           for check in checks):
        return "PENDING", "check 未完成"
    return "PASS", "check 成功"


async def wait_submission_check(client, alpha_id, report=print, max_attempts=30,
                                max_wait_seconds=120):
    """Poll only the read-only check endpoint while Retry-After is present."""
    deadline = time.monotonic() + max_wait_seconds
    for attempt in range(max_attempts):
        if time.monotonic() >= deadline:
            return "PENDING", "check 已到等待上限；未发送提交请求"
        response = client.get(f"/alphas/{alpha_id}/check", timeout=15, deadline=deadline)
        if response is None or response.status_code != 200:
            return classify_submission_check(response)
        retry_after = response.headers.get("Retry-After", response.headers.get("retry-after"))
        if retry_after is None:
            return classify_submission_check(response)
        try:
            delay = float(retry_after)
            if not math.isfinite(delay) or delay < 0:
                raise ValueError("invalid delay")
            delay = max(0.1, delay)
        except (TypeError, ValueError):
            return "PENDING", "check Retry-After 无效"
        if attempt + 1 >= max_attempts or delay > deadline - time.monotonic():
            return "PENDING", "check 仍在计算，已到等待上限；未发送提交请求"
        report(f"check 仍在计算，{delay:g} 秒后重新查询（{attempt + 1}/{max_attempts}）")
        await asyncio.sleep(delay)
    return "PENDING", "check 未完成"


def create_submit_session(config_path: str | None = None):
    """Reuse Core authentication; keep the historical session return contract."""
    return login(config_path).session


def submit_alpha_verified(client, alpha_id: str, report=print,
                          current_state=None, confirmed_alpha_id=None) -> bool:
    """只提交一次；两秒后按 Alpha ID 查询一次最终状态。"""
    if confirmed_alpha_id != alpha_id:
        report(f"BLOCKED：未获得 Alpha {alpha_id} 的本次人工确认")
        return False
    state = current_state or check_alpha_submission_status(client, alpha_id)
    if state.get("error"):
        report(f"ERROR：{state['error']}")
        return False
    if state["is_submitted"] is True:
        report("已确认此前已经提交")
        return True
    if state["is_submitted"] is not False:
        report("PENDING：当前提交状态无法确认，未发送提交请求")
        return False

    response = client.post(f"/alphas/{alpha_id}/submit")
    error = submission_error(response)
    if error:
        report(f"ERROR：{error}")
        return False

    time.sleep(2)
    state = check_alpha_submission_status(client, alpha_id)
    if state.get("error"):
        report(f"ERROR：{state['error']}")
        return False
    if state["is_submitted"] is True:
        report(f"已确认提交成功：status={state['status']}，"
               f"dateSubmitted={state['date_submitted']}")
        return True
    if state["is_submitted"] is False:
        report("未提交：两秒后按 Alpha ID 查询仍为 IS/UNSUBMITTED")
    else:
        report("PENDING：两秒后按 Alpha ID 查询仍无法确认")
    return False


async def submit_all_checked(session, alpha_ids: list[str],
                             report=print, confirmed_ids=None) -> bool:
    """检查计算中时有界只读等待；提交最多一次，之后只读核验一次。"""
    confirmed_ids = set(confirmed_ids or ())
    client = BrainClient(session=session)
    client.mark_authenticated()
    all_succeeded = True
    for index, alpha_id in enumerate(alpha_ids, 1):
        prefix = f"[{index}/{len(alpha_ids)}] {alpha_id}: "
        if alpha_id not in confirmed_ids:
            report(prefix + "BLOCKED，缺少本次人工确认")
            all_succeeded = False
            continue
        current = check_alpha_submission_status(client, alpha_id)
        if current["is_submitted"] is True:
            report(prefix + "已确认此前已经提交")
            continue
        if current.get("error"):
            report(prefix + f"ERROR，{current['error']}")
            all_succeeded = False
            continue
        if current["is_submitted"] is not False:
            report(prefix + "PENDING，当前提交状态无法确认")
            all_succeeded = False
            continue
        try:
            state, message = await wait_submission_check(
                client, alpha_id, lambda text: report(prefix + text)
            )
        except Exception as exc:
            state, message = "PENDING", f"check 异常：{type(exc).__name__}"
        report(f"{prefix}{state}，{message}")
        if state != "PASS":
            all_succeeded = False
            continue
        if not submit_alpha_verified(
            client, alpha_id, lambda text: report(prefix + text),
            current_state=current,
            confirmed_alpha_id=alpha_id,
        ):
            all_succeeded = False
    return all_succeeded


def run_submission_group(alpha_ids: list[str], report=print,
                         confirmed_ids=None) -> bool:
    """仅处理本次明确人工确认的 Alpha；定时配置不是确认。"""
    confirmed_ids = set(confirmed_ids or ())
    if set(alpha_ids) != confirmed_ids:
        report("BLOCKED：提交必须在本次运行中逐个确认全部 Alpha ID")
        return False
    session = create_submit_session()
    try:
        return asyncio.run(submit_all_checked(
            session, alpha_ids, report=report, confirmed_ids=confirmed_ids
        ))
    finally:
        session.close()
