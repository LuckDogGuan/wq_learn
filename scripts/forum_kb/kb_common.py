# -*- coding: utf-8 -*-
"""WQB 本地知识库公共模块：路径、Markdown 代码保护型切块、QA 校验、原文反查。

三处共用：
  - atomize.py / ingest_forum.py   （论坛帖 LLM 原子化）
  - ingest_official.py             （官方准则 + 管理员帖切块）
  - build_index.py / server.py     （LanceDB 建库与 MCP 检索）
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

WS = Path(__file__).resolve().parents[2]
QA_DIR = WS / "data" / "forum_kb" / "qa"
OFFICIAL_DIR = WS / "data" / "forum_kb" / "official"
DB_DIR = WS / "data" / "forum_kb" / "lancedb_data"
STATE_PATH = WS / "data" / "forum_kb" / "ingest_state.json"

REFERENCE_FORUM = WS / "reference" / "forum"
TOP100_DIR = REFERENCE_FORUM / "top100_2026Q4"
ADMIN_DIR = REFERENCE_FORUM / "admin_posts"
OFFICIAL_GUIDES_DIR = WS / "docs" / "official_guides"

MODEL_NAME = "BAAI/bge-small-zh-v1.5"
QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："
OFFICIAL_TABLE = "wqb_official_guides"
FORUM_TABLE = "wqb_forum_experiences"

POST_ID_RE = re.compile(r"posts/(\d+)")
TRAILING_ID_RE = re.compile(r"_(\d{8,})\.md$")


# ---------------------------------------------------------------- 路径与元数据
def article_id_from_path(p: Path) -> str:
    """从 `R004_ES81271_标题_42184733027991.md` 提取帖子 ID。"""
    m = TRAILING_ID_RE.search(p.name)
    if m:
        return m.group(1)
    m = POST_ID_RE.search(p.read_text(encoding="utf-8", errors="replace")[:2000])
    if m:
        return m.group(1)
    raise ValueError(f"无法从文件名解析帖子 ID: {p}")


def extract_meta(md_text: str) -> tuple[str, str, str]:
    """返回 (标题, 作者, 点赞)。"""
    title = author = votes = ""
    m = re.search(r"^# (.+)$", md_text, re.M)
    if m:
        title = m.group(1).strip()
    m = re.search(r"\*\*作者\*\*:\s*(.+)", md_text)
    if m:
        author = m.group(1).strip()
    m = re.search(r"得票:\s*(\d+)", md_text)
    if m:
        votes = m.group(1)
    return title, author, votes


def find_original_md(post_id: str) -> Path | None:
    """全文反查：reference/forum 下按帖子 ID 找原始 Markdown。"""
    for base in (TOP100_DIR, ADMIN_DIR):
        if not base.exists():
            continue
        for p in base.glob(f"*_{post_id}.md"):
            return p
    return None


# ---------------------------------------------------------------- 切块
def split_markdown_safely(text: str, max_chars: int = 1100, min_chars: int = 180) -> list[str]:
    """代码保护型 Markdown 切块。

    - 严禁在 ``` / ~~~ 代码块内部切分；
    - 优先在二/三级标题处切；超长时只在代码块外的空行/段落处平滑截断；
    - 过短块向前合并，避免碎片。
    """
    text = (text or "").replace("\r\n", "\n")
    blocks: list[str] = []
    cur: list[str] = []
    in_code = False
    fence = ""

    def flush() -> None:
        nonlocal cur
        chunk = "\n".join(cur).strip()
        if chunk:
            blocks.append(chunk)
        cur = []

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            mark = stripped[:3]
            if not in_code:
                in_code, fence = True, mark
            elif mark == fence:
                in_code, fence = False, ""
            cur.append(line)
            continue
        is_heading = bool(re.match(r"^#{2,3}\s", stripped))
        if is_heading and not in_code and cur and len("\n".join(cur)) >= max_chars * 0.9:
            flush()
            cur.append(line)
            continue
        cur.append(line)
        if not in_code and len("\n".join(cur)) > max_chars and not stripped:
            flush()

    flush()

    # 合并过短块
    merged: list[str] = []
    for b in blocks:
        if merged and len(b) < min_chars and not b.lstrip().startswith("#"):
            merged[-1] = merged[-1] + "\n\n" + b
        else:
            merged.append(b)

    # 仍超长的块（无空行长段/长代码块）按 max_chars 硬切，但优先保留代码块整体：
    # 代码块整体长度受控时不再二次切分。
    out: list[str] = []
    for b in merged:
        if len(b) <= max_chars * 2:
            out.append(b)
            continue
        start = 0
        while start < len(b):
            end = min(start + int(max_chars * 1.4), len(b))
            if end < len(b):
                cut = b.rfind("\n\n", start, end)
                if cut > start:
                    end = cut
            out.append(b[start:end].strip())
            start = end
    return [c for c in out if c.strip()]


def chunk_official_doc(path: Path, rel: str) -> list[dict]:
    """官方准则文档 → 带来源头的块。"""
    text = path.read_text(encoding="utf-8", errors="replace")
    rows = []
    for i, chunk in enumerate(split_markdown_safely(text)):
        head = _nearest_heading(text, chunk)
        rows.append(
            {
                "doc_id": f"doc:{path.stem}:{i}",
                "post_id": "",
                "kind": "official_doc",
                "title": path.stem,
                "source": rel,
                "text": f"[官方准则] {rel} 章节:{head}\n{chunk}",
            }
        )
    return rows


def chunk_admin_post(path: Path, rel: str, max_chunks: int = 10) -> list[dict]:
    """管理员原创帖 → 带 posts/{id} 头的块（保留 back-reference 锚点）。

    管理员帖普遍很长（日记/课程作业合辑可达 1MB+），只取前 max_chunks 块，避免
    单帖稀释官方层检索精度。
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    post_id = article_id_from_path(path)
    title, author, votes = extract_meta(text)
    header = f"posts/{post_id} 标题:{title} 作者:{author} 点赞:{votes} 类型:管理员原创帖"
    chunks = split_markdown_safely(text)
    if len(chunks) > max_chunks:
        chunks = chunks[:max_chunks] + ["（原文过长，以上为前 %d 块，完整原文见 %s）" % (max_chunks, rel)]
    rows = []
    for i, chunk in enumerate(chunks):
        rows.append(
            {
                "doc_id": f"post:{post_id}:{i}",
                "post_id": post_id,
                "kind": "admin_post",
                "title": title,
                "source": rel,
                "text": header + "\n" + chunk,
            }
        )
    return rows


def _nearest_heading(full_text: str, chunk: str) -> str:
    idx = full_text.find(chunk.strip()[:60]) if chunk.strip() else -1
    if idx < 0:
        return ""
    heads = re.findall(r"^#{1,3}\s+(.+)$", full_text[:idx], re.M)
    return heads[-1].strip() if heads else ""


# ---------------------------------------------------------------- QA 校验与加载
def validate_qa_text(text: str, post_id: str) -> tuple[bool, str]:
    """校验原子化产出是否可用（检索端格式：posts/{id} 头 + 成对 Q:/A:）。"""
    if not text:
        return False, "empty"
    if f"posts/{post_id}" not in text:
        return False, "missing_header"
    q = len(re.findall(r"^Q[:：]", text, re.M))
    a = len(re.findall(r"^A[:：]", text, re.M))
    if q < 3:
        return False, f"too_few_qa(q={q})"
    if a < q:
        return False, f"unpaired_qa(q={q},a={a})"
    return True, "ok"


def sanitize_qa(text: str, post_id: str) -> str:
    """去掉模型偶发的代码围栏/多余前言，并保证首行为 posts/{id} 头。"""
    s = (text or "").strip()
    s = re.sub(r"^```[a-zA-Z]*\n", "", s)
    s = re.sub(r"\n```$", "", s).strip()
    lines = s.split("\n")
    for i, ln in enumerate(lines):
        if ln.strip().startswith(f"posts/{post_id}"):
            return "\n".join(lines[i:]).strip()
    for i, ln in enumerate(lines):
        if ln.strip().startswith("posts/"):
            lines[i] = re.sub(r"^posts/\S+", f"posts/{post_id}", ln.strip())
            return "\n".join(lines[i:]).strip()
    return s


def load_qa_docs(qa_dir: Path | None = None) -> list[dict]:
    """读取全部可用 QA 文件 → 论坛经验表行。"""
    qa_dir = Path(qa_dir or QA_DIR)
    rows: list[dict] = []
    for p in sorted(qa_dir.glob("*.qa.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        m = POST_ID_RE.search(text)
        post_id = m.group(1) if m else p.stem.split(".")[0]
        ok, why = validate_qa_text(text, post_id)
        if not ok:
            continue
        title, author, votes = extract_meta(text)
        rows.append(
            {
                "doc_id": f"post:{post_id}",
                "post_id": post_id,
                "kind": "forum_qa",
                "title": title,
                "source": f"data/forum_kb/qa/{p.name}",
                "text": text,
            }
        )
    return rows


def row_text_header(row: dict) -> str:
    """从 QA 文本里取出 `posts/{id} ...` 头部，用于拼检索结果。"""
    first = (row.get("text") or "").split("\n", 1)[0]
    return first


# ---------------------------------------------------------------- 状态与输出
def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done": [], "failed": {}, "started_at": ""}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(STATE_PATH)


def iter_post_files(posts_dir: Path) -> Iterable[Path]:
    return sorted(p for p in Path(posts_dir).glob("*.md") if p.is_file())
