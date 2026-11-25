"""Build the detailed PPA workbook without Node or generated preview files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


BLUE = "1F4E78"
LIGHT_BLUE = "D9EAF7"
STATUS_FILL = {"FAIL": "FCE4D6", "PENDING": "FFF2CC", "PPA_PASS": "E2F0D9"}


def text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(map(str, value))
    return str(value)


def settings(record: dict) -> dict:
    return record.get("settings", {}) if isinstance(record.get("settings"), dict) else {}


def table(sheet, headers: list[str], rows: list[list[object]]) -> None:
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    for cell in sheet[1]:
        cell.fill = PatternFill("solid", fgColor=BLUE)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for index, column in enumerate(sheet.columns, 1):
        width = min(60, max(12, max(len(str(cell.value or "")) for cell in column) + 2))
        sheet.column_dimensions[get_column_letter(index)].width = width


def build(input_path: Path, output_path: Path) -> None:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    steps = payload.get("steps", [])
    scope = payload.get("scope", {})
    standard = payload.get("standard", {})
    req = scope.get("core_requirements", {})
    entry = standard.get("entry_requirements", {})

    workbook = Workbook()
    overview = workbook.active
    overview.title = "概览"
    for name in ("全部候选", "PPAC后全部因子", "检查明细", "字段归属", "规则与来源"):
        workbook.create_sheet(name)

    overview.append(["PPA Alpha 只读筛选报告"])
    overview["A1"].font = Font(bold=True, size=16, color="FFFFFF")
    overview["A1"].fill = PatternFill("solid", fgColor="17365D")
    overview.merge_cells("A1:F1")
    overview.append([])
    for key, value in (("主题", scope.get("theme_name")),
                       ("主题日期", f"{scope.get('duration', {}).get('start_date', '')} - {scope.get('duration', {}).get('end_date', '')}"),
                       ("Region", req.get("region")), ("Delay", req.get("delay")),
                       ("Universe", req.get("universe")),
                       ("Neutralization", text(req.get("neutralization"))),
                       ("禁用 Dataset", text(req.get("forbidden_datasets"))),
                       ("禁用字段配置", scope.get("forbidden_field_rules_source") or scope.get("forbidden_field_rules_file"))):
        overview.append([key, value])
    table_start = overview.max_row + 2
    overview.cell(table_start, 1, "阶段")
    overview.cell(table_start, 2, "输入")
    overview.cell(table_start, 3, "剩余")
    overview.cell(table_start, 4, "排除")
    overview.cell(table_start, 5, "待定")
    for cell in overview[table_start]:
        cell.fill = PatternFill("solid", fgColor=BLUE)
        cell.font = Font(bold=True, color="FFFFFF")
    for step in steps:
        overview.append([step.get("stage"), step.get("input"), step.get("remaining"), step.get("excluded"), step.get("pending")])
    overview.column_dimensions["A"].width = 42
    overview.column_dimensions["B"].width = 48
    for column in "CDE":
        overview.column_dimensions[column].width = 14

    all_rows = []
    forbidden = {str(x).lower() for x in req.get("forbidden_datasets", [])}
    for record in records:
        settings_value = settings(record)
        all_rows.append([
            record.get("alpha_id"), record.get("classification"), record.get("excluded_at", ""),
            "是" if record.get("survived_ppac") else "否", record.get("expression"),
            settings_value.get("region"), settings_value.get("delay"), settings_value.get("universe"),
            settings_value.get("neutralization"), record.get("sharpe"), record.get("fitness"),
            record.get("turnover"), record.get("operators"), text(record.get("fields")),
            text(record.get("datasets")), text([d for d in record.get("datasets", []) if str(d).lower() in forbidden]),
            text(record.get("reasons")), text(record.get("pipeline_reasons")),
        ])
    all_sheet = workbook["全部候选"]
    table(all_sheet, ["Alpha ID", "Status", "排除阶段", "PPAC后保留", "Expression", "Region", "Delay", "Universe", "Neutralization", "Sharpe", "Fitness", "Turnover", "Operators", "Fields", "Datasets", "Forbidden 命中", "Reasons", "Pipeline Reasons"], all_rows)
    for row in all_sheet.iter_rows(min_row=2):
        status = row[1].value
        if status in STATUS_FILL:
            row[1].fill = PatternFill("solid", fgColor=STATUS_FILL[status])

    ppac_rows = []
    for record in records:
        if not record.get("survived_ppac"):
            continue
        check = next((item for item in record.get("checks", []) if item.get("name") == "POWER_POOL_CORRELATION"), {})
        ppac_rows.append([record.get("alpha_id"), record.get("classification"), record.get("expression"), record.get("sharpe"), record.get("fitness"), record.get("turnover"), check.get("result", "MISSING"), check.get("value", ""), text(record.get("fields")), text(record.get("datasets")), text(record.get("reasons"))])
    if not ppac_rows:
        ppac_rows = [["", "", "本轮没有因子通过 PPAC 阶段；全部在 forbidden_datasets 阶段排除。", "", "", "", "", "", "", "", ""]]
    table(workbook["PPAC后全部因子"], ["Alpha ID", "Status", "Expression", "Sharpe", "Fitness", "Turnover", "PPAC Check", "PPAC Value", "Fields", "Datasets", "Reasons"], ppac_rows)

    check_rows = [[record.get("alpha_id"), check.get("name"), check.get("result", check.get("status", "")), text(check.get("limit", "")), text(check.get("value", "")), check.get("name") in {"MATCHES_THEMES", "PURE_POWER_POOL_THEME", "POWER_POOL_CORRELATION", "POWER_POOL_DESCRIPTION_LENGTH", "POWER_POOL_DESCRIPTION_FORMAT"}] for record in records for check in record.get("checks", [])]
    table(workbook["检查明细"], ["Alpha ID", "Check Name", "Result", "Limit", "Value", "是否 PPAC"], check_rows)

    field_rows = [[record.get("alpha_id"), field.get("field_id"), field.get("dataset_id"), field.get("dataset_name"), field.get("type"), field.get("source")] for record in records for field in record.get("resolved_field_metadata", [])]
    table(workbook["字段归属"], ["Alpha ID", "Field ID", "Dataset ID", "Dataset Name", "Type", "Source"], field_rows)

    rule_rows = [["PPA 范围 JSON", key, text(value)] for key, value in (("theme_name", scope.get("theme_name")), ("duration", scope.get("duration")), ("region", req.get("region")), ("delay", req.get("delay")), ("universe", req.get("universe")), ("neutralization", req.get("neutralization")), ("forbidden_datasets", req.get("forbidden_datasets")), ("forbidden_field_rules_file", scope.get("forbidden_field_rules_file")), ("forbidden_field_rules", scope.get("forbidden_field_rules")))]
    rule_rows.extend([["ppa_alpha_standard.json", key, text(value)] for key, value in entry.items()])
    table(workbook["规则与来源"], ["来源", "规则", "值"], rule_rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output_path)
    load_workbook(output_path, read_only=True).close()
    print(f"EXPORTED {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python build_ppa_excel.py screening_records.json output.xlsx")
    build(Path(sys.argv[1]), Path(sys.argv[2]))
