#!/usr/bin/env python3
"""Export WebDataScope evidence as Region/Delay/Universe/Category workbooks.

This tool is read-only. Dataset community grades and exact-archive field tiers
are separate evidence and never imply Alpha performance or submission status.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    from webdata_classifier import (
        annual_rows,
        classify_field,
        dataset_grade,
        flatten_neutralizations,
        load_rules,
        map_category,
        number,
    )
    from webdata_exporter import (
        safe_filename,
        verify_workbook,
        write_category_workbook,
        write_json,
        write_output_readme,
    )
    from webdata_loader import discover_sources, inventory, parse_region_delay, resolve_source
except RuntimeError as exc:
    print(exc, file=sys.stderr)
    raise SystemExit(2) from exc


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RULES = SCRIPT_DIR / "tier_rules.json"
EXPECTED_SHEETS = ["数据"]


def csv_filter(value, upper=False):
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "all":
        return None
    items = {item.strip() for item in text.split(",") if item.strip()}
    return {item.upper() for item in items} if upper else {item.lower() for item in items}


def delay_filter(value):
    items = csv_filter(value)
    if items is None:
        return None
    try:
        return {int(item) for item in items}
    except ValueError as exc:
        raise ValueError("--delay 必须是整数、逗号分隔整数、空值或 all") from exc


def metric_filter(value, name, *, allow_auto=False, integer=False):
    text = "" if value is None else str(value).strip()
    if not text or text.lower() == "all":
        return None
    if allow_auto and text.lower() == "auto":
        return "auto"
    try:
        result = int(text) if integer else float(text)
    except ValueError as exc:
        expected = "整数、空值或 all" if integer else "数字、auto、空值或 all"
        raise ValueError(f"{name} 必须是{expected}") from exc
    if integer and result < 0:
        raise ValueError(f"{name} 不能小于 0")
    return result


def build_parser():
    parser = argparse.ArgumentParser(
        description="WebDataScope 离线分类导出：Region → Delay → Universe → Category → Dataset → Field",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python webdata_quality.py --source WebData_20260219_V0.10.9.zip "
            "--region GLB --delay 1 --universe TOP3000 --categories news,model "
            "--field-tiers T1,T2 --count-min 5 --count-max 500 "
            "--sharpe-min auto --fitness-min auto --output result\\GLB_TOP3000\n\n"
            "筛选参数省略、传空字符串或 all 均表示不过滤。"
        ),
    )
    parser.add_argument("--source", help="WebDataScope ZIP、插件根目录或 data 目录")
    parser.add_argument("--zip", dest="legacy_zip", help="兼容旧命令；等同 --source")
    parser.add_argument("--region", help="Region，支持逗号分隔；空/all 表示全部")
    parser.add_argument("--delay", default="1", help="Delay，默认 1；空/all 表示全部")
    parser.add_argument("--universe", help="Universe，支持逗号分隔；空/all 表示全部")
    parser.add_argument("--universes", action="store_true", help="兼容旧命令；比较全部 Universe")
    parser.add_argument("--categories", help="Category，支持逗号分隔；空/all 表示全部")
    parser.add_argument("--dataset-grades", help="GREEN,YELLOW,RED,GRAY；空/all 表示全部")
    parser.add_argument("--field-tiers", help="T1,T2,T3,T4；空/all 表示全部")
    parser.add_argument("--neutralizations", help="中性化，支持逗号分隔；空/all 表示全部")
    parser.add_argument("--count-min", default="5", help="Count 下限（包含），默认 5；空/all 关闭")
    parser.add_argument("--count-max", default="500", help="Count 上限（不包含），默认 500；空/all 关闭")
    parser.add_argument("--sharpe-min", default="auto", help="Sharpe 下限（严格大于）；默认 auto；空/all 关闭")
    parser.add_argument("--fitness-min", default="auto", help="Fitness 下限（大于等于）；默认 auto；空/all 关闭")
    parser.add_argument("--dataset", help="仅处理一个数据集；保留旧精确查询用法")
    parser.add_argument("--output", help="按 Region/Category 保存 XLSX 的输出目录")
    parser.add_argument("--tier-config", default=str(DEFAULT_RULES), help="字段档位 JSON 配置")
    parser.add_argument("--json-out", help="兼容旧命令：另存完整 JSON 到指定位置")
    parser.add_argument("--fields", action="store_true", help="在控制台打印字段摘要")
    parser.add_argument("--top", type=int, default=30, help="控制台数据集最多显示数量")
    parser.add_argument("--field-top", type=int, default=30, help="控制台字段最多显示数量")
    parser.add_argument("--universe-top", type=int, default=20, help="保留旧参数兼容")
    return parser


def _unzip_help(path):
    path = Path(path) if path else SCRIPT_DIR / "WebData_20260219_V0.10.9.zip"
    destination = path.with_suffix("")
    return (
        "备用解压命令（工具本身可直接读取正常 ZIP）:\n"
        f'  Expand-Archive -LiteralPath "{path}" -DestinationPath "{destination}"'
    )


def fail_with_help(parser, message, source=None):
    print(f"错误: {message}\n", file=sys.stderr)
    parser.print_help(sys.stderr)
    candidates = discover_sources(SCRIPT_DIR)
    if candidates:
        print("\n脚本旁检测到:", file=sys.stderr)
        for candidate in candidates:
            print(f"  {candidate}", file=sys.stderr)
    print("\n" + _unzip_help(source), file=sys.stderr)
    return 2


def _metric_row(stats, prefix=""):
    stats = stats or {}
    return {
        f"{prefix}count": number(stats.get("count")),
        f"{prefix}sharpe": number(stats.get("sharpe_ratio")),
        f"{prefix}fitness": number(stats.get("fitness_ratio")),
    }


def _coordinate_selected(key, regions, delays):
    region, delay = parse_region_delay(key)
    return region is not None and (regions is None or region in regions) and (delays is None or delay in delays)


def _archive_selected(row, universes, dataset):
    return (universes is None or row["universe"].upper() in universes) and (not dataset or row["dataset"] == dataset)


def build_ledger(source, rules, filters):
    info = source.load_bin("data/oth/info_data.bin")
    osis = source.load_bin("data/oth/osis_data.bin")
    archives = inventory(source, info)
    parsed_archive_paths = {row["path"] for row in archives}
    unparsed_archive_paths = [
        path for path in source.archive_names() if path not in parsed_archive_paths
    ]
    selected_keys = [key for key in sorted(info) if _coordinate_selected(key, filters["regions"], filters["delays"])]
    if not selected_keys:
        raise ValueError(f"没有匹配的 Region/Delay；快照可用坐标: {', '.join(sorted(info))}")

    selected_archives = [
        row for row in archives
        if f"{row['region']}_{row['delay']}" in selected_keys
        and _archive_selected(row, filters["universes"], filters["dataset"])
    ]
    archives_by_key = defaultdict(list)
    for row in selected_archives:
        archives_by_key[f"{row['region']}_{row['delay']}"].append(row)

    categories = {}
    coordinate_means = {}
    dataset_rows, exact_fields, annual = [], [], []
    neutralizations, unobserved, community_fields, category_stats = [], [], [], []
    audit = {
        "exact_field_records": 0,
        "exported_exact_field_records": 0,
        "community_field_records": 0,
        "neutralization_only_fields": 0,
        "unmapped_input_records": 0,
        "unmapped_field_records": 0,
    }

    for key in selected_keys:
        region, delay = parse_region_delay(key)
        coordinate = {"region": region, "delay": delay, "region_delay": key}
        region_info = info[key]
        isos = region_info.get("isos") or {}
        neutral = region_info.get("neutralization") or {}
        osis_region = osis.get(key) or {}
        isos_categories = isos.get("category") or {}
        category_names = set(isos_categories) | set(osis_region.get("category") or {}) | set(neutral.get("category") or {})
        mean_sharpe = number((isos.get("mean") or {}).get("sharpe_ratio"))
        mean_fitness = number((isos.get("mean") or {}).get("fitness_ratio"))
        coordinate_means[key] = {"sharpe": mean_sharpe, "fitness": mean_fitness}

        archive_by_dataset = defaultdict(list)
        for archive in archives_by_key.get(key, []):
            archive_by_dataset[archive["dataset"]].append(archive)

        all_dataset_ids = set(isos.get("dataset") or {}) | set(osis_region.get("dataset") or {}) | set(neutral.get("dataset") or {}) | set(archive_by_dataset)
        if filters["dataset"]:
            all_dataset_ids = {item for item in all_dataset_ids if item == filters["dataset"]}
        category_map = {dataset: map_category(dataset, category_names, rules) for dataset in all_dataset_ids}

        allowed_datasets = set()
        coordinate_dataset_rows = {}
        for dataset in sorted(all_dataset_ids):
            category, mapping_source = category_map[dataset]
            community = (isos.get("dataset") or {}).get(dataset) or {}
            grade = dataset_grade(community.get("sharpe_ratio"), mean_sharpe)
            if filters["categories"] and category.lower() not in filters["categories"]:
                continue
            if filters["dataset_grades"] and grade not in filters["dataset_grades"]:
                continue
            allowed_datasets.add(dataset)
            archive_items = archive_by_dataset.get(dataset, [])
            row = {
                **coordinate,
                "category": category,
                "category_mapping_source": mapping_source,
                "dataset": dataset,
                "dataset_grade": grade,
                **_metric_row(community),
                **_metric_row((osis_region.get("dataset") or {}).get(dataset), "osis_"),
                "archive_status": "EXACT_ARCHIVE_AVAILABLE" if archive_items else "EXACT_ARCHIVE_MISSING",
                "archive_universes": sorted({item["universe"] for item in archive_items}),
                "archive_paths": [item["path"] for item in archive_items],
                "provenance": "INFO_DATA_REGION_DELAY_DATASET_STATS",
            }
            dataset_rows.append(row)
            coordinate_dataset_rows[dataset] = row
            if not archive_items:
                unobserved.append({
                    **coordinate, "category": category, "dataset": dataset, "field": None,
                    "issue": "FIELD_PROFILE_UNOBSERVED",
                    "detail": "EXACT_ARCHIVE_MISSING; 未借用其他 Universe archive",
                })

        for category in sorted(category_names):
            if filters["categories"] and category.lower() not in filters["categories"]:
                continue
            category_stats.append({
                **coordinate, "category": category,
                **_metric_row(isos_categories.get(category)),
                **_metric_row((osis_region.get("category") or {}).get(category), "osis_"),
                "dataset_grade_basis": "CATEGORY_STATS_ONLY",
            })

        field_categories = defaultdict(set)
        seen_exact_fields = set()
        for archive in archives_by_key.get(key, []):
            dataset = archive["dataset"]
            if dataset not in allowed_datasets:
                continue
            category, mapping_source = category_map[dataset]
            archive_data = source.load_bin(archive["path"]) or {}
            audit["exact_field_records"] += len(archive_data)
            for field, record in archive_data.items():
                if not isinstance(record, dict):
                    unobserved.append({
                        **coordinate, "universe": archive["universe"], "category": category,
                        "dataset": dataset, "field": field, "issue": "FIELD_PROFILE_INVALID",
                        "detail": "archive record is not an object",
                    })
                    continue
                identity = {
                    **coordinate,
                    "universe": archive["universe"],
                    "category": category,
                    "category_mapping_source": mapping_source,
                    "dataset": dataset,
                    "dataset_grade": coordinate_dataset_rows[dataset]["dataset_grade"],
                    "field": field,
                    "archive_path": archive["path"],
                }
                profile = classify_field(record, category, rules)
                row = {
                    **identity,
                    **_metric_row((isos.get("datafield") or {}).get(field)),
                    **profile,
                    "provenance": "EXACT_ARCHIVE_PLUS_REGION_DELAY_COMMUNITY_FIELD_STATS",
                }
                exact_fields.append(row)
                annual.extend(annual_rows(record, identity, rules))
                audit["exported_exact_field_records"] += 1
                seen_exact_fields.add(field)
                field_categories[field].add(category)
                if profile["risk_flags"] or profile["field_profile_status"] != "ARCHIVE_PROFILED":
                    unobserved.append({
                        **identity, "issue": profile["field_profile_status"],
                        "detail": ",".join(profile["risk_flags"]) or "PROFILE_INCOMPLETE",
                    })

        community_stats = isos.get("datafield") or {}
        neutral_field_stats = neutral.get("datafield") or {}
        all_community_field_ids = set(community_stats) | set(neutral_field_stats)
        audit["community_field_records"] += len(community_stats)
        audit["neutralization_only_fields"] += len(set(neutral_field_stats) - set(community_stats))
        unmapped_candidates = all_community_field_ids - seen_exact_fields
        audit["unmapped_input_records"] += len(unmapped_candidates)
        include_unmapped = (
            not filters["categories"]
            and not filters["dataset"]
            and not filters["dataset_grades"]
        ) or (filters["categories"] and "unmapped" in filters["categories"])
        for field in sorted(unmapped_candidates if include_unmapped else set()):
            row = {
                **coordinate,
                "universe": None,
                "category": "UNMAPPED",
                "category_mapping_source": "COMMUNITY_FIELD_HAS_NO_DATASET_LINK",
                "dataset": None,
                "dataset_grade": None,
                "field": field,
                **_metric_row(community_stats.get(field)),
                "field_tier": None,
                "field_profile_status": "FIELD_PROFILE_UNOBSERVED",
                "risk_flags": [],
                "recommendation_status": "UNOBSERVED",
                "provenance": "NEUTRALIZATION_ONLY_FIELD" if field not in community_stats else "REGION_DELAY_COMMUNITY_FIELD_WITHOUT_DATASET_LINK",
            }
            community_fields.append(row)
            audit["unmapped_field_records"] += 1
            unobserved.append({
                **coordinate, "category": "UNMAPPED", "dataset": None, "field": field,
                "issue": "FIELD_PROFILE_UNOBSERVED", "detail": row["provenance"],
            })

        selected_category_neutral = {
            item: stats for item, stats in (neutral.get("category") or {}).items()
            if not filters["categories"] or item.lower() in filters["categories"]
        }
        selected_dataset_neutral = {
            item: stats for item, stats in (neutral.get("dataset") or {}).items()
            if item in allowed_datasets
        }
        neutralizations.extend(flatten_neutralizations(selected_category_neutral, "category", coordinate))
        neutralizations.extend(flatten_neutralizations(selected_dataset_neutral, "dataset", coordinate, category_map))
        for field, stats in (neutral.get("datafield") or {}).items():
            mapped = field_categories.get(field)
            if not mapped and not include_unmapped:
                continue
            for category in sorted(mapped or {"UNMAPPED"}):
                mapping = "FIELD_EXACT_ARCHIVE_JOIN" if category != "UNMAPPED" else "CATEGORY_UNMAPPED"
                neutralizations.extend(flatten_neutralizations({field: stats}, "datafield", coordinate, {field: (category, mapping)}))
        mean_neutral = (neutral.get("mean") or {}) if include_unmapped else {}
        for name, metrics in mean_neutral.items():
            neutralizations.append({
                **coordinate,
                "category": "UNMAPPED", "category_mapping_source": "REGION_DELAY_MEAN",
                "scope": "mean", "item": "REGION_DELAY_MEAN", "neutralization": name,
                "count": number(metrics.get("count")), "sharpe": number(metrics.get("sharpe_ratio")),
                "fitness": number(metrics.get("fitness_ratio")), "osis_count": number(metrics.get("osis_count")),
            })

    include_unparsed = not any((
        filters["regions"], filters["delays"], filters["universes"],
        filters["categories"], filters["dataset_grades"], filters["dataset"],
    ))
    if include_unparsed:
        for archive_path in unparsed_archive_paths:
            archive_data = source.load_bin(archive_path) or {}
            audit["exact_field_records"] += len(archive_data)
            for field, record in archive_data.items():
                identity = {
                    "region": None, "delay": None, "region_delay": None, "universe": None,
                    "category": "UNMAPPED", "category_mapping_source": "ARCHIVE_NAME_UNPARSED",
                    "dataset": None, "dataset_grade": None, "field": field,
                    "archive_path": archive_path,
                }
                profile = classify_field(record, "UNMAPPED", rules) if isinstance(record, dict) else {}
                exact_fields.append({
                    **identity,
                    "count": None, "sharpe": None, "fitness": None,
                    **profile,
                    "field_tier": None,
                    "field_profile_status": "ARCHIVE_NAME_UNPARSED",
                    "recommendation_status": "UNOBSERVED",
                    "risk_flags": sorted(set(profile.get("risk_flags", [])) | {"ARCHIVE_NAME_UNPARSED"}),
                    "provenance": "UNPARSED_ARCHIVE_PRESERVED_WITHOUT_COORDINATE_INFERENCE",
                })
                if isinstance(record, dict):
                    annual.extend(annual_rows(record, identity, rules))
                audit["exported_exact_field_records"] += 1
                unobserved.append({
                    **identity, "issue": "ARCHIVE_NAME_UNPARSED",
                    "detail": "文件名不符合精确坐标格式；原始字段已保留，未猜测 Region/Universe",
                })

    all_fields = exact_fields + community_fields
    available_categories = {row["category"] for row in dataset_rows + category_stats + all_fields + neutralizations}
    if filters["categories"]:
        missing = filters["categories"] - {category.lower() for category in available_categories}
        if missing:
            raise ValueError(f"未知 Category: {', '.join(sorted(missing))}；可用: {', '.join(sorted(available_categories))}")

    for category in sorted(available_categories, key=lambda item: (item == "UNMAPPED", item)):
        if filters["categories"] and category.lower() not in filters["categories"]:
            continue
        categories[category] = {
            "category_stats": [row for row in category_stats if row["category"] == category],
            "datasets": [row for row in dataset_rows if row["category"] == category],
            "fields": [row for row in all_fields if row["category"] == category],
            "neutralizations": [row for row in neutralizations if row["category"] == category],
            "annual": [row for row in annual if row["category"] == category],
            "unobserved": [row for row in unobserved if row["category"] == category],
        }

    selected_fields = [
        row for row in exact_fields
        if filters["field_tiers"] is None or (row.get("field_tier") or "").upper() in filters["field_tiers"]
    ]
    return {
        "schema_version": 1,
        "snapshot": source.display_name,
        "evidence_boundary": "FIELD_HEALTH_NOT_ALPHA_PERFORMANCE",
        "filters": {key: sorted(value) if isinstance(value, set) else value for key, value in filters.items()},
        "rules": rules,
        "coordinates": selected_keys,
        "coordinate_means": coordinate_means,
        "unparsed_archives": unparsed_archive_paths,
        "category_stats": category_stats,
        "datasets": dataset_rows,
        "fields": all_fields,
        "exact_fields": exact_fields,
        "selected_fields": selected_fields,
        "neutralizations": neutralizations,
        "annual": annual,
        "unobserved": unobserved,
        "categories": categories,
        "audit": audit,
    }


def export_ledger(ledger, output_dir):
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for category, bundle in ledger["categories"].items():
        scopes = {
            (row.get("region"), row.get("delay"))
            for name, rows in bundle.items()
            if name != "category_stats" or isinstance(rows, list)
            for row in rows
        }
        for region, delay in sorted(scopes, key=lambda item: (str(item[0]), str(item[1]))):
            scoped = {
                name: [
                    row for row in rows
                    if row.get("region") == region and row.get("delay") == delay
                ]
                for name, rows in bundle.items()
            }
            region_name = region or "UNKNOWN"
            delay_name = f"D{delay}" if delay is not None else "D_UNKNOWN"
            suffix = "" if delay == 1 else f"_{delay_name}"
            path = output_dir / region_name / f"{safe_filename(category)}{suffix}.xlsx"
            rows = write_category_workbook(
                path,
                scoped,
                ledger["filters"],
                ledger["coordinate_means"].get(f"{region}_{delay}") or {},
            )
            verification = verify_workbook(path, EXPECTED_SHEETS)
            if verification["missing_sheets"] or verification["formula_errors"]:
                raise RuntimeError(f"XLSX 验证失败 {path}: {verification}")

            entries.append({
                "region": region_name,
                "delay": delay_name,
                "category": category,
                "path": str(path),
                "datasets": len(scoped["datasets"]),
                "fields": len(scoped["fields"]),
                "rows": rows,
            })
    readme = write_output_readme(output_dir, ledger["snapshot"], entries, ledger["filters"])
    return {"output_dir": output_dir, "readme": readme, "entries": entries}


def _print_summary(ledger, args):
    print(f"快照: {ledger['snapshot']}")
    print(f"坐标: {', '.join(ledger['coordinates'])}")
    print(f"数据集 {len(ledger['datasets'])}；精确字段 {len(ledger['exact_fields'])}；未映射/未观察字段 {ledger['audit']['unmapped_field_records']}")
    print("注意: 数据集档位与字段 Tier 独立，字段健康不等于 Alpha 表现。")
    if args.fields:
        print("\n| Category | Dataset | Field | Dataset Grade | Tier | Status | Risks |")
        print("|---|---|---|---|---|---|---|")
        for row in ledger["selected_fields"][: args.field_top]:
            print(f"| {row['category']} | {row['dataset']} | {row['field']} | {row['dataset_grade']} | {row['field_tier']} | {row['field_profile_status']} | {','.join(row['risk_flags'])} |")


def main(argv=None):
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return fail_with_help(parser, "未提供参数")
    args = parser.parse_args(argv)
    source_arg = args.source or args.legacy_zip
    try:
        filters = {
            "regions": csv_filter(args.region, upper=True),
            "delays": delay_filter(args.delay),
            "universes": None if args.universes else csv_filter(args.universe, upper=True),
            "categories": csv_filter(args.categories),
            "dataset_grades": csv_filter(args.dataset_grades, upper=True),
            "field_tiers": csv_filter(args.field_tiers, upper=True),
            "neutralizations": csv_filter(args.neutralizations, upper=True),
            "count_min": metric_filter(args.count_min, "--count-min", integer=True),
            "count_max": metric_filter(args.count_max, "--count-max", integer=True),
            "sharpe_min": metric_filter(args.sharpe_min, "--sharpe-min", allow_auto=True),
            "fitness_min": metric_filter(args.fitness_min, "--fitness-min", allow_auto=True),
            "dataset": args.dataset,
        }
        if (
            filters["count_min"] is not None
            and filters["count_max"] is not None
            and filters["count_min"] >= filters["count_max"]
        ):
            raise ValueError("--count-min 必须小于 --count-max")
        rules = load_rules(args.tier_config)
        with resolve_source(source_arg, SCRIPT_DIR) as source:
            ledger = build_ledger(source, rules, filters)
        _print_summary(ledger, args)
        if args.output or not args.json_out:
            output = args.output or (Path.cwd() / f"webdata_quality_output_{datetime.now():%Y%m%d_%H%M%S}")
            result = export_ledger(ledger, output)
            print(f"分类结果已写入: {result['output_dir']}")
            print(f"使用入口: {result['readme']}")
            for entry in result["entries"]:
                print(f"{entry['region']}/{entry['category']}: {entry['rows']} 条")
        if args.json_out:
            write_json(args.json_out, {key: value for key, value in ledger.items() if key != "categories"})
            print(f"JSON 已写入: {Path(args.json_out).resolve()}")
        return 0
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        return fail_with_help(parser, str(exc), source_arg)


if __name__ == "__main__":
    raise SystemExit(main())
