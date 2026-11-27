Status: ready-for-agent
Type: task
Owner: flash (main reviews)
Backtest budget: 0
Evidence: catalog sizes `[R]` (224 forum templates, 42 quarantined defect patterns per `buggy_templates_blocklist.json`)

# 08 · Public template catalog dedupe and source tagging

## Task
Collect every template skeleton the project can currently emit or has catalogued: `wq_research_v2/config/templates_50_50.json`, the playbook table in `REUSABLE_D1_RA_EXPERIENCE_PLAYBOOK.md` section 4, the admin catalog loaded by `legacy_core/Core/factor/templates/forum_verified.py`, and the code templates under `C:/Users/31186/.gemini/config/skills/worldquant-brain-cyber-game-king/references/code_templates/` (read-only).

Normalize each to a skeleton (fields `{x}`, numbers `{n}`), drop skeletons matching `wq_research_v2/config/buggy_templates_blocklist.json` or using `+`, `*`, `add`, `multiply`, `trade_when`, and deduplicate. For each unique skeleton record the sources it appears in and its operator count and nesting depth.

## Output
`docs/整理与研究/records/rules/template_catalog_dedupe_20261127.json` (small) plus a 10-line summary in the ticket. A skeleton quoted verbatim from a public Admin post gets `public_verbatim: true`; this only marks possible crowding `[U]`.

## Do not
Edit the source catalogs, `reference/`, or runner code. No backtests, no commit.

## Acceptance
Counts before and after dedupe reported; script or one-liner used is saved under `scripts/analysis/`.
