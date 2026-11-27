# GLOSSARY

Domain terms for this WorldQuant BRAIN D1 research repo. `AGENTS.md` is authoritative for red lines; this file only fixes vocabulary. Official definitions: `docs/official_guides/BRAIN_OFFICIAL_GLOSSARY.md`.

## The seven layers (never conflate)

- **Dataset** — a vendor/model data package on the platform (e.g. `model25`, `model31`).
- **Data Field** — one column inside a Dataset (`MATRIX` or `VECTOR`).
- **Operator** — a platform function (`rank`, `group_zscore`, ...). Never blacklisted as such; a usage *context* can be demoted.
- **Template** — an expression skeleton with field/number slots (`group_zscore(ts_mean({x}, 22), subindustry)`), with a named source (王哥 skill, Admin post, Top100 advisor, internal).
- **Expression** — a Template instantiated with concrete fields and numbers.
- **Simulation Settings** — region, universe, delay, neutralization, decay, truncation, mode.
- **Alpha** — a simulated Expression + Settings with an Alpha ID and results.

## Pipeline vocabulary

- **RA** — Regular Alpha track. **PPA** — Power Pool Alpha track. Kept separate.
- **Stage 1–4** — wide screen → light tuning → single-axis fix → correlation and delivery.
- **Stage-1 pack** — the fixed set of templates (each plus its `reverse`) run together in one 8-sim batch.
- **Refinement batch** — a Stage-3-style hill-climb from an already-good parent (`S3-*`, `PC*-*`). Not comparable with Stage-1 packs.
- **Controlled-variable round** — one round that changes 1–2 parameters of a frozen parent.
- **Dual-branch** — `min(rank(A), rank(B))` / `reverse(min(...))`; the only allowed fusion form.
- **Mutation** — a deliberate edit of a public or crowded template before reuse (new grouping, smoothing, nonlinearity, neutralization, or secondary field).

## Gates and tags

- **SC / PC** — self-correlation against own OS alphas / production correlation. SC < 0.65 and PC < 0.70 are the delivery gates.
- **Margin (bp)** — tie-breaker: higher Margin wins when everything else passes.
- **`Useful`** — all gates pass and pool-orthogonal; **`SC_PASS`** — RA 0-FAIL and SC pass but PC not; **`PPA_Useful`** — the independent PPA line.
- **`PENDING_RECONCILE` / `RESULTS_UNOBSERVED`** — platform answer unknown. Neither is pass nor fail.
- **`PC_STUCK_DORMANT`, `STALLED_DORMANT_AFTER_3_ROUNDS`** — shelved, not deleted; may be woken by a new method.

## Evidence tags (use in tickets, ledger, reports)

- **`[V]`** verified this session (code read, replayed, measured). **`[R]`** reported but not rechecked. **`[C]`** true only inside stated coordinates (Region/Universe/dataset/template/window). **`[U]`** unverified hypothesis. Nothing in quant is absolute: always write the coordinates next to a lesson.

## Template lifecycle (see `docs/整理与研究/records/rules/TEMPLATE_SCREENING_20261127.md`)

`UNTESTED → PROBATION → KEEP | MODIFY | RETIRE`, plus the flag `CROWDED` (public template with high PC). Status needs matched evidence, not a single hit.
