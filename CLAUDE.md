# CLAUDE.md

Guidance for coding agents working in `C:\Wq\WorldQuant Brain`.

## Active Entrypoints (2026-11-25 Unified Repo)

- **Hard rules & directory map**: Read `AGENTS.md` and `CONTEXT.md` first.
- **Master research plan & live progress**: `docs/整理与研究/00_索引.md` (`00`–`09` + `records/`).
- **Active modular Python engine**: `wq_research_v2/` (`src/wq_research_v2/`, `config/`, `tests/`, `check_env.py`, `README.md`).
- **Frozen legacy reference**: `legacy_core/Core/` (contains hard-protected read-only `runtime_data/` — NEVER delete!) and `legacy_core/pipelines/`.
- **Read-only static reference corpus**: `reference/` (2026Q4 Top100 list + 254 admin original posts + 264 verified Top100 posts — NEVER modify!).
- **Offline WebDataScope snapshot**: `WebDataScope-1.0.6/data/` (gitignored; Stage-0 D1 field screening input).
- **Credentials**: `Password/config.yaml` (gitignored; NEVER print, log, or commit).

## Hard Constraints

1. **D1-Only**: `settings.delay == 1` enforced across all research & simulations. No D0.
2. **Forbidden operators (Decision #3)**: `add` (`+`), `multiply` (`*`), `trade_when` are permanently banned. Use expression-level `min(rank(expr_A), rank(expr_B))` / `reverse(min(...))`.
3. **Zero auto-submission**: Never call `/alphas/{id}/submit`. `set_alpha_properties` requires explicit current user confirmation.
4. **Verification**: Run `python wq_research_v2/check_env.py` and `python -m pytest wq_research_v2/tests -v` after edits.
