# -*- coding: utf-8 -*-
"""批量原子化 reference/forum 帖子 → data/forum_kb/qa/{post_id}.qa.md（可续跑）。

用法:
  python scripts/forum_kb/ingest_forum.py --workers 4 --limit 300
  python scripts/forum_kb/ingest_forum.py --posts-dir reference/forum/admin_posts

特性:
  - 已存在且校验通过的 QA 直接跳过（断点续跑）；
  - 并发受控（默认 4，避免 Antigravity CLI 本地状态与账号配额抖动）；
  - 失败记录进 ingest_state.json，退出码非 0 便于巡检发现。
"""
from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:  # 兼容两种导入方式
    from .atomize import MODEL, atomize_one
    from .kb_common import (
        QA_DIR,
        TOP100_DIR,
        WS,
        article_id_from_path,
        iter_post_files,
        load_state,
        save_state,
        validate_qa_text,
    )
except ImportError:  # pragma: no cover
    from atomize import MODEL, atomize_one
    from kb_common import (
        QA_DIR,
        TOP100_DIR,
        WS,
        article_id_from_path,
        iter_post_files,
        load_state,
        save_state,
        validate_qa_text,
    )


def plan_jobs(posts_dir: Path, out_dir: Path, limit: int | None) -> list[tuple[Path, str, Path]]:
    """返回 [(md_path, post_id, out_path)]，跳过已完成且合法的 QA；按文件体积升序。"""
    jobs: list[tuple[Path, str, Path]] = []
    for p in iter_post_files(posts_dir):
        try:
            pid = article_id_from_path(p)
        except ValueError as exc:
            print(f"[skip] {p.name}: {exc}", flush=True)
            continue
        out = out_dir / f"{pid}.qa.md"
        if out.exists():
            ok, _ = validate_qa_text(out.read_text(encoding="utf-8", errors="replace"), pid)
            if ok:
                continue
        jobs.append((p, pid, out))
    jobs.sort(key=lambda j: j[0].stat().st_size)
    if limit:
        jobs = jobs[:limit]
    return jobs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--posts-dir", default=str(TOP100_DIR))
    ap.add_argument("--out-dir", default=str(QA_DIR))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--retries", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args(argv)

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    posts_dir = Path(a.posts_dir)
    if not posts_dir.is_absolute():
        posts_dir = WS / posts_dir
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    jobs = plan_jobs(posts_dir, out_dir, a.limit)
    state = load_state()
    state["started_at"] = state.get("started_at") or time.strftime("%Y-%m-%dT%H:%M:%S")
    print(
        f"[plan] posts_dir={posts_dir} pending={len(jobs)} workers={a.workers} model={a.model}",
        flush=True,
    )
    if not jobs:
        print("[plan] nothing to do", flush=True)
        return 0

    ok = fail = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=max(1, a.workers)) as pool:
        futs = {
            pool.submit(
                atomize_one,
                md,
                pid,
                out,
                model=a.model,
                retries=a.retries,
                timeout=a.timeout,
            ): pid
            for md, pid, out in jobs
        }
        for i, fut in enumerate(as_completed(futs), 1):
            pid = futs[fut]
            try:
                res = fut.result()
            except Exception as exc:  # noqa: BLE001
                res = {"post_id": pid, "ok": False, "reason": f"driver:{exc}"[:160]}
            if res["ok"]:
                ok += 1
                state.setdefault("done", [])
                if pid not in state["done"]:
                    state["done"].append(pid)
                state.get("failed", {}).pop(pid, None)
            else:
                fail += 1
                state.setdefault("failed", {})[pid] = res.get("reason", "unknown")
            if i % 5 == 0 or i == len(jobs):
                save_state(state)
                print(
                    f"[progress] {i}/{len(jobs)} ok={ok} fail={fail} "
                    f"elapsed={time.time() - t0:.0f}s",
                    flush=True,
                )
    save_state(state)
    print(f"[done] ok={ok} fail={fail} total={len(jobs)} elapsed={time.time() - t0:.0f}s", flush=True)
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
