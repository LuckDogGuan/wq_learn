"""只读重放爬山日志，计算旧基线与新状态机可收敛的确定性空转。"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


_SOURCE_FILE = re.compile(r"([^_\\/]+)_hill_climbing_v4\.7\.log$")
_RESERVED = re.compile(r"回测额度已预扣\s+(\d+)")
_STAGE_GATE = re.compile(r"阶段=([123])\s+门槛=(PASS|FAIL|PENDING)")
_GATE_FAILURES = re.compile(r"\[阶段门槛未通过\].*failed=\[(.*)\]")


def replay(log_dir):
    log_dir = Path(log_dir)
    files = sorted(log_dir.rglob("*.log"))
    metrics = Counter(log_files=len(files))
    incomplete_by_source = Counter()
    stage2_blocked_sources = set()
    for path in files:
        source_match = _SOURCE_FILE.search(str(path))
        source_id = source_match.group(1) if source_match else path.stem
        stage1_completed = False
        current_stage = None
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                metrics["lines"] += 1
                if re.search(r"(?:首次提交|重试提交|过期断点重提) Multi-Simulation", line):
                    metrics["raw_post_log_lines"] += 1
                if "首次提交 Multi-Simulation" in line:
                    metrics["logical_initial_posts"] += 1
                if "重试提交 Multi-Simulation" in line:
                    metrics["cooldown_retry_posts"] += 1
                reserved = _RESERVED.search(line)
                if reserved:
                    metrics["backtest_slots"] += int(reserved.group(1))
                if "评分]" in line:
                    metrics["score_log_lines"] += 1
                    if "总分=PENDING" not in line:
                        metrics["observable_score_records"] += 1
                gate_match = _STAGE_GATE.search(line)
                if gate_match:
                    stage, status = gate_match.groups()
                    current_stage = int(stage)
                    metrics[f"stage{stage}_scored"] += 1
                    metrics[f"stage{stage}_{status.lower()}"] += 1
                    if status != 'PENDING':
                        metrics[f"stage{stage}_fully_observable"] += 1
                if '已记录为 STAGE1_COMPLETE' in line:
                    stage1_completed = True
                if "WARNING - BLOCKED_INCOMPLETE_BATCH" in line and stage1_completed:
                    stage2_blocked_sources.add(source_id)
                if "DEFERRED_INCOMPLETE_BATCH: 7/8" in line:
                    metrics["incomplete_7_of_8"] += 1
                    incomplete_by_source[source_id] += 1
                if "unsupported format string passed to NoneType.__format__" in line:
                    metrics["none_format_exceptions"] += 1
                if "unsupported operand type(s) for -: 'float' and 'NoneType'" in line:
                    metrics["none_subtraction_exceptions"] += 1
                if "'>' not supported between instances of 'NoneType' and 'int'" in line:
                    metrics["none_compare_exceptions"] += 1
                if "BUG_BLOCKED" in line:
                    metrics["bug_blocked_lines"] += 1
                failure_match = _GATE_FAILURES.search(line)
                if failure_match and current_stage:
                    failures = failure_match.group(1)
                    if (
                        "margin_bp<=" in failures
                        and "sharpe<=" not in failures
                        and "fitness<=" not in failures
                        and "sharpe_2y<=" not in failures
                        and "turnover不在" not in failures
                    ):
                        metrics[f"stage{current_stage}_margin_ready_records"] += 1
                if re.search(r"平台.*(?:跳过SC|跳过 SC)", line, re.IGNORECASE):
                    metrics["platform_blocked_sc_lines"] += 1
                if "模板批次仍为 PENDING" in line:
                    metrics["pending_reschedules"] += 1
                if "429" in line and "Multi-Simulation" in line:
                    metrics["rate_limit_lines"] += 1
    slots = metrics["backtest_slots"]
    pending_log_lines = metrics["pending_reschedules"]
    result = {
        **dict(metrics),
        "parent_batches": slots // 8,
        "python_none_exceptions": (
            metrics["none_format_exceptions"] + metrics["none_subtraction_exceptions"]
            + metrics["none_compare_exceptions"]
        ),
        "pending_cycles": pending_log_lines // 2,
        "incomplete_7_of_8_sources": len(incomplete_by_source),
        "projected_block_records": len(incomplete_by_source),
        "projected_eliminated_7_of_8_reschedules": max(
            0, metrics["incomplete_7_of_8"] - len(incomplete_by_source)
        ),
        "stage2_cumulative_batch_blocked_sources": sorted(stage2_blocked_sources),
        "stage3_full_pass_per_1000_backtests": (
            1000 * metrics["stage3_pass"] / slots if slots else 0.0
        ),
    }
    for stage in (1, 2, 3):
        scored = metrics[f"stage{stage}_scored"]
        observable = metrics[f"stage{stage}_fully_observable"]
        passed = metrics[f"stage{stage}_pass"]
        result[f"stage{stage}_all_result_pass_rate"] = passed / scored if scored else 0.0
        result[f"stage{stage}_observable_pass_rate"] = passed / observable if observable else 0.0
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(replay(args.log_dir), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
