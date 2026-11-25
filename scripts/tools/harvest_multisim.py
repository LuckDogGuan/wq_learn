# -*- coding: utf-8 -*-
"""Re-attach to an ALREADY-DISPATCHED multisim by id, robustly (retry on transient
SSLEOFError/MaxRetry), harvest children, and read /check metrics (SUB_UNIVERSE value/
result, 2Y, ladder) WITHOUT correlation polling (resolve prod later after queue idles).
Usage: python harvest_multisim.py <multisim_id> <out_json>
Read-only. NEVER submit/set props.
"""
import os, sys, json, asyncio, time as _t
for k in ("HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy"): os.environ.pop(k,None)
import urllib3.util.connection as _u; _u.HAS_IPV6 = False
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from cnhkmcp.untracked.platform_functions import brain_client as B

def safe_get(url, tries=12, pause=6):
    for _ in range(tries):
        try:
            r = B.session.get(url)
            if r.status_code < 500:
                return r
        except Exception as e:
            print("  retry-get", type(e).__name__, str(e)[:60], flush=True)
        _t.sleep(pause)
    return None

def safe_auth():
    for _ in range(10):
        try:
            asyncio.get_event_loop()
        except Exception:
            pass
        try:
            asyncio.run(B.ensure_authenticated()); print("Auth OK", flush=True); return True
        except Exception as e:
            print("auth retry", str(e)[:60], flush=True); _t.sleep(12)
    return False

def eval_child(aid):
    a = safe_get(f"{B.base_url}/alphas/{aid}")
    if a is None: return {"alpha_id": aid, "error": "fetch_failed"}
    ad = a.json(); ism = ad.get("is", {})
    checks = ism.get("checks", [])
    fails = [c.get("name") for c in checks if c.get("result") == "FAIL"]
    sub = next((c for c in checks if c.get("name") == "LOW_SUB_UNIVERSE_SHARPE"), {})
    l2 = next((c for c in checks if c.get("name") == "LOW_2Y_SHARPE"), {})
    lad = next((c for c in checks if c.get("name") == "IS_LADDER_SHARPE"), {})
    return {"alpha_id": aid, "status": ad.get("status"),
            "sharpe": ism.get("sharpe"), "fitness": ism.get("fitness"),
            "margin_bp": round((ism.get("margin") or 0)*1e4, 2),
            "turnover_pct": round((ism.get("turnover") or 0)*100, 2),
            "sub_univ_val": sub.get("value"), "sub_univ_result": sub.get("result"),
            "sharpe_2y": l2.get("value"), "ladder_result": lad.get("result"),
            "ra_failed_count": len(fails), "failed_checks": fails}

def harvest(mid, out_path):
    loc = f"{B.base_url}/simulations/{mid}"
    children = []
    for _ in range(80):
        m = safe_get(loc)
        if m is not None and m.status_code == 200:
            try: children = m.json().get("children", [])
            except Exception: pass
        if children:
            print(f"{len(children)} children observed", flush=True); break
        _t.sleep(6)
    if not children:
        print("NO children observed", flush=True); return
    done = {}
    pending = list(enumerate(children))
    for loop in range(150):
        still = []
        for idx, cu in pending:
            url = cu if str(cu).startswith("http") else f"{B.base_url}/simulations/{cu}"
            cr = safe_get(url, tries=6, pause=6)
            if cr is None: still.append((idx, cu)); continue
            cd = cr.json() if cr.status_code == 200 else {}
            ra = cr.headers.get("Retry-After")
            if (not ra or float(ra) == 0) and cd:
                aid = cd.get("alpha")
                if aid: done[idx] = aid; print(f"  [{idx}] -> {aid}", flush=True)
                elif cd.get("status") in ("ERROR","CANCELLED"):
                    print(f"  [{idx}] {cd.get('status')} msg={cd.get('message')}", flush=True)
                else: still.append((idx, cu))
            else: still.append((idx, cu))
        pending = still
        if pending: _t.sleep(8)
        else: break
    results = []
    for idx in sorted(done):
        rec = eval_child(done[idx]); rec["child_index"] = idx
        results.append(rec); print(json.dumps(rec, ensure_ascii=False), flush=True)
    json.dump({"multisim": mid, "results": results},
              open(out_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    ra0 = [r for r in results if r.get("ra_failed_count") == 0]
    print(f"\nWROTE {out_path}. ra_failed=0: {len(ra0)}", flush=True)
    for r in ra0:
        print("  CLEAR:", r["alpha_id"], "sh", r["sharpe"], "subu", r["sub_univ_val"],
              r["sub_univ_result"], flush=True)

if __name__ == "__main__":
    mid = sys.argv[1] if len(sys.argv) > 1 else "3RV6xUf7c4zfcpteVSOdRhy"
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(__file__), "..", "result", "eur_batch39_m25_subu_attack.json")
    if not safe_auth(): print("AUTH FAILED", flush=True); sys.exit(1)
    harvest(mid, out)
