"""V6: sweep settings for the 8 best Useful source alphas.

The source expression is never changed. V6 obtains legal Universe and
Neutralization values through the project Core API, runs every setting
combination with multi-simulation, then recalculates SC/PC and synchronizes
aliases and tags for the returned child Alpha IDs.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

import filter_ra_alphas_core as core


V6_OUTPUT_PREFIX = "filtered_RAs_v6"
V6_STATE_PREFIX = "filter_ra_alphas_v6_state"
V6_TOP_USEFUL_COUNT = 8
V6_DECAYS = (0, 5, 20)
V6_BATCH_SIZE = 8
V6_MARGIN_BP_BY_REGION = {"USA": 8.0, "EUR": 8.0}
V6_DEFAULT_MARGIN_BP = 13.0
V6_MAX_NEUTRALIZATIONS = 5
V6_MAX_UNIVERSES = 4
V6_VARIANT_PLAN_VERSION = 2
V6_429_COOLDOWN_SECONDS = 300
V6_429_MAX_RETRIES = 3
V6_MIN_SHARPE = 1.6
V6_MIN_FITNESS = 1.0

# 只改这里的 True/False，然后直接运行本文件。
V6_DRY_RUN = False         # 是否只预演、不提交回测
V6_SKIP_SIMULATION = False  # 首次运行需要创建 V6 回测；后续可从断点恢复
V6_SKIP_SC_PC = False       # 是否跳过 SC/PC 和平台标签更新


def _progress(message):
    """Print and persist a concise V6 progress message."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    print(f"[V6] {message}", flush=True)
    logging.info(message)


def _abs_or_none(value):
    try:
        return abs(float(value)) if pd.notna(value) else None
    except (TypeError, ValueError):
        return None


def _number_or_none(value):
    try:
        return float(value) if pd.notna(value) else None
    except (TypeError, ValueError):
        return None


def _is_useful(value):
    return any(
        str(tag).strip().casefold() == core.USEFUL_TAG.casefold()
        for tag in str(value or "").split(",")
        if str(tag).strip()
    )


def find_latest_v5_output(output_dir):
    """Return the newest dated V5 workbook, excluding all V6 outputs."""
    candidates = []
    for path in Path(output_dir).glob("filtered_RAs_*.xlsx"):
        date_part = path.stem.removeprefix("filtered_RAs_")
        if len(date_part) == 8 and date_part.isdigit():
            candidates.append((date_part, path.stat().st_mtime_ns, path))
    return max(candidates, key=lambda item: (item[0], item[1], item[2].name))[2] if candidates else None


def _margin_cutoff(region):
    margin_bp = V6_MARGIN_BP_BY_REGION.get(str(region).upper(), V6_DEFAULT_MARGIN_BP)
    return margin_bp / 10000.0


def select_top_useful(frame, limit=V6_TOP_USEFUL_COUNT):
    """Filter Useful by regional margin first, then rank by abs SC/PC."""
    if frame is None or frame.empty or "Platform_Tags" not in frame.columns:
        return frame.iloc[0:0].copy() if frame is not None else pd.DataFrame()
    useful = frame[frame["Platform_Tags"].map(_is_useful)].copy()
    if useful.empty:
        return useful
    regions = useful.get("Region", pd.Series(index=useful.index)).fillna("").astype(str).str.upper()
    margins = pd.to_numeric(useful.get("Margin", pd.Series(index=useful.index)), errors="coerce")
    useful = useful[margins > regions.map(_margin_cutoff)].copy()
    if useful.empty:
        return useful
    useful["_v6_sc_rank"] = useful.get("self_correlation", pd.Series(index=useful.index)).map(_abs_or_none)
    pc_max = useful.get("prod_correlation_max", pd.Series(index=useful.index)).map(_abs_or_none)
    pc_min = useful.get("prod_correlation_min", pd.Series(index=useful.index)).map(_abs_or_none)
    useful["_v6_pc_rank"] = pd.concat([pc_max, pc_min], axis=1).max(axis=1, skipna=True)
    useful["_v6_sc_missing"] = useful["_v6_sc_rank"].isna()
    useful["_v6_pc_missing"] = useful["_v6_pc_rank"].isna()
    useful["_v6_alpha_sort"] = useful.get(
        "alpha_id_raw", useful.get("alpha_id", pd.Series(index=useful.index))
    ).fillna("").astype(str)
    useful = useful.sort_values(
        ["_v6_sc_missing", "_v6_sc_rank", "_v6_pc_missing", "_v6_pc_rank", "_v6_alpha_sort"],
        na_position="last",
    )
    return useful.head(max(0, int(limit))).drop(
        columns=["_v6_sc_rank", "_v6_pc_rank", "_v6_sc_missing", "_v6_pc_missing", "_v6_alpha_sort"],
        errors="ignore",
    )


def _setting_value(row, *names):
    for name in names:
        if name in row and row[name] is not None:
            return row[name]
    return None


def region_setting_options(options, region, delay):
    """Read exact platform options for one Region/Delay pair."""
    rows = options.get("instrument_options", []) if isinstance(options, dict) else []
    region = str(region).upper()
    matching = [
        row for row in rows
        if str(_setting_value(row, "InstrumentType", "instrumentType", "instrument_type") or "").upper() == "EQUITY"
        and str(_setting_value(row, "Region", "region") or "").upper() == region
    ]
    if not matching:
        raise ValueError(f"平台没有 EQUITY/{region} 的合法设置")
    try:
        requested_delay = int(delay)
    except (TypeError, ValueError):
        requested_delay = 1
    selected = next(
        (row for row in matching if int(_setting_value(row, "Delay", "delay")) == requested_delay),
        matching[0],
    )
    universes = _setting_value(selected, "Universe", "universes", "universe") or []
    neutralizations = _setting_value(selected, "Neutralization", "Neutralizations", "neutralization") or []
    if isinstance(universes, str):
        universes = [universes]
    if isinstance(neutralizations, str):
        neutralizations = [neutralizations]
    neutralizations = tuple(
        dict.fromkeys(
            str(value).upper()
            for value in neutralizations
            if str(value).strip() and str(value).upper() != "NONE"
        )
    )
    return {
        "region": region,
        "delay": int(_setting_value(selected, "Delay", "delay") or requested_delay),
        "universes": tuple(dict.fromkeys(str(value).upper() for value in universes if str(value).strip())),
        "neutralizations": neutralizations,
    }


def _balanced_random_sample(values, limit, rank, key, setting_seed):
    values = list(values)
    if len(values) <= limit:
        return tuple(values)
    shuffled = values[:]
    random.Random(f"{setting_seed}:{key}").shuffle(shuffled)
    start = ((rank - 1) * limit) % len(shuffled)
    return tuple(shuffled[(start + offset) % len(shuffled)] for offset in range(limit))


def _variant_identity(item):
    return (
        str(item.get("source_alpha_id") or ""),
        str(item.get("expression") or ""),
        str(item.get("region") or ""),
        str(item.get("universe") or ""),
        int(item.get("delay") or 0),
        str(item.get("neutralization") or ""),
        int(item.get("decay") or 0),
    )


def build_variants(useful_frame, options, decays=V6_DECAYS, setting_seed="v6"):
    variants = []
    settings_cache = {}
    region_ranks = defaultdict(int)
    sampled_settings = {}
    for source_rank, (_, row) in enumerate(useful_frame.iterrows(), start=1):
        region = str(row.get("Region") or "").upper()
        if not region:
            continue
        region_ranks[region] += 1
        delay = row.get("Delay", 1)
        cache_key = (region, str(delay))
        if cache_key not in settings_cache:
            settings_cache[cache_key] = region_setting_options(options, region, delay)
        setting = settings_cache[cache_key]
        expression_value = row.get("Expression")
        expression = "" if pd.isna(expression_value) else str(expression_value).strip()
        if not expression:
            continue
        source_id = str(row.get("alpha_id_raw") or row.get("alpha_id") or "").strip()
        expression_hash = hashlib.sha1(expression.encode("utf-8")).hexdigest()[:12]
        setting_key = (region, setting["delay"])
        if setting_key not in sampled_settings:
            sampled_settings[setting_key] = (
                _balanced_random_sample(
                    setting["universes"], V6_MAX_UNIVERSES, 1,
                    f"{region}:{setting['delay']}:universes", setting_seed
                ),
                tuple(setting["neutralizations"])
                if len(setting["neutralizations"]) <= 6
                else _balanced_random_sample(
                    setting["neutralizations"], V6_MAX_NEUTRALIZATIONS, 1,
                    f"{region}:{setting['delay']}:neutralizations", setting_seed
                ),
            )
        universes, neutralizations = sampled_settings[setting_key]
        for universe in universes:
            for neutralization in neutralizations:
                for decay in decays:
                    variants.append({
                        "variant_key": (
                            f"{source_id}:{expression_hash}:{region}:{universe}:"
                            f"{neutralization}:{int(decay)}"
                        ),
                        "source_rank": source_rank,
                        "source_alpha_id": source_id,
                        "expression": expression,
                        "region": region,
                        "universe": universe,
                        "delay": setting["delay"],
                        "neutralization": neutralization,
                        "decay": int(decay),
                        "status": "PENDING_SIMULATION",
                    })
    return variants


def group_variants(variants, by_source=False):
    groups = defaultdict(list)
    source_groups = {}
    for variant in variants:
        key = (
            variant["region"], variant["universe"], variant["delay"],
            variant["neutralization"], variant["decay"],
        )
        if by_source:
            source_key = (variant["region"], variant["delay"], variant.get("source_alpha_id", "LEGACY_UNKNOWN_SOURCE"))
            key = source_groups.setdefault(source_key, (*key, source_key[2]))
        groups[key].append(variant)
    return groups


def _source_signature(useful_frame=None, variants=None):
    if useful_frame is not None:
        return tuple(
            (
                str(row.get("alpha_id_raw") or row.get("alpha_id") or "").strip(),
                str(row.get("Expression") or "").strip(),
            )
            for _, row in useful_frame.iterrows()
        )
    sources = {
        int(item.get("source_rank") or 0): (
            str(item.get("source_alpha_id") or "").strip(),
            str(item.get("expression") or "").strip(),
        )
        for item in (variants or [])
    }
    return tuple(sources[rank] for rank in sorted(sources))


async def fetch_platform_options():
    _progress("开始认证并读取平台 Region/Delay 设置")
    options = await asyncio.to_thread(core.get_platform_setting_options_core)
    _progress(f"平台设置读取完成：{len(options.get('instrument_options', []))} 个 Region/Delay 组合")
    return options


def _save_state(state_path, state):
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _is_429(value):
    if not isinstance(value, dict):
        return "429" in str(value)
    status = value.get("status_code")
    if status == 429:
        return True
    error = value.get("error")
    return isinstance(error, str) and "429" in error


async def clear_expanded_alpha_properties(alpha_id):
    """Clear one simulated child Alpha immediately before its final SC/PC labeling."""
    return await set_expanded_alpha_properties(alpha_id, "", [], "清空扩展因子")


async def set_expanded_alpha_properties(alpha_id, name, tags, action):
    """Apply a child property update with the same 429 cooldown used by simulation."""
    response = None
    for attempt in range(1, V6_429_MAX_RETRIES + 1):
        try:
            response = await asyncio.to_thread(core.set_alpha_properties_core, alpha_id, name, tags)
        except Exception as exc:
            response = {"error": str(exc)}
        if not _is_429(response) or attempt >= V6_429_MAX_RETRIES:
            break
        _progress(
            f"{action}遇到 429：{alpha_id}，第 {attempt}/{V6_429_MAX_RETRIES} 次，"
            f"等待 {V6_429_COOLDOWN_SECONDS} 秒"
        )
        await asyncio.sleep(V6_429_COOLDOWN_SECONDS)
    return isinstance(response, dict) and not response.get("error")


async def simulate_variants(variants, state_path, dry_run=False):
    """Persist each eight-item attempt before POST; uncertain chunks are never reposted."""
    import math
    import re
    import time
    from datetime import datetime
    from zoneinfo import ZoneInfo

    state_path = Path(state_path)

    def persist():
        state["results"] = [item for item in variants if item.get("alpha_id")]
        core._atomic_write_json(state_path, state)
    if dry_run:
        source_count = None
        source_file = None
        setting_seed = None
        try:
            previous = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(previous, dict):
                source_count = previous.get("source_count")
                source_file = previous.get("source_file")
                setting_seed = previous.get("setting_seed")
        except (OSError, json.JSONDecodeError, TypeError):
            pass
        for item in variants:
            item["status"] = "DRY_RUN_NOT_SUBMITTED"
        _progress(f"预演模式：计划 {len(variants)} 个组合，不提交平台")
        _save_state(state_path, {
            "version": 6, "variant_plan_version": V6_VARIANT_PLAN_VERSION,
            "dry_run": True, "source_file": source_file, "setting_seed": setting_seed,
            "source_count": source_count,
            "variants": variants,
            "completed_batches": [], "results": [],
        })
        return variants
    state = {
        "version": 6, "variant_plan_version": V6_VARIANT_PLAN_VERSION,
        "variants": variants, "completed_batches": [], "results": [],
    }
    if state_path.is_file():
        try:
            loaded = json.loads(state_path.read_text(encoding="utf-8"))
            if (
                isinstance(loaded, dict)
                and loaded.get("variants")
                and loaded.get("variant_plan_version") == V6_VARIANT_PLAN_VERSION
            ):
                state.update(loaded)
                variants = state["variants"]
            else:
                _progress("V6=PENDING_STATE_VERSION；保留已有断点，不创建回测")
                return variants
        except (OSError, json.JSONDecodeError, TypeError):
            _progress("V6=PENDING_STATE_UNREADABLE；保留已有断点，不创建回测")
            return variants
    chunks = state.setdefault("chunk_batches", [])
    if not isinstance(chunks, list):
        _progress("V6=PENDING_STATE_STRUCTURE；保留已有断点，不创建回测")
        return variants
    attempted = {chunk["id"]: chunk for chunk in chunks if isinstance(chunk, dict) and chunk.get("id")}
    completed = set(state.get("completed_batches", []))
    groups = group_variants(variants, by_source=True)
    total_groups = len(groups)
    total_batches = sum((len(group) + V6_BATCH_SIZE - 1) // V6_BATCH_SIZE for group in groups.values())
    _progress(f"模拟阶段开始：{len(variants)} 个组合，{total_groups} 个设置组，最多 {total_batches} 个批次")
    for group_number, (key, group) in enumerate(groups.items(), start=1):
        batch_key = "|".join(map(str, key))
        if batch_key in completed:
            _progress(f"跳过已完成组 {group_number}/{total_groups}：{key}")
            continue
        group_complete = True
        for start in range(0, len(group), V6_BATCH_SIZE):
            batch = group[start:start + V6_BATCH_SIZE]
            if len(batch) != 8:
                for item in batch:
                    if not item.get("alpha_id"):
                        item["status"] = "PENDING_MULTI_SIMULATION_FULL_BATCH"
                group_complete = False
                persist()
                _progress(f"组 {group_number}/{total_groups}：不足完整八条，保留 PENDING：{key}")
                continue
            individual_settings = [{name: item[name] for name in ("region", "universe", "delay", "neutralization", "decay")}
                                   for item in batch]
            fingerprint = hashlib.sha256(json.dumps({"settings": individual_settings, "expressions": [
                item["expression"] for item in batch]}, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
            chunk = attempted.get(fingerprint)
            if chunk is None:
                chunk = next((old for old in chunks if isinstance(old, dict) and old.get("post_attempted", True)
                              and not old.get("individual_settings")
                              and old.get("expressions") == [item["expression"] for item in batch]
                              and tuple(old.get("settings") or ())[:5] == key[:5]), None)
            policy_retry = chunk is not None and chunk.get("status") == "PENDING_POLICY"
            if chunk is not None and chunk.get("status") == "LOCAL_REJECTED":
                group_complete = False
                continue
            if policy_retry:
                if time.time() < chunk.get("retry_after", 0):
                    return variants
                chunk = None
            if chunk is not None:
                if chunk.get("status") == "COMPLETE":
                    continue
                if time.time() < chunk.get("retry_after", 0):
                    _progress(f"已有八条批次 {fingerprint[:12]}={chunk.get('status')}；不重复 POST")
                    return variants
                if not chunk.get("location") or chunk.get("reconciled"):
                    if not chunk.get("location") and chunk.get("status") != "LEGACY_OBSERVED":
                        chunk["status"] = "RESULTS_UNOBSERVED"
                        chunk["readonly_unavailable"] = True
                    group_complete = False
                    persist()
                    _progress(f"跳过待人工核对批次 {fingerprint[:12]}；继续其他设置，不重复 POST")
                    continue
                # GET 前保存恢复标记；进程崩溃也不能多次恢复或重新 POST。
                chunk["reconciled"] = True
                persist()
                try:
                    response = await asyncio.to_thread(core.recover_multi_simulation_core, chunk["location"])
                except Exception as exc:
                    response = {"error_type": type(exc).__name__, "error": "RESULTS_UNOBSERVED"}
            else:
                chunk = attempted[fingerprint] if policy_retry else {
                    "id": fingerprint, "settings": list(key), "expressions": [item["expression"] for item in batch],
                    "individual_settings": individual_settings,
                    "status": "PLANNED", "post_attempted": False,
                    "created_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()}
                if not policy_retry:
                    chunks.append(chunk)
                attempted[fingerprint] = chunk
                # 旧断点的任何 Alpha ID 或失败提交记录都表明该 chunk 曾经发送；禁止重复创建。
                old_pending_group = tuple(state.get("last_pending_settings") or ()) in {key, key[:5]} and not any(
                    old is not chunk and old.get("post_attempted", True) and tuple(old.get("settings") or ()) == key
                    for old in chunks if isinstance(old, dict))
                if any(item.get("alpha_id") for item in batch) or old_pending_group:
                    chunk["status"] = "LEGACY_OBSERVED" if all(item.get("alpha_id") for item in batch) else "RESULTS_UNOBSERVED"
                    chunk["valid_alpha_ids"] = [item["alpha_id"] for item in batch if item.get("alpha_id")]
                    group_complete = False
                    persist()
                    continue
                try:
                    policies = []
                    for region, universe, delay in sorted({(item["region"], item["universe"], item["delay"]) for item in batch}):
                        checked = await asyncio.to_thread(core.check_single_dataset_batch,
                            [item["expression"] for item in batch], region=region, universe=universe, delay=int(delay))
                        if not isinstance(checked, dict):
                            checked = {"status": "PENDING", "reason": "INVALID_POLICY_RESPONSE"}
                        policies.append(checked)
                        if checked.get("status") != "PASS":
                            break
                    policy = dict(policies[-1])
                    if all(checked.get("status") == "PASS" for checked in policies):
                        datasets = {checked.get("dataset_id") for checked in policies}
                        fields = {field for checked in policies for field in checked.get("field_ids", [])}
                        policy = {"status": "PASS", "dataset_id": next(iter(datasets)), "field_ids": sorted(fields)} if (
                            len(datasets) == 1 and None not in datasets and "" not in datasets and 1 <= len(fields) <= 2
                        ) else {"status": "LOCAL_REJECTED", "reason": "MULTIPLE_DATASETS_OR_FIELD_LIMIT"}
                    policy["scope_checks"] = policies
                except Exception as exc:
                    policy = {"status": "PENDING", "reason": type(exc).__name__}
                policy = policy if isinstance(policy, dict) else {"status": "PENDING", "reason": "INVALID_POLICY_RESPONSE"}
                chunk["policy"] = policy
                chunk["dataset_id"] = policy.get("dataset_id")
                chunk["field_ids"] = policy.get("field_ids")
                if policy.get("status") != "PASS":
                    chunk["status"] = "LOCAL_REJECTED" if policy.get("status") == "LOCAL_REJECTED" else "PENDING_POLICY"
                    chunk["retry_after"] = time.time() + 300
                    group_complete = False
                    persist()
                    if chunk["status"] == "LOCAL_REJECTED":
                        continue
                    return variants
                chunk["status"] = "SUBMITTING"
                chunk["post_attempted"] = True
                if not chunk.get("reconciled"):
                    chunk["retry_after"] = time.time() + 300
                persist()
                _progress(
                    f"提交组 {group_number}/{total_groups}：Region={key[0]} Universe={key[1]} "
                    f"Neutralization={key[3]} Decay={key[4]} expressions={len(batch)}"
                )
                try:
                    response = await asyncio.to_thread(
                        core.create_multi_simulation_core,
                        alpha_expressions=[item["expression"] for item in batch],
                        instrument_type="EQUITY",
                        region=key[0], universe=key[1], delay=int(key[2]),
                        decay=int(key[4]), neutralization=key[3],
                        max_trade="OFF", pasteurization="ON", visualization=False,
                        individual_settings=individual_settings, defer_polling=True,
                    )
                except Exception as exc:
                    response = {"error_type": type(exc).__name__, "error": "RESULTS_UNOBSERVED"}
            if isinstance(response, dict):
                chunk["location"] = response.get("location") or response.get("multisimulation_location") or chunk.get("location")
                chunk["http_status"] = response.get("status_code")
            if not isinstance(response, dict) or response.get("error"):
                chunk["status"] = "PENDING" if chunk.get("location") else "RESULTS_UNOBSERVED"
                chunk["error_type"] = response.get("error_type", "PLATFORM_UNOBSERVED") if isinstance(response, dict) else "INVALID_RESPONSE"
                _progress(f"批次={chunk['status']}：{key}；不重复 POST")
                group_complete = False
                state["results"] = [item for item in variants if item.get("alpha_id")]
                state["last_pending_settings"] = key
                state["completed_batches"] = sorted(completed)
                if not chunk.get("reconciled"):
                    chunk["retry_after"] = time.time() + 300
                persist()
                return variants
            alpha_results = response.get("alpha_results") or []
            if not isinstance(alpha_results, list) or not alpha_results:
                for item in batch:
                    item["status"] = "PENDING_NO_RESULTS"
                group_complete = False
                chunk["status"] = "PENDING" if chunk.get("location") else "RESULTS_UNOBSERVED"
                state["results"] = [item for item in variants if item.get("alpha_id")]
                state["last_pending_settings"] = key
                state["last_pending_reason"] = "NO_RESULTS"
                state["completed_batches"] = sorted(completed)
                if not chunk.get("reconciled"):
                    chunk["retry_after"] = time.time() + 300
                persist()
                _progress(f"V6 group {group_number}/{total_groups}: no alpha results; skip for now: {key}")
                return variants
            if len(alpha_results) != len(batch):
                group_complete = False
            chunk_complete = len(alpha_results) == 8
            observed_ids = []
            normalize = lambda expression: re.sub(r"\s+", "", expression) if isinstance(expression, str) else None
            expression_items = defaultdict(list)
            for item in batch:
                expression_items[normalize(item["expression"])].append(item)
            matched_expressions = set()
            for result in alpha_results:
                result = result if isinstance(result, dict) else {}
                details = result.get("details") or {}
                details = details if isinstance(details, dict) else {}
                regular = details.get("regular")
                observed_expression = normalize(regular.get("code")) if isinstance(regular, dict) else None
                matching = expression_items.get(observed_expression, [])
                if len(matching) > 1:
                    observed_settings = details.get("settings") or {}
                    matching = [item for item in matching if isinstance(observed_settings, dict) and all(
                        observed_settings.get(name) == item[name] for name in ("region", "universe", "delay", "neutralization", "decay"))]
                match_key = None if len(matching) != 1 else (
                    observed_expression, *(matching[0][name] for name in ("region", "universe", "delay", "neutralization", "decay")))
                if len(matching) != 1 or match_key in matched_expressions:
                    group_complete = False
                    chunk_complete = False
                    continue
                item = matching[0]
                alpha_id = str(result.get("alpha_id") or details.get("id") or "").strip()
                if not alpha_id:
                    item["status"] = "RESULTS_UNOBSERVED"
                    group_complete = False
                    chunk_complete = False
                    continue
                matched_expressions.add(match_key)
                metrics = details.get("is") or {}
                metrics = metrics if isinstance(metrics, dict) else {}
                item.update({
                    "alpha_id": alpha_id,
                    "sharpe": metrics.get("sharpe"),
                    "fitness": metrics.get("fitness"),
                    "margin": metrics.get("margin"),
                    "turnover": metrics.get("turnover"),
                    "status": "SIMULATION_OBSERVED",
                })
                observed_ids.append(alpha_id)
                chunk_complete = chunk_complete and not result.get("error") and all(isinstance(metrics.get(metric), (int, float))
                    and not isinstance(metrics.get(metric), bool) and math.isfinite(metrics[metric])
                    for metric in ("sharpe", "fitness", "margin", "turnover"))
            chunk_complete = chunk_complete and len(set(observed_ids)) == 8 and len(matched_expressions) == 8
            chunk["valid_alpha_ids"] = observed_ids
            chunk["status"] = "COMPLETE" if chunk_complete else "PENDING"
            chunk["results"] = [{"alpha_id": item.get("alpha_id"), "status": item.get("status"),
                                 **{metric: item.get(metric) for metric in ("sharpe", "fitness", "margin", "turnover")}}
                                for item in batch]
            if chunk_complete:
                chunk["completed_at"] = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
            else:
                group_complete = False
                if not chunk.get("reconciled"):
                    chunk["retry_after"] = time.time() + 300
            state["results"] = [item for item in variants if item.get("alpha_id")]
            persist()
            _progress(f"组 {group_number}/{total_groups} 完成：观测到 {len(alpha_results)} 个 Alpha ID")
            if not chunk_complete:
                return variants
        if group_complete:
            completed.add(batch_key)
        state["completed_batches"] = sorted(completed)
        persist()
    return variants


def _variant_frame(variants):
    rows = []
    for item in variants:
        if not item.get("alpha_id"):
            continue
        rows.append({
            "alpha_id": item["alpha_id"], "alpha_id_raw": item["alpha_id"],
            "Variant_Key": item["variant_key"],
            "Expression": item["expression"], "Region": item["region"],
            "Universe": item["universe"], "Delay": item["delay"],
            "Decay": item["decay"], "Neutralization": item["neutralization"],
            "Source_Alpha_ID": item["source_alpha_id"], "Source_Rank": item["source_rank"],
            "Sharpe": item.get("sharpe"), "Fitness": item.get("fitness"), "Margin": item.get("margin"),
            "Turnover": item.get("turnover"),
            "Basic_Status": item.get("basic_status", "PENDING_BASIC_CHECK"),
            "Platform_Name": item.get("platform_name", ""),
            "Platform_Tags": item.get("platform_tags", ""),
            "Platform_Update_Status": item.get("platform_update_status", "NOT_ATTEMPTED"),
            "self_correlation": item.get("self_correlation", pd.NA),
            "prod_correlation_max": item.get("prod_correlation_max", pd.NA),
            "prod_correlation_min": item.get("prod_correlation_min", pd.NA),
            "SC_Status": item.get("sc_status", "PENDING_SC"),
            "PC_Status": item.get("pc_status", "PENDING_PC"),
            "Processing_Status": item.get("processing_status", "PENDING_SC"),
            "V6_Status": item.get("v6_status", "SIMULATION_OBSERVED"),
            "_tags": [],
        })
    return pd.DataFrame(rows)


def _dry_run_frame(variants):
    return pd.DataFrame([{
        "alpha_id": "", "alpha_id_raw": "", "Expression": item["expression"],
        "Region": item["region"], "Universe": item["universe"], "Delay": item["delay"],
        "Decay": item["decay"], "Neutralization": item["neutralization"],
        "Source_Alpha_ID": item["source_alpha_id"], "Source_Rank": item["source_rank"],
        "Simulation_Status": item["status"], "Platform_Update_Status": "DRY_RUN_NOT_SUBMITTED",
        "V6_Status": "DRY_RUN_NOT_SUBMITTED",
    } for item in variants])


def _variant_basic_status(item):
    values = {
        "sharpe": _number_or_none(item.get("sharpe")),
        "fitness": _number_or_none(item.get("fitness")),
        "margin": _number_or_none(item.get("margin")),
    }
    if any(value is None for value in values.values()):
        return "PENDING_BASIC_METRICS"
    if (
        values["sharpe"] < V6_MIN_SHARPE
        or values["fitness"] < V6_MIN_FITNESS
        or values["margin"] <= _margin_cutoff(item.get("region"))
    ):
        return "EXCLUDED_BASIC_METRICS"
    return "PASS"


def _save_label_checkpoint(frame, index, item, variants, state_path, complete=False):
    for column, key in {
        "Basic_Status": "basic_status",
        "Platform_Name": "platform_name",
        "Platform_Tags": "platform_tags",
        "Platform_Update_Status": "platform_update_status",
        "self_correlation": "self_correlation",
        "prod_correlation_max": "prod_correlation_max",
        "prod_correlation_min": "prod_correlation_min",
        "SC_Status": "sc_status",
        "PC_Status": "pc_status",
        "Processing_Status": "processing_status",
        "V6_Status": "v6_status",
    }.items():
        value = frame.at[index, column]
        item[key] = None if pd.isna(value) else value
    item["label_complete"] = bool(complete)
    if state_path is None:
        return
    try:
        state = json.loads(Path(state_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        state = {}
    state["variants"] = variants
    state["results"] = [variant for variant in variants if variant.get("alpha_id")]
    _save_state(Path(state_path), state)


async def label_variants(frame, variants=None, state_path=None):
    if frame.empty:
        return frame
    for column, default in {
        "Variant_Key": "",
        "Basic_Status": "PENDING_BASIC_CHECK",
        "Platform_Name": "",
        "Platform_Tags": "",
        "Platform_Update_Status": "NOT_ATTEMPTED",
        "self_correlation": pd.NA,
        "prod_correlation_max": pd.NA,
        "prod_correlation_min": pd.NA,
        "SC_Status": "PENDING_SC",
        "PC_Status": "PENDING_PC",
        "Processing_Status": "PENDING_SC",
        "V6_Status": "SIMULATION_OBSERVED",
    }.items():
        if column not in frame.columns:
            frame[column] = default
    total = len(frame)
    variants = variants or []
    variant_by_key = {item.get("variant_key"): item for item in variants}
    _progress(f"SC/PC 与标签阶段开始：{total} 个 Alpha")
    for position, index in enumerate(frame.index, start=1):
        alpha_id = frame.at[index, "alpha_id"]
        item = variant_by_key.get(frame.at[index, "Variant_Key"], {})
        if not item:
            item = {
                "variant_key": frame.at[index, "Variant_Key"],
                "alpha_id": alpha_id,
                "region": frame.at[index, "Region"] if "Region" in frame.columns else "",
                "sharpe": frame.at[index, "Sharpe"] if "Sharpe" in frame.columns else None,
                "fitness": frame.at[index, "Fitness"] if "Fitness" in frame.columns else None,
                "margin": frame.at[index, "Margin"] if "Margin" in frame.columns else None,
            }
        _progress(f"相关性检查 {position}/{total}：{alpha_id}")
        if item.get("label_complete"):
            _progress(f"最终标签已完成，跳过：{alpha_id}")
            continue
        if not item.get("properties_cleared") and not await clear_expanded_alpha_properties(alpha_id):
            frame.at[index, "SC_Status"] = "PENDING_CLEAR"
            frame.at[index, "PC_Status"] = "PENDING_CLEAR"
            frame.at[index, "Processing_Status"] = "PENDING_CLEAR"
            frame.at[index, "Platform_Update_Status"] = "PENDING_CLEAR"
            frame.at[index, "V6_Status"] = "PENDING_CLEAR"
            _save_label_checkpoint(frame, index, item, variants, state_path)
            _progress(f"扩展因子 name/tags 清空失败，暂不执行 SC/PC：{alpha_id}")
            continue
        if not item.get("properties_cleared"):
            item["properties_cleared"] = True
            frame.at[index, "Platform_Name"] = ""
            frame.at[index, "Platform_Tags"] = ""
            frame.at[index, "Platform_Update_Status"] = "CLEARED"
            _save_label_checkpoint(frame, index, item, variants, state_path)
            _progress(f"扩展因子 name/tags 已清空：{alpha_id}")
        basic_status = _variant_basic_status(item)
        frame.at[index, "Basic_Status"] = basic_status
        if basic_status != "PASS":
            pending = basic_status.startswith("PENDING")
            frame.at[index, "SC_Status"] = "PENDING_BASIC_METRICS" if pending else "SKIPPED_BASIC_METRICS"
            frame.at[index, "PC_Status"] = frame.at[index, "SC_Status"]
            frame.at[index, "Processing_Status"] = basic_status
            frame.at[index, "V6_Status"] = basic_status
            _save_label_checkpoint(frame, index, item, variants, state_path, complete=not pending)
            _progress(f"基础指标未通过，跳过 SC/PC：{alpha_id} -> {basic_status}")
            continue
        sc_payload = await asyncio.to_thread(core.get_correlation_payload_core, alpha_id, "self")
        sc = core.self_correlation_value(sc_payload)
        frame.at[index, "self_correlation"] = sc
        if pd.isna(sc):
            frame.at[index, "SC_Status"] = "PENDING_SC"
            frame.at[index, "Processing_Status"] = "PENDING_SC"
            _save_label_checkpoint(frame, index, item, variants, state_path)
            _progress(f"相关性结果 PENDING_SC：{alpha_id}")
            continue
        if core.is_high_correlation(sc):
            alpha_name = core.high_alias("SC", sc)
            updated = await set_expanded_alpha_properties(
                alpha_id, alpha_name, [core.SC_HIGH_TAG], "分配最终标签"
            )
            frame.at[index, "SC_Status"] = core.SC_HIGH_TAG
            frame.at[index, "PC_Status"] = "SKIPPED_BY_SC_HIGH"
            frame.at[index, "Processing_Status"] = core.SC_HIGH_TAG if updated else "PENDING_PLATFORM_UPDATE"
            frame.at[index, "Platform_Update_Status"] = "SYNCED" if updated else "PENDING_PLATFORM_UPDATE"
            frame.at[index, "V6_Status"] = frame.at[index, "Processing_Status"]
            if updated:
                frame.at[index, "Platform_Name"] = alpha_name
                frame.at[index, "Platform_Tags"] = core.SC_HIGH_TAG
            _save_label_checkpoint(frame, index, item, variants, state_path, complete=updated)
            _progress(f"SC 高：{alpha_id} -> {frame.at[index, 'Processing_Status']}")
            continue
        frame.at[index, "SC_Status"] = "PASS"
        pc_payload = await asyncio.to_thread(core.get_correlation_payload_core, alpha_id, "production")
        max_pc, min_pc = core.production_correlation_values(pc_payload)
        frame.at[index, "prod_correlation_max"] = max_pc
        frame.at[index, "prod_correlation_min"] = min_pc
        pc_value = core.pc_alias_value(max_pc, min_pc)
        if core.is_high_pc(max_pc, min_pc):
            alpha_name = core.normal_alias(sc, pc_value)
            updated = await set_expanded_alpha_properties(
                alpha_id, alpha_name, [core.PC_HIGH_TAG], "分配最终标签"
            )
            frame.at[index, "PC_Status"] = core.PC_HIGH_TAG
            frame.at[index, "Processing_Status"] = core.PC_HIGH_TAG if updated else "PENDING_PLATFORM_UPDATE"
            frame.at[index, "Platform_Update_Status"] = "SYNCED" if updated else "PENDING_PLATFORM_UPDATE"
            frame.at[index, "V6_Status"] = frame.at[index, "Processing_Status"]
            if updated:
                frame.at[index, "Platform_Name"] = alpha_name
                frame.at[index, "Platform_Tags"] = core.PC_HIGH_TAG
            _save_label_checkpoint(frame, index, item, variants, state_path, complete=updated)
            _progress(f"PC 高：{alpha_id} -> {frame.at[index, 'Processing_Status']}")
        elif core.is_complete_low_pc(max_pc, min_pc):
            alpha_name = core.normal_alias(sc, pc_value)
            updated = await set_expanded_alpha_properties(
                alpha_id, alpha_name, [core.USEFUL_TAG], "分配最终标签"
            )
            frame.at[index, "PC_Status"] = "PASS" if max_pc is not None and min_pc is not None else "PENDING_PC"
            frame.at[index, "Processing_Status"] = "COMPLETE" if updated else "PENDING_PLATFORM_UPDATE"
            frame.at[index, "Platform_Update_Status"] = "SYNCED" if updated else "PENDING_PLATFORM_UPDATE"
            frame.at[index, "V6_Status"] = "USEFUL" if updated else "PENDING_PLATFORM_UPDATE"
            if updated:
                frame.at[index, "Platform_Name"] = alpha_name
                frame.at[index, "Platform_Tags"] = core.USEFUL_TAG
            _save_label_checkpoint(frame, index, item, variants, state_path, complete=updated)
            _progress(f"{core.USEFUL_TAG}：{alpha_id} -> {frame.at[index, 'Processing_Status']}")
        else:
            frame.at[index, "PC_Status"] = "PENDING_PC_RESULT"
            frame.at[index, "Processing_Status"] = "PENDING_PC"
            frame.at[index, "V6_Status"] = "PENDING_PC"
            _save_label_checkpoint(frame, index, item, variants, state_path)
            _progress(f"PC 结果待定：{alpha_id}")
    _progress("SC/PC 与标签阶段结束")
    return frame


def run_job(
    dry_run=False,
    skip_simulation=False,
    skip_sc_pc=False,
    output_prefix=V6_OUTPUT_PREFIX,
    state_prefix=V6_STATE_PREFIX,
    log_prefix="filter_ra_alphas_v6",
):
    base_dir = Path(__file__).resolve().parent
    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)
    run_time = pd.Timestamp.now()
    suffix = "_dry_run" if dry_run else ""
    v5_output = find_latest_v5_output(output_dir)
    source_date = v5_output.stem.removeprefix("filtered_RAs_") if v5_output else f"{run_time:%Y%m%d}"
    v6_output = output_dir / f"{output_prefix}{suffix}_{source_date}.xlsx"
    state_path = output_dir / f"{state_prefix}{suffix}_{source_date}.json"
    core.configure_run_logging(output_dir / f"{log_prefix}{suffix}_{source_date}.log")
    if v5_output is None:
        _progress("阶段终止：output/ 中找不到 dated V5 Excel")
        return
    source_frame = pd.read_excel(v5_output, engine="openpyxl")
    if source_frame.empty:
        _progress(f"输入文件 {v5_output.name} 无候选，V6 安全结束；不创建回测或改属性")
        return
    required_columns = {"Platform_Tags", "Expression", "Region", "Margin"}
    if not required_columns.issubset(source_frame.columns):
        _progress(f"输入文件结构=PENDING：缺少 {sorted(required_columns - set(source_frame.columns))}；保留原文件")
        return
    useful = select_top_useful(source_frame, V6_TOP_USEFUL_COUNT)
    useful_count = int(source_frame["Platform_Tags"].map(_is_useful).sum())
    _progress(f"输入文件：{v5_output.name}，总行数={len(source_frame)}，Useful={useful_count}，Margin合格后取={len(useful)}")
    source_ids = useful.get("alpha_id_raw", useful.get("alpha_id", pd.Series(dtype=str)))
    _progress(f"选中源因子：{', '.join(source_ids.astype(str).tolist())}")
    if useful.empty:
        _progress("没有符合 Margin 门槛的 Useful 源因子，阶段结束")
        return
    if skip_simulation:
        try:
            previous = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError):
            previous = None
        variants = (previous or {}).get("variants", [])
        if (
            not isinstance(previous, dict)
            or previous.get("variant_plan_version") != V6_VARIANT_PLAN_VERSION
            or previous.get("source_file") != v5_output.name
            or not variants
            or _source_signature(useful_frame=useful) != _source_signature(variants=variants)
        ):
            _progress("跳过回测失败：V6 断点与当前 V5 源因子/表达式不匹配")
            return
        observed = [item for item in variants if item.get("alpha_id")]
        _progress(
            f"跳过剩余回测：断点共 {len(variants)} 个组合，"
            f"只处理已观测 {len(observed)} 个 Alpha；未观测组合保留待处理"
        )
        frame = _variant_frame(observed)
        if skip_sc_pc:
            core.save_snapshot(frame, v6_output)
            _progress(f"跳过 SC/PC 与平台标签更新：保存已观测回测结果 {len(frame)} 行")
            return
        frame = asyncio.run(label_variants(frame, variants, state_path))
        core.save_snapshot(frame, v6_output)
        _progress(f"V6 最终阶段完成：处理行数={len(frame)}，文件={v6_output.name}")
        return
    try:
        options = asyncio.run(fetch_platform_options())
    except Exception as exc:
        _progress(f"平台设置读取失败，流程=PENDING：{exc}")
        return
    variants = build_variants(useful, options, setting_seed=v5_output.name)
    groups = group_variants(variants)
    region_summary = Counter((item["region"], item["delay"]) for item in variants)
    _progress(
        f"组合计划：{len(variants)} 个组合，{len(groups)} 个设置组；"
        f"Region/Delay={dict(region_summary)}"
    )
    for region_delay in sorted(region_summary):
        region, delay = region_delay
        group_items = [item for item in variants if item["region"] == region and item["delay"] == delay]
        _progress(
            f"设置抽样 {region}/Delay{delay}："
            f"Universe={sorted({item['universe'] for item in group_items})}，"
            f"Neutralization={sorted({item['neutralization'] for item in group_items})}"
        )
    checkpoint = {
        "version": 6, "source_file": v5_output.name, "setting_seed": v5_output.name,
        "variant_plan_version": V6_VARIANT_PLAN_VERSION,
        "source_count": len(useful), "variants": variants,
        "completed_batches": [], "results": [],
    }
    try:
        previous = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        if state_path.exists():
            _progress("V6=PENDING_STATE_UNREADABLE；保留已有断点，不创建回测")
            return
        previous = None
    if previous is not None and not isinstance(previous, dict):
        _progress("V6=PENDING_STATE_STRUCTURE；保留已有断点，不创建回测")
        return
    previous_variants = {
        _variant_identity(item): item
        for item in (previous or {}).get("variants", [])
        if isinstance(item, dict)
    }
    current_keys = {_variant_identity(item) for item in variants}
    if (
        isinstance(previous, dict)
        and previous.get("variant_plan_version") == V6_VARIANT_PLAN_VERSION
        and previous.get("source_file") == v5_output.name
        and set(previous_variants) == current_keys
    ):
        for item in variants:
            old = previous_variants[_variant_identity(item)]
            for field in (
                "alpha_id", "sharpe", "fitness", "margin", "turnover", "status",
                "properties_cleared", "label_complete", "basic_status",
                "platform_name", "platform_tags", "platform_update_status",
                "self_correlation", "prod_correlation_max", "prod_correlation_min",
                "sc_status", "pc_status", "processing_status", "v6_status",
            ):
                if field in old:
                    item[field] = old[field]
        checkpoint["completed_batches"] = previous.get("completed_batches", [])
        checkpoint["results"] = previous.get("results", [])
        for field in ("chunk_batches", "last_pending_settings", "last_pending_reason"):
            if field in previous:
                checkpoint[field] = previous[field]
        _progress(
            f"恢复同一输入文件的 V6 断点：已完成设置组={len(checkpoint['completed_batches'])}，"
            f"已有 Alpha ID={len(checkpoint['results'])}"
        )
    else:
        if previous is not None:
            _progress("V6=PENDING_STATE_INCOMPATIBLE；保留已有断点，不创建回测")
            return
        _progress("没有已有断点，建立当前输入的 V6 状态")
    core._atomic_write_json(state_path, checkpoint)
    variants = asyncio.run(simulate_variants(variants, state_path, dry_run=dry_run))
    if dry_run:
        frame = _dry_run_frame(variants)
    else:
        frame = _variant_frame(variants)
        frame = asyncio.run(label_variants(frame, variants, state_path))
    core.save_snapshot(frame, v6_output)
    _progress(f"V6{'预演' if dry_run else ''} 完成：源因子={len(useful)}，输出行数={len(frame)}，文件={v6_output.name}")


def run_from_file_settings():
    run_job(
        dry_run=V6_DRY_RUN,
        skip_simulation=V6_SKIP_SIMULATION,
        skip_sc_pc=V6_SKIP_SC_PC,
    )


if __name__ == "__main__":
    run_from_file_settings()
