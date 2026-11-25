"""Write one simple data sheet for each Region/Category."""

from __future__ import annotations

import json
import re
from pathlib import Path

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.formatting.rule import FormulaRule
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
except ImportError as exc:  # pragma: no cover - exercised by the CLI process
    raise RuntimeError(
        "缺少依赖 openpyxl。请运行: python -m pip install msgpack openpyxl"
    ) from exc


HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(color="FFFFFF", bold=True)
GRADE_COLORS = {
    "GREEN": "C6EFCE",
    "YELLOW": "FFEB9C",
    "RED": "FFC7CE",
    "GRAY": "D9E1F2",
    "T1": "C6EFCE",
    "T2": "DDEBF7",
    "T3": "FCE4D6",
    "T4": "E7E6E6",
}


def _json_default(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    raise TypeError(f"无法序列化 {type(value).__name__}")


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, default=_json_default)


def _cell_value(value):
    if isinstance(value, (list, dict, tuple, set)):
        return json.dumps(value, ensure_ascii=False, default=_json_default)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _write_table(ws, rows, columns=None):
    rows = list(rows)
    if columns is None:
        columns = []
        for row in rows:
            for key in row:
                if key not in columns:
                    columns.append(key)
    if not columns:
        ws.append(["status"])
        ws.append(["NO_ROWS"])
        columns = ["status"]
    else:
        ws.append(columns)
        for row in rows:
            ws.append([_cell_value(row.get(column)) for column in columns])

    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    ws.sheet_view.showGridLines = False
    ws.row_dimensions[1].height = 26

    sample_rows = min(ws.max_row, 250)
    for column_index, column in enumerate(columns, start=1):
        width = len(str(column)) + 2
        for row_index in range(2, sample_rows + 1):
            value = ws.cell(row_index, column_index).value
            if value is not None:
                width = max(width, min(len(str(value)) + 2, 55))
        ws.column_dimensions[get_column_letter(column_index)].width = min(max(width, 10), 55)

    for column_index, column in enumerate(columns, start=1):
        if column in {"dataset_grade", "field_tier"} and ws.max_row >= 2:
            letter = get_column_letter(column_index)
            for label, color in GRADE_COLORS.items():
                ws.conditional_formatting.add(
                    f"{letter}2:{letter}{ws.max_row}",
                    FormulaRule(
                        formula=[f'${letter}2="{label}"'],
                        fill=PatternFill("solid", fgColor=color),
                    ),
                )
        if any(token in column for token in ("coverage", "ratio")):
            for cell in ws[get_column_letter(column_index)][1:]:
                if isinstance(cell.value, (int, float)):
                    cell.number_format = "0.0000"
        if column in {"sharpe", "fitness"}:
            for cell in ws[get_column_letter(column_index)][1:]:
                if isinstance(cell.value, (int, float)):
                    cell.number_format = "0.000"


def safe_filename(category):
    value = re.sub(r"[^0-9A-Za-z._-]+", "_", str(category)).strip("._")
    return value or "UNMAPPED"


SIMPLE_COLUMNS = [
    "region", "delay", "category", "dataset", "dataset_grade", "universe",
    "field", "field_tier", "neutralization", "count", "sharpe", "fitness",
    "coverage_mean", "field_status", "risk_flags",
]


def _threshold(value, mean, cap=None):
    if value == "auto":
        if mean is None:
            return None, False
        return (min(mean, cap) if cap is not None else mean), True
    return value, True


def simple_rows(bundle, filters, means):
    datasets = {row.get("dataset"): row for row in bundle["datasets"]}
    effects_by_field = {}
    for row in bundle["neutralizations"]:
        if row.get("scope") == "datafield":
            effects_by_field.setdefault(row.get("item"), []).append(row)

    sharpe_min, sharpe_available = _threshold(
        filters.get("sharpe_min"), means.get("sharpe"), 0.4
    )
    fitness_min, fitness_available = _threshold(
        filters.get("fitness_min"), means.get("fitness")
    )
    if not sharpe_available or not fitness_available:
        return []

    count_min = filters.get("count_min")
    count_max = filters.get("count_max")
    field_tiers = set(filters.get("field_tiers") or [])
    neutralizations = set(filters.get("neutralizations") or [])
    rows = []

    for field_row in bundle["fields"]:
        field = field_row.get("field")
        tier = (field_row.get("field_tier") or "").upper()
        if field_tiers and tier not in field_tiers:
            continue
        dataset = field_row.get("dataset")
        dataset_row = datasets.get(dataset) or {}
        for effect in effects_by_field.get(field, []):
            neutralization = (effect.get("neutralization") or "").upper()
            count = effect.get("count")
            sharpe = effect.get("sharpe")
            fitness = effect.get("fitness")
            if neutralizations and neutralization not in neutralizations:
                continue
            if count is None or sharpe is None or fitness is None:
                continue
            if count_min is not None and count < count_min:
                continue
            if count_max is not None and count >= count_max:
                continue
            if sharpe_min is not None and sharpe <= sharpe_min:
                continue
            if fitness_min is not None and fitness < fitness_min:
                continue
            rows.append({
                "region": field_row.get("region"), "delay": field_row.get("delay"),
                "category": field_row.get("category"), "dataset": dataset,
                "dataset_grade": dataset_row.get("dataset_grade"),
                "universe": field_row.get("universe"), "field": field,
                "field_tier": field_row.get("field_tier"), "neutralization": neutralization,
                "count": count, "sharpe": sharpe, "fitness": fitness,
                "coverage_mean": field_row.get("coverage_recent_mean"),
                "field_status": field_row.get("field_profile_status"),
                "risk_flags": field_row.get("risk_flags"),
            })
    return sorted(rows, key=lambda row: (-row["sharpe"], -row["fitness"], row["count"]))


def write_category_workbook(path, bundle, filters, means):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = simple_rows(bundle, filters, means)
    workbook = Workbook()
    ws = workbook.active
    ws.title = "数据"
    _write_table(ws, rows, SIMPLE_COLUMNS)
    workbook.save(path)
    return len(rows)


def write_output_readme(output_dir, source, entries, filters):
    output_dir = Path(output_dir)
    lines = [
        "# WebDataScope 导出结果",
        "",
        f"- 数据来源：`{source}`",
        "- 每个 Region/Category 一个 XLSX，每个 XLSX 只有一张筛选后的 `数据` 表。",
        f"- 本次筛选：Count ≥ {filters.get('count_min') if filters.get('count_min') is not None else '不限'}；"
        f"Count < {filters.get('count_max') if filters.get('count_max') is not None else '不限'}；"
        f"Sharpe > {filters.get('sharpe_min') if filters.get('sharpe_min') is not None else '不限'}；"
        f"Fitness ≥ {filters.get('fitness_min') if filters.get('fitness_min') is not None else '不限'}。",
        "- Count、Sharpe、Fitness 是社区已提交因子的统计先验，不等于字段未来回测表现。",
        "",
        "| Region | Delay | Category | 文件 | 筛选后行数 |",
        "|---|---:|---|---|---:|",
    ]
    for entry in entries:
        relative = Path(entry["path"]).relative_to(output_dir).as_posix()
        lines.append(
            f"| {entry['region']} | {entry['delay']} | {entry['category']} | "
            f"[{Path(relative).name}]({relative}) | {entry['rows']} |"
        )
    lines.append("")
    path = output_dir / "README.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def verify_workbook(path, expected_sheets):
    workbook = load_workbook(path, read_only=True, data_only=False)
    missing = [name for name in expected_sheets if name not in workbook.sheetnames]
    errors = []
    for ws in workbook.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and any(
                    token in cell.value
                    for token in ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A")
                ):
                    errors.append(f"{ws.title}!{cell.coordinate}={cell.value}")
    workbook.close()
    return {"missing_sheets": missing, "formula_errors": errors}
