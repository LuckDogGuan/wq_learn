# -*- coding: utf-8 -*-
"""scripts/forum_kb 单测：切块 / QA 校验 / 批量计划 / MCP 懒加载与检索装配。

约束：不联网、不加载 torch、不调用 Antigravity CLI。
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import atomize
import ingest_forum
import kb_common as kb
import server

FORUM_KB_DIR = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------------ 切块
def test_split_keeps_code_block_intact() -> None:
    code = "```python\n" + "\n".join(f"x_{i} = ts_rank(close, {i})" for i in range(40)) + "\n```"
    text = "## 第一节\n\n" + ("正文段落。" * 30) + "\n\n" + code + "\n\n## 第二节\n\n" + ("结论。" * 20)
    chunks = kb.split_markdown_safely(text, max_chars=400)
    assert chunks
    joined = "\n\n".join(chunks)
    assert "x_0 = ts_rank(close, 0)" in joined
    assert joined.count("```") % 2 == 0, "代码围栏必须成对，不能被切断"
    assert any("第二节" in c for c in chunks)


def test_split_does_not_emit_tiny_fragments() -> None:
    text = "\n\n".join(f"## 小节{i}\n" + "内容行。" * 60 for i in range(6))
    chunks = kb.split_markdown_safely(text, max_chars=500, min_chars=120)
    assert all(len(c) >= 120 for c in chunks), [len(c) for c in chunks]


def test_chunk_admin_post_caps_chunks(tmp_path: Path) -> None:
    src = tmp_path / "R001_A_管理员帖_42184733027991.md"
    src.write_text(
        "# 管理员帖标题\n\n- **作者**: WL13229\n- **发布时间/热度**: 1个月前, 得票: 12\n\n"
        + "\n\n".join(f"## 小节{i}\n" + "正文内容。" * 80 for i in range(8)),
        encoding="utf-8",
    )
    rows = kb.chunk_admin_post(src, "reference/forum/admin_posts/R001_A_管理员帖_42184733027991.md", max_chunks=3)
    assert 1 <= len(rows) <= 4
    assert all("posts/42184733027991" in r["text"] for r in rows)
    assert rows[0]["post_id"] == "42184733027991"


# ------------------------------------------------------------------ QA 校验
def test_validate_qa_accepts_well_formed_text() -> None:
    ok_text = (
        "posts/123 标题:测试 作者:ann 点赞:3\n\n"
        "Q: Turnover 太高怎么办？\nA: 用 ts_decay_linear 平滑。\n\n"
        "Q: PC 过高怎么办？\nA: 池内正交剪枝，SC < 0.65。\n\n"
        "Q: D1 还是 D0？\nA: 严格 D1-only。\n"
    )
    ok, why = kb.validate_qa_text(ok_text, "123")
    assert ok, why


def test_validate_qa_rejects_missing_header_and_unpaired() -> None:
    assert kb.validate_qa_text("Q: a\nA: b", "123")[0] is False
    bad = "posts/123 标题:t\n\nQ: a\nA: b\n\nQ: c\nA: d\n\nQ: e\n"
    ok, why = kb.validate_qa_text(bad, "123")
    assert not ok and "unpaired" in why


def test_sanitize_qa_strips_fence_and_normalizes_id() -> None:
    raw = "```\nposts/999 标题:x\n\nQ: q\nA: a\n```"
    out = kb.sanitize_qa(raw, "42")
    assert out.startswith("posts/42 标题:x")
    assert out.endswith("A: a")
    assert not out.startswith("```")


# ------------------------------------------------------------------ 长帖切段与合并
def test_split_parts_bounds_and_covers_content() -> None:
    paras = [("段落%d。" % i) * 200 for i in range(30)]  # 每段约 1600 字符
    text = "\n\n".join(paras)
    parts = atomize.split_parts(text, max_chars=5000)
    assert len(parts) > 1
    assert all(len(p) <= 5000 for p in parts)
    assert "段落0" in parts[0] and "段落29" in parts[-1]
    assert text.replace("\n\n", "") == "".join(p.replace("\n\n", "") for p in parts)


def test_merge_qa_parts_dedupes_and_keeps_first_header() -> None:
    p1 = "posts/9 标题:A 作者:x 点赞:1\n\nQ: 重复问题\nA: 答案1\n\nQ: 唯一问题一\nA: a1"
    p2 = "posts/9 标题:A 作者:x 点赞:1\n\nQ: 重复问题\nA: 答案2\n\nQ: 唯一问题二\nA: a2"
    merged = atomize.merge_qa_parts([p1, p2], "9")
    assert merged.startswith("posts/9 标题:A")
    assert merged.count("重复问题") == 1
    assert "唯一问题一" in merged and "唯一问题二" in merged


# ------------------------------------------------------------------ 批量计划
def test_plan_jobs_skips_valid_and_sorts_by_size(tmp_path: Path) -> None:
    posts = tmp_path / "posts"
    out = tmp_path / "qa"
    posts.mkdir()
    out.mkdir()
    big_src = "x" * 900
    for pid, body in (("11111111", "a"), ("22222222", "b" * 300), ("33333333", big_src)):
        (posts / f"R001_A_标题_{pid}.md").write_text(
            f"# 标题{pid}\n\n- **作者**: ann\n- **发布时间/热度**: 1个月前, 得票: 5\n\n## 帖子正文\n\n{body}",
            encoding="utf-8",
        )
    good = (
        "posts/22222222 标题:x 作者:ann 点赞:5\n\nQ: q1\nA: a1\n\nQ: q2\nA: a2\n\nQ: q3\nA: a3\n"
    )
    (out / "22222222.qa.md").write_text(good, encoding="utf-8")
    (out / "11111111.qa.md").write_text("broken", encoding="utf-8")

    jobs = ingest_forum.plan_jobs(posts, out, limit=None)
    pids = [pid for _, pid, _ in jobs]
    assert pids == ["11111111", "33333333"], pids  # 22222222 已完成跳过；按体积升序


# ------------------------------------------------------------------ MCP 懒加载
class _FakeQuery:
    def __init__(self, rows, where=None):
        self._rows = rows
        self._where = where

    def text(self, _q):
        return self

    def vector(self, _v):
        return self

    def where(self, clause):
        return _FakeQuery(self._rows, clause)

    def limit(self, n):
        rows = self._rows
        if self._where and "kind = " in self._where:
            want = self._where.split("kind = ")[1].strip().strip("'\"")
            rows = [r for r in rows if r.get("kind") == want]
        return _FakeQuery(rows[:n], self._where)

    def to_list(self):
        rows = self._rows
        if self._where and "kind = " in self._where:
            want = self._where.split("kind = ")[1].strip().strip("'\"")
            rows = [r for r in rows if r.get("kind") == want]
        return [dict(r) for r in rows]


class _FakeTable:
    def __init__(self, rows):
        self._rows = rows

    def search(self, *_a, **_k):
        return _FakeQuery(self._rows)


class _FakeVec(list):
    def tolist(self):
        return list(self)


class _FakeModel:
    def encode(self, *_a, **_k):
        return _FakeVec([0.1] * 512)


def _reset_server_state() -> None:
    server._db_tables = None
    server._model_instance = None
    server._original_md_cache.clear()


def test_server_import_is_lazy() -> None:
    assert hasattr(server, "mcp")
    assert server._db_tables is None and server._model_instance is None
    if not server.PLATFORM_PRELOAD:
        # Linux/macOS 走纯懒加载：进程启动不碰 torch/BGE
        assert "torch" not in sys.modules, "MCP 进程启动时严禁导入 torch"
        assert "sentence_transformers" not in sys.modules, "MCP 进程启动时严禁加载 BGE"
    else:
        # Windows 受 DLL 加载死锁限制，只在事件循环前预导入库，模型权重仍懒加载
        assert server._model_instance is None


def test_official_tool_puts_official_docs_first(monkeypatch) -> None:
    _reset_server_state()
    rows = [
        {"doc_id": "post:1:0", "post_id": "1", "kind": "admin_post",
         "text": "posts/1 标题:管理员帖\n正文内容"},
        {"doc_id": "doc:guide:0", "post_id": "", "kind": "official_doc",
         "text": "[官方准则] docs/guide.md 章节:门限\nTurnover 硬上限 70%。"},
    ]
    server._db_tables = {"official": _FakeTable(rows), "forum": _FakeTable([])}
    monkeypatch.setattr(server, "get_embedding_model", lambda: _FakeModel())

    out = server.search_wqb_official_guidelines("Turnover 上限", top_k=5)
    assert "官方指令级知识库" in out
    assert out.index("官方准则") < out.index("管理员帖"), "官方准则必须排在管理员帖之前"
    assert "Turnover 硬上限" in out


def test_forum_tool_back_references_original_markdown(monkeypatch) -> None:
    _reset_server_state()
    pid = "42184733027991"
    rows = [
        {"doc_id": f"post:{pid}", "post_id": pid, "kind": "forum_qa",
         "text": f"posts/{pid} 标题:浅谈我的一二三阶开发流程 作者:ES81271 点赞:19\n\nQ: 三阶怎么分工？\nA: 见正文。"},
    ]
    server._db_tables = {"official": _FakeTable([]), "forum": _FakeTable(rows)}
    monkeypatch.setattr(server, "get_embedding_model", lambda: _FakeModel())

    out = server.search_wqb_forum_experience("三阶开发流程", top_k=3)
    assert "社区高纯度经验长文原文" in out
    assert pid in out
    assert "【文章正文内容】" in out
    assert "浅谈我的一二三阶开发流程" in out  # 全文反查命中原始 Markdown


def test_tools_report_missing_index_gracefully(monkeypatch) -> None:
    _reset_server_state()
    server._db_tables = {}
    monkeypatch.setattr(server, "get_embedding_model", lambda: _FakeModel())
    assert "官方表不存在" in server.search_wqb_official_guidelines("x")
    assert "论坛经验表不存在" in server.search_wqb_forum_experience("x")


def test_empty_query_short_circuits() -> None:
    assert "query 为空" in server.search_wqb_official_guidelines("  ")
    assert "query 为空" in server.search_wqb_forum_experience("")


# ------------------------------------------------------------------ AST 校验
def test_all_forum_kb_modules_are_ast_clean() -> None:
    files = sorted(FORUM_KB_DIR.glob("*.py"))
    assert len(files) >= 5
    for p in files:
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        # 禁止顶层重型导入（懒加载红线）
        if p.name == "server.py":
            top = {n.names[0].name.split(".")[0] for n in tree.body
                   if isinstance(n, ast.Import)}
            top |= {n.module.split(".")[0] for n in tree.body
                    if isinstance(n, ast.ImportFrom) and n.module}
            assert "torch" not in top and "sentence_transformers" not in top
