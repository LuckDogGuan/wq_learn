#!/usr/bin/env python3
"""Preview, verify or launch the Route ④ Codex CLI controller."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "wq_research_v2" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from wq_research_v2.alphaforge_v4 import (  # noqa: E402
    TRACK_ID,
    TRACK_LOG_PREFIX,
    build_controller_prompt,
    build_startup_handoff,
)

DSH_TOOLS = ("dsh_worker_config", "dsh_worker_probe", "dsh_run_worker")


def verify_dsh_events(events: list[dict[str, Any]], profile: dict[str, Any]) -> dict[str, Any]:
    receipts = {}
    for event in events:
        if event["type"] != "item.completed":
            continue
        item = event["item"]
        if item["type"] != "mcp_tool_call" or item["server"] != "dsh_crew":
            continue
        if len(receipts) == len(DSH_TOOLS) or item["tool"] != DSH_TOOLS[len(receipts)]:
            continue
        if item["status"] != "completed":
            return {"ok": False, "step": item["tool"], "error": item.get("error")}
        result = item["result"]
        receipts[item["tool"]] = result["structured_content"] or json.loads(result["content"][0]["text"])

    if len(receipts) < len(DSH_TOOLS):
        return {"ok": False, "step": DSH_TOOLS[len(receipts)], "error": "No completed tool event"}

    provider, model = profile["default_provider"], profile["default_model"]
    binding, probe, worker = receipts.values()
    flash = binding.get("bindings", {}).get("flash", {})
    if not (
        binding.get("mode") == "hub" and binding.get("enabled") is True
        and binding.get("escalate_on_failure") is False
        and (flash.get("provider"), flash.get("model")) == (provider, model)
    ):
        return {"ok": False, "step": DSH_TOOLS[0], "error": "Hub binding did not match the configured flash worker"}
    if not (probe.get("tool_call_verified") is True and (probe.get("provider"), probe.get("model")) == (provider, model)):
        return {"ok": False, "step": DSH_TOOLS[1], "error": "The configured worker route did not verify tool calls"}
    if not (
        worker.get("status") == "done" and worker.get("id") and worker.get("toolCalls", 0) > 0
        and (worker.get("provider"), worker.get("model")) == (provider, model)
        and TRACK_ID in (worker.get("result") or "")
    ):
        return {
            "ok": False, "step": DSH_TOOLS[2], "job_id": worker.get("id"),
            "status": worker.get("status"), "error": worker.get("error") or "Missing verified worker result",
        }
    return {
        "ok": True, "job_id": worker["id"], "session_id": worker.get("sessionId"),
        "provider": provider, "model": model, "status": worker["status"],
        "tokens": worker.get("tokens"), "tool_calls": worker["toolCalls"],
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="launch_alphaforge_v4",
        description="Launch or preview AlphaForge Route ④ via Codex CLI.",
    )
    p.add_argument("--region")
    p.add_argument("--universe")
    p.add_argument("--dataset", default="")
    p.add_argument("--failure", default="", help="Optional bottleneck code (e.g. HIGH_PC, LOW_2Y_SHARPE)")
    p.add_argument("--goal", default="执行 Route ④ 锻造闭环巡检、失败归因与单轴推进")
    p.add_argument("--effort", choices=["low", "medium", "high", "xhigh"])
    p.add_argument("--model", default=None)
    p.add_argument("--timeout", type=int, help="Optional timeout in seconds")
    p.add_argument("--log-file", type=Path, default=None)
    p.add_argument("--codex-bin", default=None, help="Override path to the Codex CLI executable")
    p.add_argument("--show-prompt", action="store_true", help="Include the full prompt in a dry run")
    run = p.add_mutually_exclusive_group()
    run.add_argument("--execute", action="store_true", help="Run the research controller")
    run.add_argument("--verify", action="store_true", help="Verify Codex CLI and its compact handoff")
    run.add_argument("--verify-dsh", action="store_true", help="Also verify the DSH calls from inside Codex CLI")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = build_parser()
    args = parser.parse_args(argv)
    controller = json.loads(
        (REPO_ROOT / "docs/alphaforge_v4/alphaforge_v4_config.json").read_text(encoding="utf-8-sig")
    )["orchestration"]["main_controller"]
    run_config = json.loads((REPO_ROOT / "goal/run_config.json").read_text(encoding="utf-8-sig"))
    profile = run_config["subagent_profile"]
    app_cli = os.environ.get("CODEX_APP_RUNTIME_CLI_PATH")
    codex_exe = args.codex_bin or (app_cli if app_cli and Path(app_cli).is_file() else None)
    codex_exe = codex_exe or shutil.which(controller["cli_binary"])
    verifying = args.verify or args.verify_dsh
    running = args.execute or verifying
    log_file = args.log_file
    if running and log_file is None:
        run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        log_file = REPO_ROOT / "data" / "alphaforge_v4_runs" / f"{run_stamp}.log"
    if verifying:
        handoff = json.dumps(build_startup_handoff(), ensure_ascii=False, separators=(",", ":"))
        prompt = (
            "路线④只读验收。使用启动器已读取的 handoff，无需运行终端或重读文件。"
            "回传 default_track_id、一个有效和一个无效案例编号。\n"
            f"{handoff}\n"
        )
        if args.verify_dsh:
            read_command = (
                'python -B -X utf8 -c "import json; '
                "print(json.load(open('goal/run_config.json', encoding='utf-8-sig'))['default_track_id'])\""
            )
            prompt += (
                "用 dsh_crew 调用 dsh_worker_config（enabled=true, mode=hub, escalate_on_failure=false, "
                f"flash_provider={profile['default_provider']}, flash_model={profile['default_model']}），再对同一 provider/model 调 "
                "dsh_worker_probe(tier=flash)。探测成功后用 dsh_run_worker 派一个 flash/high worker，timeout_seconds=90。"
                f"派单 cwd={REPO_ROOT}，将以下任务原样传给子代理：\n"
                "仅使用终端执行一次下列只读命令，回传 stdout 的原始值。终端是允许的读取方式。"
                "禁止修改文件、读其他文件、访问 BRAIN、下发回测或派生子代理。\n"
                f"```\n{read_command}\n```\n"
                "汇报 probe 和真实 job ID/status/token。若任一步失败，报告失败步骤并省略成功标记。\n"
            )
        else:
            prompt += "直接回答，无需调用工具。\n"
        prompt += "仅在要求的核验完成时另起一行输出 ALPHAFORGE_VERIFY_OK。"
    else:
        direction = run_config["direction"]
        region = (args.region or direction["regions"][0]).upper()
        universe = args.universe or direction["universes"].get(region)
        if universe is None:
            parser.error(f"--universe is required for region {region}")
        prompt = build_controller_prompt(
            region=region,
            universe=universe,
            dataset_id=args.dataset,
            goal=args.goal,
            failure_code=args.failure,
        )
    effort = args.effort or ("low" if verifying else controller["default_effort"])
    cmd = [
        codex_exe or controller["cli_binary"], "exec", "--color", "never",
        "--sandbox", "read-only" if verifying else "workspace-write",
        "-c", f'model_reasoning_effort="{effort}"',
    ]
    if args.model:
        cmd.extend(["--model", args.model])
    if args.verify_dsh or args.execute:
        for tool in DSH_TOOLS:
            cmd.extend(["-c", f'mcp_servers.dsh_crew.tools.{tool}.approval_mode="approve"'])
        cmd.extend(["-c", f"mcp_servers.dsh_crew.tool_timeout_sec={120 if args.verify_dsh else 7230}"])
    if args.verify_dsh:
        cmd.append("--json")
    cmd.append("-")

    summary = {
        "track_id": TRACK_ID,
        "log_prefix": TRACK_LOG_PREFIX,
        "workspace": str(REPO_ROOT),
        "codex_executable_detected": codex_exe,
        "log_file": str(log_file) if log_file else None,
        "prompt_bytes": len(prompt.encode("utf-8")),
        "mode": "VERIFY_DSH" if args.verify_dsh else "VERIFY" if args.verify else "EXECUTE" if args.execute else "DRY_RUN_PREVIEW",
        "command_preview": cmd,
    }
    print(json.dumps(summary, ensure_ascii=False), flush=True)

    if not running:
        if args.show_prompt:
            print(prompt)
        return 0

    if not codex_exe:
        print("[ERROR] Codex CLI was not found in PATH.", file=sys.stderr)
        return 2

    runtime_log = REPO_ROOT / log_file
    runtime_log.parent.mkdir(parents=True, exist_ok=True)
    if runtime_log.exists():
        raise SystemExit(f"Log file already exists: {runtime_log}")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(SRC_DIR), env.get("PYTHONPATH", "")]))
    with runtime_log.open("xb") as log:
        proc = subprocess.run(
            cmd, cwd=REPO_ROOT, env=env, input=prompt, stdout=subprocess.PIPE, stderr=log,
            encoding="utf-8", errors="replace", timeout=args.timeout or (180 if verifying else None),
        )
        log.write(proc.stdout.encode("utf-8"))
    if args.verify_dsh:
        events = [json.loads(line) for line in proc.stdout.splitlines() if line.startswith("{")]
        receipt = verify_dsh_events(events, profile)
        print(json.dumps(receipt, ensure_ascii=False))
        return proc.returncode or (0 if receipt["ok"] else 1)
    print(proc.stdout, end="")
    if verifying and proc.returncode == 0 and "ALPHAFORGE_VERIFY_OK" not in proc.stdout.splitlines():
        return 1
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
