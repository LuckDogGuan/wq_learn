"""Select one unlit USA TOP1000 D1 dataset and its best fields.

Reads live pyramid status and datasets, then ranks WebDataScope fields.
Does not create simulations.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CORE_PARENT = Path(__file__).resolve().parents[1] / "优化代码"
if str(CORE_PARENT) not in sys.path:
    sys.path.insert(0, str(CORE_PARENT))

WDS_DIR = CORE_PARENT / "Core" / "tools" / "webdata_quality"
if str(WDS_DIR) not in sys.path:
    sys.path.insert(0, str(WDS_DIR))

from Core.api import get_datasets, get_datafields, get_pyramid_alphas, login
from webdata_classifier import classify_field, load_rules
from webdata_loader import inventory, resolve_source

BEIJING = ZoneInfo("Asia/Shanghai")
OUT_DIR = Path(__file__).resolve().parents[2] / "总结" / "active" / "20261013_usa_top1000_d1"
ZIP_PATH = WDS_DIR / "WebData_20260219_V0.10.9.zip"
RULES_PATH = WDS_DIR / "tier_rules.json"

RECOMMENDED = [
    "other696", "fundamental91", "other416", "analyst69", "model267",
    "other510", "model53", "model250", "other176", "model237", "risk82",
    "model262", "other432", "analyst82", "model211", "earnings4",
    "institutions7", "analyst44", "model33", "model31", "analyst83",
    "news87", "model15", "news3", "pv87", "model36", "model38", "other143",
    "macro38", "analyst11", "option9", "model10",
]
AVOID_PREFIXES = ("model", "fundamental")

PREFIX_CATEGORY = [
    ("analyst", "analyst"),
    ("news", "news"),
    ("other", "other"),
    ("option", "option"),
    ("macro", "macro"),
    ("risk", "risk"),
    ("institutions", "institutions"),
    ("earnings", "earnings"),
    ("pv", "pv"),
    ("model", "model"),
    ("fundamental", "fundamental"),
]


def preferred(dataset_id: str) -> bool:
    text = dataset_id.lower()
    return text in RECOMMENDED and not text.startswith(AVOID_PREFIXES)


def category_key(name: str) -> str:
    text = str(name or "").lower()
    for prefix, key in PREFIX_CATEGORY:
        if text.startswith(prefix) or key in text:
            return key
    return text


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = login()
    pyramid = get_pyramid_alphas(client)
    usa = []
    for item in pyramid.get("pyramids") or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("region") or "").upper() != "USA":
            continue
        if item.get("delay") != 1:
            continue
        category = (item.get("category") or {}).get("name") or "Unknown"
        usa.append({
            "category": category,
            "alphaCount": int(item.get("alphaCount") or 0),
            "lit": int(item.get("alphaCount") or 0) >= 3,
        })
    usa.sort(key=lambda row: (row["lit"], row["alphaCount"], row["category"]))

    datasets = get_datasets(client, region="USA", delay=1, universe="TOP1000")
    rows = []
    if not datasets.empty:
        for record in datasets.to_dict("records"):
            dataset_id = str(record.get("id") or "")
            if not preferred(dataset_id):
                continue
            category = record.get("category") or {}
            category_name = category.get("name") if isinstance(category, dict) else str(category)
            rows.append({
                "id": dataset_id,
                "name": record.get("name"),
                "category": category_name,
                "valueScore": record.get("valueScore"),
                "coverage": record.get("coverage"),
                "fieldCount": record.get("fieldCount"),
            })

    unlit_keys = {category_key(item["category"]) for item in usa if not item["lit"]}
    for row in rows:
        row["pyramid_key"] = category_key(row["category"] or row["id"])
        row["pyramid_unlit"] = row["pyramid_key"] in unlit_keys

    rules = load_rules(RULES_PATH)
    source = resolve_source(str(ZIP_PATH), WDS_DIR)
    try:
        archives = {
            item["dataset"].lower(): item
            for item in inventory(source, source.load_bin("data/oth/info_data.bin"))
            if item["region"] == "USA" and item["universe"] == "TOP1000" and item["delay"] == 1
        }
        field_ranks = {}
        for row in rows:
            archive = archives.get(row["id"].lower())
            row["wds_archive"] = bool(archive)
            if not archive:
                continue
            parsed = source.load_bin(archive["path"])
            ranked = []
            if isinstance(parsed, dict):
                for field_name, stats in parsed.items():
                    if not isinstance(stats, dict) or "CoverageRatio" not in stats:
                        continue
                    profile = classify_field(stats, row["pyramid_key"], rules)
                    if profile["field_tier"] not in {"T1", "T2"}:
                        continue
                    if "ONE_SIDED" in profile["risk_flags"]:
                        continue
                    ranked.append({
                        "field": str(field_name),
                        "tier": profile["field_tier"],
                        "coverage": profile["coverage_recent_mean"],
                        "coverage_min": profile["coverage_recent_min"],
                        "skew": profile["abs_skew_recent_mean"],
                        "flags": profile["risk_flags"],
                        "status": profile["recommendation_status"],
                    })
            ranked.sort(key=lambda item: (
                0 if item["tier"] == "T1" else 1,
                -(item["coverage"] or 0),
                item["skew"] or 99,
            ))
            field_ranks[row["id"]] = ranked[:12]
            row["t1_t2_count"] = len(ranked)
    finally:
        source.close()

    rows.sort(key=lambda row: (
        0 if row["pyramid_unlit"] else 1,
        -(row.get("t1_t2_count") or 0),
        row["id"],
    ))
    chosen = next((row for row in rows if row["pyramid_unlit"] and row.get("t1_t2_count")), None)
    if chosen is None:
        chosen = next((row for row in rows if row.get("t1_t2_count")), None)

    platform_fields = []
    if chosen:
        fields = get_datafields(
            client, region="USA", delay=1, universe="TOP1000", dataset_id=chosen["id"],
        )
        wanted = {item["field"] for item in field_ranks.get(chosen["id"], [])}
        if not fields.empty:
            for record in fields.to_dict("records"):
                field_id = str(record.get("id") or "")
                if field_id not in wanted:
                    continue
                platform_fields.append({
                    "id": field_id,
                    "type": record.get("type"),
                    "description": record.get("description"),
                    "coverage": record.get("coverage"),
                    "dateCoverage": record.get("dateCoverage"),
                    "alphaCount": record.get("alphaCount"),
                })

    payload = {
        "created_at": datetime.now(BEIJING).isoformat(timespec="seconds"),
        "scope": {"region": "USA", "universe": "TOP1000", "delay": 1, "type": "REGULAR", "maxTrade": "ON"},
        "usa_d1_pyramids": usa,
        "candidate_datasets": rows,
        "field_ranks": {key: value for key, value in field_ranks.items() if key == (chosen or {}).get("id")},
        "chosen_dataset": chosen,
        "platform_fields": platform_fields,
    }
    path = OUT_DIR / "scope_selection.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "out": str(path),
        "unlit": [item["category"] for item in usa if not item["lit"]],
        "chosen": chosen,
        "platform_fields": platform_fields[:8],
        "candidate_count": len(rows),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
