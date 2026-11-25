"""Tunable Seed & Candidate Pruner to eliminate redundant similar seeds and accelerate Stage-2/3 iteration.

Non-destructive by design:
- Never deletes completed alphas from SQLite.
- Prunes redundant/near-duplicate seeds ONLY when promoting POOL_B/POOL_A into Stage-2/3 refinement
  or when exporting compact funnel candidate queues, keeping the highest-quality representative
  (ranked by sharpe, sharpe_2y, fitness, margin).

Tunable pruning parameters:
- jaccard_max (default 0.78): prune expressions whose operator+field token Jaccard >= jaccard_max
  within the same (region, dataset_id).
- max_per_field (default 2): keep at most K distinct winners per (region, dataset_id, primary_field_id).
- max_per_dataset (default 6): cap promoted seeds per (region, dataset_id) to prevent single-dataset hogging.
- metric_sharpe_eps (default 0.06) & metric_to_eps (default 0.02): prune same-field clones whose
  (sharpe, turnover) sit within eps of an already-kept stronger seed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_IGNORE_TOKENS = frozenset({"ts_backfill", "group_backfill", "subindustry", "industry", "sector", "country", "market"})


@dataclass(frozen=True)
class PruningConfig:
    jaccard_max: float = 0.78
    max_per_field: int = 2
    max_per_dataset: int = 6
    metric_sharpe_eps: float = 0.06
    metric_to_eps: float = 0.02


def extract_structural_tokens(expression: str) -> frozenset[str]:
    """Extract normalized operator & field tokens (ignoring window numbers & free backfill wrappers)."""
    toks = {t.lower() for t in _TOKEN_RE.findall(expression or "")}
    core = toks - _IGNORE_TOKENS
    return frozenset(core or toks)


def token_jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _seed_sort_key(row: dict[str, Any]) -> tuple[float, float, float, float]:
    return (
        float(row.get("sharpe") if row.get("sharpe") is not None else -999.0),
        float(row.get("sharpe_2y") if row.get("sharpe_2y") is not None else -999.0),
        float(row.get("fitness") if row.get("fitness") is not None else -999.0),
        float(row.get("margin") if row.get("margin") is not None else -999.0),
    )


def prune_similar_seeds(
    candidates: Iterable[dict[str, Any]],
    *,
    config: PruningConfig = PruningConfig(),
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Prune redundant similar seeds, returning (kept_seeds, pruned_seeds).

    Each candidate dict should contain at least 'expression', 'sharpe'; optionally
    'region', 'dataset_id', 'primary_field_id', 'turnover', 'sharpe_2y', 'fitness', 'margin'.
    """
    ordered = sorted(list(candidates), key=_seed_sort_key, reverse=True)
    kept: list[dict[str, Any]] = []
    pruned: list[dict[str, Any]] = []

    kept_by_ds: dict[tuple[str, str], list[tuple[dict[str, Any], frozenset[str]]]] = {}
    count_by_field: dict[tuple[str, str, str], int] = {}

    for cand in ordered:
        reg = str(cand.get("region") or "").upper()
        ds = str(cand.get("dataset_id") or "")
        fid = str(cand.get("primary_field_id") or "")
        expr = str(cand.get("expression") or "")
        toks = extract_structural_tokens(expr)

        ds_key = (reg, ds)
        field_key = (reg, ds, fid)
        ds_kept = kept_by_ds.setdefault(ds_key, [])

        # 1) Dataset fan-out cap
        if config.max_per_dataset > 0 and len(ds_kept) >= config.max_per_dataset:
            pruned.append({**cand, "_prune_reason": f"max_per_dataset({config.max_per_dataset})"})
            continue

        # 2) Same-field cap
        if fid and config.max_per_field > 0 and count_by_field.get(field_key, 0) >= config.max_per_field:
            pruned.append({**cand, "_prune_reason": f"max_per_field({config.max_per_field})"})
            continue

        # 3) Metric-profile clone OR structural Jaccard clone against already-kept stronger seeds in same (region, ds)
        reason = ""
        sh = cand.get("sharpe")
        to = cand.get("turnover")
        for prev, prev_toks in ds_kept:
            prev_fid = str(prev.get("primary_field_id") or "")
            jac = token_jaccard(toks, prev_toks)
            if jac >= config.jaccard_max:
                reason = f"jaccard({jac:.2f}>={config.jaccard_max})~{prev.get('alpha_id') or prev.get('task_id')}"
                break
            if (
                fid
                and fid == prev_fid
                and sh is not None
                and prev.get("sharpe") is not None
                and to is not None
                and prev.get("turnover") is not None
                and abs(float(sh) - float(prev["sharpe"])) <= config.metric_sharpe_eps
                and abs(float(to) - float(prev["turnover"])) <= config.metric_to_eps
            ):
                reason = f"metric_clone(dSh<={config.metric_sharpe_eps},dTO<={config.metric_to_eps})~{prev.get('alpha_id') or prev.get('task_id')}"
                break

        if reason:
            pruned.append({**cand, "_prune_reason": reason})
            continue

        kept.append(cand)
        ds_kept.append((cand, toks))
        if fid:
            count_by_field[field_key] = count_by_field.get(field_key, 0) + 1

    return kept, pruned
