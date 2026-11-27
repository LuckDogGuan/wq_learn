Status: needs-triage
Type: research
Blocked by: 01
Owner: main
Backtest budget: 0
Evidence: legacy-only operator lift is `[C]` weak; production operator evidence missing

# 04 · Operator-in-context screening

## Question
Which operator usages (operator × position × neighbouring operators) raise or lower pass rates once dataset, field and settings are matched, in the **current** regime?

## Method
From ticket 01's CSV: normalize expressions to skeletons (fields to `{x}`, numbers to `{n}`); compare skeletons within the same (region, dataset, field, settings) cell; report only cells with at least 3 skeletons and at least 8 FULL sims; weight by cell size; keep counts next to every rate.

## Constraints
Operators are never blacklisted (AGENTS.md). Output is a ranked **usage-context** list with evidence tags. Legacy results (`legacy_alphas`) may be shown as a separate, clearly marked column, never merged.

## Acceptance
Table in `docs/整理与研究/records/rules/` with `[V]/[C]/[U]` per row and an explicit "insufficient data" bucket.
