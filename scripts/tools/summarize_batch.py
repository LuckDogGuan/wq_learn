# -*- coding: utf-8 -*-
"""Summarize a batch result JSON as a gate-oriented table (read-only, no platform calls).

Usage: python tools/summarize_batch.py result/eur_batch48_fundholdings_opt1.json [more.json ...]
Gate columns come from the campaign objective: sharpe>1.58, fitness>1, 2Y>1.6, margin>=5bp,
5%<turnover<30%, plus SUB_UNIVERSE and any hard FAIL. WARNING-class checks (LOW_SHARPE/LOW_FITNESS/
CLUSTER_TEST) are printed separately because they are NOT FAILs.
"""
import json, sys, os

def label(r):
    # harvest_multisim.py output has no "tag" - fall back to the dispatch order it preserves.
    return r.get("tag") or "#%s" % r.get("child_index", "?")

def row(r):
    if r.get("sharpe") is None:
        return "  %-22s ERROR/UNOBSERVED: %s" % (label(r), str(r.get("error"))[:90])
    hard = [f for f in r.get("hard_fails", r.get("failed_checks", [])) if f not in ("LOW_SHARPE", "LOW_FITNESS", "LOW_2Y_SHARPE")]
    warn = [w[0] if isinstance(w, (list, tuple)) else w for w in r.get("warnings", [])]
    warn = [w for w in warn if w == "CLUSTER_TEST"]
    return "  %-22s neut=%-9s sh%6.2f fit%6.2f mgn%7.2f tvr%6.2f 2y%6.2f subu%6.2f %-4s %s FAIL=%s WARN=%s" % (
        label(r), r.get("neut", r.get("decay", "-")), r["sharpe"] or 0, r["fitness"] or 0,
        r["margin_bp"] or 0, r["turnover_pct"] or 0,
        r.get("sharpe_2y") if r.get("sharpe_2y") is not None else -99,
        r.get("sub_univ_val") if r.get("sub_univ_val") is not None else -99,
        r.get("sub_univ_result", "-"), r.get("alpha_id", "-"), ",".join(hard) or "-", ",".join(warn) or "-")

def gates(r):
    if r.get("sharpe") is None:
        return False
    hard = [f for f in (r.get("hard_fails") or r.get("failed_checks") or [])
            if f not in ("LOW_SHARPE", "LOW_FITNESS", "LOW_2Y_SHARPE")]
    return (r["sharpe"] > 1.58 and (r["fitness"] or 0) > 1 and (r["margin_bp"] or 0) >= 5
            and 5 < (r["turnover_pct"] or 0) < 30 and (r.get("sharpe_2y") or 0) > 1.6
            and not hard)

def main():
    for path in sys.argv[1:] or ["result/eur_latest.json"]:
        if not os.path.exists(path):
            print("missing:", path); continue
        d = json.load(open(path, encoding="utf-8"))
        res = d.get("results") or []
        if isinstance(res, dict):
            res = [x for v in res.values() for x in v]
        print("== %s  multi_sim=%s  %d candidates" % (os.path.basename(path),
              d.get("multi_sim") or d.get("multisim"), len(res)))
        ok = [r for r in res if r.get("sharpe") is not None]
        for r in sorted(res, key=lambda r: -(r.get("sharpe") or -9)):
            print(row(r))
        print("  complete %d/%d | >0.8 bases: %s | GATE-CLEAN: %s" % (
            len(ok), len(res),
            [label(r) for r in ok if (r["sharpe"] or 0) > 0.8],
            [label(r) for r in res if gates(r)]))

if __name__ == "__main__":
    main()
