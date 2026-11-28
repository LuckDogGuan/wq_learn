# -*- coding: utf-8 -*-
"""官方层切块入库：docs/official_guides + reference/forum/admin_posts → official/chunks.jsonl。

官方准则与管理员的原创帖不做 LLM 原子化（原文即权威），只做「代码保护型切块 + 来源头」，
写入后由 build_index.py 建 `wqb_official_guides` 表（BM25 + 向量混合检索）。

用法: python scripts/forum_kb/ingest_official.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:  # 兼容两种导入方式
    from .kb_common import (
        ADMIN_DIR,
        OFFICIAL_DIR,
        OFFICIAL_GUIDES_DIR,
        WS,
        chunk_admin_post,
        chunk_official_doc,
    )
except ImportError:  # pragma: no cover
    from kb_common import (
        ADMIN_DIR,
        OFFICIAL_DIR,
        OFFICIAL_GUIDES_DIR,
        WS,
        chunk_admin_post,
        chunk_official_doc,
    )


def build_rows() -> list[dict]:
    rows: list[dict] = []
    for p in sorted(OFFICIAL_GUIDES_DIR.glob("*.md")):
        rel = p.relative_to(WS).as_posix()
        got = chunk_official_doc(p, rel)
        print(f"[official_doc] {p.name}: {len(got)} chunks", flush=True)
        rows.extend(got)
    n_admin = 0
    for p in sorted(ADMIN_DIR.rglob("*.md")):
        rel = p.relative_to(WS).as_posix()
        if p.stat().st_size > 300_000:
            print(f"[admin_post] skip huge {p.name} ({p.stat().st_size // 1024}KB)", flush=True)
            continue
        try:
            got = chunk_admin_post(p, rel)
        except Exception as exc:  # noqa: BLE001
            print(f"[admin_post] skip {p.name}: {exc}", flush=True)
            continue
        n_admin += len(got)
        rows.extend(got)
    print(f"[admin_post] {n_admin} chunks from admin_posts", flush=True)
    return rows


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    OFFICIAL_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    seen: set[str] = set()
    uniq: list[dict] = []
    for r in rows:
        if r["doc_id"] in seen:
            continue
        seen.add(r["doc_id"])
        uniq.append(r)
    out = OFFICIAL_DIR / "chunks.jsonl"
    tmp = out.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        for r in uniq:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(out)
    by_kind: dict[str, int] = {}
    for r in uniq:
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
    print(f"[write] {out} rows={len(uniq)} kinds={by_kind}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
