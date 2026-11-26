"""手动运行即授权处理所列 Alpha，不再要求二次输入确认。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

LEGACY_CORE_DIR = Path(__file__).resolve().parents[3] / "legacy_core"
if str(LEGACY_CORE_DIR) not in sys.path:
    sys.path.insert(0, str(LEGACY_CORE_DIR))
from Core.api.submission import run_submission_group


# 填写 ID 后手动运行即可；检查通过后会提交，也支持命令行传入 ID。
ALPHA_IDS = ["bl8LnbA6"]


def parse_ids(values: list[str]) -> list[str]:
    raw = values or ALPHA_IDS
    ids: list[str] = []
    for value in raw:
        ids.extend(part.strip() for part in value.replace("，", ",").replace(";", ",").split(","))
    result = list(dict.fromkeys(alpha_id for alpha_id in ids if alpha_id))
    if not result:
        raise ValueError("请填写至少一个 Alpha ID。")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="手动运行，检查并提交指定 Alpha")
    parser.add_argument("ids", nargs="*", help="Alpha ID，支持空格、逗号或分号分隔")
    args = parser.parse_args()
    alpha_ids = parse_ids(args.ids)
    print(f"提交数量：{len(alpha_ids)}；ID：{', '.join(alpha_ids)}")
    # 用户手动启动此入口即为本次授权；服务层仍阻止未授权的其他调用方。
    return 0 if run_submission_group(
        alpha_ids, confirmed_ids=set(alpha_ids)
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
