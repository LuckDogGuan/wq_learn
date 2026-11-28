# -*- coding: utf-8 -*-
"""构建 WQB 本地知识库向量索引：BGE 嵌入 + LanceDB 混合检索（BM25 + 向量）。

用法:
  python scripts/forum_kb/ingest_official.py          # 先切块（官方层）
  python scripts/forum_kb/build_index.py              # 双表重建 + 混合检索自检
  python scripts/forum_kb/build_index.py --only forum # 只重建论坛经验表

表：
  wqb_official_guides    ← docs/official_guides 切块 + 管理员原创帖切块
  wqb_forum_experiences  ← data/forum_kb/qa/*.qa.md（LLM 原子化 QA）
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

try:  # 兼容两种导入方式
    from .kb_common import (
        DB_DIR,
        FORUM_TABLE,
        MODEL_NAME,
        OFFICIAL_DIR,
        OFFICIAL_TABLE,
        QUERY_INSTRUCTION,
        load_qa_docs,
    )
except ImportError:  # pragma: no cover
    from kb_common import (
        DB_DIR,
        FORUM_TABLE,
        MODEL_NAME,
        OFFICIAL_DIR,
        OFFICIAL_TABLE,
        QUERY_INSTRUCTION,
        load_qa_docs,
    )

META_PATH = DB_DIR / "index_meta.json"


def log(msg: str) -> None:
    print(msg, flush=True)


def load_official_rows() -> list[dict]:
    src = OFFICIAL_DIR / "chunks.jsonl"
    if not src.exists():
        log(f"[official] {src} 不存在，先跑 ingest_official.py")
        return []
    rows = []
    with src.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_model():
    from sentence_transformers import SentenceTransformer

    t0 = time.time()
    model = SentenceTransformer(MODEL_NAME)
    log(f"[model] loaded {MODEL_NAME} in {time.time() - t0:.1f}s")
    return model


def encode(model, texts: list[str], batch_size: int = 64):
    t0 = time.time()
    vecs = model.encode(
        texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False
    )
    log(f"[embed] {len(texts)} texts in {time.time() - t0:.1f}s (CPU) dim={vecs.shape[1]}")
    return vecs


def build_table(db, name: str, rows: list[dict], model) -> int:
    import lancedb  # noqa: F401  (确保依赖存在)

    if not rows:
        log(f"[{name}] no rows, skip")
        return 0
    vecs = encode(model, [r["text"] for r in rows])
    payload = []
    for r, v in zip(rows, vecs):
        payload.append(
            {
                "doc_id": r["doc_id"],
                "post_id": r.get("post_id", ""),
                "kind": r.get("kind", ""),
                "title": r.get("title", ""),
                "source": r.get("source", ""),
                "text": r["text"],
                "vector": v.tolist(),
            }
        )
    if name in db.list_tables():
        db.drop_table(name)
    table = db.create_table(name, payload)
    log(f"[{name}] table created: {table.count_rows()} rows")
    if not create_fts(table, name):
        log(f"[{name}] WARN FTS unavailable; hybrid falls back to vector-only")
    return table.count_rows()


def create_fts(table, name: str) -> bool:
    """中文 BM25：默认 simple 分词器会把整句中文当成一个 token（中文查询零命中），
    改用 ngram(2,3) 字符二元/三元组索引；失败再退回 create_fts_index。"""
    try:
        from lancedb.index import FTS

        table.create_index(
            "text",
            config=FTS(base_tokenizer="ngram", ngram_min_length=2, ngram_max_length=3),
            replace=True,
        )
        log(f"[{name}] FTS index created (ngram 2-3, 中文字符级 BM25)")
        return True
    except Exception as exc:  # noqa: BLE001
        log(f"[{name}] ngram FTS failed: {exc!r}")
    try:
        table.create_fts_index("text", replace=True)
        log(f"[{name}] FTS index created (fallback simple tokenizer)")
        return True
    except Exception as exc:  # noqa: BLE001
        log(f"[{name}] WARN fts index failed: {exc!r}")
    return False


def hybrid_query(table, model, q: str, limit: int = 3):
    qv = model.encode([QUERY_INSTRUCTION + q], normalize_embeddings=True)[0].tolist()
    try:
        return table.search(query_type="hybrid").text(q).vector(qv).limit(limit).to_list()
    except Exception as exc:  # noqa: BLE001
        log(f"  [hybrid] fallback vector-only: {exc!r}")
        return table.search(qv).limit(limit).to_list()


def verify(model, official_rows: int, forum_rows: int) -> None:
    import lancedb

    db = lancedb.connect(str(DB_DIR))
    checks = [
        (OFFICIAL_TABLE, "D1 回测的 Turnover 与 Sharpe 门限", "官方准则"),
        (OFFICIAL_TABLE, "Power Pool 提交主题限制 与 Prod Correlation", "官方准则"),
        (FORUM_TABLE, "Turnover 偏高用什么算子平滑", "论坛经验"),
        (FORUM_TABLE, "MCP 启动握手超时怎么办", "论坛经验"),
        (FORUM_TABLE, "论坛帖子怎么增量爬取", "论坛经验"),
    ]
    for tname, q, tag in checks:
        if tname not in db.list_tables():
            log(f"\n=== [{tag}] {tname} 不存在，跳过: {q}")
            continue
        table = db.open_table(tname)
        res = hybrid_query(table, model, q, limit=3)
        log(f"\n=== [{tag}] {q} ===")
        for r in res:
            score = r.get("_relevance_score", r.get("_distance"))
            txt = (r.get("text") or "").replace("\n", " ")
            log(f"  - id={r.get('doc_id')} kind={r.get('kind')} score={score} :: {txt[:80]}")
    log(f"\n[verify] official_rows={official_rows} forum_rows={forum_rows}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["all", "official", "forum"], default="all")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    import lancedb

    DB_DIR.mkdir(parents=True, exist_ok=True)
    model = load_model()
    db = lancedb.connect(str(DB_DIR))

    n_off = n_for = 0
    if a.only in ("all", "official"):
        n_off = build_table(db, OFFICIAL_TABLE, load_official_rows(), model)
    if a.only in ("all", "forum"):
        n_for = build_table(db, FORUM_TABLE, load_qa_docs(), model)

    meta = {
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": MODEL_NAME,
        "dim": 512,
        "tables": {OFFICIAL_TABLE: n_off, FORUM_TABLE: n_for},
    }
    if a.only == "forum" and META_PATH.exists():
        old = json.loads(META_PATH.read_text(encoding="utf-8"))
        old.setdefault("tables", {})[FORUM_TABLE] = n_for
        old["built_at"] = meta["built_at"]
        meta = old
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"[meta] {META_PATH}")

    if a.only == "all":
        verify(model, n_off, n_for)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
