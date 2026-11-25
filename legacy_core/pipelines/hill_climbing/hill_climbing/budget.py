"""跨重启保存的每日回测额度。"""

import json
import os
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

if os.name == "nt":
    import msvcrt
else:
    import fcntl

from Core.data.runtime_paths import HILL_CLIMBING_BUDGET_STATE_PATH


BEIJING_TZ = ZoneInfo("Asia/Shanghai")


class DailyBacktestLimitReached(RuntimeError):
    """当前额度窗口无法再容纳一个完整 Multi-Simulation 批次。"""

    def __init__(self, requested, snapshot):
        self.requested = requested
        self.snapshot = snapshot
        self.reset_at = snapshot["reset_at"]
        super().__init__(
            f"每日回测额度不足：需要{requested}，剩余{snapshot['remaining']}，"
            f"将在{self.reset_at}重置"
        )


class DailyBacktestBudget:
    """按表达式数量计费的本地硬上限；缓存命中和只读对账不计数。"""

    def __init__(self, limit=3000, reset_hour=12, state_path=None, now_func=None):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 2:
            raise ValueError("每日回测上限必须是大于等于2的整数")
        if isinstance(reset_hour, bool) or not isinstance(reset_hour, int) or not 0 <= reset_hour <= 23:
            raise ValueError("重置小时必须是0到23的整数")
        self.limit = limit
        self.reset_hour = reset_hour
        self.state_path = Path(state_path or HILL_CLIMBING_BUDGET_STATE_PATH)
        self._now_func = now_func or (lambda: datetime.now(BEIJING_TZ))
        self._lock = threading.Lock()

    def _window(self, now):
        now = now.astimezone(BEIJING_TZ)
        reset_today = now.replace(
            hour=self.reset_hour, minute=0, second=0, microsecond=0
        )
        if now < reset_today:
            return reset_today - timedelta(days=1), reset_today
        return reset_today, reset_today + timedelta(days=1)

    def _read(self):
        try:
            with self.state_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return payload if isinstance(payload, dict) else {}
        except (OSError, TypeError, ValueError):
            return {}

    @contextmanager
    def _state_lock(self):
        """跨进程锁住同一额度状态，避免两个脚本同时突破上限。"""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.state_path.with_suffix(f"{self.state_path.suffix}.lock")
        with lock_path.open("a+b") as handle:
            handle.seek(0)
            handle.write(b"\0")
            handle.flush()
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if os.name == "nt":
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _save(self, state):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.state_path.with_name(
            f"{self.state_path.name}.{uuid4().hex}.tmp"
        )
        try:
            with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(state, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            for attempt in range(5):
                try:
                    os.replace(temp_path, self.state_path)
                    return
                except PermissionError:
                    if attempt == 4:
                        raise
                    time.sleep((0.1, 0.2, 0.5, 1.0)[attempt])
        finally:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    def _current_state(self):
        now = self._now_func().astimezone(BEIJING_TZ)
        window_start, reset_at = self._window(now)
        state = self._read()
        cooldown = {
            key: state.get(key) for key in (
                "post_not_before", "post_cooldown_count", "last_rate_limit_at"
            ) if state.get(key) is not None
        }
        if state.get("window_started_at") != window_start.isoformat():
            state = {
                "window_started_at": window_start.isoformat(),
                "used": 0,
                **cooldown,
            }
        used = max(0, int(state.get("used") or 0))
        state.update({
            "used": used,
            "limit": self.limit,
            "remaining": max(0, self.limit - used),
            "reset_hour": self.reset_hour,
            "reset_at": reset_at.isoformat(),
            "updated_at": now.isoformat(),
        })
        return state

    def post_cooldown_snapshot(self):
        """读取账户级 POST 冷却；过期后自动清除，不影响额度窗口。"""
        with self._lock, self._state_lock():
            state = self._current_state()
            now = self._now_func().astimezone(BEIJING_TZ)
            try:
                not_before = datetime.fromisoformat(state.get("post_not_before") or "")
            except (TypeError, ValueError):
                not_before = None
            active = bool(not_before and not_before > now)
            if not active:
                state.pop("post_not_before", None)
            self._save(state)
            return {
                "active": active,
                "retry_after": not_before.isoformat() if active else None,
                "remaining_seconds": max(0.0, (not_before - now).total_seconds())
                if active else 0.0,
                "count": int(state.get("post_cooldown_count") or 0),
            }

    def record_post_rate_limit(self, seconds=300):
        """任意父任务遇到 429 后，跨进程冻结该账户的全部新 POST。"""
        seconds = max(0.0, float(seconds))
        with self._lock, self._state_lock():
            state = self._current_state()
            now = self._now_func().astimezone(BEIJING_TZ)
            proposed = now + timedelta(seconds=seconds)
            try:
                existing = datetime.fromisoformat(state.get("post_not_before") or "")
            except (TypeError, ValueError):
                existing = None
            not_before = max(proposed, existing) if existing else proposed
            state.update({
                "post_not_before": not_before.isoformat(),
                "last_rate_limit_at": now.isoformat(),
                "post_cooldown_count": int(state.get("post_cooldown_count") or 0) + 1,
            })
            self._save(state)
            return {
                "active": True,
                "retry_after": not_before.isoformat(),
                "remaining_seconds": max(0.0, (not_before - now).total_seconds()),
                "count": state["post_cooldown_count"],
            }

    def snapshot(self):
        """读取当前窗口；跨过中午12点时自动生成新窗口并落盘。"""
        with self._lock, self._state_lock():
            state = self._current_state()
            self._save(state)
            return dict(state)

    def reserve(self, count):
        """在 POST 前预扣表达式数量；失败结果也保守计入，防止重复超额。"""
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ValueError("预扣数量必须是正整数")
        with self._lock, self._state_lock():
            state = self._current_state()
            if count > state["remaining"]:
                raise DailyBacktestLimitReached(count, dict(state))
            state["used"] += count
            state["remaining"] -= count
            self._save(state)
            return dict(state)
