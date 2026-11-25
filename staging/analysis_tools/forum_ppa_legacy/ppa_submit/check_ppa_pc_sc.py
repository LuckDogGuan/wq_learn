"""对 PPA 筛选结果执行只读 PC/SC 检查，并输出 TXT。"""

import argparse
import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "ppa_filtered_results.txt"
DEFAULT_OUTPUT = ROOT / "ppa_pc_sc_results.txt"
sys.path.insert(0, str(ROOT))
from ppa_batch_submitter_source import create_session  # noqa: E402


def read_candidates(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header = next(line.split("\t") for line in lines if line.startswith("alpha_id\t"))
    return [
        dict(zip(header, line.split("\t")))
        for line in lines
        if "\t" in line and not line.startswith("alpha_id")
    ]


async def fetch_checks(candidates: list[dict]) -> list[dict]:
    session = create_session()
    rows = []
    for candidate in candidates:
        response = await session.check(candidate["alpha_id"], log=None)
        rows.append({"candidate": candidate, "status": response.status_code, "body": response.json()})
    return rows


def write_report(path: Path, rows: list[dict]) -> None:
    lines = [
        "PPA PPAC read-only checks",
        f"count={len(rows)}",
        "",
        "alpha_id\tdateCreated\tregion\tuniverse\tdelay\tsharpe\treturns\tturnover\tfitness\tPPAC\tcheck_result",
    ]
    for row in rows:
        checks = ((row.get("body") or {}).get("is") or {}).get("checks") or []
        by_name = {item.get("name"): item for item in checks}
        summary = []
        for name in ("POWER_POOL_CORRELATION",):
            item = by_name.get(name) or {}
            result = item.get("result", "MISSING")
            value = item.get("value")
            summary.append(f"{result}:{value}" if value is not None else str(result))
        result = "PASS" if row.get("status") == 200 else f"HTTP_{row.get('status')}"
        candidate = row["candidate"]
        lines.append("\t".join([
            candidate.get("alpha_id", ""), candidate.get("dateCreated", ""),
            candidate.get("region", ""), candidate.get("universe", ""), candidate.get("delay", ""),
            candidate.get("sharpe", ""), candidate.get("returns", ""), candidate.get("turnover", ""),
            candidate.get("fitness", ""), *summary, result,
        ]))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 PPA 候选的 PC/SC，不提交 Alpha")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows = asyncio.run(fetch_checks(read_candidates(args.input)))
    write_report(args.output, rows)
    print(f"checked: {len(rows)}")
    print(f"TXT: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
