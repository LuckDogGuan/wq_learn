"""Small, explicit registry for stage-aware optimization routes."""

ROUTE_REGISTRY = {
    "stable": {"stages": (2, 3), "status": "AVAILABLE", "operators": ("ts_backfill", "ts_mean", "ts_zscore"), "targets": ("sharpe_2y", "stability")},
    "smooth": {"stages": (2, 3), "status": "AVAILABLE", "operators": ("ts_decay_linear", "hump", "ts_target_tvr_decay", "ts_target_tvr_hump"), "targets": ("turnover", "margin")},
    "template": {"stages": (1, 2, 3), "status": "AVAILABLE", "operators": (), "targets": ("sharpe", "fitness", "sharpe_2y", "margin")},
    "stat": {"stages": (2, 3), "status": "AVAILABLE", "operators": ("winsorize", "normalize", "zscore", "quantile"), "targets": ("sharpe", "fitness", "concentration")},
    "cross": {"stages": (2, 3), "status": "AVAILABLE", "operators": ("rank", "group_rank", "group_zscore", "group_neutralize"), "targets": ("concentration", "sc", "pc")},
    "cw": {"stages": (1, 2, 3), "status": "AVAILABLE", "operators": (), "targets": ("sharpe", "sharpe_2y", "turnover")},
    "twin": {"stages": (2, 3), "status": "AVAILABLE", "operators": ("ts_regression", "ts_corr", "ts_covariance"), "targets": ("sharpe", "fitness", "margin")},
    "basic": {"stages": (1, 2), "status": "AVAILABLE", "operators": ("rank", "reverse", "signed_power"), "targets": ("sharpe", "fitness")},
    "robust_sharpe": {"stages": (3,), "status": "DIAGNOSTIC_ONLY", "operators": (), "targets": ("robust_sharpe",)},
    "filter": {"stages": (), "status": "UNAVAILABLE", "operators": ("filter",), "targets": ()},
    "gvn": {"stages": (), "status": "UNAVAILABLE", "operators": ("group_vector_neut",), "targets": ()},
    "gvp": {"stages": (), "status": "UNAVAILABLE", "operators": ("group_vector_proj",), "targets": ()},
    "gvp_auto": {"stages": (), "status": "UNAVAILABLE", "operators": (), "targets": ()},
    "ai": {"stages": (), "status": "DISABLED_BY_POLICY", "operators": (), "targets": ()},
}


def candidate_route(candidate):
    family = str(candidate.get("family") or "").lower()
    template_id = str(candidate.get("template_id") or "").lower()
    if candidate.get("kind") in {"probe_neighbor", "baseline_refresh"}:
        return "cw"
    if candidate.get("kind") == "binary" or "hu_ge" in template_id:
        return "twin"
    if any(token in family or token in template_id for token in ("decay", "smooth", "turnover", "tvr", "hump")):
        return "smooth"
    if any(token in family or token in template_id for token in ("group", "neutral", "correlation", "pc_")):
        return "cross"
    if any(token in family or token in template_id for token in ("distribution", "winsor", "quantile", "zscore", "kurtosis")):
        return "stat"
    if any(token in family or token in template_id for token in ("backfill", "stability", "risk")):
        return "stable"
    if candidate.get("candidate_origin") == "FORMAL_TEMPLATE":
        return "template"
    return "basic"


def choose_route(stage, gate, attempted=()):
    attempted = set(attempted or ())
    deficits = dict((gate or {}).get("gate_deficits") or {})
    if int(stage) == 1:
        order = ("cw", "template")
    else:
        largest = max(deficits, key=deficits.get) if deficits else ""
        preferred = {
            "turnover": "smooth", "margin_bp": "smooth", "sharpe_2y": "stable",
            "sc": "cross", "pc": "cross", "sharpe": "template", "fitness": "stat",
            "platform_checks": "cross",
        }.get(largest, "stable" if int(stage) == 2 else "template")
        tail = ("cw", "stat", "cross", "twin", "template", "smooth", "stable") if int(stage) == 2 else ("cross", "stable", "smooth", "stat", "twin", "template", "cw")
        order = (preferred, *tail)
    for route in dict.fromkeys(order):
        item = ROUTE_REGISTRY[route]
        if route not in attempted and int(stage) in item["stages"] and item["status"] == "AVAILABLE":
            return route
    return next((route for route in order if ROUTE_REGISTRY[route]["status"] == "AVAILABLE"), "template")


def prioritize_route(candidates, route, prefer_catalog=False):
    if prefer_catalog:
        # 224目录内保持Core的管理员/调用次数顺序，路由只能排其后的旧候选。
        return sorted(candidates, key=lambda item: (
            0 if item.get("catalog_status") == "LOCAL_PASS_UNVALIDATED" else 1,
            0 if item.get("catalog_status") == "LOCAL_PASS_UNVALIDATED" else candidate_route(item) != route,
        ))
    return sorted(candidates, key=lambda item: (
        candidate_route(item) != route, candidate_route(item), item.get("template_id", "")
    ))


__all__ = ["ROUTE_REGISTRY", "candidate_route", "choose_route", "prioritize_route"]
