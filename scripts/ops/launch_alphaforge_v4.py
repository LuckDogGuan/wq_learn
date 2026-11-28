#!/usr/bin/env python3
"""Cross-platform launcher for Route ④ (`alphaforge_agy_dsh_v4`) using Antigravity CLI (`agy`) + DSH subagents.

Safe by default (dry-run): prints preflight status, detected `agy` binary, injected historical
experience summary, and the exact `agy` command argv. Pass `--execute` to actually launch `agy`.

Never calls `/submit`, never reads credentials, never modifies existing production daemons.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
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
    p.add_argument("--execute", action="store_true", help="Actually invoke agy (default is dry-run preview)")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    args = build_parser().parse_args(argv)
    reuser = ExperienceReuser()
    agy_exe = args.agy_bin or locate_agy_executable()

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
        mode=args.mode,
        effort=args.effort,
        model=args.model,
        print_timeout=args.print_timeout,
        log_file=args.log_file,
    )

    summary = {
        "track_id": TRACK_ID,
        "log_prefix": TRACK_LOG_PREFIX,
        "workspace": str(REPO_ROOT),
        "agy_executable_detected": agy_exe,
        "experience_sources_loaded": reuser.sources_status(),
        "prompt_bytes": len(prompt.encode("utf-8")),
        "mode": "EXECUTE" if args.execute else "DRY_RUN_PREVIEW",
        "command_preview": cmd[:-1] + [f"<prompt:{len(prompt)} chars>"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if not args.execute:
        print("\n--- AGY MAIN CONTROLLER PROMPT PREVIEW ---")
        print(prompt)
        print("--- END PREVIEW (pass --execute to run agy) ---")
        return 0

    if not agy_exe:
        print("[ERROR] Antigravity CLI (`agy`) not found in PATH or ~/.gemini/bin/agy(.exe).", file=sys.stderr)
        return 2

    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
