# -*- coding: utf-8 -*-
"""pytest 引导：把 scripts/forum_kb 与仓库根加入 sys.path。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
FORUM_KB = HERE.parents[1]
ROOT = HERE.parents[3]
for p in (str(FORUM_KB), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
