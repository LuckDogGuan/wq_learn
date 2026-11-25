"""Unified CLI entrypoint for wq_research_v2 (strictly ZERO /submit command)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from wq_research_v2.ablation_engine import build_dual_branch_ablation
from wq_research_v2.auth_session import BrainAuthSession
from wq_research_v2.blacklist_registry import BlacklistRegistry
from wq_research_v2.expr_validator import ExprValidator
from wq_research_v2.field_screener import FieldScreener
from wq_research_v2.ledger_store import LedgerStore
from wq_research_v2.pc_poller import PCPoller
from wq_research_v2.pyramid_planner import build_stage0_probe_spec
from wq_research_v2.quota_tracker import QuotaTracker, current_est_platform_date
from wq_research_v2.sc_local import LocalSCEngine
from wq_research_v2.sim_runner import SimRunner
from wq_research_v2.tagger import USEFUL_TAG, apply_alpha_tag


def _parse_csv(raw: str) -> list[str]:
    return [x.strip() for x in raw.replace(";", ",").split(",") if x.strip()]


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

    # tag (Guangzhou-style Useful / SC_IS_HIGHT / PC_IS_HIGHT tagging; dry-run by default)
    p_tag = sub.add_parser("tag", help="Preview or apply Useful/SC_IS_HIGHT/PC_IS_HIGHT tag (dry-run by default)")
    p_tag.add_argument("action", choices=["apply"])
    p_tag.add_argument("--alpha-ids", required=True)
    p_tag.add_argument("--tag", default=USEFUL_TAG, choices=["Useful", "SC_IS_HIGHT", "PC_IS_HIGHT"])
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
                apply_alpha_tag(auth, aid, args.tag, confirm_apply=bool(args.confirm_apply))
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
