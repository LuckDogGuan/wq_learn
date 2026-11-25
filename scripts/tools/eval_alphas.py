# -*- coding: utf-8 -*-
"""Evaluate a list of already-created alpha IDs: IS metrics + RA fails, and poll
prod/self correlation for candidates that clear sharpe floor. Used to recover
batch35 (runner discarded completed alphas) and to fetch M8 correlation."""
import os, sys, json, asyncio
for k in ("HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy"): os.environ.pop(k,None)
import urllib3.util.connection as u; u.HAS_IPV6=False
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from cnhkmcp.untracked.platform_functions import brain_client as bc

# (tag, alpha_id) — batch35 children in dispatch order + M8 from batch34
ALPHAS = [
    ("A1_td_gm",  "omW5xz56"), ("A2_td_vm",  "3qVr86rO"), ("A3_td_lt",  "MP3RJ8oo"),
    ("A4_rev_st", "2rmz3ZbJ"), ("A5_capbkt", "9qW1N6Ld"), ("A6_vm_ind", "QPKkwlXM"),
    ("A7_z_lt",   "N1VmYj9p"), ("A8_gm_mkt", "mL6REz91"), ("M8_gr_vm",  "qM0razJV"),
]
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "result", "eval_batch35_m8.json"))

async def poll(url, n=25, d=6.0):
    for _ in range(n):
        try:
            r = bc.session.get(url)
            if r.status_code == 200 and (r.text or "").strip():
                return r.json()
            ra = r.headers.get("Retry-After")
            await asyncio.sleep(min(max(float(ra) if ra else d, 3.0), 15.0))
        except Exception:
            await asyncio.sleep(d)
    return None

async def main():
    await bc.ensure_authenticated()
    res = []
    for tag, aid in ALPHAS:
        a = bc.session.get(f"{bc.base_url}/alphas/{aid}")
        ad = a.json() if a.status_code == 200 else {}
        ism = ad.get("is", {})
        code = (ad.get("regular") or {}).get("code", "")
        sharpe = ism.get("sharpe"); fit = ism.get("fitness")
        mgn = (ism.get("margin") or 0) * 10000; tvr = (ism.get("turnover") or 0) * 100
        checks = ism.get("checks", [])
        fails = [c.get("name") for c in checks if c.get("result") == "FAIL"]
        l2 = next((c for c in checks if c.get("name") == "LOW_2Y_SHARPE"), None)
        s2y = l2.get("value") if l2 else None
        item = {"tag": tag, "alpha_id": aid, "code": code, "sharpe": sharpe, "fitness": fit,
                "margin_bp": round(mgn,2), "turnover_pct": round(tvr,2), "sharpe_2y": s2y,
                "failed_checks": fails, "prod_corr": None, "self_corr": None}
        # poll correlation only if promising (sharpe>1.2, <=3 fails)
        if sharpe is not None and sharpe > 1.2 and len(fails) <= 4:
            p = await poll(f"{bc.base_url}/alphas/{aid}/correlations/prod", 22)
            s = await poll(f"{bc.base_url}/alphas/{aid}/correlations/self", 12)
            if p and "max" in p: item["prod_corr"] = float(p["max"])
            if s and "max" in s: item["self_corr"] = float(s["max"])
        qual = (fails==[] and sharpe and sharpe>1.58 and fit and fit>1 and s2y and s2y>1.6
                and mgn>5 and 5<tvr<30 and item["prod_corr"] is not None and item["prod_corr"]<0.7)
        item["qualified"] = qual
        res.append(item)
        print(json.dumps(item, ensure_ascii=False), flush=True)
    json.dump(res, open(OUT,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    print("WROTE", OUT, flush=True)

if __name__ == "__main__":
    asyncio.run(main())
