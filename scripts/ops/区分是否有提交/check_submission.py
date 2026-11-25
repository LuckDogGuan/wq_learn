"""
check_submission.py — 区分与判别 WorldQuant Brain Alpha 是否已提交

功能：
1. 单个或多个 Alpha ID 提交状态快速判别（支持命令行参数传入或逗号分隔）。
2. 默认模式自动比对基准样例：已提交因子 (LL9x9aA2) 与 未提交因子 (ZY0Zbxqx)。
3. 支持 --summary 模式：统计当前账户在平台上的已提交总数(OS)与未提交总数(IS)，并列出最新提交记录。
4. 完全基于 Core 工业级底座 (BrainClient/sim_api)，具备 429 退避与 Session 保护。
"""

import sys
import os
import argparse
import json
from pathlib import Path

# 确保 Windows 终端 UTF-8 编码安全
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 将项目根目录加入 sys.path 以支持模块导入
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
OPTIMIZE_CODE_DIR = CURRENT_DIR.parent
if str(OPTIMIZE_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(OPTIMIZE_CODE_DIR))

from Core.api import login
from Core.api.sim_api import (
    get_alpha_details,
    check_alpha_submission_status,
    is_alpha_submitted,
    get_user_alphas_page,
)


def format_table(rows: list[dict]) -> str:
    """格式化打印表格。"""
    if not rows:
        return "暂无数据"

    headers = [
        ("Alpha ID", 10),
        ("提交判定", 12),
        ("Stage", 7),
        ("Status", 13),
        ("提交时间 (dateSubmitted)", 27),
        ("Sharpe", 8),
        ("Fitness", 8),
        ("Region/Univ", 16),
        ("表达式代码 (前35字符)", 38),
    ]

    # 分隔线
    line_parts = ["-" * width for _, width in headers]
    sep_line = "+-" + "-+-".join(line_parts) + "-+"

    header_titles = [f"{title:<{width}}" for title, width in headers]
    header_line = "| " + " | ".join(header_titles) + " |"

    output_lines = [sep_line, header_line, sep_line]

    for row in rows:
        alpha_id = str(row.get("alpha_id") or "-")
        is_sub = {True: "[已提交]", False: "[未提交]", None: "[待确认]"}[row.get("is_submitted")]
        stage = str(row.get("stage") or "-")
        status = str(row.get("status") or "-")
        date_sub = str(row.get("date_submitted") or "null (无提交时间)")
        sharpe = f"{row.get('sharpe'):.2f}" if isinstance(row.get("sharpe"), (int, float)) else "-"
        fitness = f"{row.get('fitness'):.2f}" if isinstance(row.get("fitness"), (int, float)) else "-"
        reg = row.get("region") or "-"
        univ = row.get("universe") or "-"
        reg_univ = f"{reg}/{univ}"
        code = str(row.get("code") or "")
        code_short = (code[:32] + "...") if len(code) > 35 else code

        vals = [
            f"{alpha_id:<10}",
            f"{is_sub:<10}",
            f"{stage:<7}",
            f"{status:<13}",
            f"{date_sub:<27}",
            f"{sharpe:<8}",
            f"{fitness:<8}",
            f"{reg_univ:<16}",
            f"{code_short:<38}",
        ]
        output_lines.append("| " + " | ".join(vals) + " |")

    output_lines.append(sep_line)
    return "\n".join(output_lines)


def run_summary(client):
    """查询账户总提交情况。"""
    print("\n" + "=" * 70)
    print("[INFO] 正在查询账户 Alpha 资产全貌（OS 已提交 vs IS 未提交）...")
    print("=" * 70)

    # 1. 查询 OS (已提交)
    resp_os = client.get("/users/self/alphas?limit=5&stage=OS&order=-dateSubmitted")
    os_count = 0
    recent_os_alphas = []
    if resp_os and resp_os.status_code == 200:
        data = resp_os.json()
        os_count = data.get("count", 0)
        recent_os_alphas = data.get("results", [])

    # 2. 查询 IS (未提交)
    resp_is = client.get("/users/self/alphas?limit=1&stage=IS")
    is_count = 0
    if resp_is and resp_is.status_code == 200:
        data = resp_is.json()
        is_count = data.get("count", 0)

    print(f"[*] 已提交因子总数 (OS): {os_count} 个  -->  https://platform.worldquantbrain.com/alphas/submitted")
    print(f"[*] 未提交因子总数 (IS): {is_count} 个  -->  https://platform.worldquantbrain.com/alphas/unsubmitted")

    if recent_os_alphas:
        print("\n[*] 最新提交的 5 个 Alpha 记录：")
        rows = []
        for a in recent_os_alphas:
            rows.append({
                "alpha_id": a.get("id"),
                "is_submitted": True,
                "stage": a.get("stage"),
                "status": a.get("status"),
                "date_submitted": a.get("dateSubmitted"),
                "sharpe": (a.get("is") or {}).get("sharpe"),
                "fitness": (a.get("is") or {}).get("fitness"),
                "region": (a.get("settings") or {}).get("region"),
                "universe": (a.get("settings") or {}).get("universe"),
                "code": (a.get("regular") or {}).get("code"),
            })
        print(format_table(rows))


def main():
    parser = argparse.ArgumentParser(description="WorldQuant Brain Alpha 提交状态判定工具")
    parser.add_argument(
        "alpha_ids",
        nargs="*",
        help="要检查的 Alpha ID 列表 (例如: LL9x9aA2 ZY0Zbxqx)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="查询账户当前的已提交与未提交 Alpha 汇总统计",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出判定结果",
    )

    args = parser.parse_args()

    # 登录客户端
    try:
        client = login()
    except Exception as e:
        print(f"[ERROR] 登录失败，请检查 Password/config.yaml: {e}")
        sys.exit(1)

    if args.summary:
        run_summary(client)
        if not args.alpha_ids:
            return

    # 若未指定参数，默认以用户提供的两个基准因子进行对比演示
    targets = []
    if args.alpha_ids:
        for item in args.alpha_ids:
            for piece in item.replace(",", " ").replace(";", " ").split():
                clean_id = piece.strip()
                if clean_id and clean_id not in targets:
                    targets.append(clean_id)
    else:
        print("[NOTICE] 未指定 Alpha ID，使用基准对比样本: LL9x9aA2 (已提交) 与 ZY0Zbxqx (未提交)\n")
        targets = ["LL9x9aA2", "ZY0Zbxqx"]

    print(f"[SEARCH] 正在查询并诊断 {len(targets)} 个 Alpha 的状态...")
    results = []
    for alpha_id in targets:
        info = check_alpha_submission_status(client, alpha_id)
        results.append(info)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    print("\n" + "=" * 80)
    print(" WorldQuant Brain Alpha 提交状态判定报告")
    print("=" * 80)
    print(format_table(results))

    print("\n[判别依据说明]")
    print("  1. 【第一黄金判据】dateSubmitted 字段：非空即代表已在平台提交，null 代表未提交。")
    print("  2. 【生命周期划分】stage 字段：OS (Out-of-Sample) 代表已提交，IS (In-Sample) 代表未提交。")
    print("  3. 【结构标志】os 字段：已提交因子含有完整的样本外评测结构 os，未提交因子为 null。")
    print("  4. 【平台列表对应】：")
    print("     - 已提交列表: https://platform.worldquantbrain.com/alphas/submitted (API: stage=OS)")
    print("     - 未提交列表: https://platform.worldquantbrain.com/alphas/unsubmitted (API: stage=IS)")


if __name__ == "__main__":
    main()
