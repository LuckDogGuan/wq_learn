Status: ready-for-agent
Type: task
Owner: flash (main reviews)
Backtest budget: 0
Evidence: schema is new `[U]`; initial rows come from findings doc section 2

# 02 · Template register file + schema test

## Deliverable
- `wq_research_v2/config/template_register.json`: data only, **not read by any runner code**. One entry per template pack with fields `pack_id, source_side (ADMIN_ORIGINAL|TOP100_2026Q4|WANGGE_SKILL|INTERNAL), skeleton, status (UNTESTED|PROBATION|KEEP|MODIFY|RETIRE), crowded (true|false|null), evidence_tag (V|R|C|U), coordinates (region/universe/dataset or "unmatched"), sample (cells, full_sims), note`.
- Initial entries = the table in `docs/整理与研究/records/rules/TEMPLATE_SCREENING_20261127.md` section 2 (copy statuses and tags exactly; do not invent new statuses).
- `tests/unit/test_template_register.py`: file parses; all statuses/tags in the allowed sets; `pack_id` unique; no entry has status `RETIRE` without `sample.cells >= 3` and a non-null `coordinates`.

## Do not
Edit runner code, change which templates are queued, commit, or run backtests.

## Acceptance
`python -m pytest tests/unit/test_template_register.py -q` passes; `git diff` shows only the two new files.
