"""Single-axis ablation, expression-level dual-branch min(rank,rank), and Gate-3 stress test engine.

Strictly obeys Decision #3:
- ZERO +, *, add(), multiply(), trade_when()
- Dual-branch A-E sequence:
  A: rank(expr_a)
  B: rank(expr_b)
  C1: min(rank(expr_a), rank(expr_b))
  C2: reverse(min(rank(expr_a), rank(expr_b)))
  D: group_rank(min(rank(expr_a), rank(expr_b)), industry)
  E (optional): max(rank(expr_a), rank(expr_b))
- Auto sign-flip for Sharpe < -1.2 using reverse(...) with anti-recursion guard
- Gate-3 pre-submission stress test: Decay [0, 1, 3, 5, 10, 20] + 9 Neutralization sweep
"""
from __future__ import annotations

from typing import Any

from wq_research_v2.expr_validator import ExprValidator

DECAY_STRESS_SEQUENCE = (0, 1, 3, 5, 10, 20)
NEUT_STRESS_SEQUENCE = (
    "STATISTICAL",
    "CROWDING",
    "FAST",
    "SLOW",
    "MARKET",
    "SECTOR",
    "INDUSTRY",
    "SUBINDUSTRY",
    "REVERSION_AND_MOMENTUM",
)


def build_sign_flip_expression(expr: str) -> str:
    """Flip expression sign with reverse(...) while preventing reverse(reverse(...)) recursion."""
    s = expr.strip()
    if s.startswith("reverse(") and s.endswith(")"):
        return s[len("reverse(") : -1].strip()
    if s.startswith("-(") and s.endswith(")"):
        return s[2:-1].strip()
    if s.startswith("-") and "(" not in s[:2]:
        return s[1:].strip()
    return f"reverse({s})"


def build_dual_branch_ablation(
    expr_a: str,
    expr_b: str,
    *,
    region: str,
    universe: str,
    base_settings: dict[str, Any],
    include_max: bool = False,
    group_dim: str = "industry",
) -> list[dict[str, Any]]:
    """Build Decision #3 compliant expression-level A-E single-axis ablation items."""
    a = expr_a.strip()
    b = expr_b.strip()
    items = [
        {
            "step": "A",
            "single_changed_axis": "baseline_branch_a",
            "atlas_layer": "L4",
            "source_side": "ADMIN_ORIGINAL",
            "author_id": "WL13229",
            "canonical_post_id": "23906082201239",
            "expression": f"rank({a})",
        },
        {
            "step": "B",
            "single_changed_axis": "baseline_branch_b",
            "atlas_layer": "L4",
            "source_side": "ADMIN_ORIGINAL",
            "author_id": "WL13229",
            "canonical_post_id": "23906082201239",
            "expression": f"rank({b})",
        },
        {
            "step": "C1",
            "single_changed_axis": "dual_branch_min",
            "atlas_layer": "L1-L4",
            "source_side": "ADMIN_ORIGINAL",
            "author_id": "WL13229",
            "canonical_post_id": "23906082201239",
            "expression": f"min(rank({a}), rank({b}))",
        },
        {
            "step": "C2",
            "single_changed_axis": "dual_branch_reverse_min",
            "atlas_layer": "L1-L4",
            "source_side": "ADMIN_ORIGINAL",
            "author_id": "WL13229",
            "canonical_post_id": "23906082201239",
            "expression": f"reverse(min(rank({a}), rank({b})))",
        },
        {
            "step": "D",
            "single_changed_axis": f"outer_group_rank_{group_dim}",
            "atlas_layer": "L5",
            "source_side": "TOP100_2026Q4",
            "author_id": "SZ83096",
            "canonical_post_id": "42509573118999",
            "expression": f"group_rank(min(rank({a}), rank({b})), {group_dim})",
        },
    ]
    if include_max:
        items.append({
            "step": "E",
            "single_changed_axis": "single_side_max",
            "atlas_layer": "L1-L4",
            "source_side": "TOP100_2026Q4",
            "author_id": "ZS59763",
            "canonical_post_id": "wangge_atlas",
            "expression": f"max(rank({a}), rank({b}))",
        })

    validator = ExprValidator()
    settings = dict(base_settings)
    settings.update({"region": region.upper(), "universe": universe.upper(), "delay": 1, "visualization": False})
    for it in items:
        rep = validator.validate(it["expression"], settings)
        it["validation_ok"] = rep.valid
        it["validation_errors"] = rep.errors
        it["counted_ops"] = rep.total_counted_calls
    return items


def build_gate3_stress_sweep(
    expression: str,
    base_settings: dict[str, Any],
    *,
    region: str,
) -> dict[str, list[dict[str, Any]]]:
    """Wang Ge Gate-3 stability stress suite: separate Decay [0,1,3,5,10,20] & 9 Neut sweeps (no Cartesian product)."""
    reg = region.upper()
    s_base = dict(base_settings)
    s_base["region"] = reg
    s_base["delay"] = 1
    s_base["visualization"] = False

    decay_items = []
    for d in DECAY_STRESS_SEQUENCE:
        decay_items.append({
            "single_changed_axis": f"decay={d}",
            "atlas_layer": "L6",
            "source_side": "TOP100_2026Q4",
            "author_id": "ZS59763",
            "expression": expression,
            "settings_override": {"decay": d},
        })

    neuts = list(NEUT_STRESS_SEQUENCE)
    if reg == "AMR":
        neuts = ["STATISTICAL", "MARKET", "SECTOR", "INDUSTRY", "SUBINDUSTRY", "COUNTRY"]
    elif reg in ("GLB", "EUR", "ASI"):
        neuts.append("COUNTRY")

    neut_items = []
    for n in neuts:
        neut_items.append({
            "single_changed_axis": f"neutralization={n}",
            "atlas_layer": "L6",
            "source_side": "TOP100_2026Q4",
            "author_id": "ZS59763",
            "expression": expression,
            "settings_override": {"neutralization": n},
        })

    return {"decay_sweep": decay_items, "neutralization_sweep": neut_items}
