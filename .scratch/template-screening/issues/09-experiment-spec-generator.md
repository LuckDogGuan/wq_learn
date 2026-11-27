Status: ready-for-agent
Type: task
Owner: flash builds, main reviews
Backtest budget: 0
Evidence: design from findings doc section 3; AST/whitelist rules are `[V]` repo facts

# 09 · Spec generator for the paired experiment (ticket 06 step 1)

## Task
Create `wq_research_v2/src/wq_research_v2/template_experiment_specs.py` (pure functions, no network, no ledger writes) and `tests/unit/test_template_experiment_specs.py`.

Inputs: a list of `(region, universe, dataset_id, field_id, direction)` rows (direction `pos` or `rev`), read from `data/exports/task_template_rows.csv` through `scripts/analysis/task_template_audit.py::family_cells` filtered to alive QUICK cells (any family Sharpe >= 0.8); the better family direction is taken from the higher of the pos/rev QUICK Sharpe.

Output: per field the seven expressions V0..V6 in findings doc section 3, wrapped with `reverse(...)` for `rev`, plus settings (`decay=0`, `neutralization=SUBINDUSTRY`, `truncation=0.04`, `maxTrade=OFF`, D1, FULL) and a `variant_id`, `parent_field`, `single_changed_axis` label. Dedupe against the CSV by `(expression, settings)` so already-run tasks are skipped.

## Validation inside the generator
- Reuse the existing AST/operator validator and the Gold-81 whitelist (`wq_research_v2/config/operators_gold_81.json`); reject `+`, `*`, `add`, `multiply`, `trade_when`.
- Record `operator_count` and `nesting_depth` via `compute_expression_nesting_metrics`.
- Cap output at a `--max-sims` argument (default 700).

## Do not
Submit anything to the platform, touch the runner or the daemon, write to `legacy_core/`, `reference/`, or SQLite, or commit.

## Acceptance
`python -m pytest tests/unit/test_template_experiment_specs.py -q` passes; a dry run on the real CSV prints counts per region and per variant, with zero rejected expressions or an explicit list of rejects.
