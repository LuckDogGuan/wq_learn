"""按北京时间执行多组 Alpha 定时提交任务，只依赖 Core。"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Core.api.submission import run_submission_group


# 每项格式：(北京时间, [同一时间提交的多个 Alpha ID])
SCHEDULES = [
    # ("2026-09-08 14:00", ["因子1", "因子2", "因子3"]),
    # ("2026-09-09 15:00", ["因子4", "因子5"]),
    # ("2026-09-10 16:00", ["因子6", "因子7"]),
]

BEIJING = timezone(timedelta(hours=8), "Asia/Shanghai")
TIME_FORMATS = (
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H",
    "%Y年%m月%d日 %H点%M分",
    "%Y年%m月%d日 %H点",
)


def parse_submit_at(value: str) -> datetime:
    value = str(value or "").strip()
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=BEIJING)
        except ValueError:
            pass
    raise ValueError("时间格式应为 2026-09-08 14:00 或 2026年09月08日 14点")


def parse_ids(values) -> list[str]:
    ids: list[str] = []
    for value in values:
        if isinstance(value, str):
            parts = value.replace("，", ",").replace("；", ",").replace(";", ",").split(",")
        else:
            parts = value
        ids.extend(str(part).strip() for part in parts if str(part).strip())
    result = list(dict.fromkeys(ids))
    if not result:
        raise ValueError("每个日期必须填写至少一个 Alpha ID")
    return result


def parse_schedules(values: list[str] | None) -> list[tuple[datetime, list[str]]]:
    raw = values if values else SCHEDULES
    schedules = []
    for item in raw:
        if isinstance(item, str):
            submit_at, separator, ids = item.partition("|")
            if not separator:
                raise ValueError("--schedule 格式为：时间|ID1,ID2")
        else:
            submit_at, ids = item
        schedules.append((parse_submit_at(submit_at), parse_ids(ids if not isinstance(ids, str) else [ids])))
    if not schedules:
        raise ValueError("请在 SCHEDULES 中填写任务，或使用 --schedule 传入")
    return sorted(schedules, key=lambda item: item[0])


def wait_until(run_at: datetime, *, now_fn=None, sleep_fn=time.sleep) -> None:
    now_fn = now_fn or (lambda: datetime.now(BEIJING))
    while True:
        remaining = (run_at - now_fn()).total_seconds()
        if remaining <= 0:
            return
        sleep_fn(min(remaining, 30))


def run_schedules(schedules: list[tuple[datetime, list[str]]], *,
                  submit_group=run_submission_group, now_fn=None,
                  sleep_fn=time.sleep, report=print) -> bool:
    """到时即独立启动各组；上一组重试不会阻塞下一日期。"""
    results = []
    with ThreadPoolExecutor(max_workers=len(schedules)) as executor:
        for run_at, alpha_ids in schedules:
            report(f"等待 {run_at:%Y-%m-%d %H:%M}（北京时间）：{', '.join(alpha_ids)}")
            wait_until(run_at, now_fn=now_fn, sleep_fn=sleep_fn)
            report(f"启动 {run_at:%Y-%m-%d %H:%M}：{', '.join(alpha_ids)}")
            results.append(executor.submit(submit_group, alpha_ids, report))
    outcomes = []
    for future in results:
        try:
            outcomes.append(future.result())
        except Exception as exc:
            report(f"ERROR，任务异常：{type(exc).__name__}: {exc}")
            outcomes.append(False)
    return all(outcomes)


def main() -> int:
    parser = argparse.ArgumentParser(description="按北京时间执行多组 Alpha 定时提交")
    parser.add_argument(
        "--schedule", action="append",
        help='可重复传入，格式："2026-09-08 14:00|ID1,ID2"',
    )
    args = parser.parse_args()
    try:
        schedules = parse_schedules(args.schedule)
    except (TypeError, ValueError) as exc:
        parser.error(str(exc))
    return 0 if run_schedules(schedules) else 1


if __name__ == "__main__":
    raise SystemExit(main())
