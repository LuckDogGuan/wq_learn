# -*- coding: utf-8 -*-
"""专等 correlations/prod 的 max 出值（首次请求触发异步计算，后续请求取回）。只读、不模拟、不提交。
用法: python poll_corr.py  （内置 batch36 突破候选；可自行扩 ID）"""
import os, json, asyncio

for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(k, None)
import urllib3.util.connection as _u
_u.HAS_IPV6 = False
from cnhkmcp.untracked.platform_functions import brain_client as B

# 仅 3 条 FAST value_momentum 赢家（换手入 5-30、sh>3、2Y>2），决定性 prod_corr 未知量
ALPHAS = [
    ("npPREbna", "Q1_vmg_fast",   "value_momentum_global @TOP2500/FAST sh3.11 tvr5.74"),
    ("omW5deV2", "Q3_vmi_fast",   "value_momentum_industry @TOP2500/FAST sh3.08 tvr5.90"),
    ("88P9wqnl", "Q4_vmsec_fast", "value_momentum_sector @TOP2500/FAST sh3.10 tvr5.75"),
]

async def wait_corr(session, url, attempts=40, pause=8):
    """correlations/prod 常先返回 202/pending 或 200 无 max；反复请求直到出现 max。"""
    last = None
    for _ in range(attempts):
        try:
            r = session.get(url)
            last = (r.status_code, (r.text or "")[:120])
            if r.status_code == 200 and (r.text or "").strip():
                j = r.json()
                if isinstance(j, dict) and "max" in j:
                    return j
        except Exception:
            pass
        await asyncio.sleep(pause)
    return {"_timeout": True, "_last": last}

async def main():
    for _ in range(8):
        try:
            await B.ensure_authenticated(); break
        except Exception:
            await asyncio.sleep(20)
    out = []
    for aid, tag, note in ALPHAS:
        prod = await wait_corr(B.session, f"{B.base_url}/alphas/{aid}/correlations/prod")
        slf = await wait_corr(B.session, f"{B.base_url}/alphas/{aid}/correlations/self")
        rec = {"id": aid, "tag": tag, "note": note,
               "prod_max": prod.get("max") if "max" in prod else None,
               "self_max": slf.get("max") if "max" in slf else None,
               "prod_raw": None if "max" in prod else prod,
               "self_raw": None if "max" in slf else slf}
        pc = rec["prod_max"]
        rec["qualifies_corr"] = (pc is not None and float(pc) < 0.7)
        out.append(rec); print(json.dumps(rec, ensure_ascii=False), flush=True)
    json.dump(out, open("result/corr36.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("WROTE result/corr36.json", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
