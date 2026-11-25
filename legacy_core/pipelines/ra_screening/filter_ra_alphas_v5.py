"""V5 RA screening operation.

Pipeline order lives here. Shared category/alias/snapshot behavior is in
``filter_ra_alphas_core`` so future operation variants can reuse it.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from urllib.parse import quote

import pandas as pd

print("[V5] 正在加载核心模块...", flush=True)
import filter_ra_alphas_core as core


V5_OUTPUT_PREFIX = "filtered_RAs"


def _server_useful_alphas(session):
    """读取平台全部 IS Useful，独立于 V5 的日期和基础指标窗口。"""
    alphas = []
    offset = 0
    while True:
        url = (
            "https://api.worldquantbrain.com/users/self/alphas"
            f"?limit=100&offset={offset}&stage=IS&tag={quote(core.USEFUL_TAG)}"
            "&order=-dateCreated"
        )
        response = core.get_alpha_page_with_retry(
            session, url, f"UsefulAudit offset={offset}"
        )
        if response is None:
            core.progress(
                f"[V5][UsefulAudit] offset={offset} 获取失败；本次只处理已获取的 {len(alphas)} 条"
            )
            break
        try:
            payload = response.json()
            page = payload.get("results", [])
            total = int(payload.get("count", len(alphas) + len(page)))
            if not isinstance(page, list):
                raise TypeError("results 不是列表")
        except (TypeError, ValueError, AttributeError) as exc:
            core.progress(f"[V5][UsefulAudit] offset={offset} 响应异常：{exc}")
            break
        alphas.extend(page)
        core.progress(
            f"[V5][UsefulAudit] 平台分页 offset={offset}：返回 {len(page)} 条，"
            f"累计 {len(alphas)}/{total}"
        )
        if not page or len(alphas) >= total or len(page) < 100:
            break
        offset += len(page)
    return alphas


def _basic_exclusion_reasons(alpha):
    """返回平台 Useful 中能够直接确认的 V5 基础排除原因。"""
    stats = alpha.get("is") or {}
    reasons = []
    for field, operator, threshold in (
        ("sharpe", ">=", 1.6),
        ("fitness", ">=", 1.0),
        ("margin", ">", 0.0005),
    ):
        value = stats.get(field)
        try:
            failed = float(value) < threshold if operator == ">=" else float(value) <= threshold
        except (TypeError, ValueError):
            failed = False
        if failed:
            reasons.append(f"{field.upper()}={value} 不满足 {operator}{threshold}")
    checks = stats.get("checks") or []
    fail_count = sum(
        str(check.get("result", "")).strip().upper() == "FAIL"
        for check in checks
    )
    if fail_count:
        reasons.append(f"FAIL_COUNT={fail_count}")
    warning_codes = [match["code"] for match in core.find_warning_exclusions(alpha)]
    if warning_codes:
        reasons.append(f"WARNING={','.join(warning_codes)}")
    return reasons


def audit_server_useful(session):
    """修复全平台 Useful 中 name 高值或基础排除项，并打印完整对账日志。"""
    alphas = _server_useful_alphas(session)
    lower_bound = pd.Timestamp(core.beijing_date_window_utc()[0])
    repaired_high = removed_excluded = retained = update_failed = outside_window = 0
    core.progress(
        f"[V5][UsefulAudit] 开始逐条核对：服务器 {core.USEFUL_TAG}={len(alphas)}，"
        f"V5 主流程窗口={core.CONFIG_DAYS_AGO} 天"
    )

    for number, alpha in enumerate(alphas, start=1):
        alpha_id = str(alpha.get("id") or "").strip()
        name = str(alpha.get("name") or "")
        tags = core.tag_names(alpha.get("tags"))
        sc = core.parse_alias_value(name, "SC")
        pc = core.parse_alias_value(name, "PC")
        existing = {tag.casefold() for tag in tags}
        high_tags = [
            tag for tag in (core.SC_HIGH_TAG, core.PC_HIGH_TAG)
            if tag.casefold() in existing
        ]
        if core.is_high_correlation(sc):
            high_tags.append(core.SC_HIGH_TAG)
        if core.is_high_correlation(pc):
            high_tags.append(core.PC_HIGH_TAG)
        high_tags = list(dict.fromkeys(high_tags))
        reasons = _basic_exclusion_reasons(alpha)
        created = pd.to_datetime(alpha.get("dateCreated"), utc=True, errors="coerce")
        in_window = pd.isna(created) or created >= lower_bound
        if not in_window:
            outside_window += 1
        stats = alpha.get("is") or {}
        prefix = (
            f"[V5][UsefulAudit] {number}/{len(alphas)} {alpha_id}："
            f"name={name!r}，tags={','.join(tags)}，created={alpha.get('dateCreated')}，"
            f"窗口内={'YES' if in_window else 'NO'}，"
            f"Sharpe={stats.get('sharpe')}，Fitness={stats.get('fitness')}，"
            f"Margin={stats.get('margin')}"
        )

        if high_tags:
            removed_tags = {core.USEFUL_TAG.casefold(), core.SUBMIT_TAG.casefold()}
            target_tags = [
                tag for tag in tags
                if tag.casefold() not in removed_tags
                and tag.casefold() not in {value.casefold() for value in high_tags}
            ] + high_tags
            alias = name
            if sc is not None:
                alias = core.partial_alias(alias, "SC", sc)
            if pc is not None:
                alias = core.partial_alias(alias, "PC", pc)
            core.progress(
                f"{prefix}，终态tag/name高值={','.join(high_tags)}，动作=替换 Useful，"
                f"目标name={alias!r}，目标tags={','.join(target_tags)}"
            )
            if core.set_alpha_properties(session, alpha_id, name=alias, tags=target_tags):
                repaired_high += 1
            else:
                update_failed += 1
                core.progress(
                    f"[V5][UsefulAudit] {alpha_id} 高值替换失败："
                    f"status={core.platform_update_status()}，下次运行重试"
                )
            continue

        if reasons:
            removed_tags = {core.USEFUL_TAG.casefold(), core.SUBMIT_TAG.casefold()}
            target_tags = [
                tag for tag in tags if tag.casefold() not in removed_tags
            ]
            core.progress(
                f"{prefix}，基础排除={'; '.join(reasons)}，动作=移除 Useful，"
                f"目标tags={','.join(target_tags) or '(空)'}"
            )
            if core.set_alpha_properties(session, alpha_id, tags=target_tags):
                removed_excluded += 1
            else:
                update_failed += 1
                core.progress(
                    f"[V5][UsefulAudit] {alpha_id} 排除清理失败："
                    f"status={core.platform_update_status()}，下次运行重试"
                )
            continue

        retained += 1
        pc_evidence = (
            "name无PC值"
            if pc is None
            else f"name中PC={pc}<=0.7，但不能证明远程PC max/min均通过"
        )
        core.progress(f"{prefix}，{pc_evidence}，动作=暂时保留 Useful，交给原 SC→PC 流程")

    current = _server_useful_alphas(session)
    core.progress(
        f"[V5][UsefulAudit] 完成：运行前={len(alphas)}，运行后服务器={len(current)}，"
        f"name高值替换={repaired_high}，基础排除移除={removed_excluded}，"
        f"暂时保留={retained}，平台更新失败={update_failed}，"
        f"窗口外={outside_window}"
    )
    return current


def _sync_pyramid_audit_to_output(output_path, records):
    """把全量审计中与当天主表重合的结果写回主表。"""
    if not output_path.is_file() or not records:
        return
    try:
        df = pd.read_excel(output_path, engine="openpyxl").astype(object)
    except Exception as exc:
        logging.warning("Pyramid 审计写回主表失败：%s", exc)
        return
    if "alpha_id" not in df.columns:
        return
    by_id = {str(row["alpha_id"]): row for row in records}
    for column in (
        "Matched_Categories", "Category_Status", "Category_Evidence",
        "Pyramid_Status", "Unlit_Pyramid_Scopes",
    ):
        if column not in df.columns:
            df[column] = ""
    for index in df.index:
        raw = df.at[index, "alpha_id_raw"] if "alpha_id_raw" in df.columns else df.at[index, "alpha_id"]
        record = by_id.get(str(core.raw_alpha_id(raw)))
        if not record:
            continue
        df.at[index, "Matched_Categories"] = record["Matched_Categories"]
        df.at[index, "Category_Status"] = record["Pyramid_Status"]
        df.at[index, "Category_Evidence"] = record["Pyramid_Evidence"]
        df.at[index, "Pyramid_Status"] = record["Pyramid_Status"]
        df.at[index, "Unlit_Pyramid_Scopes"] = record["Unlit_Pyramid_Scopes"]
    core.save_snapshot(df, output_path)


def audit_server_useful_pyramids(session, audit_path, output_path=None):
    """按实时 Pyramid 状态同步服务器全部 Useful 的 Submit 标签。"""
    diversity = core.get_user_diversity(session)
    alphas = _server_useful_alphas(session)
    records = []
    counts = {"HAS_GAP": 0, "ALL_PASS": 0, "PENDING": 0, "UPDATED": 0}
    core.progress(f"[V5][Pyramid] 开始全量审计：Useful={len(alphas)}")
    for number, alpha in enumerate(alphas, start=1):
        alpha_id = str(alpha.get("id") or "").strip()
        original_tags = core.tag_names(alpha.get("tags"))
        info = core.get_alpha_pyramid_pass_info(session, alpha_id)
        coverage = core.evaluate_pyramid_coverage(diversity, info)
        status = coverage["status"]
        counts[status] += 1
        target_tags = list(original_tags)
        update_status = "UNCHANGED"
        if status != "PENDING":
            target_tags = [tag for tag in original_tags if tag.casefold() != core.SUBMIT_TAG.casefold()]
            if status == "HAS_GAP":
                target_tags.append(core.SUBMIT_TAG)
            target_tags = list(dict.fromkeys(target_tags))
            original_set = {tag.casefold() for tag in original_tags}
            target_set = {tag.casefold() for tag in target_tags}
            if target_set != original_set:
                if core.set_alpha_properties(session, alpha_id, tags=target_tags):
                    update_status = "SYNCED"
                    counts["UPDATED"] += 1
                else:
                    update_status = (
                        "PENDING_PLATFORM_RATE_LIMIT"
                        if core.platform_update_status() in {"RATE_LIMITED", "SKIPPED_RATE_LIMIT"}
                        else "PENDING_PLATFORM_UPDATE"
                    )
        else:
            update_status = "PENDING_PYRAMID"

        categories = info.get("categories") or []
        gaps = coverage.get("gap_scopes") or []
        evidence = json.dumps(coverage.get("scopes") or [], ensure_ascii=False)
        records.append({
            "alpha_id": alpha_id,
            "Matched_Categories": ", ".join(categories),
            "Pyramid_Status": status,
            "Unlit_Pyramid_Scopes": ", ".join(str(item.get("raw_scope")) for item in gaps),
            "Pyramid_Evidence": evidence,
            "Original_Tags": ", ".join(original_tags),
            "Target_Tags": ", ".join(target_tags),
            "Platform_Update_Status": update_status,
            "Reason": coverage.get("reason"),
        })
        core.progress(
            f"[V5][Pyramid] {number}/{len(alphas)} {alpha_id}：status={status}，"
            f"categories={categories}，gaps={[item.get('raw_scope') for item in gaps]}，"
            f"update={update_status}"
        )

    columns = [
        "alpha_id", "Matched_Categories", "Pyramid_Status", "Unlit_Pyramid_Scopes",
        "Pyramid_Evidence", "Original_Tags", "Target_Tags", "Platform_Update_Status", "Reason",
    ]
    core.save_snapshot(pd.DataFrame(records, columns=columns), audit_path)
    if output_path is not None:
        _sync_pyramid_audit_to_output(output_path, records)
    core.progress(
        f"[V5][Pyramid] 完成：HAS_GAP={counts['HAS_GAP']}，ALL_PASS={counts['ALL_PASS']}，"
        f"PENDING={counts['PENDING']}，标签更新={counts['UPDATED']}，输出={audit_path.name}"
    )
    return records


def _high_correlation_state(df, index):
    """从已知 SC/PC 数值生成需要同步的终态标签和完整别名。"""
    sc = df.at[index, "self_correlation"]
    pc_max = df.at[index, "prod_correlation_max"]
    pc_min = df.at[index, "prod_correlation_min"]
    tags = []
    alias = df.at[index, "Platform_Name"]
    if core.is_high_correlation(sc):
        tags.append(core.SC_HIGH_TAG)
        alias = core.partial_alias(alias, "SC", sc)
    if core.is_high_pc(pc_max, pc_min):
        tags.append(core.PC_HIGH_TAG)
        alias = core.partial_alias(alias, "PC", core.pc_alias_value(pc_max, pc_min))
    return tags, alias


def _sync_high_correlation_state(session, df, index, fallback_tag=None):
    tags, alias = _high_correlation_state(df, index)
    fallback_tags = (
        [fallback_tag] if isinstance(fallback_tag, str) else list(fallback_tag or [])
    )
    tags = list(dict.fromkeys([*tags, *fallback_tags]))
    existing = {tag.casefold() for tag in core.tag_names(df.at[index, "_tags"])}
    missing_tags = any(tag.casefold() not in existing for tag in tags)
    useful_present = core.USEFUL_TAG.casefold() in existing
    alias_changed = bool(alias) and str(alias) != str(df.at[index, "Platform_Name"] or "")
    if tags and (missing_tags or useful_present or alias_changed):
        core.mark_platform(session, df, index, tags, alias)


def _set_terminal_status(df, index, high_tags):
    sc_high = core.SC_HIGH_TAG in high_tags
    pc_high = core.PC_HIGH_TAG in high_tags
    df.at[index, "SC_Status"] = core.SC_HIGH_TAG if sc_high else "SKIPPED_BY_PC_HIGH"
    df.at[index, "PC_Status"] = core.PC_HIGH_TAG if pc_high else "SKIPPED_BY_SC_HIGH"
    df.at[index, "Processing_Status"] = f"{high_tags[0]}_SKIPPED"


def _prefilter_terminal_states(session, df):
    """严格按 tag -> name 高值处理，只把非终态行交给 SC。"""
    tagged_indices = set()
    tag_count = name_count = 0
    core.progress(f"[V5][预过滤] 开始：先检查 {len(df)} 条的终态 tag，再检查 name 高值")

    # 第一遍只按现有终态 tag 过滤；同时补齐同一 name 中可确认的另一高值标签。
    for index in df.index:
        existing = {tag.casefold() for tag in core.tag_names(df.at[index, "_tags"])}
        terminal_tags = [
            tag for tag in (core.SC_HIGH_TAG, core.PC_HIGH_TAG)
            if tag.casefold() in existing
        ]
        if not terminal_tags:
            continue
        name_high_tags, _ = _high_correlation_state(df, index)
        high_tags = list(dict.fromkeys([*terminal_tags, *name_high_tags]))
        _sync_high_correlation_state(session, df, index, fallback_tag=high_tags)
        _set_terminal_status(df, index, high_tags)
        tagged_indices.add(index)
        tag_count += 1
        core.progress(
            f"[V5][预过滤][tag] {df.at[index, 'alpha_id']}："
            f"name={df.at[index, 'Platform_Name']!r}，"
            f"终态={','.join(high_tags)}，动作=跳过 SC/PC"
        )

    # 第二遍只检查未被 tag 过滤的行；name/已知缓存高值会补终态标签。
    remaining = []
    for index in df.index:
        if index in tagged_indices:
            continue
        high_tags, _ = _high_correlation_state(df, index)
        if not high_tags:
            remaining.append(index)
            continue
        _sync_high_correlation_state(session, df, index)
        _set_terminal_status(df, index, high_tags)
        name_count += 1
        core.progress(
            f"[V5][预过滤][name] {df.at[index, 'alpha_id']}："
            f"name={df.at[index, 'Platform_Name']!r}，检测终态={','.join(high_tags)}，"
            "动作=补齐高相关 tag、移除 Useful 并跳过 SC/PC"
        )

    core.progress(
        f"[V5][预过滤] 完成：tag 终态 {tag_count} 条，name 高值补漏 {name_count} 条，"
        f"进入 SC {len(remaining)} 条"
    )
    return remaining


def _apply_pc_state(session, df, index, alpha_by_id):
    """Apply the same PC decision to fresh and cached PC results."""
    alpha_id = df.at[index, "alpha_id"]
    max_pc = df.at[index, "prod_correlation_max"]
    min_pc = df.at[index, "prod_correlation_min"]
    sc = df.at[index, "self_correlation"]
    if core.is_high_pc(max_pc, min_pc):
        pc_alias = core.partial_alias(
            core.partial_alias(df.at[index, "Platform_Name"], "SC", sc),
            "PC",
            core.pc_alias_value(max_pc, min_pc),
        )
        core.mark_platform(session, df, index, core.PC_HIGH_TAG, pc_alias)
        df.at[index, "PC_Status"] = core.PC_HIGH_TAG
        df.at[index, "Processing_Status"] = core.PC_HIGH_TAG
        return False

    if core.is_correlation_pass(sc) and core.is_complete_low_pc(max_pc, min_pc):
        core.apply_low_correlation_categories(session, df, index, alpha_by_id[alpha_id])
        return True

    alias = core.partial_alias(
        core.partial_alias(df.at[index, "Platform_Name"], "SC", sc),
        "PC",
        core.pc_alias_value(max_pc, min_pc),
    )
    updated = core.set_alpha_properties(session, alpha_id, name=alias)
    df.at[index, "PC_Status"] = "PASS"
    df.at[index, "Processing_Status"] = "COMPLETE" if updated else "PENDING_ALIAS_UPDATE"
    df.at[index, "Platform_Update_Status"] = (
        "SYNCED_ALIAS_ONLY"
        if updated
        else (
            "PENDING_PLATFORM_RATE_LIMIT"
            if core.platform_update_status() in {"RATE_LIMITED", "SKIPPED_RATE_LIMIT"}
            else "PENDING_PLATFORM_UPDATE"
        )
    )
    if updated:
        df.at[index, "Platform_Name"] = alias
    return False


def _invalidate_sc_cache_after_base_change(df, indices):
    """Refresh SC after its comparison base changes without discarding known PC."""
    preserved_high_pc = 0
    for index in indices:
        df.at[index, "_sc_cached"] = False
        pc_high = df.at[index, "_pc_cached"] and core.is_high_pc(
            df.at[index, "prod_correlation_max"],
            df.at[index, "prod_correlation_min"],
        )
        tags = [
            tag for tag in core.tag_names(df.at[index, "_tags"])
            if tag.casefold() != core.SC_HIGH_TAG.casefold()
            and not (pc_high and tag.casefold() == core.USEFUL_TAG.casefold())
        ]
        df.at[index, "_tags"] = tags
        df.at[index, "Platform_Tags"] = ", ".join(tags)
        if pc_high:
            preserved_high_pc += 1
    core.progress(
        f"[V5] SC 基础数据有新增：仅刷新 SC；保留已有 PC，"
        f"其中 PC>0.7 终态 {preserved_high_pc} 条不重复查询"
    )


def restore_existing_output_usefuls(session, output_path):
    """从当天 Excel 恢复 SC/PC 已通过行的 Useful；Pyramid 在最终阶段查询。"""
    if not output_path.is_file():
        return 0
    try:
        df = pd.read_excel(output_path, engine="openpyxl")
    except Exception as exc:
        logging.warning("读取 Useful 补偿输入失败：%s", exc)
        return 0
    required = {"alpha_id", "Expression", "Region", "Universe", "Delay",
                "self_correlation", "prod_correlation_max", "prod_correlation_min",
                "SC_Status", "PC_Status"}
    if not required.issubset(df.columns):
        return 0

    candidate_mask = (
        df["SC_Status"].astype(str).eq("PASS")
        & df["PC_Status"].astype(str).eq("PASS")
        & df["self_correlation"].map(core.is_correlation_pass)
        & df["prod_correlation_max"].map(core.is_correlation_pass)
        & df["prod_correlation_min"].map(core.is_correlation_pass)
    )
    # Excel 全为空的 ID/状态列可能被 pandas 推断为 float64；补偿流程会写回字符串。
    # 统一使用 object，避免给 float64 列写入 Alpha ID 或平台状态时触发 LossySetitemError。
    df = df.astype(object)
    if not candidate_mask.any():
        core.progress("[V5][Useful] 没有需要补偿的 SC/PC 通过因子")
        return 0

    for column, default in {
        "Matched_Categories": "",
        "Category_Status": "NOT_ELIGIBLE",
        "Category_Evidence": "",
        "Platform_Tags": "",
        "Platform_Name": "",
        "Platform_Update_Status": "NOT_ATTEMPTED",
        "Processing_Status": "",
    }.items():
        if column not in df.columns:
            df[column] = default
    df["_tags"] = df["Platform_Tags"].map(
        lambda value: [tag.strip() for tag in str(value).split(",") if tag.strip()]
    )

    processed = 0
    core.progress(f"[V5][Useful] 开始断点补偿：{int(candidate_mask.sum())} 个因子")
    for index in df.index[candidate_mask]:
        raw_column_id = df.at[index, "alpha_id_raw"] if "alpha_id_raw" in df.columns else None
        source_id = raw_column_id if pd.notna(raw_column_id) else df.at[index, "alpha_id"]
        alpha_id = core.raw_alpha_id(source_id)
        if pd.isna(alpha_id) or not str(alpha_id).strip() or str(alpha_id).lower() == "nan":
            df.at[index, "Platform_Update_Status"] = "PENDING_MISSING_ALPHA_ID"
            core.progress(
                f"[V5][Useful] 跳过无效 Alpha ID：行={index}，"
                f"alpha_id={df.at[index, 'alpha_id']!r}，"
                f"alpha_id_raw={raw_column_id!r}，"
                f"Expression={df.at[index, 'Expression']!r}，"
                f"SC={df.at[index, 'self_correlation']!r}，"
                f"PC={df.at[index, 'prod_correlation_max']!r}"
            )
            continue
        alpha = {
            "regular": {"code": df.at[index, "Expression"]},
            "settings": {
                "region": df.at[index, "Region"],
                "universe": df.at[index, "Universe"],
                "delay": df.at[index, "Delay"],
            },
        }
        df.at[index, "alpha_id"] = alpha_id
        if core.apply_low_correlation_categories(session, df, index, alpha):
            processed += 1
        core.progress(f"[V5][Useful] {alpha_id} 完成 ({processed}/{int(candidate_mask.sum())})")

    core.save_snapshot(df, output_path)
    logging.info("V5 Excel Useful 补偿：候选 %s，成功更新 %s", int(candidate_mask.sum()), processed)
    return processed


def remove_excluded_rows_from_output(output_path, alpha_ids):
    """从当天断点 Excel 中移除命中 Warning 排除规则的 Alpha。"""
    if not output_path.is_file():
        return 0
    try:
        old_df = pd.read_excel(output_path, engine="openpyxl")
    except Exception as exc:
        logging.warning("移除 Warning 排除因子时读取 Excel 失败：%s", exc)
        return 0
    excluded = {str(alpha_id).strip() for alpha_id in alpha_ids}

    def row_alpha_id(row):
        source = row.get("alpha_id_raw") if "alpha_id_raw" in old_df.columns else None
        if pd.isna(source):
            source = row.get("alpha_id")
        value = core.raw_alpha_id(source)
        if pd.isna(value):
            return ""
        return str(value).strip()

    row_ids = (
        old_df.apply(row_alpha_id, axis=1)
        if "alpha_id" in old_df.columns
        else pd.Series("", index=old_df.index)
    )
    legacy_warning_mask = pd.Series(False, index=old_df.index)
    for column, values in {
        "Processing_Status": {"EXCLUDED_WARNING"},
        "SC_Status": {"SKIPPED_WARNING"},
        "PC_Status": {"SKIPPED_WARNING"},
    }.items():
        if column in old_df.columns:
            legacy_warning_mask |= old_df[column].astype(str).isin(values)

    remove_mask = row_ids.isin(excluded) | legacy_warning_mask
    keep_mask = ~remove_mask
    removed = int((~keep_mask).sum())
    legacy_columns = [
        column for column in ("Warning_Exclusion_Rules", "Warning_Exclusion_Evidence")
        if column in old_df.columns
    ]
    cleaned_df = old_df.loc[keep_mask].drop(columns=legacy_columns, errors="ignore")
    if removed or legacy_columns:
        core.save_snapshot(cleaned_df, output_path)
    if removed:
        core.progress(f"[V5][Warning] 已从现有 Excel 移除 {removed} 个排除因子")
    return removed


def remove_excluded_usefuls(session, excluded_by_filter, live_useful_by_id):
    """只按阶段0.5实时 Useful 结果清理，禁止使用断点里的旧 tags PATCH。"""
    checked = set()
    for cached_alpha, reason in excluded_by_filter:
        alpha_id = str(cached_alpha.get("id") or "").strip()
        if not alpha_id or alpha_id in checked:
            continue
        checked.add(alpha_id)
        live_alpha = live_useful_by_id.get(alpha_id)
        if live_alpha is None:
            core.progress(
                f"[V5][ExcludedTag] {alpha_id}：原因={reason}，"
                "当前服务器 Useful=NO；忽略断点缓存中的旧 tags，不执行 PATCH"
            )
            continue
        if core.remove_useful_tag_if_present(session, live_alpha, reason):
            live_useful_by_id.pop(alpha_id, None)


def run_job():
    base_dir = Path(__file__).resolve().parent
    cache_dir = base_dir / "cache"
    output_dir = base_dir / "output"
    cache_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    run_time = pd.Timestamp.now()
    output_path = output_dir / f"{V5_OUTPUT_PREFIX}_{run_time:%Y%m%d}.xlsx"
    pyramid_audit_path = output_dir / f"useful_pyramid_audit_{run_time:%Y%m%d}.xlsx"
    log_path = output_dir / f"filter_ra_alphas_v5_{run_time:%Y%m%d}.log"
    core.configure_run_logging(log_path)
    core.progress(f"[V5] 日志文件：{log_path.name}")
    core.progress("[V5] 阶段0：开始登录")
    session = core.get_session()
    if not session:
        core.progress("[V5] 阶段0：登录失败，结束")
        return
    core.progress("[V5] 阶段0：登录成功")
    history_path = output_path
    core.progress(f"[V5] 本次输出：{output_path.name}")
    core.progress(f"[V5] 断点输入：{history_path.name}")

    core.progress(f"[V5] 阶段0.5：核对服务器全部 Useful，不受 {core.CONFIG_DAYS_AGO} 天窗口限制")
    live_useful = audit_server_useful(session)
    live_useful_by_id = {
        str(alpha.get("id")): alpha for alpha in live_useful if alpha.get("id")
    }

    core.progress("[V5] 阶段1：获取 Alpha 列表")
    core.progress(
        f"[V5] 阶段1范围：最近 {core.CONFIG_DAYS_AGO} 天、UNSUBMITTED、hidden=false、"
        "Sharpe>=1.6、Fitness>=1.0、Margin>0.0005"
    )
    fetched, fetch_failures = core.fetch_recent_alphas(
        session,
        checkpoint_path=cache_dir / "alpha_fetch_state.json",
    )
    core.progress(f"[V5] 阶段1完成：获取 {len(fetched)} 条，失败切片 {len(fetch_failures)} 个")
    core.progress("[V5] 阶段2：按 FAIL 数量 < 1 过滤")
    candidates = []
    excluded_by_filter = []
    for alpha in fetched:
        checks = alpha.get("is", {}).get("checks", []) or []
        # V5 不再执行阶段 2 的 RA/PPA 分类；只保留 FAIL 数量 < 1 的 Alpha。
        fail_count = sum(str(check.get("result", "")).strip().upper() == "FAIL" for check in checks)
        if fail_count < 1:
            candidates.append(alpha)
        else:
            excluded_by_filter.append((alpha, f"FAIL_COUNT={fail_count}"))
    core.progress(f"[V5] 阶段2完成：保留 {len(candidates)} 条，剔除 {len(excluded_by_filter)} 条")

    warning_exclusions_by_id = {}
    for alpha in candidates:
        matches = core.find_warning_exclusions(alpha)
        if matches:
            warning_exclusions_by_id[alpha.get("id")] = matches
            codes = ", ".join(str(match["code"]) for match in matches)
            evidence = json.dumps(matches, ensure_ascii=False)
            core.progress(
                f"[V5][Warning] 排除 {alpha.get('id')}：规则={codes}，证据={evidence}"
            )
            excluded_by_filter.append((alpha, f"WARNING={codes}"))
    warning_excluded_ids = set(warning_exclusions_by_id)
    core.progress(f"[V5] Warning 排除检查：命中 {len(warning_excluded_ids)} 个")
    excluded_ids = {str(alpha.get("id")) for alpha, _ in excluded_by_filter if alpha.get("id")}
    remove_excluded_usefuls(session, excluded_by_filter, live_useful_by_id)
    remove_excluded_rows_from_output(output_path, excluded_ids)
    candidates = [alpha for alpha in candidates if alpha.get("id") not in excluded_ids]
    alpha_by_id = {alpha.get("id"): alpha for alpha in candidates}
    core.progress(f"[V5] 全部排除处理后：剩余 {len(candidates)} 条")

    if not candidates:
        # 仅在本轮没有正常候选可处理时执行断点补偿；正常主流程会更新 Useful，
        # 提前补偿会让同一行产生两次平台 PATCH。
        core.progress("[V5][Useful] 本轮无正常候选，执行同日断点 Useful 补偿")
        restore_existing_output_usefuls(session, history_path)
        if fetch_failures:
            core.save_snapshot(pd.DataFrame([{
                "alpha_id": "FETCH_PENDING",
                "Processing_Status": "PENDING_ALPHA_FETCH",
                "Fetch_Status": "PENDING",
                "Fetch_Detail": "; ".join(fetch_failures),
            }]), output_path)
        core.progress("[V5] 最终阶段：同步服务器全部 Useful 的 Pyramid/Submit")
        audit_server_useful_pyramids(session, pyramid_audit_path, output_path)
        return

    core.progress("[V5][Useful] 正常主流程将处理 Useful，跳过断点补偿以避免重复平台更新")
    same_day_history = core.load_excel_history(history_path)
    df = core.build_dataframe(candidates, same_day_history)
    core.progress(f"[V5] 阶段3：终态预过滤后执行本地 SC，候选 {len(df)} 条")
    df["Fetch_Status"] = "PENDING_PARTIAL_FETCH" if fetch_failures else "COMPLETE"
    df["Fetch_Detail"] = "; ".join(fetch_failures) if fetch_failures else ""
    df["Matched_Categories"] = ""
    df["Category_Status"] = "NOT_ELIGIBLE"
    df["Category_Evidence"] = ""
    if "Platform_Update_Status" not in df.columns:
        df["Platform_Update_Status"] = "NOT_ATTEMPTED"

    # 先过滤平台终态标签，再按平台 name 中的高值补齐遗漏标签。
    sc_indices = _prefilter_terminal_states(session, df)
    sc_skipped_count = len(df) - len(sc_indices)
    sc_cache_count = sum(bool(df.at[index, "_sc_cached"]) for index in sc_indices)

    # SC 可能耗时较长，先落盘一份已完成 Warning/终态筛选的阶段性快照。
    core.save_snapshot(df, output_path)
    core.progress(f"[V5] 阶段3：SC 前快照已保存到 {output_path.name}")

    base_data_changed = False
    sc_result = None
    if sc_indices and core.sc_skill:
        core.progress(f"[V5] 阶段3：开始 SC，仅检查预过滤后的 {len(sc_indices)} 条")
        sc_input = df.loc[sc_indices, [
            "alpha_id", "Expression", "Region", "Universe", "Delay",
            "Sharpe", "Fitness", "Margin", "Date Created",
        ]].copy()
        known_sc_results = {
            df.at[index, "alpha_id"]: df.at[index, "self_correlation"]
            for index in sc_indices
            if pd.notna(df.at[index, "self_correlation"])
        }
        try:
            sc_result = core.calculate_self_correlation_for_alphas_optimized(
                session,
                cache_dir,
                sc_input,
                tag="SelfCorr",
                max_workers=core.CONFIG_SC_MAX_WORKERS,
                known_sc_results=known_sc_results,
            )
        except Exception as exc:
            logging.exception("SC 计算异常，保留为 PENDING：%s", exc)
            sc_result = None
        if sc_result is not None and "self_correlation" in sc_result.columns:
            base_data_changed = bool(sc_result.attrs.get("base_data_changed", False))
            correlation_by_id = dict(zip(sc_result["alpha_id"], sc_result["self_correlation"]))
            for index in sc_indices:
                df.at[index, "self_correlation"] = correlation_by_id.get(df.at[index, "alpha_id"])
            if base_data_changed:
                _invalidate_sc_cache_after_base_change(df, sc_indices)
        core.progress("[V5] 阶段3完成：SC 结果已写入内存")
    elif not sc_indices:
        core.progress("[V5] 阶段3跳过：全部候选已被终态 tag/name 预过滤")
    else:
        core.progress("[V5] 阶段3阻塞：SC 技能库不可用")

    pc_indices = []
    for index in sc_indices:
        sc_value = df.at[index, "self_correlation"]
        if pd.isna(sc_value):
            df.at[index, "SC_Status"] = "PENDING_SC_RESULT" if core.sc_skill else "PENDING_SC_LIBRARY"
            df.at[index, "PC_Status"] = "PENDING_SC"
            df.at[index, "Processing_Status"] = "PENDING_SC"
        elif core.is_high_correlation(sc_value):
            _sync_high_correlation_state(session, df, index, fallback_tag=core.SC_HIGH_TAG)
            df.at[index, "SC_Status"] = core.SC_HIGH_TAG
            df.at[index, "PC_Status"] = (
                core.PC_HIGH_TAG
                if core.is_high_pc(
                    df.at[index, "prod_correlation_max"],
                    df.at[index, "prod_correlation_min"],
                )
                else "SKIPPED_BY_SC_HIGH"
            )
            df.at[index, "Processing_Status"] = core.SC_HIGH_TAG
        else:
            df.at[index, "SC_Status"] = "PASS"
            if df.at[index, "_pc_cached"]:
                core.progress(
                    f"[V5][PC] {df.at[index, 'alpha_id']} 使用已有 PC="
                    f"{df.at[index, 'prod_correlation_max']}/{df.at[index, 'prod_correlation_min']}，"
                    "跳过远程查询并立即同步 tag/name"
                )
                _apply_pc_state(session, df, index, alpha_by_id)
            else:
                sc_alias = core.partial_alias(df.at[index, "Platform_Name"], "SC", sc_value)
                if str(sc_alias) != str(df.at[index, "Platform_Name"] or ""):
                    before_tags = ",".join(core.tag_names(df.at[index, "_tags"]))
                    updated = core.set_alpha_properties(
                        session, df.at[index, "alpha_id"], name=sc_alias
                    )
                    df.at[index, "Platform_Update_Status"] = (
                        "SYNCED_ALIAS_ONLY"
                        if updated
                        else (
                            "PENDING_PLATFORM_RATE_LIMIT"
                            if core.platform_update_status() in {"RATE_LIMITED", "SKIPPED_RATE_LIMIT"}
                            else "PENDING_PLATFORM_UPDATE"
                        )
                    )
                    if updated:
                        df.at[index, "Platform_Name"] = sc_alias
                    core.progress(
                        f"[V5][SC] {df.at[index, 'alpha_id']} PC 尚未确认："
                        f"仅同步 name={sc_alias!r}，不写 Useful，"
                        f"保留tags={before_tags}，"
                        f"平台同步={df.at[index, 'Platform_Update_Status']}"
                    )
                else:
                    core.progress(
                        f"[V5][SC] {df.at[index, 'alpha_id']} 已有 name={sc_alias!r}，"
                        "不重复 PATCH，不写 Useful"
                    )
                df.at[index, "PC_Status"] = "PENDING_PC"
                df.at[index, "Processing_Status"] = "READY_FOR_PC"
                pc_indices.append(index)
        core.progress(
            f"[V5][SC] {df.at[index, 'alpha_id']} 结果："
            f"SC={df.at[index, 'self_correlation']}，"
            f"PC={df.at[index, 'prod_correlation_max']}/{df.at[index, 'prod_correlation_min']}，"
            f"状态={df.at[index, 'Processing_Status']}，"
            f"平台同步={df.at[index, 'Platform_Update_Status']}"
        )
        core.save_snapshot(df, output_path)

    pc_indices.sort(key=lambda index: core.pc_priority_key(df, index))
    core.save_snapshot(df, output_path)
    core.progress(f"[V5] 阶段4：开始 PC，待计算 {len(pc_indices)} 条")
    pc_low_count = 0
    pc_processed_count = 0
    pc_started = time.monotonic()
    pc_stop_reason = "全部 PC 候选均已处理"
    for number, index in enumerate(pc_indices, start=1):
        alpha_id = df.at[index, "alpha_id"]
        core.progress(f"[V5][PC] 开始 {number}/{len(pc_indices)}：{alpha_id}")
        max_pc, min_pc, session = core.get_prod_correlation_stats_resilient(session, alpha_id)
        pc_processed_count += 1
        df.at[index, "prod_correlation_max"] = max_pc
        df.at[index, "prod_correlation_min"] = min_pc
        if core.is_high_pc(max_pc, min_pc):
            _apply_pc_state(session, df, index, alpha_by_id)
        elif max_pc is None or min_pc is None:
            df.at[index, "PC_Status"] = "PENDING_PC_RESULT"
            df.at[index, "Processing_Status"] = "PENDING_PC"
        else:
            if _apply_pc_state(session, df, index, alpha_by_id):
                pc_low_count += 1

        core.save_snapshot(df, output_path)
        core.progress(
            f"[V5][PC] 完成 {number}/{len(pc_indices)}：{alpha_id}，"
            f"PC={df.at[index, 'prod_correlation_max']}/{df.at[index, 'prod_correlation_min']}，"
            f"状态={df.at[index, 'Processing_Status']}，"
            f"平台同步={df.at[index, 'Platform_Update_Status']}"
        )
        stop_reason = core.get_pc_stop_reason(pc_processed_count, pc_low_count)
        if stop_reason is not None:
            pc_stop_reason = stop_reason
            break
        if core.CONFIG_PC_SUCCESS_DELAY_SECONDS > 0 and number < len(pc_indices):
            time.sleep(core.CONFIG_PC_SUCCESS_DELAY_SECONDS)

    useful_mask = df["_tags"].map(
        lambda tags: any(
            tag.casefold() == core.USEFUL_TAG.casefold() for tag in core.tag_names(tags)
        )
    )
    confirmed_useful_mask = (
        useful_mask
        & df["SC_Status"].astype(str).eq("PASS")
        & df["PC_Status"].astype(str).eq("PASS")
    )
    useful_count = int(confirmed_useful_mask.sum())
    retained_useful_count = int((useful_mask & ~confirmed_useful_mask).sum())
    sc_high_count = int(df["SC_Status"].astype(str).eq(core.SC_HIGH_TAG).sum())
    pc_high_count = int(df["PC_Status"].astype(str).eq(core.PC_HIGH_TAG).sum())
    pending_count = int(df["Processing_Status"].astype(str).str.startswith("PENDING").sum())
    core.progress(
        f"[V5] 阶段4完成：PC 远程处理 {pc_processed_count}/{len(pc_indices)}，"
        f"SC 预过滤跳过={sc_skipped_count}，SC 缓存候选={sc_cache_count}，"
        f"双低 {core.USEFUL_TAG}={useful_count}，待确认但保留的旧 {core.USEFUL_TAG}="
        f"{retained_useful_count}，SC高={sc_high_count}，"
        f"PC高={pc_high_count}，PENDING={pending_count}，输出={output_path.name}"
    )
    logging.info("V5 完成：PC 处理 %s/%s，双低 Useful %s，停止原因=%s，总耗时=%s，输出=%s",
                 pc_processed_count, len(pc_indices), useful_count,
                 pc_stop_reason, core.format_duration(time.monotonic() - pc_started), output_path)
    core.progress("[V5] 最终阶段：同步服务器全部 Useful 的 Pyramid/Submit")
    audit_server_useful_pyramids(session, pyramid_audit_path, output_path)


if __name__ == "__main__":
    if core.CONFIG_RUN_DAILY:
        while True:
            core.wait_until_midnight()
            run_job()
    else:
        run_job()
