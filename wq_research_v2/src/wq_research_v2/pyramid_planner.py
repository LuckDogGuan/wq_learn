"""5:5 Balanced D1 Stage-0 / Stage-2 Batch Planner integrated with BlacklistRegistry."""
from __future__ import annotations

import datetime
from typing import Any, Optional

from wq_research_v2.blacklist_registry import BlacklistRegistry
from wq_research_v2.config_loader import load_templates_50_50
from wq_research_v2.expr_validator import ExprValidator


def build_stage0_probe_spec(
    *,
    region: str,
    universe: str,
    dataset_id: str,
    field_id: str,
    field_type: str = "MATRIX",
    queue_type: str = "NORMAL",
    neutralization: str = "INDUSTRY",
    max_trade: str = "OFF",
    hypothesis_id: Optional[str] = None,
    blacklist: Optional[BlacklistRegistry] = None,
    is_fake_single_vector: bool = False,
) -> dict[str, Any]:
    """Generate a strict 4 Admin : 4 Top100 Stage-0 D1 probe spec (decay=0, single Neut)."""
    reg = region.upper()
    univ = universe.upper()
    ftype = field_type.upper()
    tpls = load_templates_50_50()["stage0_probe_4_4"]

    if reg in ("ASI", "HKG", "KOR", "JPN", "TWN"):
        max_trade = "ON"

    settings = {
        "instrumentType": "EQUITY",
        "region": reg,
        "universe": univ,
        "delay": 1,
        "decay": 0,
        "neutralization": neutralization.upper(),
        "truncation": 0.08,
        "pasteurization": "ON",
        "unitHandling": "VERIFY",
        "nanHandling": "OFF",
        "maxTrade": max_trade,
        "maxPosition": "OFF",
        "language": "FASTEXPR",
        "visualization": False,
    }

    validator = ExprValidator()
    items: list[dict[str, Any]] = []
    for tpl in tpls:
        raw_expr = tpl["expr_vector"] if ftype == "VECTOR" else tpl["expr_matrix"]
        # JX14975 rule: fake single-value VECTOR only uses vec_avg
        if ftype == "VECTOR" and is_fake_single_vector and "vec_min(" in raw_expr:
            raw_expr = raw_expr.replace("vec_min(", "vec_avg(")
        expr = raw_expr.format(x=field_id)

        if blacklist is not None:
            blocked, _ = blacklist.is_blocked(
                region=reg, universe=univ, delay=1, dataset_id=dataset_id,
                field_id=field_id, method_id=tpl["id"],
            )
            if blocked:
                continue

        rep = validator.validate(expr, settings)
        items.append({
            "template_id": tpl["id"],
            "source_side": tpl["source_side"],
            "author_id": tpl["author_id"],
            "canonical_post_id": tpl["canonical_post_id"],
            "atlas_layer": tpl["atlas_layer"],
            "single_changed_axis": f"stage0_{tpl['id']}",
            "dataset_id": dataset_id,
            "primary_field_id": field_id,
            "expression": expr,
            "validation_ok": rep.valid,
            "validation_errors": rep.errors,
        })

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return {
        "batch_id": f"EXP-{reg}-{dataset_id}-S0-{ts}",
        "hypothesis_id": hypothesis_id or f"HYP-{reg}-{dataset_id}-{field_id}",
        "queue_type": queue_type.upper(),
        "source_side": "MIXED_4_4",
        "region": reg,
        "universe": univ,
        "delay": 1,
        "dataset_id": dataset_id,
        "settings": settings,
        "items": items,
    }
