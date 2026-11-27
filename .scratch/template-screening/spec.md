# Template & operator screening

Status: in-progress · Created: 2026-11-27 · Findings: `docs/整理与研究/records/rules/TEMPLATE_SCREENING_20261127.md`

## Problem

Most templates and operators in the current pipeline are only ordinary; a small subset is effective. Template sources are the 王哥 skill and Admin posts, some of which are public and likely over-used (crowded) or over-fitted. We must not use a template merely because it exists: screen it, modify it when needed, and verify that earlier experience still holds before reusing it.

## What we already know

See the findings doc, section 1. Short version: dataset choice dominates (5 of 75 datasets give 92.8% of Stage-3 hits); generic Stage-1 packs are indistinguishable once dataset and settings are matched `[V]`; per-template and per-operator evidence is missing because the exported ledger is batch-level.

## Rules for every ticket here

- Backtest budget defaults to `0`; tickets needing FULL sims or SSH say so and stay `needs-info` until authorized in the current conversation.
- Never blacklist an Operator (AGENTS.md); demote a template-in-context instead.
- Matched comparisons only: same region, universe, dataset, settings. Refinement batches (`S3-*`, `PC*-*`) are never template evidence.
- Subagents: `dsh-opencode-go/deepseek-v4.1-flash`, probe first, max 4 rounds then discard (ADR-0001). Briefs must be self-contained.
- Not wired into the runner: nothing here changes what the daemon queues until a ticket says so and the user approves.

## Tickets

| # | Ticket | Status |
| --- | --- | --- |
| 01 | Export task-level template rows (read-only) | resolved |
| 02 | Template register file + schema test | ready-for-agent |
| 03 | Matched pack audit script + tests (batch level) | resolved |
| 04 | Operator-in-context screening (task level) | needs-triage (unblocked; superseded in part by 06) |
| 05 | Crowding measurement (PC by template/source) | needs-triage (low priority: PC is descriptive only) |
| 06 | Template / operator / mutation paired experiment, 500-1000 FULL | needs-triage (authorized; launch needs one go/no-go) |
| 07 | Experience-reuse audit (ledger + IMP rules) | ready-for-agent |
| 08 | Public template catalog dedupe and source tagging | ready-for-agent |
| 09 | Spec generator for the paired experiment | ready-for-agent |

## Priority (user, 2026-11-27)

Mainline is the pyramid ("点塔"): once a category has more than 5 submittable alphas, move to other categories. These tickets are side work for idle time, except template/operator validation (06, 09), which is the core. Do not displace pyramid runs; use `Alphas=0` fields until 2026-12-06 where possible.
