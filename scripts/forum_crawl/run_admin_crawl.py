# -*- coding: utf-8 -*-
"""管理员论坛帖子爬取入口：复用 wq_download_user_skills 的爬虫逻辑，输出到本目录。

目标用户：WL13229 (12285040305687)、KH94146 (15208008142871)，均为 support 社区管理员。
"""
import asyncio
import sys
from pathlib import Path

TARGET_DIR = Path(__file__).resolve().parent
SKILL_DIR = Path(r"D:\code\Skills\wq_download_user_skills")

REPLACEMENTS = [
    (
        'MAP_FILE = Path("reference/top100Rank-2026Q2/user_activity/advisor_zendesk_map.json")',
        f'MAP_FILE = Path({str(TARGET_DIR / "advisor_zendesk_map.json")!r})',
    ),
    (
        'rank_file = Path("reference/top100Rank-2026Q2/user_rank.md")',
        f'rank_file = Path({str(TARGET_DIR / "user_rank.md")!r})',
    ),
    (
        'output_base_dir = Path("reference/top100Rank-2026Q2/user_activity")',
        f'output_base_dir = Path({str(TARGET_DIR)!r})',
    ),
]


def build_namespace() -> dict:
    src = (SKILL_DIR / "extract_top100_activity.py").read_text(encoding="utf-8")
    for old, new in REPLACEMENTS:
        if old not in src:
            raise RuntimeError(f"补丁失败，未找到原始片段: {old}")
        src = src.replace(old, new)
    ns = {"__name__": "admin_forum_crawler", "__file__": str(SKILL_DIR / "extract_top100_activity.py")}
    exec(compile(src, "extract_top100_activity_patched.py", "exec"), ns)
    return ns


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ns = build_namespace()
    asyncio.run(ns["main"]())
