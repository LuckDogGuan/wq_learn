"""RA常驻检测的进度与日计数；不生成模板，不创建回测，不提交Alpha。"""

import json
import math
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


BEIJING = ZoneInfo("Asia/Shanghai")


def completed_batches_today(output, now=None):
    now = now or datetime.now(BEIJING)
    if now.tzinfo is None:
        now = now.replace(tzinfo=BEIJING)
    date = now.astimezone(BEIJING).date()
    completed = set()
    for path in Path(output).glob("filter_ra_alphas_v6_state_*.json"):
        if "dry_run" in path.name:
            continue
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for chunk in state.get("chunk_batches", []) if isinstance(state, dict) else []:
            if chunk.get("status") != "COMPLETE" or not chunk.get("id") or not chunk.get("completed_at"):
                continue
            try:
                stamp = datetime.fromisoformat(chunk["completed_at"])
                stamp = stamp.replace(tzinfo=BEIJING) if stamp.tzinfo is None else stamp
            except (ValueError, TypeError):
                continue
            results = chunk.get("results")
            if stamp.astimezone(BEIJING).date() != date or stamp > now or not isinstance(results, list) or len(results) != 8:
                continue
            ids = {result.get("alpha_id") for result in results if isinstance(result, dict)}
            if len(ids) != 8 or None in ids or "" in ids:
                continue
            if not all(isinstance(result.get(metric), (int, float)) and not isinstance(result.get(metric), bool)
                       and math.isfinite(result[metric]) for result in results for metric in ("sharpe", "fitness", "margin", "turnover")):
                continue
            completed.add(chunk["id"])
    return len(completed)


def keep_running(run_job, core, output, target=10, retry_seconds=300, scan_seconds=1800):
    """持续V5检测及V6设置扩展；异常恢复后重进断点，不凭空补次数。"""
    next_scan = 0.0
    last_error = None
    error_detail = None
    while True:
        now = datetime.now(BEIJING)
        scan_due = time.monotonic() >= next_scan
        # 每轮复用RA模块，但认证客户端重建，避免跨日沿用过期会话。
        previous = core._CORE_CLIENT
        if previous is not None:
            previous.session.close()
        core._CORE_CLIENT = None
        core._atomic_write_json(Path(output) / "ra_runtime_health.json", {
            "heartbeat_at": now.isoformat(), "cycle_started_at": now.isoformat(),
            "daily_completed_batches": completed_batches_today(output), "daily_target_batches": target,
            "status": "V5_V6_RUNNING", "last_error_type": last_error,
        })
        try:
            run_job(run_v5=scan_due, run_v6=True)
            last_error = None
            error_detail = None
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            last_error = type(exc).__name__
            error_detail = str(exc) if isinstance(exc, (AttributeError, ImportError, NameError)) else last_error
            core.progress(f"RA本轮=PENDING：{error_detail}；保留断点，冷却后继续")
        if scan_due:
            next_scan = time.monotonic() + scan_seconds
        count = completed_batches_today(output)
        core.progress(f"RA今日完整回测={count}/{target}批；持续检测；不足时不伪报达标")
        remaining = max(300, retry_seconds)
        while remaining > 0:
            core._atomic_write_json(Path(output) / "ra_runtime_health.json", {
                "heartbeat_at": datetime.now(BEIJING).isoformat(), "cycle_started_at": now.isoformat(),
                "daily_completed_batches": count, "daily_target_batches": target,
                "status": "DAILY_TARGET_MET" if count >= target else "PENDING_DAILY_TARGET",
                "last_error_type": last_error, "next_cycle_seconds": remaining,
                "last_error_detail": error_detail,
            })
            wait = min(60, remaining)
            time.sleep(wait)
            remaining -= wait
