# Frozen read-only comparison fixture from commit 51125a1310e6cc573f85fb5b224ff5e87ee5e02e.
# Never import as an operational workflow; tests inject every dependency.
def fetch_recent_alphas(session, checkpoint_path=None):
    """按水位增量读取 Alpha，使用时间切片绕开平台 1000 条分页上限。"""
    checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
    filters = ["is.sharpe>=1.6", "is.fitness>=1.0", "is.margin>0.0005"]
    signature = {
        "days": CONFIG_DAYS_AGO,
        "filters": filters,
        "status": "UNSUBMITTED",
        "hidden": False,
        "overlap_hours": CONFIG_FETCH_OVERLAP_HOURS,
    }
    state = _load_json(checkpoint_path, {}) if checkpoint_path else {}
    if state.get("version") != 2 or state.get("signature") != signature:
        previous_records = state.get("records", {}) if isinstance(state.get("records"), dict) else {}
        state = {"version": 2, "signature": signature, "records": previous_records, "watermark_utc": None}

    cached_records = state.get("records", {})
    if not isinstance(cached_records, dict):
        cached_records = {}
    lower_bound, window_end = beijing_date_window_utc()
    active = state.get("active_query")
    if isinstance(active, dict) and isinstance(active.get("slices"), dict):
        query_start = _parse_utc(active.get("start")) or lower_bound
        query_end = _parse_utc(active.get("end")) or window_end
        slices = active["slices"]
        progress(f"[Core][阶段1] 恢复中间文件：已缓存 {len(slices)} 个时间切片")
    else:
        watermark = _parse_utc(state.get("watermark_utc"))
        query_start = max(lower_bound, watermark - timedelta(hours=CONFIG_FETCH_OVERLAP_HOURS)) if watermark else lower_bound
        query_end = window_end
        slices = {}
        for slice_start, slice_end in _build_fetch_slices(query_start, query_end):
            slice_key = f"{slice_start.isoformat()}|{slice_end.isoformat()}"
            slices[slice_key] = {
                "start": slice_start.isoformat(),
                "end": slice_end.isoformat(),
                "pages": {},
                "complete": False,
            }
        state["active_query"] = {
            "start": query_start.isoformat(),
            "end": query_end.isoformat(),
            "slices": slices,
        }
        progress(
            f"[Core][阶段1] 增量区间：{query_start.isoformat()} -> {query_end.isoformat()}，"
            f"时间切片 {len(slices)} 个，已有缓存 {len(cached_records)} 条"
        )
        if checkpoint_path:
            _atomic_write_json(checkpoint_path, state)

    encoded_filters = [quote(item) for item in filters]
    failures = []
    for slice_number, (slice_key, slice_state) in enumerate(slices.items(), start=1):
        if not isinstance(slice_state, dict):
            failures.append(f"slice={slice_number} invalid")
            continue
        slice_start = _parse_utc(slice_state.get("start"))
        slice_end = _parse_utc(slice_state.get("end"))
        if slice_start is None or slice_end is None:
            failures.append(f"slice={slice_number} invalid_range")
            continue
        pages = slice_state.setdefault("pages", {})
        if not isinstance(pages, dict):
            pages = slice_state["pages"] = {}
        if slice_state.get("complete"):
            progress(f"[Core][阶段1] 使用已完成切片：{slice_number}/{len(slices)}")
            continue

        q_start = quote(f"dateCreated>={slice_start.strftime('%Y-%m-%dT%H:%M:%S-00:00')}")
        q_end = quote(f"dateCreated<{slice_end.strftime('%Y-%m-%dT%H:%M:%S-00:00')}")
        offset = 0
        slice_failed = False
        while True:
            page_key = str(offset)
            context = f"slice={slice_number}/{len(slices)} offset={offset}"
            if page_key in pages:
                page = pages[page_key]
                progress(f"[Core][阶段1] 使用缓存分页：{context}，{len(page)} 条")
            else:
                url = ("https://api.worldquantbrain.com/users/self/alphas"
                       f"?limit=100&offset={offset}&status=UNSUBMITTED&{encoded_filters[0]}&{encoded_filters[1]}&{encoded_filters[2]}"
                       f"&{q_start}&{q_end}&order=-dateCreated&hidden=false")
                response = get_alpha_page_with_retry(session, url, context)
                if response is None:
                    failures.append(context)
                    slice_failed = True
                    break
                try:
                    page = response.json().get("results", [])
                    if not isinstance(page, list):
                        raise ValueError("results 不是列表")
                except (ValueError, TypeError, AttributeError):
                    failures.append(context)
                    slice_failed = True
                    logging.error("Alpha 列表响应结构异常：%s", context)
                    break
                pages[page_key] = page
                state["updated_at"] = datetime.now(timezone.utc).isoformat()
                if checkpoint_path:
                    _atomic_write_json(checkpoint_path, state)
                progress(f"[Core][阶段1] 获取分页：{context}，{len(page)} 条，已写入中间文件")
            if not isinstance(page, list):
                failures.append(context)
                slice_failed = True
                logging.error("Alpha checkpoint 分页结构异常：%s", context)
                break
            if len(page) < 100:
                slice_state["complete"] = True
                break
            offset += 100
        if slice_failed:
            continue
        progress(f"[Core][阶段1] 时间切片完成：{slice_number}/{len(slices)}")

    page_records = [
        alpha
        for slice_state in slices.values()
        if isinstance(slice_state, dict)
        for page in (slice_state.get("pages", {}) or {}).values()
        if isinstance(page, list)
        for alpha in page
    ]
    merged = dict(cached_records)
    merged.update(_keep_recent_alpha_records(page_records, lower_bound))
    merged = _keep_recent_alpha_records(merged.values(), lower_bound)
    state["records"] = merged
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    complete = bool(slices) and all(
        isinstance(slice_state, dict) and slice_state.get("complete")
        for slice_state in slices.values()
    )
    if complete and not failures:
        state["watermark_utc"] = query_end.isoformat()
        state.pop("active_query", None)
        progress(f"[Core][阶段1] 增量读取完成：本地保留 {len(merged)} 条 Alpha")
    else:
        progress(f"[Core][阶段1] 部分完成：本地保留 {len(merged)} 条，待重试分页 {len(failures)} 个")
    if checkpoint_path:
        _atomic_write_json(checkpoint_path, state)
    progress(f"[Core][阶段1] 拉取完成：{len(merged)} 条，失败分页 {len(failures)} 个")
    return list(merged.values()), failures
