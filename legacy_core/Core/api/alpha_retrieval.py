"""Reliable, read-only Alpha list retrieval shared by business workflows."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable
from urllib.parse import quote, unquote


COMPLETE = "COMPLETE"
PARTIAL = "PARTIAL"
PENDING = "PENDING"


@dataclass
class AlphaFetchResult:
    records: list[dict]
    status: str
    failures: list[dict] = field(default_factory=list)
    request_count: int = 0


def _iso(value: datetime) -> str:
    return value.isoformat()


def _validate_range(start: datetime, end: datetime) -> None:
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        raise TypeError("start/end 必须是 datetime")
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("start/end 必须包含时区")
    if start >= end:
        raise ValueError("start 必须早于 end")


def _query_clauses(query) -> list[str]:
    raw = query.split("&") if isinstance(query, str) else list(query or ())
    ignored = ("limit=", "offset=", "order=", "dateCreated")
    return [
        str(item).strip().lstrip("?")
        for item in raw
        if str(item).strip() and not str(item).strip().startswith(ignored)
    ]


def build_alpha_page_url(query, start: datetime, end: datetime, *, offset: int,
                         limit: int, descending: bool = True) -> str:
    """Build one /users/self/alphas page using a half-open time range."""
    _validate_range(start, end)
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset 必须是非负整数")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit 必须是 1 到 100 的整数")
    clauses = [
        quote(unquote(clause), safe="") if any(op in unquote(clause) for op in (">", "<", "!"))
        else clause for clause in _query_clauses(query)
    ]
    clauses.extend((
        f"limit={limit}",
        f"offset={offset}",
        quote(f"dateCreated>={_iso(start)}", safe=""),
        quote(f"dateCreated<{_iso(end)}", safe=""),
        f"order={'-' if descending else ''}dateCreated",
    ))
    return "/users/self/alphas?" + "&".join(clauses)


def _read_checkpoint(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _write_checkpoint(path: Path | None, document: dict) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    os.replace(temporary, path)


def _new_node(start: datetime, end: datetime) -> dict:
    return {"start": _iso(start), "end": _iso(end), "pages": {}, "complete": False}


def _initial_windows(start: datetime, end: datetime, slice_size: timedelta) -> list[dict]:
    windows = []
    cursor = start
    while cursor < end:
        window_end = min(cursor + slice_size, end)
        windows.append(_new_node(cursor, window_end))
        cursor = window_end
    return windows


def _valid_windows(windows, start, end, page_size):
    """Corrupt/incompatible checkpoints are re-read, never trusted as complete."""
    from Core.api.pagination import validate_alpha_page
    try:
        if not isinstance(windows, list) or not windows:
            return False
        cursor = start
        for node in windows:
            left, right = datetime.fromisoformat(node["start"]), datetime.fromisoformat(node["end"])
            if left != cursor or not left < right <= end:
                return False
            cursor = right
            if not isinstance(node["complete"], bool) or not isinstance(node["pages"], dict):
                return False
            offset = 0
            last = None
            for key in sorted(node["pages"], key=int):
                if str(offset) != key:
                    return False
                last = validate_alpha_page(node["pages"][key], offset, page_size)
                offset += len(last["results"])
            if node.get("children"):
                if not _valid_windows(node["children"], left, right, page_size):
                    return False
                if node["complete"] and not all(child["complete"] for child in node["children"]):
                    return False
            elif node["complete"] and (last is None or offset != last["count"]):
                return False
        return cursor == end
    except (KeyError, TypeError, ValueError, RuntimeError, RecursionError):
        return False


def fetch_alpha_window(
    client,
    start: datetime,
    end: datetime,
    *,
    query=(),
    page_size: int = 100,
    slice_size: timedelta = timedelta(days=1),
    dense_window_threshold: int = 500,
    min_window_size: timedelta = timedelta(seconds=1),
    descending: bool = True,
    checkpoint_path: str | Path | None = None,
    checkpoint_namespace: str = "alpha_fetch",
    page_loader: Callable | None = None,
    refresh_completed: bool = False,
) -> AlphaFetchResult:
    """Fetch Alpha records completely or return an explicit incomplete state.

    page_loader is a compatibility hook for legacy callers. It receives
    (url, context) and must return a page mapping or None. New callers should
    omit it so every request goes through client.get.
    """
    _validate_range(start, end)
    if not isinstance(page_size, int) or isinstance(page_size, bool) or not 1 <= page_size <= 100:
        raise ValueError("page_size 必须是 1 到 100 的整数")
    if slice_size <= timedelta(0) or min_window_size <= timedelta(0):
        raise ValueError("时间切片必须大于 0")
    if dense_window_threshold < page_size:
        raise ValueError("dense_window_threshold 不能小于 page_size")

    checkpoint = Path(checkpoint_path) if checkpoint_path else None
    document = _read_checkpoint(checkpoint)
    signature = {
        "start": _iso(start),
        "end": _iso(end),
        "query": _query_clauses(query),
        "page_size": page_size,
        "slice_seconds": slice_size.total_seconds(),
        "dense_window_threshold": dense_window_threshold,
        "min_window_seconds": min_window_size.total_seconds(),
        "descending": descending,
    }
    state = document.get(checkpoint_namespace)
    if isinstance(state, dict) and not _valid_windows(state.get("windows"), start, end, page_size):
        state = None
    if (
        refresh_completed
        and isinstance(state, dict)
        and state.get("signature") == signature
        and state.get("windows")
        and all(window.get("complete") for window in state["windows"])
    ):
        state = None
    if not isinstance(state, dict) or state.get("version") != 2 or state.get("signature") != signature:
        state = {
            "version": 2,
            "signature": signature,
            "windows": _initial_windows(start, end, slice_size),
        }
        document[checkpoint_namespace] = state
        _write_checkpoint(checkpoint, document)

    failures = []
    records = []
    request_count = 0

    def persist():
        document[checkpoint_namespace] = state
        _write_checkpoint(checkpoint, document)

    def load_page(node, window_number, window_total, offset):
        nonlocal request_count
        pages = node.setdefault("pages", {})
        page_key = str(offset)
        if page_key in pages:
            return pages[page_key]
        window_start = datetime.fromisoformat(node["start"])
        window_end = datetime.fromisoformat(node["end"])
        context = f"slice={window_number}/{window_total} offset={offset}"
        url = build_alpha_page_url(
            query, window_start, window_end,
            offset=offset, limit=page_size, descending=descending,
        )
        request_count += 1
        if page_loader is not None:
            payload = page_loader(url, context)
        else:
            response = client.get(url, timeout=30)
            if response is None or response.status_code != 200:
                payload = None
            else:
                try:
                    payload = response.json()
                except (TypeError, ValueError):
                    payload = None
        from Core.api.pagination import validate_alpha_page, AlphaPageUnavailable
        try:
            page = validate_alpha_page(payload, offset, page_size)
            previous_ids = {
                item["id"] for saved in pages.values() for item in saved["results"]
            }
            ids = [item["id"] for item in page["results"]]
            if len(set(ids)) != len(ids) or previous_ids.intersection(ids):
                raise AlphaPageUnavailable("UNSTABLE_PAGINATION")
            if pages and any(saved["count"] != page["count"] for saved in pages.values()):
                raise AlphaPageUnavailable("COUNT_CHANGED")
        except AlphaPageUnavailable as exc:
            failures.append({"context": context, "reason": str(exc)})
            return None
        pages[page_key] = page
        persist()
        return page

    def visit(node, window_number, window_total):
        if node.get("children"):
            for child in node["children"]:
                visit(child, window_number, window_total)
            node["complete"] = all(child.get("complete") for child in node["children"])
            persist()
            return

        if node.get("complete"):
            for page in node.get("pages", {}).values():
                records.extend(page.get("results", []))
            return

        window_start = datetime.fromisoformat(node["start"])
        window_end = datetime.fromisoformat(node["end"])
        offset = 0
        while True:
            page = load_page(node, window_number, window_total, offset)
            if page is None:
                return
            page_records = page["results"]
            count = page.get("count")

            dense = count is not None and count > dense_window_threshold
            dense = dense or (count is None and offset + len(page_records) >= dense_window_threshold)
            if dense:
                duration = window_end - window_start
                if duration <= min_window_size:
                    records.extend(page_records)
                    failures.append({
                        "context": f"slice={window_number}/{window_total} offset={offset}",
                        "reason": "DENSE_WINDOW_UNSPLITTABLE",
                    })
                    return
                midpoint = window_start + duration / 2
                if not window_start < midpoint < window_end:
                    failures.append({"context": f"slice={window_number}/{window_total} offset={offset}", "reason": "DENSE_WINDOW_UNSPLITTABLE"})
                    return
                node["children"] = [
                    _new_node(window_start, midpoint),
                    _new_node(midpoint, window_end),
                ]
                persist()
                visit(node, window_number, window_total)
                return

            records.extend(page_records)
            if len(page_records) < page_size or (count is not None and offset + len(page_records) >= count):
                node["complete"] = True
                persist()
                return
            offset += len(page_records)

    windows = state.get("windows", [])
    for number, window in enumerate(windows, 1):
        visit(window, number, len(windows))

    # Preserve parent observations across failed child splits; completed children
    # supersede parent snapshots, including after restart.
    def collect(node):
        children = node.get("children", [])
        if not children or not node.get("complete"):
            for page in node.get("pages", {}).values():
                yield from page["results"]
        for child in children:
            yield from collect(child)

    records = [record for window in windows for record in collect(window)]
    unique = {}
    for record in records:
        if isinstance(record, dict) and record.get("id"):
            unique[str(record["id"])] = record
    complete = bool(windows) and all(window.get("complete") for window in windows)
    status = COMPLETE if complete and not failures else PARTIAL if unique else PENDING
    return AlphaFetchResult(list(unique.values()), status, failures, request_count)
