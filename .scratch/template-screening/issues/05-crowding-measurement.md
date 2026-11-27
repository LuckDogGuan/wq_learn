Status: needs-triage
Type: research
Blocked by: 01
Owner: main
Backtest budget: 0
Evidence: crowding mechanism plausible but not measured here `[U]`

# 05 · Crowding measurement

## Question
Do public-source templates (Admin posts, 王哥 skill) show higher production correlation than internal or mutated ones, at comparable Sharpe?

## Method
Join task rows (ticket 01) with `pc_poll_queue` / stored PC results by `alpha_id`. Group by `source_side` and template pack; report n, median PC, share with `pc_max < 0.70`, plus how many rows have **no** PC yet (unknown, never counted as pass or fail). Use the numeric `pc_max` plus the bucket table (see TODO T02 for the histogram caveats); do not trust the empty-body `check_correlation` pass.

## Acceptance
Report with n per group; groups with n < 10 labelled `[U]`. No platform writes.
