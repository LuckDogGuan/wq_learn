"""Shared offset pagination; preserves caller sorting and stop boundaries."""

class AlphaPageUnavailable(RuntimeError):
    pass


def validate_alpha_page(payload, offset, limit, *, require_count=True):
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise AlphaPageUnavailable("PAGE_UNOBSERVED")
    count = payload.get("count")
    if count is None and require_count:
        raise AlphaPageUnavailable("COUNT_UNOBSERVED")
    if count is not None and (isinstance(count, bool) or not isinstance(count, int) or count < 0):
        raise AlphaPageUnavailable("INVALID_COUNT")
    records = payload["results"]
    if len(records) > limit or any(not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"] for item in records):
        raise AlphaPageUnavailable("INVALID_RECORD")
    if count is not None and (offset + len(records) > count or
            (len(records) < limit and offset + len(records) < count)):
        raise AlphaPageUnavailable("INCONSISTENT_COUNT")
    return {"results": records, "count": count}


def iter_alpha_pages(page_loader, *, page_size=100, max_records=None):
    """Yield validated pages; incomplete reads raise, never masquerade as empty."""
    if isinstance(page_size, bool) or not isinstance(page_size, int) or not 1 <= page_size <= 100:
        raise ValueError("page_size must be 1..100")
    if max_records is not None and (isinstance(max_records, bool) or not isinstance(max_records, int) or max_records <= 0):
        raise ValueError("max_records must be positive or None")
    offset = 0
    seen = set()
    while max_records is None or offset < max_records:
        page = validate_alpha_page(page_loader(offset), offset, page_size)
        records = page["results"]
        ids = {item["id"] for item in records}
        if len(ids) != len(records) or ids & seen:
            raise AlphaPageUnavailable("UNSTABLE_PAGINATION")
        seen.update(ids)
        yield page
        offset += len(records)
        if len(records) < page_size or offset >= page["count"]:
            return

