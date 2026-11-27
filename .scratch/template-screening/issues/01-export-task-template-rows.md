Status: resolved
Type: task
Owner: main
Backtest budget: 0
Evidence: [V]

# 01 · Export task-level template rows (read-only)

## Answer
Authorized by the user 2026-11-27 15:31. Done via `scripts/ops/export_guangzhou_task_templates.py` (SQLite `mode=ro`, streamed CSV on stdout, no writes). Output `data/exports/task_template_rows.csv` (git-ignored): 15,193 rows = COMPLETED_FULL 6,865 + COMPLETED_QUICK 8,328.

## Findings that changed earlier numbers
- The batch export's `completed_full` (14,729) **mixes FULL and QUICK**; real FULL is 6,865. Findings doc corrected (revision note).
- `template_id` carries the neutralization as a suffix (`<template>_<NEUTRALIZATION>`); fields and settings are recoverable from `primary_field_id` and `settings_json`.
- Server row counts at export time: DEDUP_SKIPPED 326, RESULTS_UNOBSERVED 815, QUEUED 152, SUBMITTED 162 (not exported).
