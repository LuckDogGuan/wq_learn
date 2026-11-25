"""Lightweight Guangzhou-style Useful / SC / PC tagger & low-memory incremental scanner.

Design principles (user-specified):
- NO Web GUI / dashboard needed; users filter by the `Useful` tag directly on BRAIN and submit manually.
- Matches Guangzhou RA V7 tag conventions: `Useful`, `SC_IS_HIGHT`, `PC_IS_HIGHT`.
- Low-memory streaming scan: filters strictly at the API query layer
  (`stage=IS&status=UNSUBMITTED&settings.delay=1&is.sharpe>...`) and yields compact
  metadata records page-by-page without retaining full history or bulky payloads in RAM.
- Safe by default: `apply=False` (dry-run) unless caller explicitly passes `confirm_apply=True`.
- Zero `/alphas/{id}/submit` paths.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, Optional

USEFUL_TAG = "Useful"
SC_PASS_TAG = "SC_PASS"
SC_HIGH_TAG = "SC_IS_HIGHT"
PC_HIGH_TAG = "PC_IS_HIGHT"
TERMINAL_HIGH_TAGS = {SC_HIGH_TAG, PC_HIGH_TAG}
SC_ALIAS_MAX_THRESHOLD = 0.65


def format_sc_pc_alias(sc_val: Optional[float], pc_val: Optional[float]) -> Optional[str]:
    """Format standardized BRAIN alpha alias `SC 0.xxx PC 0.xxx` (user-mandated format)."""
    if sc_val is None and pc_val is None:
        return None
    sc_str = f"{float(sc_val):.3f}" if sc_val is not None else "NA"
    pc_str = f"{float(pc_val):.3f}" if pc_val is not None else "NA"
    return f"SC {sc_str} PC {pc_str}"


def sort_passing_candidates_margin_first(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Among fully passing RA candidates, prioritize HIGHER margin (bp) first, then Sharpe & Fitness."""
    return sorted(
        candidates,
        key=lambda c: (
            -(float(c["margin_bp"]) if c.get("margin_bp") is not None else -1e9),
            -(float(c["sharpe"]) if c.get("sharpe") is not None else -1e9),
            -(float(c["fitness"]) if c.get("fitness") is not None else -1e9),
        ),
    )


def compute_merged_tags(
    existing_tags: list[str],
    target_tag: str,
) -> tuple[list[str], bool]:
    """Compute idempotent merged tag list matching Guangzhou RA V7 + SC_PASS PC-rescue semantics.

    - If `target_tag` is `SC_IS_HIGHT` or `PC_IS_HIGHT`, strips stale `Useful` (and strips `SC_PASS` on `SC_IS_HIGHT`).
    - If `target_tag` is `SC_PASS` (all hard checks PASS + local SC < 0.68, ONLY PC >= 0.70), preserves
      non-conflicting tags and marks `SC_PASS` cleanly for dedicated PC-reduction queue.
    - If `target_tag` is `Useful`, preserves non-terminal tags and removes stale `SC_PASS` / high-corr markers.
    - Returns `(new_tags, changed)`.
    """
    cleaned = [str(t).strip() for t in (existing_tags or []) if str(t).strip()]
    target = str(target_tag).strip()
    if not target:
        return cleaned, False

    if target == SC_HIGH_TAG:
        filtered = [t for t in cleaned if t.casefold() not in {USEFUL_TAG.casefold(), SC_PASS_TAG.casefold()}]
        merged = list(dict.fromkeys([*filtered, target]))
    elif target == PC_HIGH_TAG:
        filtered = [t for t in cleaned if t.casefold() != USEFUL_TAG.casefold()]
        merged = list(dict.fromkeys([*filtered, target]))
    elif target.casefold() == SC_PASS_TAG.casefold():
        filtered = [t for t in cleaned if t not in {SC_HIGH_TAG} and t.casefold() != SC_PASS_TAG.casefold()]
        merged = list(dict.fromkeys([*filtered, SC_PASS_TAG]))
    elif target.casefold() == USEFUL_TAG.casefold():
        # Preserve non-terminal tags (e.g., competition tags) and put Useful cleanly once
        filtered = [
            t for t in cleaned
            if t not in TERMINAL_HIGH_TAGS and t.casefold() not in {USEFUL_TAG.casefold(), SC_PASS_TAG.casefold()}
        ]
        merged = list(dict.fromkeys([USEFUL_TAG, *filtered]))
    else:
        merged = list(dict.fromkeys([*cleaned, target]))

    changed = merged != cleaned
    return merged, changed


@dataclass(frozen=True)
class CompactAlphaItem:
    """Minimal RAM footprint record yielded by the low-memory incremental scanner."""
    alpha_id: str
    region: str
    universe: str
    delay: int
    alpha_type: str
    sharpe: Optional[float]
    fitness: Optional[float]
    turnover: Optional[float]
    margin_bp: Optional[float]
    tags: tuple[str, ...]
    date_created: str


def iter_unsubmitted_d1_window(
    client: Any,
    *,
    start_iso: str,
    end_iso: Optional[str] = None,
    region: Optional[str] = None,
    min_sharpe: float = 1.58,
    min_fitness: float = 1.0,
    page_limit: int = 100,
    max_pages: int = 50,
    skip_already_tagged_terminal: bool = True,
) -> Iterator[CompactAlphaItem]:
    """Stream unsubmitted D1 candidates page-by-page with minimal memory overhead.

    Push all filters (`stage=IS`, `status=UNSUBMITTED`, `settings.delay=1`, `is.sharpe>`,
    `is.fitness>`, date window, optional region) directly to the BRAIN query string so
    useless alphas are never fetched or stored in RAM.
    """
    offset = 0
    for _ in range(max_pages):
        params = [
            f"limit={int(page_limit)}",
            f"offset={int(offset)}",
            "stage=IS",
            "status=UNSUBMITTED",
            "settings.delay=1",
            f"is.sharpe>{float(min_sharpe)}",
            f"is.fitness>{float(min_fitness)}",
            f"dateCreated>={start_iso}",
            "order=-is.fitness",
        ]
        if end_iso:
            params.append(f"dateCreated<{end_iso}")
        if region:
            params.append(f"settings.region={region.upper()}")

        resp = client.get(f"/users/self/alphas?{'&'.join(params)}", timeout=30)
        if resp.status_code != 200:
            break
        payload = resp.json() or {}
        results = payload.get("results") or []
        if not results:
            break

        for row in results:
            settings = row.get("settings") or {}
            if int(settings.get("delay", 1)) != 1:
                continue
            tags = tuple(str(t).strip() for t in (row.get("tags") or []) if str(t).strip())
            if skip_already_tagged_terminal and any(t in TERMINAL_HIGH_TAGS for t in tags):
                continue
            is_obj = row.get("is") or {}
            margin = is_obj.get("margin")
            yield CompactAlphaItem(
                alpha_id=str(row.get("id") or ""),
                region=str(settings.get("region") or "").upper(),
                universe=str(settings.get("universe") or "").upper(),
                delay=1,
                alpha_type=str(row.get("type") or "REGULAR"),
                sharpe=is_obj.get("sharpe"),
                fitness=is_obj.get("fitness"),
                turnover=is_obj.get("turnover"),
                margin_bp=round(float(margin) * 10000, 2) if isinstance(margin, (int, float)) else None,
                tags=tags,
                date_created=str(row.get("dateCreated") or ""),
            )

        if len(results) < page_limit:
            break
        offset += page_limit


def apply_alpha_tag(
    client: Any,
    alpha_id: str,
    target_tag: str = USEFUL_TAG,
    *,
    alias_name: Optional[str] = None,
    confirm_apply: bool = False,
) -> dict[str, Any]:
    """Inspect current tags/name and apply `target_tag` (+ optional `alias_name` like `SC 0.xxx PC 0.xxx`) only if `confirm_apply=True`.

    Never modifies description/color/category; never calls `/submit`.
    """
    resp = client.get(f"/alphas/{alpha_id}", timeout=30)
    if resp.status_code != 200:
        return {
            "alpha_id": alpha_id,
            "applied": False,
            "reason": f"GET /alphas/{alpha_id} failed HTTP {resp.status_code}",
        }
    meta = resp.json() or {}
    existing = [str(t) for t in (meta.get("tags") or [])]
    existing_name = meta.get("name")
    merged, tags_changed = compute_merged_tags(existing, target_tag)
    clean_alias = alias_name.strip() if isinstance(alias_name, str) and alias_name.strip() else None
    name_changed = clean_alias is not None and clean_alias != existing_name

    if not tags_changed and not name_changed:
        return {
            "alpha_id": alpha_id,
            "applied": False,
            "dry_run": not confirm_apply,
            "existing_tags": existing,
            "merged_tags": merged,
            "existing_name": existing_name,
            "target_name": clean_alias,
            "reason": "ALREADY_UP_TO_DATE",
        }

    payload: dict[str, Any] = {}
    if tags_changed:
        payload["tags"] = merged
    if name_changed:
        payload["name"] = clean_alias

    if not confirm_apply:
        return {
            "alpha_id": alpha_id,
            "applied": False,
            "dry_run": True,
            "existing_tags": existing,
            "merged_tags": merged,
            "existing_name": existing_name,
            "target_name": clean_alias,
            "payload": payload,
            "reason": "DRY_RUN_ONLY (pass --confirm-apply to execute PATCH)",
        }

    patch_resp = client.patch(
        f"/alphas/{alpha_id}",
        explicit_user_confirmed=True,
        json=payload,
        timeout=30,
    )
    ok = 200 <= patch_resp.status_code < 300
    return {
        "alpha_id": alpha_id,
        "applied": ok,
        "dry_run": False,
        "http_status": patch_resp.status_code,
        "existing_tags": existing,
        "merged_tags": merged,
        "existing_name": existing_name,
        "target_name": clean_alias,
        "reason": "OK" if ok else f"PATCH HTTP {patch_resp.status_code}",
    }
