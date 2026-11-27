Status: needs-triage
Type: research
Owner: main
Backtest budget: 500-1000 FULL (authorized 2026-11-27 15:31; launch needs one go/no-go after the expression list is generated)
Evidence: paired Stage-1 evidence `[V]`; single-operator effects `[U]` until this runs

# 06 · Template / operator / mutation paired experiment

## Authorization and meaning of PC
Budget 500-1000 FULL granted. PC is the overlap/similarity with other users' submitted alphas; failing to lower it is normal. **PC is recorded descriptively only; it is not a pass/fail criterion here.** Judge by Sharpe, 2Y, Fitness, turnover, Margin and retention versus the literal baseline.

## Design
Findings doc section 3 (variants V0..V6 per field, 70-140 alive fields, 490-980 FULL; optional neutralization side experiment <= 120). Fields come from QUICK cells where any family reached Sharpe >= 0.8 (ASI 49, EUR 54, USA 84, GLB 9), preferring `Alphas=0` free fields (until 2026-12-06) and the category being climbed for the pyramid. Direction taken from the better QUICK side.

## Steps
1. (flash, main reviews) Build a spec generator that emits the V0..V6 expressions per field; validate each with the local AST checker, the Gold operator whitelist, D1 lock, and forbidden-operator rules; record `operator_count` and `nesting_depth`. 0 backtests. Unit-tested.
2. (main) Show the user the expression list and budget once; wait for "go".
3. (main) Queue through the existing runner as a separate low-priority batch family so it never starves the pyramid line (slot caps unchanged: GLB 3, others 4).
4. (main) Analyze with a paired script; write `[有效]`/`[无效]` with coordinates to `OPTIMIZATION_LEDGER.json`.

## Pre-registered rule (draft, user may edit)
Supported in a region: paired mean dSharpe > 0, win rate >= 60%, n >= 30 fields, sign test p < 0.05. Rejected: mean < 0 with the same significance. Otherwise `[U]`.

## Constraints
D1 only; no `+`, `*`, `trade_when`; no noise injection; no `/submit`; 429/5xx/timeout use the one-shot read-only reconcile rule.
