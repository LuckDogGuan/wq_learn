# WorldQuant BRAIN Research Context & Domain Language

This file defines the canonical domain terms across `wq_research_v2/`, `docs/整理与研究/`, and any future local GUI or assistant workflows.

## Canonical Terms

- **Formal Alpha Submission**: Calling `POST /alphas/{id}/submit`. Permanently prohibited for all automated scripts and agents; always performed manually by the user on the BRAIN platform.
- **Alpha Pre-Submission Check**: Calling read-only `GET /alphas/{id}/check` and `GET /alphas/{id}/correlations/prod` to evaluate readiness without submitting. Never shorten to "submit".
- **Alpha Labeling**: Offline/local classification (`RA`, `PPA`, `ATOM`, `GATE4_CANDIDATE_FOR_MANUAL_REVIEW`).
- **Remote Rename Application**: Calling `PATCH /alphas/{id}` (`set_alpha_properties`) to update name/tags/description. Disabled by default; requires explicit per-action user confirmation.
- **WorldQuant Credential**: The BRAIN platform account secret stored in `Password/config.yaml` (gitignored) or environment variables `WQ_USERNAME` / `WQ_PASSWORD`. Never log, display, or commit.
- **Valid Completed Alpha (4,000/day metric)**: A unique `(normalized_expression, full_settings)` `FULL`-mode simulation on `Delay = 1` returning a valid `alpha_id` and finite `Sharpe`, `Fitness`, `Turnover`, and `Margin`, attributed to its first confirmed `America/New_York` (EST 00:00) platform date.
- **Quick Screened Alpha**: A `QUICK`-mode (`visualization=false`) simulation tracked separately from `Valid Completed`.
- **STOP_EARLY / FAST_DEMOTED**: Budget-protection early stop (e.g., Stage-0 24–40 probe or flat-PnL kill), distinct from formal 200-sample `SCOPE_BLACKLISTED`.
- **RESULTS_UNOBSERVED**: Terminal state after 1 read-only reconciliation attempt following `429 / 5xx / timeout / missing ID`; never resend blindly and never count in the 200-sample denominator.
