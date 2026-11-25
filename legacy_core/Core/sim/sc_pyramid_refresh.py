"""在安全检查点统一增量刷新 SC 参考池和 Pyramid diversity 快照。"""

import hashlib
import json
import os
import re
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from Core.api.activity_api import get_user_diversity
from Core.data.runtime_paths import (
    SC_PPA_CACHE_DIR, SC_PYRAMID_REFRESH_STATE_PATH,
)
from Core.sim.sc_engine import download_data_with_report
from Core.sim.validator import invalidate_cache


DEFAULT_REFRESH_HOURS = 6
RETRY_SECONDS = 300
FAILED_PNL_RETRY_SECONDS = 300
FAILED_PNL_MAX_QUICK_RETRIES = 2
_REPLACE_RETRY_DELAYS = (0.1, 0.2, 0.5, 1.0)
_refresh_lock = threading.Lock()


def _now():
    return datetime.now().astimezone()


def _iso(value):
    return value.isoformat(timespec="seconds") if value else None


def _parse_time(value):
    try:
        return datetime.fromisoformat(value) if value else None
    except (TypeError, ValueError):
        return None


def _json_hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _category_key(category):
    value = category.get("id") or category.get("name") or ""
    token = re.sub(r"[^a-z0-9]+", "", str(value).lower())
    return {"pricevolume": "pv", "pricevol": "pv"}.get(token, token)


def _coverage_hash(payload):
    """只让塔PASS语义变化触发候选重筛，忽略 alphaCount 波动。"""
    rows = payload.get("alphas") if isinstance(payload, dict) else None
    normalized = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        category = row.get("dataCategory") or {}
        category_key = _category_key(category)
        if not category_key or row.get("delay") is None or not row.get("region"):
            continue
        diversity = row.get("dataDiversity") or {}
        normalized.append((
            str(row.get("region")).strip().upper(), row.get("delay"), category_key,
            str(diversity.get("check") or "").strip().upper(), diversity.get("limit"),
        ))
    return _json_hash(sorted(normalized))


def _default_state():
    return {
        "schema_version": 1,
        "status": "PENDING",
        "sc_status": "NEVER_REFRESHED",
        "pyramid_status": "NEVER_REFRESHED",
        "observed_new_os_alpha_ids": [],
        "cached_new_os_alpha_ids": [],
        "failed_pnl_alpha_ids": [],
        "failed_pnl_retry_at": None,
        "failed_pnl_quick_retry_count": 0,
        "cached_os_count": 0,
        "diversity_payload": {},
        "diversity_payload_hash": None,
        "diversity_coverage_hash": None,
        "last_attempt_at": None,
        "last_sc_success_at": None,
        "last_success_at": None,
        "next_due_at": None,
        "retry_after": None,
        "pending_pyramid_refresh": False,
        "reason": "尚未刷新",
    }


def load_sc_pyramid_refresh_state(state_path=None):
    """读取刷新状态；文件不存在或损坏时返回可初始化的默认状态。"""
    path = Path(state_path or SC_PYRAMID_REFRESH_STATE_PATH)
    if not path.exists():
        return _default_state()
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return _default_state()
    if not isinstance(state, dict):
        return _default_state()
    result = _default_state()
    result.update(state)
    return result


def _save_state(state, state_path):
    path = Path(state_path or SC_PYRAMID_REFRESH_STATE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.{uuid4().hex}.tmp")
    try:
        temp_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        for attempt in range(len(_REPLACE_RETRY_DELAYS) + 1):
            try:
                os.replace(temp_path, path)
                break
            except PermissionError:
                if attempt >= len(_REPLACE_RETRY_DELAYS):
                    raise
                time.sleep(_REPLACE_RETRY_DELAYS[attempt])
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def _public_result(state, status=None):
    result = dict(state)
    result.pop("pending_pyramid_refresh", None)
    if status:
        result["status"] = status
    return result


def refresh_sc_pyramid_bundle(client, interval_hours=DEFAULT_REFRESH_HOURS,
                              force=False, cache_dir=None, state_path=None):
    """按6小时安全检查点刷新SC；发现新OS Alpha后再刷新塔。

    ``force=True`` 会忽略时间并同时强制刷新 SC 与 Pyramid。函数只做只读平台
    请求和本地缓存写入，不创建模拟、不修改 Alpha 属性。
    """
    if isinstance(interval_hours, bool) or not isinstance(interval_hours, (int, float)) \
            or interval_hours <= 0:
        raise ValueError("interval_hours 必须是正数")

    cache_dir = Path(cache_dir or SC_PPA_CACHE_DIR)
    state_path = Path(state_path or SC_PYRAMID_REFRESH_STATE_PATH)
    with _refresh_lock:
        state = load_sc_pyramid_refresh_state(state_path)
        now = _now()
        retry_after = _parse_time(state.get("retry_after"))
        if not force and retry_after and now < retry_after:
            return _public_result(state, "PENDING")

        last_sc_success = _parse_time(state.get("last_sc_success_at"))
        scheduled_sc_due = force or last_sc_success is None or (
            now >= last_sc_success + timedelta(hours=float(interval_hours))
        )
        failed_pnl_ids = list(dict.fromkeys(state.get("failed_pnl_alpha_ids") or []))
        failed_pnl_retry_at = _parse_time(state.get("failed_pnl_retry_at"))
        # 兼容升级前已经落盘的 PARTIAL 状态：旧文件只有失败ID，没有补偿时间。
        # 从上次尝试后5分钟起即可在下一个安全检查点补偿，不必等满6小时。
        if failed_pnl_ids and failed_pnl_retry_at is None \
                and int(state.get("failed_pnl_quick_retry_count") or 0) \
                < FAILED_PNL_MAX_QUICK_RETRIES:
            retry_base = _parse_time(state.get("last_attempt_at")) or now
            failed_pnl_retry_at = retry_base + timedelta(
                seconds=FAILED_PNL_RETRY_SECONDS
            )
            state["failed_pnl_retry_at"] = _iso(failed_pnl_retry_at)
        quick_retry_due = bool(
            not scheduled_sc_due and failed_pnl_ids and failed_pnl_retry_at
            and now >= failed_pnl_retry_at
            and int(state.get("failed_pnl_quick_retry_count") or 0)
            < FAILED_PNL_MAX_QUICK_RETRIES
        )
        sc_due = scheduled_sc_due or quick_retry_due
        pyramid_needed = bool(
            force or state.get("pending_pyramid_refresh")
            or not isinstance(state.get("diversity_payload", {}).get("alphas"), list)
        )
        if not sc_due and not pyramid_needed:
            state["next_due_at"] = _iso(
                last_sc_success + timedelta(hours=float(interval_hours))
            )
            return _public_result(state, "NOT_DUE")

        state["last_attempt_at"] = _iso(now)
        sc_report = None
        if sc_due:
            previously_observed = set(state.get("observed_new_os_alpha_ids") or [])
            previously_failed = set(failed_pnl_ids)
            sc_report = download_data_with_report(
                client, cache_dir=cache_dir, flag_increment=True,
                retry_alpha_ids=failed_pnl_ids,
            )
            newly_observed_ids = set(sc_report["observed_new_os_alpha_ids"]) - (
                previously_observed | previously_failed
            )
            state.update({
                "sc_status": sc_report["status"],
                "observed_new_os_alpha_ids": sc_report["observed_new_os_alpha_ids"],
                "cached_new_os_alpha_ids": sc_report["cached_new_os_alpha_ids"],
                "failed_pnl_alpha_ids": sc_report["failed_pnl_alpha_ids"],
                "cached_os_count": sc_report["cached_os_count"],
            })
            if sc_report["status"] == "PENDING":
                state.update({
                    "status": "PENDING", "reason": sc_report["reason"],
                    "retry_after": _iso(now + timedelta(seconds=RETRY_SECONDS)),
                })
                _save_state(state, state_path)
                return _public_result(state)
            if scheduled_sc_due:
                state["last_sc_success_at"] = _iso(now)
            if sc_report["cache_changed"]:
                invalidate_cache()
            pyramid_needed = pyramid_needed or bool(newly_observed_ids)
            if sc_report["failed_pnl_alpha_ids"]:
                quick_retry_count = (
                    int(state.get("failed_pnl_quick_retry_count") or 0) + 1
                    if quick_retry_due else 0
                )
                state["failed_pnl_quick_retry_count"] = quick_retry_count
                state["failed_pnl_retry_at"] = (
                    _iso(now + timedelta(seconds=FAILED_PNL_RETRY_SECONDS))
                    if quick_retry_count < FAILED_PNL_MAX_QUICK_RETRIES else None
                )
            else:
                state["failed_pnl_quick_retry_count"] = 0
                state["failed_pnl_retry_at"] = None

        if pyramid_needed:
            diversity_payload = get_user_diversity(client)
            if not isinstance(diversity_payload.get("alphas"), list):
                state.update({
                    "status": "PENDING", "pyramid_status": "PENDING",
                    "pending_pyramid_refresh": True,
                    "reason": "Pyramid diversity响应不可观察",
                    "retry_after": _iso(now + timedelta(seconds=RETRY_SECONDS)),
                })
                _save_state(state, state_path)
                return _public_result(state)
            state.update({
                "pyramid_status": "REFRESHED",
                "pending_pyramid_refresh": False,
                "diversity_payload": diversity_payload,
                "diversity_payload_hash": _json_hash(diversity_payload),
                "diversity_coverage_hash": _coverage_hash(diversity_payload),
            })

        last_sc_success = _parse_time(state.get("last_sc_success_at"))
        final_status = "PARTIAL" if sc_report and sc_report["status"] == "PARTIAL" else "REFRESHED"
        state.update({
            "status": final_status, "reason": "",
            "last_success_at": _iso(now), "retry_after": None,
            "next_due_at": _iso(
                last_sc_success + timedelta(hours=float(interval_hours))
            ) if last_sc_success else None,
        })
        _save_state(state, state_path)
        return _public_result(state)
