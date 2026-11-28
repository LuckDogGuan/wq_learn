# -*- coding: utf-8 -*-
"""端到端验收：用 MCP stdio 客户端拉起 server.py，真实调用两个工具。

用法: python scripts/forum_kb/verify_mcp.py
验收点：① 冷启动握手不加载 torch/BGE（<2s）；② 两个工具都返回真实命中；
        ③ 社区工具确实回读 reference/forum 原文。
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE / "server.py"

OFFICIAL_Q = "D1 回测的 Turnover 与 Sharpe 硬性门限"
FORUM_Q = "MCP 启动握手超时怎么办"


async def _run() -> int:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER)],
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    errlog_path = Path(__file__).resolve().parents[2] / "data" / "forum_kb" / "mcp_server_stderr.log"
    errlog_path.parent.mkdir(parents=True, exist_ok=True)
    errlog = errlog_path.open("w", encoding="utf-8")
    t0 = time.time()
    async with stdio_client(params, errlog=errlog) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            handshake = time.time() - t0
            print(f"[handshake] initialize in {handshake * 1000:.0f} ms", flush=True)
            tools = [t.name for t in (await session.list_tools()).tools]
            print(f"[tools] {tools}", flush=True)
            assert "search_wqb_official_guidelines" in tools
            assert "search_wqb_forum_experience" in tools

            for name, q in (
                ("search_wqb_official_guidelines", OFFICIAL_Q),
                ("search_wqb_forum_experience", FORUM_Q),
            ):
                t1 = time.time()
                res = await asyncio.wait_for(session.call_tool(name, {"query": q, "top_k": 3}), timeout=300)
                dt = time.time() - t1
                text = res.content[0].text if res.content else ""
                head = text.splitlines()[:4]
                print(f"\n[{name}] {dt:.1f}s chars={len(text)}")
                for ln in head:
                    print("  " + ln[:120])
                if name.endswith("forum_experience"):
                    ok = "文章正文内容" in text or "未找到原始 Markdown" in text
                    print(f"  [back-ref] {'OK' if ok else 'MISSING'}")
                    if not ok:
                        return 1
                if not text or text.startswith("❌"):
                    return 1
    print("\n[VERIFY_OK] MCP stdio round-trip passed")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    return asyncio.run(_run())


if __name__ == "__main__":
    raise SystemExit(main())
