# -*- coding: utf-8 -*-
"""Post-batch patient PROD/SELF correlation resolver.
Runs ONLY after sims have idled (correlation compute shares the sim worker pool;
polling DURING a batch keeps PROD_CORRELATION=PENDING forever).

For each alpha it reads BOTH sources and accepts the first that resolves:
  - GET /alphas/{id}/check        -> is.checks[PROD_CORRELATION].value/result
  - GET /alphas/{id}/correlations/prod -> {"max": v}
Also re-reads LOW_SUB_UNIVERSE_SHARPE value/result (confirms which fix cleared it).

IDs are taken from:
  (a) batch38 result file -> only candidates whose LOW_SUB_UNIVERSE_SHARPE PASS
  (b) an explicit EXTRA list (A5/Q1/Q3 to keep them live).
Read-only. NEVER submit, NEVER set properties.
"""
import os, sys, json, asyncio, time as _t
for k in ("HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy"): os.environ.pop(k, None)
import urllib3.util.connection as _u; _u.HAS_IPV6 = False
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from cnhkmcp.untracked.platform_functions import brain_client as B

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
B38 = os.path.join(ROOT, "result", "eur_batch38_valmom_subuniv.json")
OUT = os.path.join(ROOT, "result", "prod_final_resolve.json")

# Always keep these model25 legs in the poll set.
EXTRA = [
    ("9qW1N6Ld", "A5_capbkt_g"),
    ("npPREbna", "Q1_vmg_fast"),
    ("omW5deV2", "Q3_vmi_fast"),
    ("88P9wqnl", "Q4_vmsec_fast"),
]

def load_ids():
    ids = list(EXTRA)
    if os.path.exists(B38):
        try:
            d = json.load(open(B38, encoding="utf-8"))
            for r in d.get("results", []):
                aid = r.get("alpha_id")
                if not aid: continue
                # only worth polling prod if SUB_UNIVERSE got fixed (no LOW_SUB_UNIVERSE fail)
                fails = r.get("failed_checks", [])
                if "LOW_SUB_UNIVERSE_SHARPE" not in fails:
                    ids.append((aid, r.get("tag", aid)))
        except Exception as e:
            print("b38 parse skip:", e, flush=True)
    # de-dup
    seen = {}
    for a, t in ids:
        seen.setdefault(a, t)
    return list(seen.items())

async def auth():
    for _ in range(12):
        try:
            await B.ensure_authenticated(); return
        except Exception:
            await asyncio.sleep(15)

def check_prod(aid):
    """Return (value, result, subuniv_val, subuniv_res) from /check, may be None/PENDING."""
    r = B.session.get(f"{B.base_url}/alphas/{aid}/check")
    if r.status_code != 200: return None, None, None, None
    j = r.json()
    checks = j.get("is", {}).get("checks", []) if isinstance(j.get("is"), dict) else j.get("checks", [])
    pv = pr = sv = sr = None
    for c in checks:
        n = c.get("name") or ""
        if n == "PROD_CORRELATION": pv = c.get("value"); pr = c.get("result")
        elif n == "SELF_CORRELATION": pass
        elif n == "LOW_SUB_UNIVERSE_SHARPE": sv = c.get("value"); sr = c.get("result")
    return pv, pr, sv, sr

def corr_endp(aid, kind="prod"):
    r = B.session.get(f"{B.base_url}/alphas/{aid}/correlations/{kind}")
    if r.status_code == 200 and (r.text or "").strip():
        try:
            j = r.json()
            if "max" in j and j["max"] is not None: return float(j["max"])
        except Exception: return None
    return None

async def resolve(aid, tag, tries=90, wait=8):
    prod = None; subv = None; subr = None; src = None
    for i in range(tries):
        pv, pr, sv, sr = check_prod(aid)
        subv, subr = sv, sr
        if pv is not None:
            prod = float(pv); src = "check"; break
        ep = corr_endp(aid, "prod")
        if ep is not None:
            prod = ep; src = "endpoint"; break
        if i % 6 == 0:
            print(f"  [{tag} {aid}] prod still PENDING (try {i}); sub_univ={sv}({sr})", flush=True)
        await asyncio.sleep(wait)
    sc = None
    for _ in range(6):
        sc = corr_endp(aid, "self")
        if sc is not None: break
        await asyncio.sleep(5)
    rec = {"tag": tag, "alpha": aid, "prod_corr": prod, "prod_src": src,
           "self_corr": sc, "sub_univ_val": subv, "sub_univ_result": subr,
           "prod_lt_0.7": (prod is not None and prod < 0.7)}
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    return rec

async def main():
    await auth()
    ids = load_ids()
    print(f"Poll set ({len(ids)}):", [t for _, t in ids], flush=True)
    out = []
    for aid, tag in ids:
        out.append(await resolve(aid, tag))
    json.dump({"resolved": out}, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    winners = [o for o in out if o["prod_lt_0.7"] and o.get("sub_univ_result") == "PASS"]
    print(f"\nWROTE {OUT}. prod<0.7 AND sub_universe PASS: {len(winners)}", flush=True)
    for w in winners: print("  WINNER:", w["tag"], w["alpha"], "prod", w["prod_corr"], "self", w["self_corr"], flush=True)

if __name__ == "__main__":
    asyncio.run(main())
