# -*- coding: utf-8 -*-
"""达标 alpha 的 robust + 过拟合核验（只读，不改属性/不提交）。
用法: python robust_check.py <alpha_id> [alpha_id ...]
检查: IS checks 全过、逐年稳定性、子universe、self/prod corr、margin/turnover 结构。"""
import os, sys, json, asyncio
for k in ("HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy"): os.environ.pop(k,None)
import urllib3.util.connection as _u; _u.HAS_IPV6=False
from cnhkmcp.untracked.platform_functions import brain_client as B

async def poll(session,url,attempts=15):
    for _ in range(attempts):
        try:
            r=session.get(url)
            if r.status_code==200 and (r.text or "").strip(): return r.json()
            ra=r.headers.get("Retry-After"); await asyncio.sleep(min(max(float(ra) if ra else 5.0,3.0),15.0))
        except Exception: await asyncio.sleep(5.0)
    return None

async def check(aid):
    await B.ensure_authenticated()
    a=B.session.get(f"{B.base_url}/alphas/{aid}").json()
    ism=a.get("is",{})
    checks={c.get("name"):c.get("result") for c in ism.get("checks",[])}
    fails=[n for n,v in checks.items() if v=="FAIL"]
    yearly=await poll(B.session,f"{B.base_url}/alphas/{aid}/yearly-stats")
    ys=[]
    if yearly:
        recs=yearly.get("values") or yearly.get("yearly") or yearly.get("results") or []
        for r in recs:
            ys.append({"y":r.get("year"),"sharpe":r.get("sharpe"),"ret":r.get("returns"),"tvr":r.get("turnover")})
    # 子universe/robustness via self & prod corr
    prod=await poll(B.session,f"{B.base_url}/alphas/{aid}/correlations/prod")
    selfc=await poll(B.session,f"{B.base_url}/alphas/{aid}/correlations/self")
    # submission check (ra_failed / gates) 只读
    sub=await poll(B.session,f"{B.base_url}/alphas/{aid}/check")
    pc=float(prod["max"]) if prod and "max" in prod else None
    sc=float(selfc["max"]) if selfc and "max" in selfc else None
    neg_years=sum(1 for r in ys if (r.get("sharpe") or 0)<0)
    res={"alpha":aid,"status":a.get("status"),
         "sharpe":ism.get("sharpe"),"fitness":ism.get("fitness"),
         "margin_bp":round((ism.get("margin") or 0)*1e4,2),"turnover_pct":round((ism.get("turnover") or 0)*100,2),
         "checks":checks,"failed":fails,"prod_corr":pc,"self_corr":sc,
         "years_n":len(ys),"neg_years":neg_years,"yearly":ys,"sub_check":sub}
    print(json.dumps(res,ensure_ascii=False,indent=2))
    return res

async def main():
    out=[]
    for aid in sys.argv[1:]:
        out.append(await check(aid))
    os.makedirs("result",exist_ok=True)
    json.dump(out,open("result/robust_checks.json","w",encoding="utf-8"),indent=2,ensure_ascii=False)

if __name__=="__main__": asyncio.run(main())
