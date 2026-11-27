# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout: single-context

No monorepo signals were found, so this repo uses one `GLOSSARY.md` at the root and ADRs under `docs/adr/`.

## Before exploring, read these

- **`GLOSSARY.md`** at the repo root.
- **`docs/adr/`**: read ADRs that touch the area you're about to work in.

If any of these files don't exist, proceed silently.

## Use the glossary's vocabulary

When your output names a domain concept (ticket title, hypothesis, test name, ledger entry), use the term as defined in `GLOSSARY.md`. In particular keep the seven layers apart: Dataset, Data Field, Operator, Template, Expression, Simulation Settings, Alpha.

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding.

## Relationship to other sources of truth

`AGENTS.md` holds the hard red lines and wins on conflict. `docs/agents/CORE_STATE.json` and `OPTIMIZATION_LEDGER.json` hold current state and attributed experiments. `GLOSSARY.md` defines words; ADRs record why a rule exists; neither replaces the ledger.
