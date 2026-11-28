# -*- coding: utf-8 -*-
"""LLM 原子化：用 Antigravity CLI (agy.exe, gemini-3.8-flash) 把论坛帖子整理成原子 QA 索引。

用法:
  python scripts/forum_kb/atomize.py <md_path> <post_id> --out <out_qa_md> [--model M] [--retries 2]

输出格式对齐检索端（论坛帖 server.py 格式）：`posts/{id} 标题/作者/点赞` 头 + 成对 `Q:`/`A:` 块。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:  # 兼容 `python scripts/forum_kb/atomize.py` 与 `import scripts.forum_kb.atomize`
    from .kb_common import extract_meta, sanitize_qa, validate_qa_text
except ImportError:  # pragma: no cover
    from kb_common import extract_meta, sanitize_qa, validate_qa_text

AGY = os.environ.get("WQB_KB_AGY") or os.path.join(
    os.path.expanduser("~"), ".gemini", "bin", "agy.exe"
)
MODEL = os.environ.get("WQB_KB_LLM_MODEL", "gemini-3.8-flash-medium")
WORKDIR = str(Path(__file__).resolve().parents[2])

# 单篇帖子单次喂给模型的字符上限（Windows 命令行 32K 上限 + 控制单次延迟）
MAX_INPUT_CHARS = 18_000

INSTRUCTIONS = """你是 WorldQuant BRAIN 论坛知识整理助手。把下面这篇论坛帖子正文整理成「原子化 QA」索引，用于向量库混合检索（BM25 + 向量）。

整理要求：
1. 提炼 6~12 个「痛点问题(Q) + 答案(A)」原子对。Q 必须是真实可检索的具体痛点/报错/诉求（例如「MCP 启动握手超时怎么办」「Turnover 偏高用什么算子平滑」「论坛帖子怎么增量爬取」），严禁模糊提问。
2. A 要保留帖子里的具体技术要点：模型名、算子名、参数、文件路径、代码关键行、阈值等；直接给结论与做法，不空话。
3. 自动补全 WQB 平台黑话关键词（SA、RA、正交化、过拟合、中性化、Sharpe、PC、SC、Turnover、回测、D1、Power Pool 等），提升 BM25 词法命中。
4. 严格按下面格式输出（一个块，Q/A 成对，不要任何多余说明、不要 Markdown 标题、不要代码围栏）：

posts/{post_id} 标题:{title} 作者:{author} 点赞:{votes}

Q: <问题1>
A: <答案1>

Q: <问题2>
A: <答案2>

...
"""


def build_prompt(
    md_text: str, post_id: str, title: str, author: str, votes: str, part_info: str = ""
) -> str:
    head = (
        INSTRUCTIONS.replace("{post_id}", post_id)
        .replace("{title}", title)
        .replace("{author}", author)
        .replace("{votes}", votes)
    )
    if part_info:
        head = head.replace(
            "4. 严格按下面格式输出",
            f"4. 本输入是长帖的{part_info}，只提炼本部分内容，Q/A 对本部分独立成立。\n5. 严格按下面格式输出",
        )
    return head + "\n帖子正文如下：\n---\n" + md_text + "\n---\n"


def split_parts(text: str, max_chars: int = MAX_INPUT_CHARS) -> list[str]:
    """长帖按段落边界切成 ≤max_chars 的多段（保证每段都能安全放进命令行）。"""
    if len(text) <= max_chars:
        return [text]
    parts, cur, cur_len = [], [], 0
    for para in text.split("\n\n"):
        if cur and cur_len + len(para) + 2 > max_chars:
            parts.append("\n\n".join(cur))
            cur, cur_len = [], 0
        cur.append(para)
        cur_len += len(para) + 2
    if cur:
        parts.append("\n\n".join(cur))
    return parts


def _strip_header(text: str, post_id: str) -> tuple[str, str]:
    """拆出头部行与 Q/A 正文。"""
    lines = (text or "").split("\n")
    if lines and lines[0].strip().startswith("posts/"):
        return lines[0].strip(), "\n".join(lines[1:]).strip()
    return f"posts/{post_id}", (text or "").strip()


def merge_qa_parts(parts: list[str], post_id: str, max_pairs: int = 30) -> str:
    """多段 QA 合并：头部取第一段，Q/A 去重并封顶 max_pairs 对。"""
    header = f"posts/{post_id}"
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for i, text in enumerate(parts):
        head, body = _strip_header(text, post_id)
        if i == 0 and head.startswith("posts/"):
            header = head
        for block in re.split(r"\n(?=Q[:：])", body):
            m = re.search(r"Q[:：]\s*(.+?)\nA[:：]\s*(.+)", block, re.S)
            if not m:
                continue
            q, a = m.group(1).strip(), m.group(2).strip()
            key = re.sub(r"\s+", "", q)[:60]
            if key in seen:
                continue
            seen.add(key)
            pairs.append((q, a))
            if len(pairs) >= max_pairs:
                break
        if len(pairs) >= max_pairs:
            break
    out = [header, ""]
    for q, a in pairs:
        out.append(f"Q: {q}")
        out.append(f"A: {a}")
        out.append("")
    return "\n".join(out).strip() + "\n"


def parse_agy_output(stdout: str):
    """从 agy --output-format json 的 stdout 里解析 response / status。"""
    s = (stdout or "").strip()
    if not s:
        return None, ""
    try:
        j = json.loads(s)
        return j.get("status"), j.get("response", "")
    except Exception:
        pass
    m = re.search(r"\{.*\}", s, re.S)
    if m:
        try:
            j = json.loads(m.group(0))
            return j.get("status"), j.get("response", "")
        except Exception:
            pass
    return None, s


def call_agy(prompt: str, model: str = MODEL, timeout: int = 600) -> tuple[str | None, str, str]:
    """调用 agy CLI，返回 (status, response, stderr_tail)。"""
    cmd = [
        AGY,
        "--model",
        model,
        "--print",
        prompt,
        "--output-format",
        "json",
        "--dangerously-skip-permissions",
    ]
    r = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=WORKDIR,
        timeout=timeout,
    )
    status, resp = parse_agy_output(r.stdout)
    return status, resp, (r.stderr or "").strip()[-400:]


def atomize_one(
    md_path: str | Path,
    post_id: str,
    out_path: str | Path,
    model: str = MODEL,
    retries: int = 2,
    timeout: int = 600,
    verbose: bool = True,
) -> dict:
    """原子化单篇，落盘 QA 文件。返回 {post_id, ok, reason, seconds}。

    长帖（>MAX_INPUT_CHARS）按段落切段分别原子化再合并去重，规避 Windows
    命令行 32K 上限与单次调用过慢。
    """
    md_path = Path(md_path)
    out_path = Path(out_path)
    t0 = time.time()
    md_text = md_path.read_text(encoding="utf-8", errors="replace")
    title, author, votes = extract_meta(md_text)
    parts = split_parts(md_text)

    got: list[str] = []
    reason = "unknown"
    for idx, part in enumerate(parts):
        info = f"第 {idx + 1}/{len(parts)} 部分" if len(parts) > 1 else ""
        prompt = build_prompt(part, post_id, title, author, votes, info)
        for attempt in range(1, retries + 2):
            try:
                status, resp, err = call_agy(prompt, model=model, timeout=timeout)
            except subprocess.TimeoutExpired:
                reason = "timeout"
                status, resp, err = None, "", "timeout"
            except Exception as exc:  # noqa: BLE001
                reason = f"spawn_error:{type(exc).__name__}"
                status, resp, err = None, "", str(exc)[:200]
            if resp:
                cand = sanitize_qa(resp, post_id)
                ok, why = validate_qa_text(cand, post_id)
                if ok or cand.count("Q:") >= 2:
                    got.append(cand)
                    reason = "ok"
                    break
                reason = f"invalid:{why}"
            if verbose:
                print(
                    f"[retry] {post_id} part={idx + 1}/{len(parts)} attempt={attempt} "
                    f"status={status} reason={reason} err={err[:120]}",
                    flush=True,
                )
            time.sleep(min(3 * attempt, 10))
        if len(got) == 0 and idx == len(parts) - 1:
            break

    if got:
        merged = merge_qa_parts(got, post_id)
        ok, why = validate_qa_text(merged, post_id)
        if ok:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=str(out_path.parent), suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                f.write(merged.strip() + "\n")
            os.replace(tmp, out_path)
            dt = time.time() - t0
            if verbose:
                print(
                    f"[ok] {post_id} q={merged.count('Q:')} chars={len(merged)} "
                    f"parts={len(parts)} {dt:.1f}s",
                    flush=True,
                )
            return {"post_id": post_id, "ok": True, "reason": "ok", "seconds": dt}
        reason = f"invalid_merged:{why}"

    dt = time.time() - t0
    if verbose:
        print(f"[fail] {post_id} {reason} {dt:.1f}s", flush=True)
    return {"post_id": post_id, "ok": False, "reason": reason, "seconds": dt}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("md_path")
    ap.add_argument("post_id")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args(argv)
    res = atomize_one(
        a.md_path, a.post_id, a.out, model=a.model, retries=a.retries, timeout=a.timeout
    )
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
