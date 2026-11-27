Status: ready-for-agent
Type: research
Owner: main (judgment task; not for flash)
Backtest budget: 0
Evidence: n/a (this ticket produces the evidence labels)

# 07 · Experience-reuse audit

## Task
Use the `worldquant-experience-reuse` skill in `consult` mode (read-only; do not run `refresh`, do not edit the skill). Classify each of: the 17 `effective_cases` and 14 `ineffective_cases` in `docs/agents/OPTIMIZATION_LEDGER.json`, and rules IMP-01..IMP-08 in `REUSABLE_D1_RA_EXPERIENCE_PLAYBOOK.md`.

## Output
`docs/整理与研究/records/rules/EXPERIENCE_REUSE_AUDIT_20261127.md` with one row per item: `结论` (apply / adapt / retest / reject / unknown), `适用坐标`, `反例与代价`, `置信度`, `最小验证`. Group near-duplicate parameter sweeps as one evidence family. Preserve disagreements; do not delete counterexamples.

## Acceptance
Every row carries `[V]/[R]/[C]/[U]`. Items that imply a rule change are listed separately and are **not** applied.
