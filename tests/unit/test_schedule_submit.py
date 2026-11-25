"""多日期定时提交入口的离线测试；不会连接平台。"""

import importlib.util
from datetime import datetime
from pathlib import Path
import threading
import unittest
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "代码/优化代码/定时提交因子/schedule_submit.py"
SPEC = importlib.util.spec_from_file_location("schedule_submit", SCRIPT)
schedule_submit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(schedule_submit)


class ScheduleSubmitTests(unittest.TestCase):
    def test_multiple_dates_and_multiple_ids_are_sorted(self):
        schedules = schedule_submit.parse_schedules([
            "2026-09-09 15:00|D,E",
            "2026-09-08 14:00|A,B,C",
            "2026年09月10日 16点|F,G",
        ])
        self.assertEqual(
            [(item[0].day, item[1]) for item in schedules],
            [(8, ["A", "B", "C"]), (9, ["D", "E"]), (10, ["F", "G"])],
        )
        self.assertTrue(all(item[0].tzinfo is schedule_submit.BEIJING for item in schedules))

    def test_due_groups_run_independently(self):
        due = datetime(2026, 9, 7, 14, 0, tzinfo=schedule_submit.BEIJING)
        second_started = threading.Event()

        def submit_group(ids, report):
            if ids == ["A"]:
                return second_started.wait(1)
            second_started.set()
            return True

        result = schedule_submit.run_schedules(
            [(due, ["A"]), (due, ["B", "C"])],
            submit_group=submit_group, now_fn=lambda: due,
            sleep_fn=Mock(), report=Mock(),
        )
        self.assertTrue(result)
        self.assertTrue(second_started.is_set())

    def test_wait_and_input_validation(self):
        run_at = datetime(2026, 9, 7, 14, 0, tzinfo=schedule_submit.BEIJING)
        times = iter([
            datetime(2026, 9, 7, 13, 59, 20, tzinfo=schedule_submit.BEIJING),
            datetime(2026, 9, 7, 13, 59, 50, tzinfo=schedule_submit.BEIJING),
            run_at,
        ])
        sleep = Mock()
        schedule_submit.wait_until(run_at, now_fn=lambda: next(times), sleep_fn=sleep)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [30, 10])
        with self.assertRaises(ValueError):
            schedule_submit.parse_schedules([])
        with self.assertRaises(ValueError):
            schedule_submit.parse_schedules(["2026-09-08 14:00"])

    def test_one_group_error_does_not_hide_other_group(self):
        due = datetime(2026, 9, 7, 14, 0, tzinfo=schedule_submit.BEIJING)
        calls = []

        def submit_group(ids, report):
            calls.append(ids)
            if ids == ["A"]:
                raise RuntimeError("login failed")
            return True

        self.assertFalse(schedule_submit.run_schedules(
            [(due, ["A"]), (due, ["B"])], submit_group=submit_group,
            now_fn=lambda: due, report=Mock(),
        ))
        self.assertCountEqual(calls, [["A"], ["B"]])


if __name__ == "__main__":
    unittest.main()
