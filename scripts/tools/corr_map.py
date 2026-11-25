# -*- coding: utf-8 -*-
"""Read-only production/self correlation mapper for a list of alpha ids.

Why this exists: `robust_check.py` resolves one alpha at a time and also calls a `/yearly-stats` path that
returns 404 (the working shape is the MCP `get_alpha_yearly_stats` / `/alphas/{id}/performance?period=YEARLY`).
More importantly, once a batch of near-neighbour candidates exists, the campaign's binding constraint is
PROD_CORRELATION <= 0.7 (user rule: an alpha whose production correlation is unreturned or >0.7 does not qualify),
so the whole neighbourhood has to be mapped in one patient pass.

Evidence on what these two numbers mean (measured 2026-10-01 on N1Vvgwzo):
  /correlations/prod  -> a HISTOGRAM over ~1.7M platform production alphas + `max`; max 0.7812 came from the
                         single alpha in the [0.7,0.8] bucket, i.e. prod corr is measured against the whole
                         platform pool, NOT against my own submissions.
  /correlations/self  -> a RECORD LIST of my own correlated submitted alphas (id, region, correlation, sharpe...);
                         max 0.079 (vs `YP52x6JJ`), so the family is decorrelated inside the account.
First GET triggers the async compute, so both endpoints must be polled until a non-empty body appears; a 200 with
an empty body is COMPUTE-PENDING = UNOBSERVED, never a pass. No simulations, no submits, no property writes.

Usage: python tools/corr_map.py <alpha_id> [alpha_id ...]
"""
import os, sys, json, time
for k in ("HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy"): os.environ.pop(k,None)
import urllib3.util.connection as _u; _u.HAS_IPV6=False
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from cnhkmcp.untracked.platform_functions import brain_client as B

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def poll_json(url, tries=45, pause=5):
    """Return parsed body once non-empty, else None (= still computing / unobserved)."""
    for _ in range(tries):
        try:
            r=B.session.get(url,timeout=40)
            if r.status_code==200 and (r.text or "").strip():
                try: return r.json()
                except Exception: return None
            if r.status_code==429:
                time.sleep(float(r.headers.get("Retry-After",20))); continue
        except Exception as e:
            print("   exc",type(e).__name__,str(e)[:40],flush=True)
        time.sleep(pause)
    return None

def main(ids):
    import asyncio
    for i in range(10):
        try: asyncio.run(B.ensure_authenticated()); print("Auth OK",flush=True); break
        except Exception as e: print("auth retry",str(e)[:40],flush=True); time.sleep(12)
    rows=[]
    for aid in ids:
        p=poll_json(f"{B.base_url}/alphas/{aid}/correlations/prod")
        s=poll_json(f"{B.base_url}/alphas/{aid}/correlations/self")
        a=poll_json(f"{B.base_url}/alphas/{aid}",tries=6,pause=3)
        ism=(a or {}).get("is",{})
        pmax=p.get("max") if isinstance(p,dict) else None
        smax=s.get("max") if isinstance(s,dict) else None
        top_self=None
        if isinstance(s,dict) and s.get("records"):
            rec=max(s["records"], key=lambda r: r[5] if len(r)>5 else -1)
            top_self={"id":rec[0],"region":rec[3],"corr":rec[5],"sharpe":rec[6]}
        row={"alpha":aid,"prod_corr":pmax,"self_corr":smax,"top_self":top_self,
             "sharpe":ism.get("sharpe"),"fitness":ism.get("fitness"),
             "margin_bp":round((ism.get("margin") or 0)*1e4,2),
             "turnover_pct":round((ism.get("turnover") or 0)*100,2),
             "expr":(a or {}).get("regular"),
             "prod_observed":p is not None,"self_observed":s is not None,
             "prod_pass":(pmax is not None and pmax<=0.7)}
        rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
    out=os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__),"..")),"result","corr_map.json")
    json.dump(rows,open(out,"w",encoding="utf-8"),indent=2,ensure_ascii=False)
    print("\nWROTE",out,flush=True)
    print("%-10s %8s %8s %6s %6s %s"%("alpha","prod","self","sh","fit","note"),flush=True)
    for r in sorted(rows,key=lambda r:(r["prod_corr"] if r["prod_corr"] is not None else 9)):
        print("%-10s %8s %8s %6s %6s %s"%(r["alpha"],r["prod_corr"],r["self_corr"],r["sharpe"],r["fitness"],
              "PASS<=0.7" if r["prod_pass"] else ("UNOBSERVED" if not r["prod_observed"] else "OVER 0.7")),flush=True)

if __name__=="__main__":
    main(sys.argv[1:])
