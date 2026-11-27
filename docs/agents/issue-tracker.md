# Issue tracker: Local Markdown

Issues and specs for this repo live as markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- The spec is `.scratch/<feature-slug>/spec.md`
- Implementation issues are one file per ticket at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`, never a single combined tickets file
- Triage state is recorded as a `Status:` line near the top of each issue file (see `triage-labels.md` for the role strings)
- Comments and conversation history append to the bottom of the file under a `## Comments` heading

## Repo-specific rules

- `.scratch/` is tracked by git (the repo `.gitignore` only ignores `scratch/`, not `.scratch/`). Keep files small; no data dumps, credentials, or raw logs.
- Every ticket carries an `Evidence:` line using the tags `[V]` verified / `[R]` reported-not-rechecked / `[C]` conditional / `[U]` unverified (see `GLOSSARY.md`).
- Every ticket states its **backtest budget** (default `0`) and its **owner** (`main` = main agent, `flash` = DSH flash subagent, `human`).
- A ticket that needs new backtests, platform writes, or remote (SSH) access is `needs-info` until the user authorizes it in the current conversation.
- The standing queue index is `docs/agents/TODO_20261127.md`; it links to feature directories here instead of duplicating their tickets.

## When a skill says "publish to the issue tracker"

Create a new file under `.scratch/<feature-slug>/` (creating the directory if needed).

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the issue number directly.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a file with one **child** file per ticket.

- **Map**: `.scratch/<effort>/map.md` (the Notes / Decisions-so-far / Fog body).
- **Child ticket**: `.scratch/<effort>/issues/NN-<slug>.md`, numbered from `01`, with the question in the body. A `Type:` line records the ticket type (`research`/`prototype`/`grilling`/`task`); a `Status:` line records `claimed`/`resolved`.
- **Blocking**: a `Blocked by: NN, NN` line near the top. A ticket is unblocked when every file it lists is `resolved`.
- **Frontier**: scan `.scratch/<effort>/issues/` for files that are open, unblocked, and unclaimed; first by number wins.
- **Claim**: set `Status: claimed` and save before any work.
- **Resolve**: append the answer under an `## Answer` heading, set `Status: resolved`, then append a context pointer (gist + link) to the map's Decisions-so-far in `map.md`.
