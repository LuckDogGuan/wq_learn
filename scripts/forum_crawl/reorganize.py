# -*- coding: utf-8 -*-
"""把管理员爬取结果按作者身份分到子文件夹，并修复图片与帖子间本地链接。

分类规则（依据文件名前缀，由爬虫阶段已判定作者身份）：
- [Commented] 开头 -> 参与回复的帖子/
- [L2] 开头       -> 引用的关联帖L2/
- 其余            -> 自己发布的帖子/
"""
import os
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
ADMINS = ["WL13229", "KH94146"]

CATEGORY_DIRS = {
    "[Commented]": "参与回复的帖子",
    "[L2]": "引用的关联帖L2",
    "": "自己发布的帖子",
}


def category_of(name: str) -> str:
    for prefix, folder in CATEGORY_DIRS.items():
        if prefix and name.startswith(prefix):
            return folder
    return CATEGORY_DIRS[""]


def main():
    move_map = {}
    for adv in ADMINS:
        adv_dir = BASE / adv
        for folder in CATEGORY_DIRS.values():
            (adv_dir / folder).mkdir(exist_ok=True)
        for md in adv_dir.glob("*.md"):
            target = adv_dir / category_of(md.name) / md.name
            md.rename(target)
            move_map[md.resolve().as_posix()] = target.resolve().as_posix()
        print(f"{adv}: moved {len([p for p in move_map if f'/{adv}/' in p])} files")

    img_link = re.compile(r'(\]\()(images/[^)]+)\)')
    md_link = re.compile(r'(\])\(([^)]+\.md)\)')

    reverse = {n: o for o, n in move_map.items()}
    fixed_images = fixed_links = 0
    for new_path in move_map.values():
        path = Path(new_path)
        old_dir = Path(os.path.dirname(reverse[new_path]))
        content = path.read_text(encoding="utf-8")
        original = content

        content = img_link.sub(r'\1../\2)', content)

        def remap(match):
            nonlocal fixed_links
            rel = match.group(2)
            resolved = (old_dir / rel).resolve().as_posix()
            if resolved in move_map:
                fixed_links += 1
                new_rel = os.path.relpath(move_map[resolved], path.parent).replace('\\', '/')
                return f"{match.group(1)}({new_rel})"
            return match.group(0)

        content = md_link.sub(remap, content)

        if content != original:
            path.write_text(content, encoding="utf-8")
            if img_link.search(original):
                fixed_images += 1

    print(f"Done. image refs rewritten in {fixed_images} files; md links remapped {fixed_links} times.")

    broken = 0
    for new_path in move_map.values():
        path = Path(new_path)
        content = path.read_text(encoding="utf-8")
        for m in md_link.finditer(content):
            target = (path.parent / m.group(2))
            if not target.exists():
                print("BROKEN:", path.name, "->", m.group(2))
                broken += 1
        for m in re.finditer(r'\.\./(images/[^)]+)', content):
            if not (path.parent / m.group(0)).exists():
                print("MISSING IMG:", path.name, m.group(1))
                broken += 1
    print(f"Broken references: {broken}")


if __name__ == "__main__":
    main()
