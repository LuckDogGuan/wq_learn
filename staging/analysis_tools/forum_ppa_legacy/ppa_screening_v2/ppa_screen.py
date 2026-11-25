"""Read-only PPA Alpha screening.

Uses the installed ``wqb`` client for live platform access.  It never simulates,
submits, or patches Alpha properties.
"""

from __future__ import annotations

import argparse
import asyncio
import calendar
import json
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
STANDARD_FILE = ROOT / "不同阿尔法标准" / "ppa_alpha_standard.json"
SCOPE_DIR = ROOT / "PPA 范围"
DEFAULT_OUTPUT = ROOT / "总结" / "ppa_screening"
SUPPORT_FIELDS = {
    "country", "industry", "subindustry", "currency", "market", "sector", "exchange"
}
CORRELATION_NAMES = {
    "POWER_POOL_CORRELATION", "POWER_POOL_SELF_CORRELATION", "PPA_CORRELATION",
}
PPAC_REQUIRED_NAMES = {
    "MATCHES_THEMES", "PURE_POWER_POOL_THEME", "POWER_POOL_CORRELATION",
    "POWER_POOL_DESCRIPTION_LENGTH", "POWER_POOL_DESCRIPTION_FORMAT",
}
PLATFORM_TZ = ZoneInfo("America/New_York")
PPA_CHECK_NAMES = {
    "LOW_TURNOVER", "HIGH_TURNOVER", "LOW_SUB_UNIVERSE_SHARPE",
    "LOW_ROBUST_UNIVERSE_SHARPE", "LOW_ROBUST_UNIVERSE_SHARPE.WITH_RATIO",
    "LOW_ROBUST_UNIVERSE_RETURNS", "LOW_INVESTABILITY_CONSTRAINED_SHARPE",
}
NEUTRALIZATION_ALIASES = {
    "RAM": "REVERSION_AND_MOMENTUM",
    "SLOW FACTORS": "SLOW_FACTORS",
    "SLOW": "SLOW_FACTORS",
    "FAST FACTORS": "FAST_FACTORS",
    "SLOW + FAST FACTORS": "SLOW_AND_FAST_FACTORS",
    "SLOW_AND_FAST": "SLOW_AND_FAST_FACTORS",
    "CROWDING FACTORS": "CROWDING_FACTORS",
}


@dataclass(frozen=True)
class Window:
    start: datetime
    end: datetime


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def load_scope(path: Path) -> dict[str, Any]:
    scope = read_json(path)
    config_name = scope.get("forbidden_field_rules_file")
    if not config_name:
        return scope
    config_path = path.parent / str(config_name)
    config = read_json(config_path)
    rules = config.get("forbidden_field_rules", config)
    if not isinstance(rules, dict):
        raise ValueError(f"forbidden_field_rules object required: {config_path}")
    scope["forbidden_field_rules"] = rules
    scope["forbidden_field_rules_source"] = str(config_path)
    return scope


def latest_scope(scope_dir: Path = SCOPE_DIR, today: date | None = None) -> Path:
    files = []
    for path in sorted(scope_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            value = read_json(path)
            if value.get("duration") and value.get("core_requirements"):
                files.append(path)
        except (OSError, ValueError):
            continue
    if not files:
        raise FileNotFoundError(f"No PPA scope JSON found in {scope_dir}")
    today = today or date.today()
    active = []
    for path in files:
        try:
            duration = read_json(path).get("duration", {})
            if duration.get("start_date") <= today.isoformat() <= duration.get("end_date"):
                active.append(path)
        except (OSError, KeyError, TypeError):
            continue
    if len(active) > 1:
        raise ValueError("Multiple active PPA scopes found; pass --scope explicitly")
    return active[0] if active else files[0]


def subtract_months(value: date, months: int = 1) -> date:
    month = value.month - months
    year = value.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    return date(year, month, min(value.day, calendar.monthrange(year, month)[1]))


def date_window(start: str | None = None, end: str | None = None) -> Window:
    today = date.today()
    finish = date.fromisoformat(end) if end else today
    begin = date.fromisoformat(start) if start else subtract_months(finish, 1)
    if begin > finish:
        raise ValueError("start date cannot be later than end date")
    # User-facing dates use Beijing time; the API range is half-open and includes
    # the complete requested end date.
    return Window(datetime.combine(begin, time.min, PLATFORM_TZ),
                  datetime.combine(finish + timedelta(days=1), time.min, PLATFORM_TZ))


def intersect_scope_window(window: Window, scope: dict[str, Any]) -> Window:
    duration = scope.get("duration", {})
    try:
        theme = Window(
            datetime.combine(date.fromisoformat(duration["start_date"]), time.min, PLATFORM_TZ),
            datetime.combine(date.fromisoformat(duration["end_date"]) + timedelta(days=1), time.min, PLATFORM_TZ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("PPA scope duration must contain ISO start_date/end_date") from exc
    start, end = max(window.start, theme.start), min(window.end, theme.end)
    if start >= end:
        raise ValueError("screening window does not overlap the PPA theme duration")
    return Window(start, end)


def _first(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if mapping.get(key) is not None:
            return mapping[key]
    return None


def _settings(alpha: dict[str, Any]) -> dict[str, Any]:
    settings = alpha.get("settings")
    if isinstance(settings, dict):
        return settings
    for key in ("regular", "alpha"):
        value = alpha.get(key)
        if isinstance(value, dict) and isinstance(value.get("settings"), dict):
            return value["settings"]
    return {}


def _number(alpha: dict[str, Any], *keys: str) -> float | None:
    value = _first(alpha, *keys)
    if value is None and isinstance(alpha.get("is"), dict):
        value = _first(alpha["is"], *keys)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _expression(alpha: dict[str, Any]) -> str:
    for value in (alpha.get("expression"), alpha.get("formula"), alpha.get("code"), alpha.get("regular")):
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            found = _first(value, "code", "regular", "expression", "formula")
            if isinstance(found, str):
                return found
    return ""


def _expression_field_candidates(alpha: dict[str, Any]) -> list[str]:
    expression = _expression(alpha)
    if not expression:
        return []
    functions = set(re.findall(r"\b([A-Za-z_]\w*)\s*\(", expression))
    excluded = {"true", "false", "inf", "nan", "target_tvr"}
    return sorted({token for token in re.findall(r"\b[A-Za-z_]\w*\b", expression)
                   if token not in functions and token.lower() not in excluded})


def _list_value(alpha: dict[str, Any], *keys: str) -> list[str]:
    value = _first(alpha, *keys)
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _datasets(alpha: dict[str, Any]) -> list[str]:
    explicit = _list_value(alpha, "datasets", "dataset_ids", "dataset_id")
    if explicit:
        return explicit
    return sorted({str(item.get("dataset_id")) for item in alpha.get("resolved_field_metadata", [])
                   if isinstance(item, dict) and item.get("dataset_id")})


def _operator_count(alpha: dict[str, Any]) -> int | None:
    explicit = _first(alpha, "operator_count", "operators_count")
    regular = alpha.get("regular")
    if explicit is None and isinstance(regular, dict):
        explicit = _first(regular, "operatorCount", "operator_count", "operators_count")
    if explicit is not None:
        try:
            return int(explicit)
        except (TypeError, ValueError):
            pass
    expression = _expression(alpha)
    if not expression:
        return None
    return len(re.findall(r"\b[A-Za-z_]\w*\s*\(", expression))


def _fields(alpha: dict[str, Any]) -> list[str]:
    values = _list_value(alpha, "fields", "datafields", "data_fields", "field_ids")
    if values:
        return values
    values = _list_value(alpha, "field")
    if values:
        return values
    return sorted({str(item.get("field_id")) for item in alpha.get("resolved_field_metadata", [])
                   if isinstance(item, dict) and item.get("field_id")})


def _forbidden_field_hits(alpha: dict[str, Any], scope: dict[str, Any]) -> list[str]:
    fields = _fields(alpha)
    rules = scope.get("forbidden_field_rules", {})
    hits = []
    for rule in rules.values() if isinstance(rules, dict) else []:
        if not isinstance(rule, dict):
            continue
        exact = {str(item).lower() for item in rule.get("forbidden_fields", [])}
        prefixes = tuple(str(item).lower() for item in rule.get("forbidden_prefixes", []))
        hits.extend(field for field in fields
                    if field.lower() in exact or field.lower().startswith(prefixes))
    return sorted(set(hits))


def _forbidden_support_exception(fields: list[str], datasets: list[str], scope: dict[str, Any]) -> bool:
    rules = scope.get("forbidden_field_rules", {})
    for dataset in datasets:
        allowed = SUPPORT_FIELDS
        for label, rule in rules.items() if isinstance(rules, dict) else []:
            if not isinstance(rule, dict):
                continue
            dataset_id = str(rule.get("dataset_id", label)).lower()
            if dataset_id == dataset.lower() and "support_field_exception" in rule:
                allowed = {str(item).lower() for item in rule["support_field_exception"]}
                break
        if not all(field.lower() in allowed for field in fields):
            return False
    return True


def _checks(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []
    current: Any = payload
    if isinstance(payload.get("is"), dict):
        current = payload["is"]
    checks = current.get("checks") if isinstance(current, dict) else None
    return [item for item in checks if isinstance(item, dict)] if isinstance(checks, list) else []


def _result(item: dict[str, Any]) -> str:
    return str(item.get("result") or item.get("status") or "").upper()


def _check_by_name(checks: list[dict[str, Any]], names: set[str]) -> dict[str, Any] | None:
    for item in checks:
        if str(item.get("name", "")).upper() in names:
            return item
    return None


def _ppac_gate(checks: list[dict[str, Any]]) -> tuple[str, list[str], list[str]]:
    failures: list[str] = []
    pending: list[str] = []
    observed: list[str] = []
    pass_states = {"PASS", "PASSED", "SUCCESS", "OK"}
    for name in sorted(PPAC_REQUIRED_NAMES):
        item = _check_by_name(checks, {name})
        if item is None:
            pending.append(f"{name} result missing")
            continue
        observed.append(name)
        state = _result(item)
        if state in pass_states:
            continue
        if state in {"PENDING", "WARNING", "WAITING"}:
            pending.append(f"{name}: {state}")
        else:
            failures.append(f"{name}: {state}")
    status = "FAIL" if failures else "PENDING" if pending else "PASS"
    return status, failures, pending


def _neutralization_key(value: Any) -> str:
    text = str(value or "").strip().upper()
    return NEUTRALIZATION_ALIASES.get(text, text)


def _base_scope(scope: dict[str, Any]) -> dict[str, Any]:
    requirements = scope.get("core_requirements", {})
    return {
        "source": "PPA 范围 JSON",
        "theme_name": scope.get("theme_name"),
        "duration": scope.get("duration", {}),
        "multiplier": scope.get("multiplier"),
        "region": requirements.get("region"),
        "delay": requirements.get("delay"),
        "universe": requirements.get("universe"),
        "allowed_neutralization_labels": requirements.get("neutralization", []),
        "forbidden_datasets": requirements.get("forbidden_datasets", []),
        "forbidden_field_rules_file": scope.get("forbidden_field_rules_file"),
        "forbidden_field_rules_source": scope.get("forbidden_field_rules_source"),
        "warnings": scope.get("warnings", {}),
    }


def _failed_ppa(checks: list[dict[str, Any]]) -> tuple[int | None, list[dict[str, Any]]]:
    relevant = []
    failed = []
    for item in checks:
        name = str(item.get("name", "")).upper()
        if name in PPA_CHECK_NAMES:
            relevant.append(item)
            if _result(item) not in {"PASS", "PENDING"}:
                failed.append(item)
        elif name == "LOW_SHARPE" and _number(item, "value") is not None and float(item["value"]) < 1:
            relevant.append(item)
            failed.append(item)
    return (None, []) if not relevant else (len(failed), failed)


def _status(alpha: dict[str, Any]) -> str:
    return str(alpha.get("status", "")).upper()


def _conflicts(standard: dict[str, Any], scope: dict[str, Any]) -> list[str]:
    entry = standard.get("entry_requirements", {})
    req = scope.get("core_requirements", {})
    conflicts = []
    for key in ("sharpe_min", "operators_max"):
        if key in req and key in entry and req[key] != entry[key]:
            conflicts.append(f"{key}: standard={entry[key]} scope={req[key]}")
    return conflicts


def classify(alpha: dict[str, Any], standard: dict[str, Any], scope: dict[str, Any],
             check_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    req = scope.get("core_requirements", {})
    entry = standard.get("entry_requirements", {})
    reasons: list[str] = []
    pending: list[str] = []
    settings = _settings(alpha)
    result = {"alpha_id": alpha.get("id") or alpha.get("alpha_id"), "checks": [],
              "base_scope": _base_scope(scope)}

    conflicts = _conflicts(standard, scope)
    if conflicts:
        return {**result, "classification": "RULE_CONFLICT", "reasons": conflicts}

    duration = scope.get("duration", {})
    if duration.get("start_date") and duration.get("end_date"):
        today = date.today().isoformat()
        if not duration["start_date"] <= today <= duration["end_date"]:
            pending.append("theme is not active")

    if _status(alpha) in {"SUBMITTED", "IS_SUBMITTED", "HIDDEN"} or alpha.get("hidden") is True:
        return {**result, "classification": "EXCLUDED", "reasons": ["submitted or hidden"]}

    for key, expected in (("region", req.get("region")), ("universe", req.get("universe")), ("delay", req.get("delay"))):
        actual = settings.get(key, alpha.get(key))
        if expected is not None and str(actual).upper() != str(expected).upper():
            return {**result, "classification": "EXCLUDED", "reasons": [f"{key}: expected {expected}, got {actual}"]}

    allowed_neutralization = req.get("neutralization")
    actual_neutralization = settings.get("neutralization", alpha.get("neutralization"))
    allowed_keys = {_neutralization_key(value) for value in allowed_neutralization or []}
    if allowed_keys and _neutralization_key(actual_neutralization) not in allowed_keys:
        return {**result, "classification": "EXCLUDED", "reasons": [f"neutralization not allowed: {actual_neutralization}"]}

    fields = _fields(alpha)
    field_hits = _forbidden_field_hits(alpha, scope)
    if field_hits:
        return {**result, "classification": "FAIL",
                "reasons": [f"forbidden field: {field}" for field in field_hits]}
    datasets = {item.lower() for item in _datasets(alpha)}
    forbidden = {str(item).lower() for item in req.get("forbidden_datasets", [])}
    blocked = sorted(datasets & forbidden)
    if blocked:
        if not fields:
            pending.append("forbidden dataset support-field exception lacks field evidence")
        elif not _forbidden_support_exception(fields, blocked, scope):
            return {**result, "classification": "FAIL", "reasons": [f"forbidden dataset: {item}" for item in blocked]}

    sharpe = _number(alpha, "sharpe")
    turnover = _number(alpha, "turnover")
    operators = _operator_count(alpha)
    if sharpe is None:
        pending.append("sharpe missing")
    elif sharpe < float(entry.get("sharpe_min", 1.0)):
        reasons.append(f"sharpe {sharpe} < {entry.get('sharpe_min', 1.0)}")
    if turnover is None:
        pending.append("turnover missing")
    else:
        bounds = entry.get("turnover", {})
        if not float(bounds.get("min", 0.01)) <= turnover <= float(bounds.get("max", 0.70)):
            reasons.append(f"turnover {turnover} outside allowed range")
    if operators is None:
        pending.append("operator count missing")
    elif operators > int(entry.get("operators_max", 8)):
        reasons.append(f"operators {operators} > {entry.get('operators_max', 8)}")
    if not fields:
        pending.append("data fields missing")
    else:
        non_support = sorted({field.lower() for field in fields} - SUPPORT_FIELDS)
        if len(non_support) > int(entry.get("unique_data_fields_max_excluding_support_fields", 3)):
            reasons.append(f"non-support fields {len(non_support)} > 3")

    checks = _checks(check_payload)
    ppac_status, ppac_failures, ppac_pending = _ppac_gate(checks)
    if ppac_failures:
        reasons.extend(f"PPAC {item}" for item in ppac_failures)
    pending.extend(f"PPAC {item}" for item in ppac_pending)
    failed_ppa, failed_items = _failed_ppa(checks)
    if failed_ppa is None:
        pending.append("Failed PPA result missing")
    elif failed_ppa:
        reasons.append(f"Failed PPA count={failed_ppa}")

    correlation = _check_by_name(checks, CORRELATION_NAMES)
    if correlation is None:
        pending.append("Power Pool correlation result missing")
    elif _result(correlation) == "PENDING":
        pending.append("Power Pool correlation is pending")
    elif _result(correlation) not in {"PASS", "PASSED", "SUCCESS", "OK"}:
        reasons.append(f"Power Pool correlation: {_result(correlation)}")
    else:
        correlation_value = correlation.get("value")
        try:
            correlation_value = float(correlation_value)
        except (TypeError, ValueError):
            correlation_value = None
        maximum = float(entry.get("power_pool_self_correlation_max", 0.5))
        if correlation_value is None:
            pending.append("Power Pool correlation value missing")
        elif correlation_value > maximum:
            exception_ok = bool(alpha.get("self_correlation_exception_pass"))
            if not exception_ok:
                reasons.append(f"Power Pool self-correlation {correlation_value} > {maximum} without exception evidence")

    result.update({"sharpe": sharpe, "turnover": turnover, "operators": operators,
                   "fields": fields, "failed_ppa": failed_ppa,
                   "failed_ppa_items": [{"name": item.get("name"), "limit": item.get("limit"),
                                         "value": item.get("value"), "result": item.get("result")}
                                        for item in failed_items],
                   "ppac_status": ppac_status,
                   "platform_checks": [{"name": item.get("name"), "result": item.get("result"),
                                         "limit": item.get("limit"), "value": item.get("value")}
                                        for item in checks]})
    if reasons:
        result.update(classification="FAIL", reasons=reasons)
    elif pending:
        result.update(classification="PENDING", reasons=pending)
    else:
        result.update(classification="PPA_PASS", reasons=[])
    return result


def _credentials(path: str | None) -> tuple[str, str]:
    path = path or str(ROOT / "Password" / "config.yaml")
    credential_path = Path(path)
    if credential_path.suffix.lower() in {".yaml", ".yml"}:
        data: dict[str, str] = {}
        for line in credential_path.read_text(encoding="utf-8").splitlines():
            if ":" in line and not line.lstrip().startswith("#"):
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip().strip("'\"")
        return str(data.get("username") or data.get("email")), str(data["password"])
    if credential_path.exists():
        data = read_json(credential_path)
        return str(data.get("email") or data.get("username")), str(data["password"])
    email, password = os.getenv("WQB_EMAIL"), os.getenv("WQB_PASSWORD")
    if not email or not password:
        raise RuntimeError("Set WQB_EMAIL/WQB_PASSWORD or pass --credentials JSON")
    return email, password


def _api_query_spec(scope: dict[str, Any], standard: dict[str, Any], window: Window) -> dict[str, Any]:
    req = scope["core_requirements"]
    sharpe_min = float(standard.get("entry_requirements", {}).get("sharpe_min", 1.0))
    return {
        "client": "wqbmcp.WQBSession.filter_alphas",
        "timezone": "America/New_York",
        "date_created_boundary": "[inclusive, exclusive)",
        "filters": {
            "type": "REGULAR",
            "status": "UNSUBMITTED",
            "instrument_type": "EQUITY",
            "region": req["region"],
            "delay": req["delay"],
            "universe": req["universe"],
            # Match the platform list's visible `>1` filter. The later PPA
            # gate still records the standard minimum separately.
            "sharpe": f"({sharpe_min:g}, inf)",
            "date_created": f"[{window.start.isoformat()}, {window.end.isoformat()})",
            "order": "dateCreated",
        },
    }


def _live_candidates(session: Any, scope: dict[str, Any], standard: dict[str, Any], window: Window) -> list[dict[str, Any]]:
    import wqb

    spec = _api_query_spec(scope, standard, window)["filters"]
    query = dict(type=spec["type"], status=spec["status"], instrument_type=spec["instrument_type"],
                 region=spec["region"], delay=spec["delay"], universe=spec["universe"],
                 sharpe=wqb.FilterRange.from_str(spec["sharpe"]),
                 date_created=wqb.FilterRange.from_str(
                     f"[{window.start.isoformat()}, {window.end.isoformat()})"),
                 order="dateCreated", log=None)
    rows: list[dict[str, Any]] = []
    for response in session.filter_alphas(**query):
        if not response.ok:
            raise RuntimeError(f"candidate query HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, (dict, list)):
            raise RuntimeError("candidate query returned an invalid JSON shape")
        page = payload if isinstance(payload, list) else payload.get("results", [])
        rows.extend(item for item in page if isinstance(item, dict))
    unique = {}
    for item in rows:
        key = item.get("id") or item.get("alpha_id")
        if key:
            unique[str(key)] = item
    return list(unique.values())


def _resolve_field_metadata(session: Any, alpha: dict[str, Any]) -> list[dict[str, Any]]:
    metadata = []
    for field_id in _expression_field_candidates(alpha):
        try:
            response = session.locate_field(field_id)
            if not response.ok:
                continue
            payload = response.json()
            if not isinstance(payload, dict) or payload.get("id") != field_id:
                continue
            dataset = payload.get("dataset") if isinstance(payload.get("dataset"), dict) else {}
            metadata.append({"field_id": field_id, "dataset_id": dataset.get("id"),
                             "dataset_name": dataset.get("name"), "type": payload.get("type"),
                             "source": "platform.locate_field"})
        except Exception:
            continue
    return metadata


async def _live_checks(session: Any, ids: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for alpha_id in ids:
        try:
            response = await session.check(alpha_id, log=None)
            result[alpha_id] = response.json() if response.ok else {"http_status": response.status_code}
        except Exception as exc:  # network/auth errors become PENDING, never PASS
            result[alpha_id] = {"error": type(exc).__name__, "message": str(exc)}
    return result


def _error_reason(alpha: dict[str, Any], check_payload: dict[str, Any] | None) -> str | None:
    # Platform FAIL is handled by its specific gate/classify logic; this stage
    # is only for transport/payload errors and literal ERROR/ERR check states.
    for key in ("error", "errors", "http_status"):
        if alpha.get(key) or (check_payload and check_payload.get(key)):
            return f"{key} present"
    for item in _checks(check_payload):
        if _result(item) in {"ERROR", "ERR"} or "ERROR" in str(item.get("name", "")).upper():
            return f"platform check error: {item.get('name')}"
    return None


def _power_pool_state(alpha: dict[str, Any], check_payload: dict[str, Any] | None,
                      standard: dict[str, Any]) -> tuple[str, str]:
    checks = _checks(check_payload)
    item = _check_by_name(checks, {"POWER_POOL_CORRELATION"})
    if item is None:
        return "PENDING", "POWER_POOL_CORRELATION missing"
    state = _result(item)
    if state in {"PENDING", "WARNING", "WAITING"}:
        return "PENDING", f"POWER_POOL_CORRELATION {state}"
    if state not in {"PASS", "PASSED", "SUCCESS", "OK"}:
        return "FAIL", f"POWER_POOL_CORRELATION {state}"
    value = item.get("value")
    if value is None:
        return "PENDING", "POWER_POOL_CORRELATION value missing"
    maximum = float(standard.get("entry_requirements", {}).get("power_pool_self_correlation_max", 0.5))
    try:
        if value is not None and float(value) > maximum:
            return "FAIL", f"Power Pool self-correlation {value} > {maximum}"
    except (TypeError, ValueError):
        return "PENDING", "POWER_POOL_CORRELATION value invalid"
    return "PASS", f"POWER_POOL_CORRELATION <= {maximum}"


def _support_dataset_state(alpha: dict[str, Any], scope: dict[str, Any]) -> tuple[str, str]:
    field_hits = _forbidden_field_hits(alpha, scope)
    if field_hits:
        return "FAIL", "forbidden field: " + ", ".join(field_hits)
    requirements = scope.get("core_requirements", {})
    datasets = {item.lower() for item in _datasets(alpha)}
    blocked = sorted(datasets & {str(item).lower() for item in requirements.get("forbidden_datasets", [])})
    if not blocked:
        return "PASS", "no forbidden dataset"
    fields = _fields(alpha)
    if not fields:
        return "PENDING", "forbidden dataset support-field exception lacks field evidence"
    if _forbidden_support_exception(fields, blocked, scope):
        return "PASS", "forbidden dataset used only by support fields"
    return "FAIL", "forbidden dataset: " + ", ".join(blocked)


def _stage_result(row: dict[str, Any], classification: str, reason: str,
                  scope: dict[str, Any]) -> dict[str, Any]:
    return {"alpha_id": row.get("id") or row.get("alpha_id"),
            "classification": classification, "reasons": [reason],
            "base_scope": _base_scope(scope)}


def screen_pipeline(candidates: list[dict[str, Any]], check_map: dict[str, dict[str, Any]],
                    standard: dict[str, Any], scope: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Run the requested filters in the same order they are reported."""
    req = scope.get("core_requirements", {})
    entry = standard.get("entry_requirements", {})
    active = list(candidates)
    reports: list[dict[str, Any]] = []
    steps = [{"stage": "load_scope_json", "scope_loaded": 1, "input": 0,
              "remaining": 0, "excluded": 0, "pending": 0},
             {"stage": "query_scope_region_delay_universe_sharpe", "input": len(active),
              "remaining": len(active), "excluded": 0, "pending": 0}]

    terminal: dict[str, str] = {}
    next_active = []
    excluded = pending = 0
    allowed = {_neutralization_key(value) for value in req.get("neutralization", [])}
    bounds = entry.get("turnover", {})
    for row in active:
        settings = _settings(row)
        actual = _neutralization_key(settings.get("neutralization", row.get("neutralization")))
        turnover = _number(row, "turnover")
        if not actual or actual not in allowed:
            row["_excluded_at"] = "neutralization_and_turnover"
            reports.append(_stage_result(row, "EXCLUDED", f"neutralization not allowed: {settings.get('neutralization')}", scope)); excluded += 1
        elif turnover is None:
            row.setdefault("_stage_reasons", []).append("turnover missing"); next_active.append(row); pending += 1
        elif not float(bounds.get("min", 0.01)) <= turnover <= float(bounds.get("max", 0.70)):
            row["_excluded_at"] = "neutralization_and_turnover"
            reports.append(_stage_result(row, "EXCLUDED", f"turnover {turnover} outside allowed range", scope)); excluded += 1
        else:
            next_active.append(row)
    active = next_active
    steps.append({"stage": "neutralization_and_turnover", "input": len(active) + excluded,
                  "remaining": len(active), "excluded": excluded, "pending": pending})

    next_active = []
    excluded = 0
    for row in active:
        reason = _error_reason(row, check_map.get(str(row.get("id"))))
        if reason:
            row["_excluded_at"] = "error_check"
            reports.append(_stage_result(row, "EXCLUDED", reason, scope)); excluded += 1
        else:
            next_active.append(row)
    active = next_active
    steps.append({"stage": "error_check", "input": len(active) + excluded,
                  "remaining": len(active), "excluded": excluded, "pending": 0})

    next_active = []
    excluded = pending = 0
    for row in active:
        state, reason = _support_dataset_state(row, scope)
        if state == "FAIL":
            row["_excluded_at"] = "forbidden_datasets"
            reports.append(_stage_result(row, "FAIL", reason, scope)); excluded += 1
        else:
            if state == "PENDING": pending += 1
            row.setdefault("_stage_reasons", []).append(reason); next_active.append(row)
    active = next_active
    steps.append({"stage": "forbidden_datasets", "input": len(active) + excluded,
                  "remaining": len(active), "excluded": excluded, "pending": pending})

    next_active = []
    excluded = pending = 0
    for row in active:
        state, reason = _power_pool_state(row, check_map.get(str(row.get("id"))), standard)
        ppac_status, ppac_failures, ppac_pending = _ppac_gate(_checks(check_map.get(str(row.get("id")))))
        if state == "FAIL" or ppac_failures:
            row["_excluded_at"] = "power_pool_self_correlation"
            details = [reason] + [f"PPAC {item}" for item in ppac_failures]
            reports.append(_stage_result(row, "FAIL", "; ".join(details), scope)); excluded += 1
        else:
            row["_survived_ppac"] = True
            if state == "PENDING" or ppac_pending: pending += 1
            row.setdefault("_stage_reasons", []).extend([reason] + [f"PPAC {item}" for item in ppac_pending])
            next_active.append(row)
    active = next_active
    steps.append({"stage": "power_pool_self_correlation", "input": len(active) + excluded,
                  "remaining": len(active), "excluded": excluded, "pending": pending})

    post_ppac = list(active)
    next_active = []
    excluded = pending = 0
    maximum_fields = int(entry.get("unique_data_fields_max_excluding_support_fields", 3))
    maximum_operators = int(entry.get("operators_max", 8))
    for row in active:
        fields, operators = _fields(row), _operator_count(row)
        non_support = {field.lower() for field in fields} - SUPPORT_FIELDS
        if not fields or operators is None:
            row.setdefault("_stage_reasons", []).append("unique fields or operators missing"); next_active.append(row); pending += 1
        elif len(non_support) > maximum_fields:
            terminal[str(row.get("id"))] = f"non-support fields {len(non_support)} > {maximum_fields}"; excluded += 1
        elif operators > maximum_operators:
            terminal[str(row.get("id"))] = f"operators {operators} > {maximum_operators}"; excluded += 1
        else:
            next_active.append(row)
    active = next_active
    steps.append({"stage": "unique_fields_and_operators", "input": len(active) + excluded,
                  "remaining": len(active), "excluded": excluded, "pending": pending})

    final_rows = []
    for row in post_ppac:
        result = classify(row, standard, scope, check_map.get(str(row.get("id"))))
        if row.get("_stage_reasons"):
            result["pipeline_reasons"] = row["_stage_reasons"]
        if str(row.get("id")) in terminal:
            row["_excluded_at"] = "unique_fields_and_operators"
            result["classification"] = "FAIL"
            result["reasons"] = [terminal[str(row.get("id"))]] + result.get("reasons", [])
        reports.append(result)
        final_rows.append({**row, "check_payload": check_map.get(str(row.get("id")))} | result)
    return reports, final_rows, steps


def _ppac_display(row: dict[str, Any]) -> str:
    item = _check_by_name(_checks(row.get("check_payload")), {"POWER_POOL_CORRELATION"})
    if not item:
        return "MISSING"
    return f"{_result(item)}:{item.get('value')}" if item.get("value") is not None else "PENDING:value missing"


def write_final_table(rows: list[dict[str, Any]], output: Path) -> None:
    lines = ["| Alpha ID | Expression | Sharpe | Fitness | Turnover | PPAC | Status |",
             "|---|---|---:|---:|---:|---|---|"]
    for row in rows:
        values = [str(row.get("id") or row.get("alpha_id") or ""), _expression(row).replace("|", "\\|").replace("\n", " "),
                  row.get("sharpe", ""), _number(row, "fitness") or "", row.get("turnover", ""),
                  _ppac_display(row), row.get("classification", "")]
        lines.append("| " + " | ".join(map(str, values)) + " |")
    (output / "final_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_steps(steps: list[dict[str, Any]], output: Path) -> None:
    lines = ["PPA 筛选阶段计数", "=" * 24]
    for step in steps:
        if step["stage"] == "load_scope_json":
            line = (f"{step['stage']}: scope_loaded={step['scope_loaded']} candidates={step['remaining']} "
                    "(scope only; Alpha query pending)")
        else:
            line = (f"{step['stage']}: input={step['input']} remaining={step['remaining']} "
                    f"excluded={step['excluded']} pending={step['pending']}")
        lines.append(line)
        print(line)
    (output / "filter_steps.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_screening_records(details: list[dict[str, Any]], reports: list[dict[str, Any]],
                            check_map: dict[str, dict[str, Any]], standard: dict[str, Any],
                            scope: dict[str, Any], steps: list[dict[str, Any]],
                            api_query: dict[str, Any], output: Path) -> None:
    report_map = {str(row.get("alpha_id")): row for row in reports if row.get("alpha_id")}
    records = []
    missing_lines = ["PPA 缺失信息与本地补齐结果", "=" * 30]
    for detail in details:
        alpha_id = str(detail.get("id") or detail.get("alpha_id"))
        report = report_map.get(alpha_id, {"classification": "PENDING", "reasons": ["no final report"]})
        checks = _checks(check_map.get(alpha_id))
        local_evidence = []
        missing_information = []
        platform_failures = sorted({
            str(item.get("name")) for item in checks
            if _result(item) in {"FAIL", "ERROR", "ERR"} and item.get("name")
        })
        resolved_fields = detail.get("resolved_field_metadata") or []
        if resolved_fields:
            mappings = ", ".join(
                f"{item.get('field_id')}->{item.get('dataset_id') or 'unknown'}"
                for item in resolved_fields
            )
            local_evidence.append(f"字段/Dataset 已由 platform.locate_field 补齐: {mappings}")
        else:
            missing_information.append("字段/Dataset 未能由 platform.locate_field 补齐")
        description = (detail.get("regular") or {}).get("description") if isinstance(detail.get("regular"), dict) else None
        if isinstance(description, str):
            local_evidence.append(f"本地描述长度={len(description)}")
        else:
            missing_information.append("regular.description 未返回")
        for name in sorted(PPAC_REQUIRED_NAMES):
            item = _check_by_name(checks, {name})
            if item is None:
                missing_information.append(f"{name} result missing")
            elif name == "POWER_POOL_CORRELATION" and item.get("value") is None:
                missing_information.append(f"{name} numeric value missing")
        missing_lines.append(f"\n[{alpha_id}] status={report.get('classification')}")
        missing_lines.append("local: " + ("; ".join(local_evidence) if local_evidence else "none"))
        missing_lines.append("platform_failures: " + (", ".join(platform_failures) if platform_failures else "none"))
        missing_lines.append("platform_pending: " + ("; ".join(missing_information) if missing_information else "none"))
        records.append({
            "alpha_id": alpha_id,
            "expression": _expression(detail),
            "settings": _settings(detail),
            "sharpe": _number(detail, "sharpe"),
            "fitness": _number(detail, "fitness"),
            "turnover": _number(detail, "turnover"),
            "operators": _operator_count(detail),
            "fields": _fields(detail),
            "datasets": _datasets(detail),
            "resolved_field_metadata": detail.get("resolved_field_metadata", []),
            "classification": report.get("classification"),
            "reasons": report.get("reasons", []),
            "pipeline_reasons": report.get("pipeline_reasons", []),
            "survived_ppac": bool(detail.get("_survived_ppac")),
            "excluded_at": detail.get("_excluded_at"),
            "base_scope": report.get("base_scope", _base_scope(scope)),
            "checks": checks,
            "local_evidence": local_evidence,
            "platform_failures": platform_failures,
            "missing_information": missing_information,
            "raw_detail": detail,
        })
    payload = {"standard": standard, "scope": scope, "api_query": api_query,
               "steps": steps, "records": records}
    (output / "screening_records.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "missing_info.txt").write_text("\n".join(missing_lines) + "\n", encoding="utf-8")


def write_reports(rows: list[dict[str, Any]], output: Path) -> None:
    for row in rows:
        folder = output / str(row["classification"]).lower().replace("ppa_", "")
        folder.mkdir(parents=True, exist_ok=True)
        alpha_id = row.get("alpha_id") or "unknown"
        (folder / f"{alpha_id}.json").write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {"count": len(rows), "by_classification": {}}
    for row in rows:
        key = row["classification"]
        summary["by_classification"][key] = summary["by_classification"].get(key, 0) + 1
    (output / "summary.json").parent.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def run_dry(input_path: Path, standard: dict[str, Any], scope: dict[str, Any]) -> list[dict[str, Any]]:
    payload = read_json(input_path)
    rows = payload.get("alphas", payload if isinstance(payload, list) else [])
    output = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        output.append(classify(item, standard, scope, item.get("check_payload")))
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only WorldQuant BRAIN PPA Alpha screening")
    parser.add_argument("--scope", type=Path, help="PPA scope JSON; defaults to newest file")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--credentials", help="JSON/YAML credential file; defaults to Password/config.yaml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--input", type=Path, help="Fixture JSON used with --dry-run")
    parser.add_argument("--query-only", action="store_true",
                        help="Only fetch and save the read-only API candidate list")
    args = parser.parse_args()

    standard = read_json(STANDARD_FILE)
    scope_path = args.scope or latest_scope()
    scope = load_scope(scope_path)
    window = date_window(args.start_date, args.end_date)
    args.output.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        if not args.input:
            parser.error("--dry-run requires --input")
        rows = run_dry(args.input, standard, scope)
    else:
        import wqb

        session = wqb.WQBSession(_credentials(args.credentials))
        try:
            window = intersect_scope_window(window, scope)
        except ValueError as exc:
            rows = [{"alpha_id": "__run__", "classification": "PENDING",
                     "base_scope": _base_scope(scope), "reasons": [str(exc)]}]
            write_reports(rows, args.output)
            print(json.dumps({"scope": str(scope_path), "count": 0, "pending": True,
                              "output": str(args.output)}, ensure_ascii=False))
            return 0
        api_query = _api_query_spec(scope, standard, window)
        (args.output / "api_query.json").write_text(
            json.dumps(api_query, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            candidates = _live_candidates(session, scope, standard, window)
        except Exception as exc:
            rows = [{"alpha_id": "__run__", "classification": "PENDING",
                     "reasons": [f"candidate query unavailable: {type(exc).__name__}: {exc}"]}]
            write_reports(rows, args.output)
            print(json.dumps({"scope": str(scope_path), "count": 0, "pending": True,
                              "output": str(args.output)}, ensure_ascii=False))
            return 0
        if args.query_only:
            (args.output / "api_candidates.json").write_text(
                json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"query": api_query, "count": len(candidates),
                              "output": str(args.output)}, ensure_ascii=False))
            return 0
        details = []
        for candidate in candidates:
            alpha_id = candidate.get("id") or candidate.get("alpha_id")
            if not alpha_id:
                continue
            try:
                detail = session.locate_alpha(alpha_id).json()
            except Exception as exc:
                details.append({**candidate, "id": alpha_id,
                                "check_payload": {"error": type(exc).__name__, "message": str(exc)}})
                continue
            detail = {**candidate, **detail, "id": alpha_id}
            detail["resolved_field_metadata"] = _resolve_field_metadata(session, detail)
            details.append(detail)
        check_map = asyncio.run(_live_checks(session, [str(item["id"]) for item in details]))
        rows, final_rows, steps = screen_pipeline(details, check_map, standard, scope)
        seen_expressions: dict[str, str] = {}
        for item, row in zip(details, rows):
            expression = _expression(item).strip()
            if expression and expression in seen_expressions:
                row.update(classification="EXCLUDED",
                           reasons=[f"duplicate expression of {seen_expressions[expression]}"])
            elif expression:
                seen_expressions[expression] = str(row.get("alpha_id"))
        write_steps(steps, args.output)
        write_final_table(final_rows, args.output)
        write_screening_records(details, rows, check_map, standard, scope, steps, api_query, args.output)
    write_reports(rows, args.output)
    print(json.dumps({"scope": str(scope_path), "window": [window.start.isoformat(), window.end.isoformat()],
                      "count": len(rows), "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
