# -*- coding: utf-8 -*-
"""WQB-Knowledge-Base MCP 服务（FastMCP stdio）。

两个工具（对齐论坛帖《本地知识库MCP构建》）：
  1. search_wqb_official_guidelines —— 官方准则/管理员帖（最高优先级）
  2. search_wqb_forum_experience   —— 社区论坛经验（次高优先级，全文反查）

极致懒加载：进程启动只导入 stdlib + mcp，`torch`/`sentence-transformers`/`lancedb`
全部推迟到工具首次被调用时才加载，冷启动握手 <50ms，避免 IDE 端 10s 超时断开。

挂载示例（antigravity.json / claude_desktop_config.json）:
  {"mcpServers": {"wqb-knowledge-base": {
      "command": "python",
      "args": ["C:/Wq/WorldQuant Brain/scripts/forum_kb/server.py"],
      "env": {"PYTHONUNBUFFERED": "1"}}}}
"""
from __future__ import annotations

import datetime
import os
import random
import re
import sys

# Windows 实证坑（2026-11-28）：MCP stdio 服务进入 anyio 事件循环后，工具线程/预热线程
# 再 import numpy / scipy / torch 会永久卡死在扩展 DLL 加载（faulthandler 栈停在
# importlib create_module，实测 >300s 无返回；纯 asyncio 循环下无此问题）。
# 因此 Windows 上必须「拿到事件循环前」把重型库导入完；numpy/torch 等库导入 ~12s，
# 属可接受的冷启动代价（仍不加载模型权重与建表，那部分保持懒加载）。
# Linux/macOS（原帖环境）无此限制，可用 WQB_KB_PRELOAD=0 走纯懒加载。
PLATFORM_PRELOAD = os.name == "nt" and os.environ.get("WQB_KB_PRELOAD", "1") != "0"

if PLATFORM_PRELOAD:
    import importlib as _importlib

    for _mod in ("numpy", "scipy.special", "sklearn", "torch", "sentence_transformers", "lancedb"):
        try:
            _importlib.import_module(_mod)
        except Exception:  # pragma: no cover - 缺依赖时保持懒加载失败可见
            pass

try:  # 兼容 `python server.py` 与 `import scripts.forum_kb.server`
    from .kb_common import (
        DB_DIR,
        FORUM_TABLE,
        OFFICIAL_TABLE,
        QUERY_INSTRUCTION,
        find_original_md,
        row_text_header,
    )
except ImportError:  # pragma: no cover
    from kb_common import (
        DB_DIR,
        FORUM_TABLE,
        OFFICIAL_TABLE,
        QUERY_INSTRUCTION,
        find_original_md,
        row_text_header,
    )

from mcp.server.fastmcp import FastMCP

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = str(DB_DIR)

mcp = FastMCP("WQB-Knowledge-Base")

# ==========================================
# 极致懒加载器：只有工具被调用时才导入重型库并连接
# ==========================================
_model_instance = None
_db_tables = None
_original_md_cache: dict[str, str] = {}

MAX_ORIGINAL_CHARS = 6000


def get_tables() -> dict:
    """延迟加载 LanceDB 数据库与两张表。"""
    global _db_tables
    if _db_tables is None:
        import lancedb

        db = lancedb.connect(DB_PATH)
        names = set(db.list_tables())
        tables = {}
        if OFFICIAL_TABLE in names:
            tables["official"] = db.open_table(OFFICIAL_TABLE)
        if FORUM_TABLE in names:
            tables["forum"] = db.open_table(FORUM_TABLE)
        _db_tables = tables
    return _db_tables


def get_embedding_model():
    """延迟加载 PyTorch 与 BGE 向量模型（纯离线、静默）。"""
    global _model_instance
    if _model_instance is None:
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        import warnings

        warnings.filterwarnings("ignore")
        from sentence_transformers import SentenceTransformer

        _model_instance = SentenceTransformer("BAAI/bge-small-zh-v1.5")
    return _model_instance


def _encode_query(query: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(QUERY_INSTRUCTION + query, normalize_embeddings=True).tolist()


def _hybrid(table, query: str, qv: list[float], limit: int, where: str | None = None) -> list[dict]:
    def _apply(qb):
        return qb.where(where) if where else qb

    try:
        return _apply(table.search(query_type="hybrid").text(query).vector(qv)).limit(limit).to_list()
    except Exception:
        pass
    try:
        return _apply(table.search(qv)).limit(limit).to_list()
    except Exception:
        return []


def _dedupe(rows: list[dict]) -> list[dict]:
    seen, out = set(), []
    for r in rows:
        key = r.get("doc_id") or id(r)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def _read_original(post_id: str) -> str:
    """全文反查：从 reference/forum 读回 Markdown 原文（缓存 + 长度上限）。"""
    if post_id in _original_md_cache:
        return _original_md_cache[post_id]
    try:
        p = find_original_md(post_id)
        text = p.read_text(encoding="utf-8", errors="replace") if p else ""
    except Exception:
        text = ""
    if len(text) > MAX_ORIGINAL_CHARS:
        text = text[:MAX_ORIGINAL_CHARS] + f"\n\n……（原文过长，已截断，完整原文见 reference/forum）"
    _original_md_cache[post_id] = text
    return text


# ==========================================
# 工具定义
# ==========================================
@mcp.tool()
def search_wqb_official_guidelines(query: str, top_k: int = 15) -> str:
    """【绝对最高优先级调用】检索 WorldQuant Brain (WQB) 官方标准的规则约束与动作指令。

    覆盖：官方准则、竞赛规则、地区/Universe 硬性门限（Turnover、Sharpe、Coverage、
    Sub-universe、D1 设置）、算子语义、API/MCP 接口约束，以及管理员原创帖。
    调整因子表达式或提交前必须先调用本工具。
    """
    query = (query or "").strip()
    if not query:
        return "⚠️ query 为空。"
    try:
        tables = get_tables()
        table = tables.get("official")
        if table is None:
            return "⚠️ 官方表不存在，请先运行：python scripts/forum_kb/build_index.py"
        qv = _encode_query(query)
        top_k = max(1, int(top_k))
        # 官方准则单独检索再补管理员帖：管理员帖占比 95%，混检会淹没官方准则
        official = _hybrid(table, query, qv, top_k, where="kind = 'official_doc'")
        admin = _hybrid(table, query, qv, top_k, where="kind = 'admin_post'")
        results = _dedupe(official + admin)
        if not results:
            results = _dedupe(_hybrid(table, query, qv, top_k))
        if not results:
            return "⚠️ 未找到相关规则。"
        # 双保险：官方准则块必须排在管理员帖之前；总量封顶 top_k
        results = sorted(results, key=lambda r: 0 if r.get("kind") == "official_doc" else 1)[:top_k]
        out = ["💡 【官方指令级知识库】检索结果："]
        out.append(f"🔔 [系统强制指令]: 今天是 {datetime.date.today()}。请优先采纳最新记录。\n")
        for idx, row in enumerate(results):
            kind = "官方准则" if row.get("kind") == "official_doc" else "管理员帖"
            out.append(f"【官方规则 {idx + 1} | {kind} | {row.get('source', '')}】")
            out.append(row.get("text", ""))
            out.append("=" * 40)
        return "\n".join(out)
    except Exception as exc:  # noqa: BLE001
        return f"❌ 官方检索失败: {type(exc).__name__}: {exc}"


@mcp.tool()
def search_wqb_forum_experience(query: str, top_k: int = 10) -> str:
    """【次高优先级 / 辅助补充调用】检索 WorldQuant Brain (WQB) 社区论坛经验。

    动态采样：多倍候选池去重后保留最相关前 7 篇，其余随机采样（防信息茧房）；
    全文反查：按帖子 ID 读回 reference/forum 下的完整 Markdown 原文，
    保留代码、算子参数与上下文。
    """
    query = (query or "").strip()
    if not query:
        return "💬 query 为空。"
    top_k = max(1, int(top_k))
    try:
        tables = get_tables()
        table = tables.get("forum")
        if table is None:
            return "⚠️ 论坛经验表不存在，请先运行：python scripts/forum_kb/ingest_forum.py 与 build_index.py"
        qv = _encode_query(query)

        # 候选池：目标 max(top_k*3, 30)，检索窗口逐级翻倍直到凑够或触顶
        target_pool = max(top_k * 3, 30)
        limit = max(target_pool * 10, 300)
        unique: list[tuple[str, str]] = []
        while len(unique) < target_pool and limit <= 5000:
            rows = _hybrid(table, query, qv, limit)
            if not rows:
                break
            unique, seen = [], set()
            for row in rows:
                text = row.get("text", "") or ""
                pid = row.get("post_id") or ""
                if not pid:
                    m = re.search(r"posts/(\d+)", text)
                    pid = m.group(1) if m else ""
                if not pid or pid in seen:
                    continue
                seen.add(pid)
                unique.append((pid, row_text_header(row)))
            if len(unique) >= target_pool or len(rows) < limit:
                break
            limit *= 2

        if not unique:
            return "未能从检索结果中提取到有效的文章ID链接。"

        # 动态采样：前 7 篇核心命中，其余随机扩充
        if len(unique) > top_k:
            core = unique[: min(7, len(unique))]
            rest = unique[len(core):]
            need = top_k - len(core)
            final = core + (random.sample(rest, min(need, len(rest))) if need > 0 else [])
        else:
            final = unique

        out = [f"💬 【社区高纯度经验长文原文】检索结果（共关联 {len(final)} 篇文章）：", ""]
        for idx, (pid, header) in enumerate(final):
            mark = "核心命中" if idx < 7 else "随机扩充"
            out.append(f"==================== 【社区经验文档 {idx + 1} ({mark}) | 文章ID: {pid}】 ====================")
            out.append(header or f"posts/{pid}")
            original = _read_original(pid)
            if original:
                out.append("【文章正文内容】")
                out.append(original)
            else:
                out.append("（未找到原始 Markdown，仅返回检索片段）")
            out.append("")
        return "\n".join(out)
    except Exception as exc:  # noqa: BLE001
        return f"❌ 社区检索失败: {type(exc).__name__}: {exc}"


def _deferred_warmup(delay: float = 0.0) -> None:
    """后台预热：MCP 事件循环起来后，在独立线程里把重型 C 扩展导入并连库/加载模型。

    Windows 实证：事件循环已运行时，工具线程里 import numpy/scipy/torch 会卡死在
    扩展 DLL 加载；因此把整条重依赖链放到预热线程里，工具调用只等待预热完成。
    """
    import importlib
    import time

    time.sleep(delay)
    for mod in ("scipy.special", "sklearn", "torch", "sentence_transformers", "lancedb"):
        try:
            importlib.import_module(mod)
        except Exception:
            pass
    try:
        get_tables()
    except Exception:
        pass
    try:
        get_embedding_model()
    except Exception:
        pass


if __name__ == "__main__":
    # 排障用：WQB_KB_FAULTHANDLER=20 时每 20s 往 stderr 打一次全线程栈
    if os.environ.get("WQB_KB_FAULTHANDLER"):
        import faulthandler

        faulthandler.dump_traceback_later(int(os.environ["WQB_KB_FAULTHANDLER"]), repeat=True)
    if os.environ.get("WQB_KB_PRELOAD", "1") != "0":
        import threading

        threading.Thread(target=_deferred_warmup, daemon=True).start()
    mcp.run()
