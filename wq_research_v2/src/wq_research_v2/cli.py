"""Unified CLI entrypoint for wq_research_v2 (strictly ZERO /submit command)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from wq_research_v2.ablation_engine import build_dual_branch_ablation
from wq_research_v2.alphaforge_v4 import (
    attribute_ppa_first_routing,
    build_agy_cli_command,
    build_controller_prompt,
    build_dsh_subagent_brief,
    build_platform_day_funnel,
    build_startup_handoff,
    evaluate_dispatch_preflight,
    locate_agy_executable,
    select_three_plus_one_roster,
)
from wq_research_v2.auth_session import BrainAuthSession
from wq_research_v2.blacklist_registry import BlacklistRegistry
from wq_research_v2.experience_reuser import ExperienceReuser
from wq_research_v2.expr_validator import ExprValidator
from wq_research_v2.field_screener import FieldScreener
from wq_research_v2.ledger_store import LedgerStore
from wq_research_v2.legacy_merger import (
    merge_all_legacy_to_v2,
    query_legacy_candidates,
    summarize_legacy_pool,
)
from wq_research_v2.pc_poller import PCPoller
from wq_research_v2.pyramid_planner import build_stage0_probe_spec
from wq_research_v2.quota_tracker import QuotaTracker, current_est_platform_date
from wq_research_v2.sa_runner import (
    SA_TRACK_ID,
    SaOwnLedger,
    SaRunner,
    build_sa_payload,
)
from wq_research_v2.sc_local import LocalSCEngine
from wq_research_v2.sim_runner import SimRunner
from wq_research_v2.tagger import USEFUL_TAG, apply_alpha_tag


def _parse_csv(raw: str) -> list[str]:
    return [x.strip() for x in raw.replace(";", ",").split(",") if x.strip()]


def _sa_simulation_capability(auth: BrainAuthSession) -> dict[str, Any]:
    resp = auth.request("OPTIONS", "/simulations", timeout=30)
    if resp.status_code != 200:
        return {"super_simulation_available": None, "simulation_options_http": resp.status_code}
    choices = resp.json().get("actions", {}).get("POST", {}).get("type", {}).get("choices")
    if not choices:
        return {"super_simulation_available": None}
    supported = [choice["value"] for choice in choices]
    return {"super_simulation_available": "SUPER" in supported, "simulation_types": supported}


def _sa_status(auth: BrainAuthSession, region: str) -> dict[str, Any]:
    """Read-only SuperAlpha eligibility query (never prints credentials): genius level +
    submitted REGULAR alpha count + existing SUPER alpha count."""
    out: dict[str, Any] = {"region": region.upper()}
    try:
        prof = auth.get("/users/self", timeout=30)
        if prof.status_code == 200:
            out["genius_level"] = prof.json().get("geniusLevel")
        else:
            out["profile_http"] = prof.status_code
    except Exception as exc:  # pragma: no cover - live network
        out["profile_error"] = type(exc).__name__

    try:
        r = auth.get(
            "/users/self/alphas?limit=1&type=REGULAR&status=ACTIVE",
            timeout=30,
        )
        if r.status_code == 200:
            out["active_regular_count"] = r.json().get("count")
        else:
            out["regular_count_http"] = r.status_code
    except Exception as exc:  # pragma: no cover - live network
        out["regular_count_error"] = type(exc).__name__

    try:
        r = auth.get("/users/self/alphas?limit=1&hidden=false&type=SUPER", timeout=30)
        if r.status_code == 200:
            out["super_alpha_count"] = r.json().get("count")
        else:
            out["sa_count_http"] = r.status_code
    except Exception as exc:  # pragma: no cover - live network
        out["sa_count_error"] = type(exc).__name__
    out.update(_sa_simulation_capability(auth))
    return out


def _sa_ammo(auth: BrainAuthSession, region: str, limit: int) -> dict[str, Any]:
    """Read-only SuperAlpha 'own 弹药库' listing: submitted REGULAR D1 alphas for a region."""
    reg = region.upper()
    params = {
        "limit": max(1, min(500, limit)),
        "type": "REGULAR",
        "status": "ACTIVE",
        "settings.delay": 1,
        "settings.region": reg,
        "order": "-is.sharpe",
    }
    try:
        resp = auth.get("/users/self/alphas", params=params, timeout=30)
        if resp.status_code != 200:
            return {"region": reg, "http": resp.status_code}
        data = resp.json()
        rows = []
        for a in data.get("results") or []:
            ism = a.get("is") or {}
            rows.append(
                {
                    "id": a.get("id"),
                    "name": a.get("name"),
                    "sharpe": ism.get("sharpe"),
                    "fitness": ism.get("fitness"),
                    "prod_correlation": ism.get("prodCorrelation"),
                }
            )
        return {"region": reg, "count": data.get("count"), "results": rows}
    except Exception as exc:  # pragma: no cover - live network
        return {"region": reg, "error": type(exc).__name__}


def _run_sa_command(args: argparse.Namespace) -> int:
    if args.action == "resume":
        ledger = SaOwnLedger()
        try:
            pending = ledger.get_resumable_tasks()
            print(json.dumps({"resumable_count": len(pending), "task_ids": [task["task_id"] for task in pending[:20]]}, indent=2))
            return 0
        finally:
            ledger.close()

    if args.action == "run" and not args.spec:
        raise SystemExit("--spec is required for sa run")
    quota = QuotaTracker()
    auth = BrainAuthSession(quota_observer=quota.observe_response)
    try:
        auth.authenticate()
        if args.action == "status":
            out = _sa_status(auth, args.region)
        elif args.action == "ammo":
            out = _sa_ammo(auth, args.region, args.limit)
        else:
            capability = _sa_simulation_capability(auth)
            if capability["super_simulation_available"] is not True:
                print(json.dumps(capability, indent=2))
                return 1
            spec = json.loads(args.spec.read_text(encoding="utf-8"))
            ledger = SaOwnLedger()
            try:
                runner = SaRunner(auth, ledger, quota, daily_budget=args.budget, max_workers=args.workers)
                batch_id, runnable, skipped = runner.prepare_batch_tasks(spec)
                result = runner.run_prepared_tasks(batch_id, runnable)
                out = {"batch_id": batch_id, "skipped": len(skipped), **result}
            finally:
                ledger.close()
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return int(bool(out.get("errors") or out.get("unobserved")))
    finally:
        auth.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="wq_research_v2", description="WorldQuant BRAIN D1-Only Research Engine")
    sub = p.add_subparsers(dest="cmd", required=True)

    # auth
    p_auth = sub.add_parser("auth", help="Verify credentials and TLS session")
    p_auth.add_argument("action", choices=["check"])

    # screen
    p_scr = sub.add_parser("screen", help="Stage-0 WebDataScope D1 + Huazi Ge gap field screening")
    p_scr.add_argument("target", choices=["fields"])
    p_scr.add_argument("--region", default="GLB,ASI,CHN,DEU,GBR")
    p_scr.add_argument("--top", type=int, default=15)
    p_scr.add_argument("--export", action="store_true")
    p_scr.add_argument("--out", type=Path, default=None)

    # validate
    p_val = sub.add_parser("validate", help="Run 10-gate static FASTEXPR D1 validator")
    p_val.add_argument("--expr", required=True)
    p_val.add_argument("--region", default="DEU")
    p_val.add_argument("--universe", default="TOP500")
    p_val.add_argument("--delay", type=int, default=1)
    p_val.add_argument("--neut", default="INDUSTRY")
    p_val.add_argument("--queue", default="NORMAL", choices=["NORMAL", "UNUSED_ALPHA0"])

    # plan
    p_plan = sub.add_parser("plan", help="Generate 5:5 balanced Stage-0 probe spec")
    p_plan.add_argument("target", choices=["batch"])
    p_plan.add_argument("--region", required=True)
    p_plan.add_argument("--universe", required=True)
    p_plan.add_argument("--dataset", required=True)
    p_plan.add_argument("--field", required=True)
    p_plan.add_argument("--field-type", default="MATRIX", choices=["MATRIX", "VECTOR"])
    p_plan.add_argument("--queue", default="NORMAL", choices=["NORMAL", "UNUSED_ALPHA0"])
    p_plan.add_argument("--out", type=Path, default=None)

    # sc
    p_sc = sub.add_parser("sc", help="Portable local SC cache sync, check, and N×N candidate matrix")
    p_sc.add_argument("action", choices=["sync", "check", "matrix"])
    p_sc.add_argument("--alpha-id", default=None)
    p_sc.add_argument("--alpha-ids", default="")
    p_sc.add_argument("--region", default="GBR")
    p_sc.add_argument("--pool", default="REGULAR_ALL", choices=["REGULAR_ALL", "REGULAR_NO_PPA", "PPAC_ONLY"])
    p_sc.add_argument("--max-pair", type=float, default=0.68)

    # pc
    p_pc = sub.add_parser("pc", help="Read-only remote PC & Alpha Pre-Submission Check poller")
    p_pc.add_argument("action", choices=["check"])
    p_pc.add_argument("--alpha-ids", required=True)
    p_pc.add_argument("--region", default="GBR")

    # tag (Guangzhou-style Useful / SC_PASS / SC_IS_HIGHT / PC_IS_HIGHT tagging + optional SC/PC alias; dry-run by default)
    p_tag = sub.add_parser("tag", help="Preview or apply Useful/SC_PASS/SC_IS_HIGHT/PC_IS_HIGHT tag & alias (dry-run by default)")
    p_tag.add_argument("action", choices=["apply"])
    p_tag.add_argument("--alpha-ids", required=True)
    p_tag.add_argument("--tag", default=USEFUL_TAG, choices=["Useful", "SC_PASS", "SC_IS_HIGHT", "PC_IS_HIGHT"])
    p_tag.add_argument("--name", default=None, help="Optional alpha alias (e.g. 'SC 0.360 PC 0.782')")
    p_tag.add_argument("--confirm-apply", action="store_true", help="Explicit confirmation required to send PATCH")

    # ablate
    p_ab = sub.add_parser("ablate", help="Generate Decision #3 compliant dual-branch min(rank,rank) ablation")
    p_ab.add_argument("action", choices=["dual"])
    p_ab.add_argument("--expr-a", required=True)
    p_ab.add_argument("--expr-b", required=True)
    p_ab.add_argument("--region", default="DEU")
    p_ab.add_argument("--universe", default="TOP500")

    # blacklist
    p_bl = sub.add_parser("blacklist", help="Inspect or restore scoped demotions/blacklists")
    p_bl.add_argument("action", choices=["list", "restore"])
    p_bl.add_argument("--status", default="ACTIVE")
    p_bl.add_argument("--record-id", default=None)
    p_bl.add_argument("--reason", default="")

    # report
    p_rep = sub.add_parser("report", help="Generate EST platform-day volume report")
    p_rep.add_argument("action", choices=["daily"])
    p_rep.add_argument("--date", default=None)

    # sim
    p_sim = sub.add_parser("sim", help="Run prepared D1 spec JSON or resume checkpoints")
    p_sim.add_argument("action", choices=["run", "resume"])
    p_sim.add_argument("--spec", type=Path, default=None)
    p_sim.add_argument("--mode", default="FULL", choices=["QUICK", "FULL"])
    p_sim.add_argument("--slots", type=int, default=2)
    p_sim.add_argument("--batch-size", type=int, default=8)

    # legacy (read-only merge from legacy_core/Core/runtime_data into wq_v2_ledger.db + D1 screening)
    p_leg = sub.add_parser("legacy", help="Read-only merge and D1 screening of legacy_core historical data")
    p_leg.add_argument("action", choices=["merge", "screen", "stats"])
    p_leg.add_argument("--region", default="", help="Comma-separated regions (e.g. USA,EUR,GBR,GLB)")
    p_leg.add_argument("--tier", default="", help="Comma-separated opt_tiers")
    p_leg.add_argument("--min-sharpe", type=float, default=1.40)
    p_leg.add_argument("--max-sc", type=float, default=0.68)
    p_leg.add_argument("--only-compliant", action="store_true")
    p_leg.add_argument("--top", type=int, default=25)

    # forge (Route ④: AlphaForge AGY-DSH v4.0 offline guards, experience reuse, funnel, DSH brief & agy CLI builder)
    p_fg = sub.add_parser(
        "forge",
        help="Route ④ (alphaforge_agy_dsh_v4): experience reuse, P0/P1/P2 guards, funnel, DSH brief & agy command",
    )
    p_fg.add_argument(
        "action",
        choices=["handoff", "experience", "preflight", "funnel", "ppa-check", "dsh-brief", "agy-cmd", "roster"],
    )
    p_fg.add_argument("--region", default="USA")
    p_fg.add_argument("--universe", default="TOP3000")
    p_fg.add_argument("--dataset", default="")
    p_fg.add_argument("--neut", default="")
    p_fg.add_argument("--failure", default="")
    p_fg.add_argument("--ops", default="", help="Comma-separated operator names")
    p_fg.add_argument("--queue", default="NORMAL", choices=["NORMAL", "UNUSED_ALPHA0"])
    p_fg.add_argument("--normal-completed", type=int, default=0)
    p_fg.add_argument("--threshold", type=int, default=4500)
    p_fg.add_argument("--threads", type=int, default=2)
    p_fg.add_argument("--stage", default="STAGE_3")
    p_fg.add_argument("--mode", default="FULL", choices=["QUICK", "FULL"])
    p_fg.add_argument("--expr", default=None)
    p_fg.add_argument("--db", type=Path, default=Path("data/wq_v2_ledger.db"))
    p_fg.add_argument("--date", default=None)
    p_fg.add_argument("--target-track", default="RA", choices=["RA", "PPA"])
    p_fg.add_argument("--goal", default="执行 Route ④ 锻造闭环巡检、失败归因与单轴推进")
    p_fg.add_argument("--evidence", default="", help="Comma-separated read-only evidence paths")
    p_fg.add_argument("--interactive", action="store_true")
    p_fg.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    p_fg.add_argument("--model", default=None)
    p_fg.add_argument("--input", type=Path, default=None, help="JSON candidate list for 3+1 roster")
    p_fg.add_argument("--json", dest="as_json", action="store_true")

    # sa (Route ⑤: super_alpha_own_v1 — SuperAlpha backtest + read-only ammo/status, isolated ledger)
    p_sa = sub.add_parser("sa", help="Route ⑤ SuperAlpha backtest (preview/run/resume) + read-only status/ammo")
    p_sa.add_argument("action", choices=["preview", "run", "resume", "status", "ammo"])
    p_sa.add_argument("--spec", type=Path, default=None, help="JSON spec {region, universe, selection, combo, settings, items[]}")
    p_sa.add_argument("--region", default="EUR", help="Region for status/ammo (default EUR)")
    p_sa.add_argument("--universe", default="TOP2500", help="Universe for ammo/status")
    p_sa.add_argument("--budget", type=int, default=400, help="SuperAlpha daily simulation budget")
    p_sa.add_argument("--workers", type=int, default=3, help="SuperAlpha concurrency (max 3)")
    p_sa.add_argument("--limit", type=int, default=100, help="Read-only ammo list page size")

    return p


def main(argv: Optional[list[str]] = None) -> int:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    args = build_parser().parse_args(argv)

    if args.cmd == "validate":
        settings = {
            "region": args.region.upper(),
            "universe": args.universe.upper(),
            "delay": args.delay,
            "neutralization": args.neut.upper(),
            "visualization": False,
        }
        rep = ExprValidator().validate(args.expr, settings, queue_type=args.queue)
        print(json.dumps(rep.__dict__, indent=2, ensure_ascii=False))
        return 0 if rep.valid else 2

    if args.cmd == "screen":
        screener = FieldScreener()
        res = screener.screen_regions_offline(_parse_csv(args.region), top_datasets_per_region=args.top)
        if args.export:
            out = screener.export_queue(res, out_path=args.out)
            print(f"Exported Stage-0 D1 queue to: {out}")
        summary = {
            reg: {
                "status": info["status"],
                "selected_count": info["selected_count"],
                "top5": [d["dataset_id"] for d in info["datasets"][:5]],
            }
            for reg, info in res["regions"].items()
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    if args.cmd == "plan":
        ledger = LedgerStore()
        try:
            bl = BlacklistRegistry(ledger)
            spec = build_stage0_probe_spec(
                region=args.region, universe=args.universe, dataset_id=args.dataset,
                field_id=args.field, field_type=args.field_type, queue_type=args.queue,
                blacklist=bl,
            )
            txt = json.dumps(spec, indent=2, ensure_ascii=False)
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(txt, encoding="utf-8")
                print(f"Wrote spec to {args.out}")
            else:
                print(txt)
            return 0
        finally:
            ledger.close()

    if args.cmd == "ablate":
        items = build_dual_branch_ablation(
            args.expr_a, args.expr_b, region=args.region, universe=args.universe,
            base_settings={"neutralization": "INDUSTRY", "decay": 0},
        )
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return 0

    if args.cmd == "blacklist":
        ledger = LedgerStore()
        try:
            bl = BlacklistRegistry(ledger)
            if args.action == "list":
                print(json.dumps(bl.list_records(status=args.status), indent=2, ensure_ascii=False))
            elif args.action == "restore":
                if not args.record_id:
                    raise SystemExit("--record-id is required")
                print(json.dumps(bl.restore(args.record_id, args.reason), indent=2, ensure_ascii=False))
            return 0
        finally:
            ledger.close()

    if args.cmd == "report":
        ledger = LedgerStore()
        try:
            est_day = args.date or current_est_platform_date()
            print(json.dumps(ledger.compute_daily_summary(est_day), indent=2, ensure_ascii=False))
            return 0
        finally:
            ledger.close()

    if args.cmd == "legacy":
        if args.action == "merge":
            res = merge_all_legacy_to_v2()
            print(json.dumps(res, indent=2, ensure_ascii=False))
            return 0
        if args.action == "stats":
            print(json.dumps(summarize_legacy_pool(), indent=2, ensure_ascii=False))
            return 0
        if args.action == "screen":
            rows = query_legacy_candidates(
                regions=_parse_csv(args.region) if args.region else None,
                tiers=_parse_csv(args.tier) if args.tier else None,
                min_sharpe=args.min_sharpe,
                max_sc=args.max_sc,
                only_compliant=bool(args.only_compliant),
                limit=args.top,
            )
            print(json.dumps(rows, indent=2, ensure_ascii=False))
            return 0

    if args.cmd == "forge":
        if args.action == "handoff":
            print(json.dumps(build_startup_handoff(), ensure_ascii=False, indent=2))
            return 0
        reuser = ExperienceReuser()
        if args.action == "experience":
            pkt = reuser.retrieve(
                region=args.region,
                universe=args.universe,
                dataset_id=args.dataset,
                neutralization=args.neut,
                failure_code=args.failure,
                operators=_parse_csv(args.ops) if args.ops else [],
            )
            if args.as_json:
                print(json.dumps(pkt.to_dict(), indent=2, ensure_ascii=False))
            else:
                print(pkt.render_compact_markdown())
            return 0
        if args.action == "preflight":
            settings = (
                {
                    "region": args.region.upper(),
                    "universe": args.universe.upper(),
                    "delay": 1,
                    "neutralization": (args.neut or "SUBINDUSTRY").upper(),
                    "visualization": False,
                }
                if args.expr
                else None
            )
            res = evaluate_dispatch_preflight(
                region=args.region,
                queue_type=args.queue,
                normal_completed_today=args.normal_completed,
                alpha0_switch_threshold=args.threshold,
                requested_threads=args.threads,
                expression=args.expr,
                settings=settings,
                stage=args.stage,
                simulation_mode=args.mode,
                db_path=args.db,
            )
            print(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
            return 0 if res.allowed else 2
        if args.action == "funnel":
            rep = build_platform_day_funnel(args.db, est_platform_date=args.date)
            print(json.dumps(rep, indent=2, ensure_ascii=False))
            return 0
        if args.action == "ppa-check":
            if not args.expr:
                raise SystemExit("--expr is required for forge ppa-check")
            rep = attribute_ppa_first_routing(args.expr, target_track=args.target_track)
            print(json.dumps(rep, indent=2, ensure_ascii=False))
            return 0
        if args.action == "dsh-brief":
            brief = build_dsh_subagent_brief(
                task_goal=args.goal,
                region=args.region,
                universe=args.universe,
                dataset_id=args.dataset or "UNSPECIFIED",
                readonly_evidence=_parse_csv(args.evidence) if args.evidence else [],
                acceptance_criteria=[
                    "独立核对母版、设置、数值指标与历史经验适用边界",
                    "返回 [V]/[R]/[C]/[U] 分级证据与最多 1 条单轴可证伪假设",
                ],
                failure_code=args.failure,
                neutralization=args.neut,
                operators=_parse_csv(args.ops) if args.ops else [],
                reuser=reuser,
            )
            print(brief)
            return 0
        if args.action == "agy-cmd":
            prompt = build_controller_prompt(
                region=args.region,
                universe=args.universe,
                dataset_id=args.dataset,
                goal=args.goal,
                failure_code=args.failure,
                controller="Antigravity CLI (agy)",
                reuser=reuser,
            )
            cmd = build_agy_cli_command(
                prompt,
                interactive=bool(args.interactive),
                effort=args.effort,
                model=args.model,
            )
            print(
                json.dumps(
                    {
                        "agy_executable_detected": locate_agy_executable(),
                        "argv": cmd,
                        "prompt_bytes": len(prompt.encode("utf-8")),
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0
        if args.action == "roster":
            if not args.input or not args.input.exists():
                raise SystemExit("--input <candidates.json> is required for forge roster")
            cands = json.loads(args.input.read_text(encoding="utf-8"))
            if not isinstance(cands, list):
                raise SystemExit("--input JSON must be a list of candidate dicts")
            out = select_three_plus_one_roster(cands)
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0

    if args.cmd == "sa" and args.action == "preview":
        # Offline SuperAlpha payload preview (zero API cost) — review before running.
        spec = json.loads(args.spec.read_text(encoding="utf-8")) if args.spec else {}
        region = str(spec.get("region") or args.region).upper()
        universe = str(spec.get("universe") or args.universe).upper()
        base_settings = dict(spec.get("settings") or {})
        base_settings.setdefault("region", region)
        base_settings.setdefault("universe", universe)
        base_settings.setdefault("delay", 1)
        base_settings.setdefault("selectionLimit", 100)
        base_settings.setdefault("selectionHandling", "POSITIVE")
        base_settings.setdefault("componentActivation", "IS")
        base_selection = str(spec.get("selection") or "").strip()
        base_combo = str(spec.get("combo") or "").strip()
        if not base_selection or not base_combo:
            raise SystemExit("sa preview requires --spec with 'selection' and 'combo'")
        payloads = []
        for item in (spec.get("items") or [{}]):
            item_settings = dict(base_settings)
            item_settings.update(item.get("settings_override") or {})
            payloads.append(
                build_sa_payload(
                    str(item.get("selection") or base_selection),
                    str(item.get("combo") or base_combo),
                    item_settings,
                )
            )
        print(json.dumps({"track_id": SA_TRACK_ID, "payloads": payloads}, indent=2, ensure_ascii=False))
        return 0

    if args.cmd == "sa":
        return _run_sa_command(args)

    # Live read-only / authenticated commands
    ledger = LedgerStore()
    quota = QuotaTracker(ledger)
    auth = BrainAuthSession(quota_observer=quota.observe_response)
    try:
        auth.authenticate()
        if args.cmd == "auth":
            print(json.dumps({"authenticated": True, "auth_epoch": auth.auth_epoch, "jwt_exp_ts": auth.jwt_exp_ts}, indent=2))
            return 0

        if args.cmd == "sc":
            eng = LocalSCEngine()
            try:
                if args.action == "sync":
                    print(json.dumps(eng.sync_os_alphas(auth), indent=2, ensure_ascii=False))
                elif args.action == "check":
                    if not args.alpha_id:
                        raise SystemExit("--alpha-id required")
                    pnl = eng.fetch_and_cache_pnl(auth, args.alpha_id)
                    if pnl is None:
                        print(json.dumps({"alpha_id": args.alpha_id, "sc_state": "PENDING_NO_OVERLAP"}))
                        return 1
                    res = eng.evaluate_sc(args.alpha_id, args.region, pnl, pool_mode=args.pool)
                    ledger.record_sc_evaluation(res.__dict__)
                    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))
                elif args.action == "matrix":
                    ids = _parse_csv(args.alpha_ids)
                    pnls = {}
                    for aid in ids:
                        s = eng.fetch_and_cache_pnl(auth, aid)
                        if s is not None:
                            pnls[aid] = s
                    mat = eng.compute_pairwise_matrix(pnls)
                    kept, pruned = eng.select_orthogonal_subset(ids, mat, max_pairwise_corr=args.max_pair)
                    print(json.dumps({
                        "kept_orthogonal": kept,
                        "pruned": pruned,
                        "matrix": mat.round(4).to_dict(),
                    }, indent=2, ensure_ascii=False))
                return 0
            finally:
                eng.close()

        if args.cmd == "pc":
            poller = PCPoller(auth, ledger)
            ids = _parse_csv(args.alpha_ids)
            out = [poller.poll_once(aid, args.region).__dict__ for aid in ids]
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0

        if args.cmd == "tag":
            ids = _parse_csv(args.alpha_ids)
            out = [
                apply_alpha_tag(auth, aid, args.tag, alias_name=args.name, confirm_apply=bool(args.confirm_apply))
                for aid in ids
            ]
            print(json.dumps(out, indent=2, ensure_ascii=False))
            return 0

        if args.cmd == "sim":
            bl = BlacklistRegistry(ledger)
            runner = SimRunner(auth, ledger, quota, blacklist_registry=bl, max_slots=args.slots)
            if args.action == "run":
                if not args.spec:
                    raise SystemExit("--spec is required")
                spec = json.loads(args.spec.read_text(encoding="utf-8"))
                bid, runnable, skipped = runner.prepare_batch_tasks(spec, simulation_mode=args.mode)
                res = runner.run_prepared_tasks(bid, runnable, batch_size=args.batch_size)
                print(json.dumps({"batch_id": bid, "skipped": len(skipped), **res}, indent=2, ensure_ascii=False))
            elif args.action == "resume":
                pending = ledger.get_resumable_tasks()
                print(json.dumps({"resumable_count": len(pending), "task_ids": [t["task_id"] for t in pending[:20]]}, indent=2))
            return 0

    finally:
        auth.close()
        ledger.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
