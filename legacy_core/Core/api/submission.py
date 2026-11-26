"""通用 Alpha 提交 API：检查等待、单次 POST、异步 GET /submit 轮询与结果核验；不包含业务筛选规则。"""

import asyncio
import math
import time

from Core.api.auth import login
from Core.api.client import BrainClient
from Core.api.sim_api import check_alpha_submission_status

DEFAULT_POLL_MAX_ATTEMPTS = 120
DEFAULT_POLL_MAX_WAIT_SECONDS = 180
DEFAULT_POST_CHECK_COOLDOWN = 1.0
DEFAULT_BETWEEN_ALPHAS_COOLDOWN = 2.0


def _safe_json(response):
    if response is None:
        return None
    try:
        return response.json()
    except (ValueError, TypeError, AttributeError):
        return None


def _extract_checks(data) -> list[dict]:
    if not isinstance(data, dict):
        return []
    checks = data.get("checks")
    if checks is None and isinstance(data.get("is"), dict):
        checks = data["is"].get("checks")
    return checks if isinstance(checks, list) else []


def _format_failed_checks(checks: list) -> str:
    failed: list[str] = []
    for check in checks:
        if not isinstance(check, dict) or check.get("result") != "FAIL":
            continue
        name = check.get("name", "UNKNOWN")
        result = check.get("result", "UNKNOWN")
        extras = []
        if check.get("value") is not None:
            extras.append(f"value={check['value']}")
        if check.get("limit") is not None:
            extras.append(f"limit={check['limit']}")
        if check.get("message"):
            extras.append(str(check["message"]))
        suffix = f"({', '.join(extras)})" if extras else ""
        failed.append(f"{name}={result}{suffix}")
    return ", ".join(failed)


def _is_already_submitted_checks(checks: list) -> bool:
    if not isinstance(checks, list) or not checks:
        return False
    failed = [
        check for check in checks
        if isinstance(check, dict) and check.get("result") == "FAIL"
    ]
    if failed:
        return all(check.get("name") == "ALREADY_SUBMITTED" for check in failed)
    return all(
        isinstance(check, dict) and check.get("name") == "ALREADY_SUBMITTED"
        for check in checks
    )


def _parse_retry_after(response, *, min_delay: float = 0.1) -> tuple[bool, float | None]:
    headers = getattr(response, "headers", None) or {}
    raw = headers.get("Retry-After", headers.get("retry-after"))
    if raw is None or str(raw).strip() == "":
        return False, None
    try:
        delay = float(raw)
        if not math.isfinite(delay) or delay < 0:
            return True, None
        return True, max(min_delay, delay)
    except (TypeError, ValueError):
        return True, None


def _summarize_response_body(response, limit: int = 200) -> str:
    data = _safe_json(response)
    if isinstance(data, dict):
        for key in ("error", "errors", "detail", "message"):
            if data.get(key):
                return str(data[key])[:limit]
        checks = _extract_checks(data)
        failed = _format_failed_checks(checks)
        if failed:
            return failed[:limit]
    text = getattr(response, "text", None)
    if isinstance(text, str):
        compact = " ".join(text.split())
        if compact:
            return compact[:limit]
    return ""


def _state_label(state: dict) -> str:
    stage = state.get("stage") or "UNKNOWN"
    status = state.get("status") or "UNKNOWN"
    return f"{stage}/{status}"


def submission_error(response):
    """无响应、限流和服务故障待确认；明确拒绝停止。"""
    if response is None:
        return None
    if response.status_code in (401, 408, 429) or response.status_code >= 500:
        return None
    data = _safe_json(response)
    if isinstance(data, dict):
        for key in ("error", "errors"):
            if data.get(key):
                return str(data[key])
        if str(data.get("status", "")).upper() in ("ERROR", "FAIL", "FAILED"):
            return str(data.get("message") or data.get("detail") or data["status"])
    if 400 <= response.status_code < 500 and response.status_code not in (408, 429):
        detail = _summarize_response_body(response)
        return f"HTTP {response.status_code}（{detail}）" if detail else f"HTTP {response.status_code}"
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
    data = _safe_json(response)
    checks = _extract_checks(data)
    if not checks:
        return "PENDING", "check 无检查项"
    failed_text = _format_failed_checks(checks)
    if failed_text:
        return "ERROR", f"check 失败：{failed_text}"
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
        has_retry_after, delay = _parse_retry_after(response, min_delay=0.1)
        if not has_retry_after:
            return classify_submission_check(response)
        if delay is None:
            return "PENDING", "check Retry-After 无效"
        if attempt + 1 >= max_attempts or delay > deadline - time.monotonic():
            return "PENDING", "check 仍在计算，已到等待上限；未发送提交请求"
        report(f"check 仍在计算，{delay:g} 秒后重新查询（{attempt + 1}/{max_attempts}）")
        await asyncio.sleep(delay)
    return "PENDING", "check 未完成"


def poll_submission_result(
    client,
    alpha_id: str,
    report=print,
    *,
    initial_delay: float | None = None,
    max_attempts: int = DEFAULT_POLL_MAX_ATTEMPTS,
    max_wait_seconds: float = DEFAULT_POLL_MAX_WAIT_SECONDS,
) -> tuple[str, str]:
    """只读轮询 GET /alphas/{id}/submit，直到平台完成异步提交或明确拒绝。"""
    deadline = time.monotonic() + max_wait_seconds
    if initial_delay is not None and initial_delay > 0:
        if initial_delay >= deadline - time.monotonic():
            return "PENDING", "提交已受理，但初始等待超出上限；切勿立即重跑，请稍后使用 --check-only 复核"
        time.sleep(initial_delay)

    for attempt in range(max_attempts):
        if time.monotonic() >= deadline:
            return (
                "PENDING",
                "GET /submit 轮询已到等待上限；后台可能仍在处理，切勿立即重复提交，请稍后使用 --check-only 复核",
            )
        response = client.get(f"/alphas/{alpha_id}/submit", timeout=15, deadline=deadline)
        if response is None:
            return (
                "PENDING",
                "GET /submit 无响应（网络异常或超时）；后台可能仍在处理，请稍后使用 --check-only 复核",
            )
        code = response.status_code
        if code == 403:
            checks = _extract_checks(_safe_json(response))
            if _is_already_submitted_checks(checks):
                return "ALREADY_SUBMITTED", "GET /submit 返回 ALREADY_SUBMITTED"
            failed_text = _format_failed_checks(checks)
            if failed_text:
                return "ERROR", f"异步提交校验被拒绝（HTTP 403）：{failed_text}"
            detail = _summarize_response_body(response)
            return "ERROR", f"异步提交被平台拒绝（HTTP 403）{f'：{detail}' if detail else ''}"
        if code == 404:
            return "EXPIRED", "GET /submit 返回 HTTP 404（提交任务不存在或已超时失效）"
        if code in (401, 408, 429) or code >= 500:
            return (
                "PENDING",
                f"GET /submit 返回 HTTP {code}，状态待确认；请稍后使用 --check-only 复核",
            )
        if not 200 <= code < 300:
            detail = _summarize_response_body(response)
            return "ERROR", f"GET /submit 返回 HTTP {code}{f'：{detail}' if detail else ''}"

        has_retry_after, delay = _parse_retry_after(response, min_delay=0.5)
        if has_retry_after:
            if delay is None:
                return "PENDING", "GET /submit 返回无效 Retry-After；请稍后使用 --check-only 复核"
            if attempt + 1 >= max_attempts or delay > deadline - time.monotonic():
                return (
                    "PENDING",
                    f"提交仍在平台处理中（已轮询 {attempt + 1} 次，已达等待上限）；切勿立即重复提交，请稍后使用 --check-only 复核",
                )
            if attempt < 5 or (attempt + 1) % 5 == 0 or delay >= 2.0:
                report(f"提交仍在平台处理中，{delay:g} 秒后重新查询（{attempt + 1}/{max_attempts}）")
            time.sleep(delay)
            continue

        data = _safe_json(response)
        if isinstance(data, dict):
            for key in ("error", "errors"):
                if data.get(key):
                    return "ERROR", f"GET /submit 返回错误：{data[key]}"
            if str(data.get("status", "")).upper() in ("ERROR", "FAIL", "FAILED"):
                return "ERROR", f"GET /submit 返回失败：{data.get('message') or data.get('detail') or data['status']}"
        checks = _extract_checks(data)
        if _is_already_submitted_checks(checks):
            return "ALREADY_SUBMITTED", "GET /submit 返回 ALREADY_SUBMITTED"
        failed_text = _format_failed_checks(checks)
        if failed_text:
            return "ERROR", f"提交校验未通过：{failed_text}"
        return "DONE", f"GET /submit 完成（HTTP {code}）"

    return (
        "PENDING",
        f"提交仍在平台处理中（已达 {max_attempts} 次轮询上限）；切勿立即重复提交，请稍后使用 --check-only 复核",
    )


def create_submit_session(config_path: str | None = None):
    """Reuse Core authentication; keep the historical session return contract."""
    return login(config_path).session


def _reconcile_alpha_status(client, alpha_id: str, report, *, reason: str,
                            delay_seconds: float = 2.0) -> bool:
    """只读对账 1 次；绝不重发 POST。"""
    if delay_seconds > 0:
        time.sleep(delay_seconds)
    state = check_alpha_submission_status(client, alpha_id)
    if state.get("error"):
        report(f"ERROR：{reason}；只读对账失败：{state['error']}")
        return False
    if state["is_submitted"] is True:
        report(
            f"已确认提交成功：status={state['status']}，"
            f"dateSubmitted={state['date_submitted']}"
        )
        return True
    if state["is_submitted"] is False:
        report(
            f"PENDING_RECONCILE：{reason}；只读对账仍为 {_state_label(state)}，"
            "请稍后使用 --check-only 复核"
        )
    else:
        report(
            f"PENDING_RECONCILE：{reason}；只读对账仍无法确认状态，"
            "请稍后使用 --check-only 复核"
        )
    return False


def submit_alpha_verified(
    client,
    alpha_id: str,
    report=print,
    current_state=None,
    confirmed_alpha_id=None,
    *,
    poll_max_attempts: int = DEFAULT_POLL_MAX_ATTEMPTS,
    poll_max_wait_seconds: float = DEFAULT_POLL_MAX_WAIT_SECONDS,
) -> bool:
    """只发一次 POST；按官方两阶段协议只读轮询 GET /submit，再核验 Alpha 详情状态。"""
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
    if response is None:
        report("PENDING_RECONCILE：POST /submit 无响应（网络异常或超时），绝不盲重发；2 秒后只读对账 1 次")
        return _reconcile_alpha_status(client, alpha_id, report, reason="POST /submit 无响应")

    code = response.status_code
    if code == 429:
        has_ra, ra_delay = _parse_retry_after(response, min_delay=0.1)
        ra_note = f"，Retry-After={ra_delay:g}s" if (has_ra and ra_delay is not None) else ""
        report(f"RATE_LIMITED：POST /submit 返回 HTTP 429（触发平台限流{ra_note}），未触发提交，请稍后重试")
        return False

    if code in (401, 408) or code >= 500:
        report(f"PENDING_RECONCILE：POST /submit 返回 HTTP {code}，绝不盲重发；2 秒后只读对账 1 次")
        return _reconcile_alpha_status(client, alpha_id, report, reason=f"POST /submit 返回 HTTP {code}")

    if code == 403:
        checks = _extract_checks(_safe_json(response))
        if _is_already_submitted_checks(checks):
            report("已确认此前已经提交（POST 403 ALREADY_SUBMITTED）")
            return True
        failed_text = _format_failed_checks(checks)
        if failed_text:
            report(f"ERROR：POST /submit 被拒绝（HTTP 403）：{failed_text}")
            return False
        detail = _summarize_response_body(response)
        report(f"ERROR：POST /submit 被拒绝（HTTP 403）{f'：{detail}' if detail else ''}")
        return False

    if code == 400:
        detail = _summarize_response_body(response)
        if "already" in detail.lower():
            report(f"POST /submit 返回 HTTP 400（{detail}），改为只读核验状态...")
            state = check_alpha_submission_status(client, alpha_id)
            if state["is_submitted"] is True:
                report(
                    f"已确认此前已经提交：status={state['status']}，"
                    f"dateSubmitted={state['date_submitted']}"
                )
                return True
            poll_state, poll_msg = poll_submission_result(
                client, alpha_id, report=report,
                initial_delay=0.0,
                max_attempts=poll_max_attempts,
                max_wait_seconds=poll_max_wait_seconds,
            )
            if poll_state == "ALREADY_SUBMITTED":
                report(f"已确认此前已经提交（{poll_msg}）")
                return True
            if poll_state == "DONE":
                return _reconcile_alpha_status(
                    client, alpha_id, report, reason="GET /submit 已完成", delay_seconds=0.0
                )
            report(f"{poll_state}：{poll_msg}")
            return False
        report(f"ERROR：POST /submit 返回 HTTP 400{f'（{detail}）' if detail else ''}")
        return False

    error = submission_error(response)
    if error:
        report(f"ERROR：POST /submit 失败：{error}")
        return False

    has_ra, ra_delay = _parse_retry_after(response, min_delay=0.5)
    if code in (201, 202) or has_ra:
        if has_ra and ra_delay is None:
            report("PENDING：POST /submit 返回无效 Retry-After；请稍后使用 --check-only 复核")
            return False
        initial_delay = ra_delay if (has_ra and ra_delay is not None) else 1.0
        report(f"POST /submit 已受理（HTTP {code}），开始轮询 GET /submit 等待平台完成...")
        poll_state, poll_msg = poll_submission_result(
            client,
            alpha_id,
            report=report,
            initial_delay=initial_delay,
            max_attempts=poll_max_attempts,
            max_wait_seconds=poll_max_wait_seconds,
        )
        if poll_state == "ALREADY_SUBMITTED":
            report(f"已确认此前已经提交（{poll_msg}）")
            return True
        if poll_state == "ERROR":
            report(f"ERROR：{poll_msg}")
            return False
        if poll_state == "PENDING":
            report(f"PENDING：{poll_msg}")
            return False
        if poll_state == "EXPIRED":
            state = check_alpha_submission_status(client, alpha_id)
            if state["is_submitted"] is True:
                report(
                    f"已确认提交成功：status={state['status']}，"
                    f"dateSubmitted={state['date_submitted']}"
                )
                return True
            report(f"ERROR：{poll_msg}（当前 {_state_label(state)}）")
            return False

        # poll_state == "DONE": 立即只读核验 Alpha 详情；若状态同步有短暂延迟则 2 秒后再核验 1 次
        state = check_alpha_submission_status(client, alpha_id)
        if state["is_submitted"] is True:
            report(
                f"已确认提交成功：status={state['status']}，"
                f"dateSubmitted={state['date_submitted']}"
            )
            return True
        if state.get("error"):
            report(f"ERROR：{state['error']}")
            return False
        return _reconcile_alpha_status(
            client, alpha_id, report, reason="GET /submit 已返回完成", delay_seconds=2.0
        )

    # 同步 200 / 204（不带 Retry-After）
    checks = _extract_checks(_safe_json(response))
    if _is_already_submitted_checks(checks):
        report("已确认此前已经提交（ALREADY_SUBMITTED）")
        return True
    failed_text = _format_failed_checks(checks)
    if failed_text:
        report(f"ERROR：POST /submit 校验未通过：{failed_text}")
        return False

    time.sleep(2)
    state = check_alpha_submission_status(client, alpha_id)
    if state.get("error"):
        report(f"ERROR：{state['error']}")
        return False
    if state["is_submitted"] is True:
        report(
            f"已确认提交成功：status={state['status']}，"
            f"dateSubmitted={state['date_submitted']}"
        )
        return True
    if state["is_submitted"] is False:
        report(f"未提交：POST 返回 HTTP {code}，两秒后按 Alpha ID 查询仍为 {_state_label(state)}")
    else:
        report(f"PENDING：POST 返回 HTTP {code}，两秒后按 Alpha ID 查询仍无法确认")
    return False


async def submit_all_checked(
    session,
    alpha_ids: list[str],
    report=print,
    confirmed_ids=None,
    *,
    check_only: bool = False,
    post_check_cooldown: float = DEFAULT_POST_CHECK_COOLDOWN,
    between_alphas_cooldown: float = DEFAULT_BETWEEN_ALPHAS_COOLDOWN,
    poll_max_attempts: int = DEFAULT_POLL_MAX_ATTEMPTS,
    poll_max_wait_seconds: float = DEFAULT_POLL_MAX_WAIT_SECONDS,
) -> bool:
    """检查计算中时有界只读等待；提交最多发一次 POST，再按两阶段协议只读轮询确认。"""
    confirmed_ids = set(confirmed_ids or ())
    client = BrainClient(session=session)
    client.mark_authenticated()
    all_succeeded = True
    for index, alpha_id in enumerate(alpha_ids, 1):
        prefix = f"[{index}/{len(alpha_ids)}] {alpha_id}: "
        if not check_only and alpha_id not in confirmed_ids:
            report(prefix + "BLOCKED，缺少本次人工确认")
            all_succeeded = False
            continue
        current = check_alpha_submission_status(client, alpha_id)
        if current["is_submitted"] is True:
            report(
                prefix
                + f"已确认此前已经提交（status={current.get('status')}，dateSubmitted={current.get('date_submitted')}）"
            )
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
        if check_only:
            report(prefix + f"只读模式（--check-only）：当前状态 {_state_label(current)}，未发送 POST /submit")
            if state != "PASS":
                all_succeeded = False
            continue
        if state != "PASS":
            all_succeeded = False
            continue
        if post_check_cooldown > 0:
            await asyncio.sleep(post_check_cooldown)
        if not submit_alpha_verified(
            client,
            alpha_id,
            lambda text: report(prefix + text),
            current_state=current,
            confirmed_alpha_id=alpha_id,
            poll_max_attempts=poll_max_attempts,
            poll_max_wait_seconds=poll_max_wait_seconds,
        ):
            all_succeeded = False
        if index < len(alpha_ids) and between_alphas_cooldown > 0:
            await asyncio.sleep(between_alphas_cooldown)
    return all_succeeded


def run_submission_group(
    alpha_ids: list[str],
    report=print,
    confirmed_ids=None,
    *,
    check_only: bool = False,
    poll_max_wait_seconds: float = DEFAULT_POLL_MAX_WAIT_SECONDS,
) -> bool:
    """仅处理本次明确人工确认的 Alpha；定时配置不是确认。check_only=True 仅执行只读检查。"""
    confirmed_ids = set(confirmed_ids or ())
    if not check_only and set(alpha_ids) != confirmed_ids:
        report("BLOCKED：提交必须在本次运行中逐个确认全部 Alpha ID")
        return False
    session = create_submit_session()
    try:
        return asyncio.run(submit_all_checked(
            session,
            alpha_ids,
            report=report,
            confirmed_ids=confirmed_ids,
            check_only=check_only,
            poll_max_wait_seconds=poll_max_wait_seconds,
        ))
    finally:
        session.close()
