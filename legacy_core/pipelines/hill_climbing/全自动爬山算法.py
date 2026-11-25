"""全自动爬山算法兼容入口。

原启动命令保持不变；实现已拆到 ``hill_climbing`` 包。
"""

import sys
from pathlib import Path


HILL_ROOT = Path(__file__).resolve().parent
OPTIMIZATION_ROOT = HILL_ROOT.parent
for path in (HILL_ROOT, OPTIMIZATION_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from hill_climbing.optimizer import *  # noqa: F401,F403,E402


if __name__ == '__main__':
    main()
