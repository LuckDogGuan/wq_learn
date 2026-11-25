"""Classify WebDataScope datasets and exact-archive fields."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path


def number(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def values(items):
    return [value for item in (items or []) if (value := number(item)) is not None]


def average(items):
    items = values(items)
    return sum(items) / len(items) if items else None


def load_rules(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def dataset_grade(sharpe, mean_sharpe):
    sharpe = number(sharpe)
    mean_sharpe = number(mean_sharpe)
    if sharpe is None:
        return "GRAY"
    if mean_sharpe is not None and sharpe > mean_sharpe:
        return "GREEN"
    return "YELLOW" if sharpe >= 0 else "RED"


def map_category(dataset, categories, rules):
    aliases = rules.get("category_aliases", {})
    if dataset in aliases:
        return aliases[dataset], "CATEGORY_ALIAS"
    matches = [
        category
        for category in categories
        if dataset.lower().startswith(category.lower())
    ]
    if matches:
        return max(matches, key=len), "CATEGORY_PREFIX"
    return "UNMAPPED", "CATEGORY_UNMAPPED"


def _mode(items):
    cleaned = [str(item) for item in (items or []) if item not in (None, "")]
    return Counter(cleaned).most_common(1)[0][0] if cleaned else None


def _round(value, digits=6):
    return round(value, digits) if value is not None else None


def classify_field(record, category, rules):
    recent_slots = int(rules.get("recent_slots", 3))
    coverage_all = values(record.get("CoverageRatio"))
    coverage_recent = coverage_all[-recent_slots:]
    skew_recent = [abs(value) for value in values(record.get("skenewss"))[-recent_slots:]]
    kurtosis_recent = values(record.get("kurtosis"))[-recent_slots:]
    positive_recent = values(record.get("IndicativePositiveRatio"))[-recent_slots:]
    negative_recent = values(record.get("IndicativeNegativeRatio"))[-recent_slots:]
    integer_recent = values(record.get("IntegerStatus"))[-recent_slots:]

    coverage_mean = average(coverage_recent)
    coverage_min = min(coverage_recent) if coverage_recent else None
    skew_mean = average(skew_recent)
    kurtosis_mean = average(kurtosis_recent)
    positive_mean = average(positive_recent)
    negative_mean = average(negative_recent)
    one_sided_limit = number(rules.get("risk_thresholds", {}).get("one_sided", 0.99))
    one_sided = max(positive_mean or 0, negative_mean or 0) >= one_sided_limit

    warnings = []
    if len(coverage_recent) < recent_slots:
        warnings.append("HISTORY_INCOMPLETE")
    if any(value < 0 or value > 1 for value in coverage_all):
        warnings.append("COVERAGE_OUT_OF_RANGE")
    if one_sided:
        warnings.append("ONE_SIDED")
    if average(integer_recent) is not None and average(integer_recent) >= 0.5:
        warnings.append("DISCRETE")
    if skew_mean is not None and skew_mean >= number(
        rules.get("risk_thresholds", {}).get("skewed", 2)
    ):
        warnings.append("SKEWED")
    if kurtosis_mean is not None and kurtosis_mean >= number(
        rules.get("risk_thresholds", {}).get("thick_tailed", 5)
    ):
        warnings.append("THICK_TAILED")

    tier = None
    profile_status = "ARCHIVE_PROFILED"
    if len(coverage_recent) < recent_slots:
        profile_status = "FIELD_PROFILE_INCOMPLETE"
    else:
        family = "sparse" if category in rules.get("sparse_categories", []) else "regular"
        limits = rules["field_tiers"][family]
        for candidate in ("T1", "T2"):
            limit = limits[candidate]
            if (
                coverage_mean >= limit["coverage_recent_mean"]
                and coverage_min >= limit["coverage_recent_min"]
                and skew_mean is not None
                and skew_mean <= limit["abs_skew_recent_mean"]
                and not one_sided
            ):
                tier = candidate
                break
        if tier is None:
            tier = "T3" if coverage_mean >= limits["T3"]["coverage_recent_mean"] else "T4"

    return {
        "field_tier": tier,
        "field_profile_status": profile_status,
        "coverage_recent_mean": _round(coverage_mean),
        "coverage_recent_min": _round(coverage_min),
        "coverage_all_mean": _round(average(coverage_all)),
        "abs_skew_recent_mean": _round(skew_mean),
        "kurtosis_recent_mean": _round(kurtosis_mean),
        "positive_ratio_recent_mean": _round(positive_mean),
        "negative_ratio_recent_mean": _round(negative_mean),
        "frequency": _mode(record.get("frequency")),
        "history_slots": len(coverage_all),
        "risk_flags": warnings,
        "recommendation_status": (
            "GOOD_WITH_WARNINGS"
            if tier in {"T1", "T2"} and warnings
            else "GOOD_CLEAN"
            if tier in {"T1", "T2"}
            else "REVIEW"
            if tier == "T3"
            else "LOW_PRIORITY"
            if tier == "T4"
            else "UNOBSERVED"
        ),
    }


def annual_rows(record, identity, rules):
    array_keys = [
        "Coverage",
        "CoverageRatio",
        "PositiveValues",
        "NegativeValues",
        "IndicativePositiveRatio",
        "IndicativeNegativeRatio",
        "absValueBetween1and0ratio",
        "IntegerStatus",
        "skenewss",
        "kurtosis",
        "frequency",
    ]
    length = max((len(record.get(key) or []) for key in array_keys), default=0)
    first_year = int(rules.get("first_year", 2012))
    rows = []
    for index in range(length):
        row = {**identity, "slot": index + 1, "year": first_year + index}
        for key in array_keys:
            data = record.get(key) or []
            row[key] = data[index] if index < len(data) else None
        rows.append(row)
    return rows


def flatten_neutralizations(stats, scope, coordinate, category_map=None):
    rows = []
    for item_id, neutralizations in (stats or {}).items():
        category = "UNMAPPED"
        mapping_source = "CATEGORY_UNMAPPED"
        if scope == "category":
            category, mapping_source = item_id, "CATEGORY_DIRECT"
        elif category_map and item_id in category_map:
            category, mapping_source = category_map[item_id]
        for name, metrics in (neutralizations or {}).items():
            rows.append({
                **coordinate,
                "category": category,
                "category_mapping_source": mapping_source,
                "scope": scope,
                "item": item_id,
                "neutralization": name,
                "count": number(metrics.get("count")),
                "sharpe": number(metrics.get("sharpe_ratio")),
                "fitness": number(metrics.get("fitness_ratio")),
            })
    return rows
