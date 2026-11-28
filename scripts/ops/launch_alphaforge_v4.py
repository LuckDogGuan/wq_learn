#!/usr/bin/env python3
"""Preview, verify or launch the Route ④ Antigravity controller."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "wq_research_v2" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from wq_research_v2.alphaforge_v4 import (  # noqa: E402
    TRACK_ID,
    TRACK_LOG_PREFIX,
    build_agy_cli_command,
    build_agy_main_prompt,
    locate_agy_executable,
)
from wq_research_v2.experience_reuser import ExperienceReuser  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="launch_alphaforge_v4",
        description="Launch or preview Route ④ (AlphaForge AGY-DSH v4.0) via Antigravity CLI (`agy`).",
    )
    p.add_argument("--region", default="USA")
    p.add_argument("--universe", default="TOP3000")
    p.add_argument("--dataset", default="")
    p.add_argument("--failure", default="", help="Optional bottleneck code (e.g. HIGH_PC, LOW_2Y_SHARPE)")
    p.add_argument("--goal", default="执行 Route ④ 锻造闭环巡检、失败归因与单轴推进")
    p.add_argument("--interactive", action="store_true", help="Launch agy in interactive mode (-i)")
    p.add_argument("--mode", default="accept-edits", choices=["accept-edits", "auto", "plan"])
    p.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    p.add_argument("--model", default=None)
    p.add_argument("--print-timeout", default=None, help="Optional timeout for --print mode (e.g. 30m)")
    p.add_argument("--log-file", type=Path, default=None)
    p.add_argument("--agy-bin", default=None, help="Override path to agy executable")
    p.add_argument("--show-prompt", action="store_true", help="Include the full prompt in a dry run")
    run = p.add_mutually_exclusive_group()
    run.add_argument("--execute", action="store_true", help="Run the research controller")
    run.add_argument("--verify", action="store_true", help="Run a read-only controller and DSH smoke test")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    args = build_parser().parse_args(argv)
    if args.verify and args.interactive:
        raise SystemExit("--verify requires a non-interactive run")
    reuser = None if args.verify else ExperienceReuser()
    agy_exe = args.agy_bin or locate_agy_executable()
    running = args.execute or args.verify
    log_file = args.log_file
    if running and log_file is None:
        run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        log_file = REPO_ROOT / "data" / "alphaforge_v4_runs" / f"{run_stamp}.log"
    if args.verify:
        prompt = (
            "路线④只读验收，禁止写文件、回测、访问 BRAIN、读凭据、改守护进程。"
            "用终端执行 python -m wq_research_v2 forge handoff，核对 default_track_id=alphaforge_agy_dsh_v4。"
            "用 dsh-crew 绑定 hub/flash（enabled=true, mode=hub, escalate_on_failure=false, "
            "flash_provider=dsh-opencode-go, flash_model=deepseek-v4.1-flash），然后对相同 provider/model 调 "
            "dsh_worker_probe。仅在 tool_call_verified=true 时派一个 flash/high worker，timeout_seconds=60，"
            f"任务仅只读核对 {REPO_ROOT / 'goal/run_config.json'} 的 default_track_id 并回传值，不准递归。"
            "汇报最多四行，逐项给出 handoff、probe、真实派单 job ID/status 与 token（若有），明确失败步骤。"
            "只有三项都观察成功时才另起一行输出 ALPHAFORGE_VERIFY_OK。"
        )
    else:
        prompt = build_agy_main_prompt(
            region=args.region,
            universe=args.universe,
            dataset_id=args.dataset,
            goal=args.goal,
            failure_code=args.failure,
            reuser=reuser,
        )
    cmd = build_agy_cli_command(
        prompt,
        agy_bin=agy_exe or "agy",
        interactive=bool(args.interactive),
        mode="plan" if args.verify else args.mode,
        effort=args.effort,
        model=args.model,
        print_timeout=args.print_timeout or ("3m" if args.verify else None),
        log_file=log_file,
    )

    summary = {
        "track_id": TRACK_ID,
        "log_prefix": TRACK_LOG_PREFIX,
        "workspace": str(REPO_ROOT),
        "agy_executable_detected": agy_exe,
        "prompt_bytes": len(prompt.encode("utf-8")),
        "mode": "VERIFY" if args.verify else "EXECUTE" if args.execute else "DRY_RUN_PREVIEW",
        "command_preview": cmd[:-1] + [f"<prompt:{len(prompt)} chars>"],
    }
    print(json.dumps(summary, ensure_ascii=False), flush=True)

    if not running:
        if args.show_prompt:
            print(prompt)
        return 0

    if not agy_exe:
        print("[ERROR] Antigravity CLI (`agy`) not found in PATH or ~/.gemini/bin/agy(.exe).", file=sys.stderr)
        return 2

    if log_file is not None:
        runtime_log = REPO_ROOT / log_file
        runtime_log.parent.mkdir(parents=True, exist_ok=True)
        if runtime_log.exists():
            raise SystemExit(f"Log file already exists: {runtime_log}")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(SRC_DIR), env.get("PYTHONPATH", "")]))
    if args.verify:
        proc = subprocess.run(cmd, cwd=REPO_ROOT, env=env, stdout=subprocess.PIPE, encoding="utf-8", errors="replace")
        print(proc.stdout, end="")
        return proc.returncode or (0 if "ALPHAFORGE_VERIFY_OK" in proc.stdout.splitlines() else 1)
    return subprocess.run(cmd, cwd=REPO_ROOT, env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
