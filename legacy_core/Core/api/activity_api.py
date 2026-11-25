"""WorldQuant BRAIN user activity endpoints."""

import re

from Core.api.client import BrainClient


USER_DIVERSITY_PATH = "/users/self/activities/diversity"
PYRAMID_ALPHAS_PATH = "/users/self/activities/pyramid-alphas"


def get_current_quarter_dates(client: BrainClient = None, dt=None):
    """获取当前自然季度的起止日期（startDate, endDate）。

    策略：
    1. 优先通过平台官方接口 /users/self/consultant/summary 读取平台权威判定的 currentQuarter；
    2. 若接口不可用或未传 client，则基于本地自然日历月份自动推算（Q1: 01-01~04-01, Q2: 04-01~07-01...）。
    """
    if client is not None:
        try:
            resp = client.get("/users/self/consultant/summary")
            if resp and resp.status_code == 200:
                q = (resp.json() or {}).get("performance", {}).get("currentQuarter", {})
                s = q.get("startDate")
                e = q.get("endDate")
                if s and e:
                    return s, e
        except Exception:
            pass

    import datetime
    if dt is None:
        dt = datetime.datetime.now()
    y, m = dt.year, dt.month
    if m in (1, 2, 3):
        return f"{y}-01-01", f"{y}-04-01"
    elif m in (4, 5, 6):
        return f"{y}-04-01", f"{y}-07-01"
    elif m in (7, 8, 9):
        return f"{y}-07-01", f"{y}-10-01"
    else:
        return f"{y}-10-01", f"{y+1}-01-01"


def get_pyramid_alphas(
    client: BrainClient,
    start_date: str = None,
    end_date: str = None,
) -> dict:
    """获取指定或当前季度金字塔看板的原生 API 数据源。"""
    if not start_date or not end_date:
        start_date, end_date = get_current_quarter_dates(client)
    url = f"{PYRAMID_ALPHAS_PATH}?startDate={start_date}&endDate={end_date}"
    response = client.get(url)
    if not response or response.status_code != 200:
        return {}
    try:
        return response.json()
    except Exception:
        return {}


def get_pyramid_tower_status(
    client: BrainClient,
    delay: int = 1,
    min_count: int = 3,
    start_date: str = None,
    end_date: str = None,
) -> dict:
    """一次性获取各 Region 的已点亮塔数、未点亮塔数、已点亮类别、未点亮类别。

    返回格式：
    {
        "USA": {
            "lit_count": 0,
            "unlit_count": 16,
            "lit_cats": [],
            "unlit_cats": ["Price Volume(0)", "Fundamental(0)", ...],
            "almost_lit_cats": []  # 已有 1~2 个 Alpha，差 1~2 个即可点亮的类别
        },
        ...
    }
    """
    data = get_pyramid_alphas(client, start_date=start_date, end_date=end_date)
    pyramids = data.get("pyramids") if isinstance(data, dict) else []
    if not isinstance(pyramids, list):
        return {}

    status = {}
    for p in pyramids:
        if not isinstance(p, dict):
            continue
        if p.get("delay") != delay:
            continue
        reg = str(p.get("region") or "").strip().upper()
        if not reg:
            continue
        cat = (p.get("category") or {}).get("name") or "Unknown"
        cnt = int(p.get("alphaCount", 0))

        if reg not in status:
            status[reg] = {
                "lit_count": 0,
                "unlit_count": 0,
                "lit_cats": [],
                "unlit_cats": [],
                "almost_lit_cats": [],
            }

        if cnt >= min_count:
            status[reg]["lit_count"] += 1
            status[reg]["lit_cats"].append(f"{cat}({cnt})")
        else:
            status[reg]["unlit_count"] += 1
            status[reg]["unlit_cats"].append(f"{cat}({cnt})")
            if cnt > 0:
                status[reg]["almost_lit_cats"].append(f"{cat}({cnt})")

    return status


def get_pyramid_lit_tower_counts(
    client: BrainClient,
    delay: int = 1,
    min_count: int = 3,
    start_date: str = None,
    end_date: str = None,
) -> dict:
    """返回当前季度各 Region 已点亮（alphaCount >= min_count）的子塔数量字典 {region: count}。"""
    tower_status = get_pyramid_tower_status(
        client, delay=delay, min_count=min_count, start_date=start_date, end_date=end_date
    )
    return {reg: s["lit_count"] for reg, s in tower_status.items() if s["lit_count"] > 0}



def get_alpha_pyramid_pass_info(client: BrainClient, alpha_id: str) -> dict:
    """Return the PASS information used to classify an Alpha's pyramid scope.

    The platform exposes one or more pyramid scopes in
    ``is.checks[name=MATCHES_PYRAMID].pyramids``.  This helper keeps the
    platform names intact instead of deriving categories from expression
    fields, and also returns the platform's effective count and multiplier.

    ``status`` is ``PASS`` when the check is present and passed, ``NO_PASS``
    when the check is present but did not pass, and ``PENDING`` when the
    response is unavailable or incomplete.
    """
    alpha_id = str(alpha_id or "").strip()
    if not alpha_id:
        return {"status": "PENDING", "alpha_id": alpha_id, "categories": []}

    response = client.get(f"/alphas/{alpha_id}")
    if response is None or response.status_code != 200:
        return {"status": "PENDING", "alpha_id": alpha_id, "categories": []}

    try:
        payload = response.json()
    except (TypeError, ValueError):
        return {"status": "PENDING", "alpha_id": alpha_id, "categories": []}

    checks = payload.get("is", {}).get("checks") if isinstance(payload, dict) else None
    if not isinstance(checks, list):
        return {"status": "PENDING", "alpha_id": alpha_id, "categories": []}

    pyramid_check = next(
        (check for check in checks
         if isinstance(check, dict) and check.get("name") == "MATCHES_PYRAMID"),
        None,
    )
    if pyramid_check is None:
        return {"status": "PENDING", "alpha_id": alpha_id, "categories": []}

    pyramids = pyramid_check.get("pyramids")
    if not isinstance(pyramids, list):
        pyramids = []
    valid_pyramids = [
        {"name": item.get("name"), "multiplier": item.get("multiplier")}
        for item in pyramids
        if isinstance(item, dict) and item.get("name")
    ]

    if pyramid_check.get("result") == "PASS" and not valid_pyramids:
        return {"status": "PENDING", "alpha_id": alpha_id, "categories": []}

    return {
        "status": "PASS" if pyramid_check.get("result") == "PASS" else "NO_PASS",
        "alpha_id": alpha_id,
        "categories": [item["name"] for item in valid_pyramids],
        "pyramids": valid_pyramids,
        "effective": pyramid_check.get("effective"),
        "multiplier": pyramid_check.get("multiplier"),
    }


def get_user_diversity(client: BrainClient) -> dict:
    """Return the platform's per-region/category diversity payload.

    The endpoint is the source of truth for the displayed 30% limit.  The
    response is intentionally returned without recalculating or truncating
    values locally, so new regions/categories added by the platform remain
    usable.

    An unavailable, invalid, or non-object response returns ``{}``, matching
    the existing read-only platform API helpers.
    """
    response = client.get(USER_DIVERSITY_PATH)
    if not response or response.status_code != 200:
        return {}

    try:
        payload = response.json()
    except (TypeError, ValueError):
        return {}

    return payload if isinstance(payload, dict) else {}


_CATEGORY_ALIASES = {
    "pricevolume": "pv",
    "pricevol": "pv",
}


def _canonical_category(value) -> str:
    token = re.sub(r"[^a-z0-9]+", "", str(value or "").lower())
    return _CATEGORY_ALIASES.get(token, token)


def evaluate_pyramid_coverage(diversity_payload: dict, pyramid_info: dict) -> dict:
    """判断 Alpha 关联的塔是否已在相同 Region/Delay 下全部 PASS。

    返回 ``ALL_PASS``、``HAS_GAP`` 或 ``PENDING``。只使用平台返回的
    ``dataDiversity.check``，不根据 ``alphaCount`` 自行推算 30% 比例。
    """
    rows = diversity_payload.get("alphas") if isinstance(diversity_payload, dict) else None
    categories = pyramid_info.get("categories") if isinstance(pyramid_info, dict) else None
    if not isinstance(rows, list):
        return {"status": "PENDING", "scopes": [], "gap_scopes": [],
                "reason": "diversity响应不可用或结构不完整"}
    if (not isinstance(pyramid_info, dict) or pyramid_info.get("status") == "PENDING"
            or not isinstance(categories, list) or not categories):
        return {"status": "PENDING", "scopes": [], "gap_scopes": [],
                "reason": "Alpha金字塔分类不可用或结构不完整"}

    diversity_index = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        category = row.get("dataCategory") or {}
        category_key = _canonical_category(category.get("id") or category.get("name"))
        region = str(row.get("region") or "").strip().upper()
        delay = row.get("delay")
        if not region or delay is None or not category_key:
            continue  # 忽略 dataCategory 为空的地区汇总行。
        try:
            delay = int(delay)
        except (TypeError, ValueError):
            continue
        diversity = row.get("dataDiversity") or {}
        diversity_index[(region, delay, category_key)] = {
            "check": str(diversity.get("check") or "").strip().upper() or "MISSING",
            "limit": diversity.get("limit"),
            "alpha_count": row.get("alphaCount"),
            "category_id": category.get("id"),
            "category_name": category.get("name"),
        }

    scopes = []
    for raw_scope in categories:
        match = re.fullmatch(r"([^/]+)/D(\d+)/(.+)", str(raw_scope or "").strip(), re.IGNORECASE)
        if not match:
            return {"status": "PENDING", "scopes": scopes, "gap_scopes": [],
                    "reason": f"无法解析平台塔名称: {raw_scope!r}"}
        region = match.group(1).upper()
        delay = int(match.group(2))
        category_key = _canonical_category(match.group(3))
        row = diversity_index.get((region, delay, category_key))
        scopes.append({
            "raw_scope": raw_scope,
            "region": region,
            "delay": delay,
            "category": category_key,
            "check": row["check"] if row else "MISSING",
            "limit": row.get("limit") if row else None,
            "alpha_count": row.get("alpha_count") if row else None,
            "matched_category_id": row.get("category_id") if row else None,
            "matched_category_name": row.get("category_name") if row else None,
        })

    gap_scopes = [scope for scope in scopes if scope["check"] != "PASS"]
    return {
        "status": "HAS_GAP" if gap_scopes else "ALL_PASS",
        "scopes": scopes,
        "gap_scopes": gap_scopes,
        "reason": "存在未PASS或未返回的关联塔" if gap_scopes else "所有关联塔均由平台判定为PASS",
    }
