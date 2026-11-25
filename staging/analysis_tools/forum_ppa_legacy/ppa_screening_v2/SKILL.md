---
name: ppa-screening
description: 通用 WorldQuant Brain PPA Alpha 只读筛选、字段 Dataset 归属、PPAC 检查、阶段计数和审计输出。用于 PPA 范围 JSON、ppa_alpha_standard.json、Alpha 筛选、Power Pool 主题、forbidden datasets、neutralization 枚举和逐步剩余数量任务。
---

# PPA Screening

Use Python first. The canonical implementation is in this same folder; do not create a second screening implementation.

Use the installed `wqb.WQBSession` from `skills/wqbmcp` for platform access. It supplies the permanent session and request helpers; do not hand-write authentication, raw HTTP requests, or duplicate pagination. Use `filter_alphas`, `locate_alpha`, `locate_field`, and read-only `check` only.

## Fixed files

- `ppa_screen.py`: screening, field lineage, text/JSON/Markdown outputs.
- `test_ppa_screen.py`: targeted tests.
- `config/ppa_scope_format.json`: scope shape.
- `PPA 范围/ppa_forbidden_fields.json`: dynamic PV1/MODEL110 forbidden-field rules; the selected theme JSON points to it with `forbidden_field_rules_file`.
- `build_ppa_excel.py`: optional Excel export using installed Python `openpyxl`; no Node runtime is required.
- `agents/openai.yaml`: UI metadata.
- `Password/config.yaml`: read in memory only; never print or persist credentials.
- `代码/ppa_submit/` is reference-only and must not be modified.

Basic run:

```powershell
python 代码/ppa_screening_v2/ppa_screen.py `
  --scope "PPA 范围\theme.json" `
  --output "总结\ppa_screening_run"
```

One-line live run:

```powershell
python 代码\ppa_screening_v2\ppa_screen.py --credentials Password\config.yaml --scope "PPA 范围\20260727_0809_GLB_Power_Pool_Aug26_Rules.json" --output "代码\ppa_screening_v2\output\ppa_screening_live"
```

API-only audit:

```powershell
python 代码/ppa_screening_v2/ppa_screen.py `
  --query-only `
  --output "总结/ppa_api_query"
```

Excel is optional:

```powershell
python 代码/ppa_screening_v2/build_ppa_excel.py `
  总结/ppa_screening_run/screening_records.json `
  总结/ppa_screening_run/ppa_screening_detailed.xlsx
```

## Fixed rule precedence

Use platform Alpha detail, field metadata, and live checks first; then the selected PPA scope JSON; then the general PPA standard. On conflict, return `RULE_CONFLICT`; never guess or relax a gate. `theme_name` is a report label only. Filtering uses `duration` and `core_requirements`.

## Fixed linear workflow

Start counting after loading the selected scope JSON. Write human-facing counts to `filter_steps.txt`, not a count JSON.

1. Load the selected scope JSON.
2. Intersect the default recent-one-month window with `duration`; honor explicit `--start-date` and `--end-date`. Interpret `Date Created` in `America/New_York` (the platform EST/EDT display timezone) with an inclusive start and exclusive end. Do not restore two-month compatibility.
3. Query `REGULAR`, `UNSUBMITTED`, `EQUITY`, exact `region`, `delay`, `universe`, the platform-list strict `sharpe > sharpe_min` boundary, and the date window.
4. Read each Alpha with `locate_alpha`.
5. Resolve expression identifiers with read-only `locate_field`; record field ID, Dataset ID/name, type, and source. Example: `close -> pv1`.
6. Filter allowed neutralization and inclusive turnover.
7. Exclude platform errors and error-result checks.
8. Exclude forbidden Datasets. A forbidden Dataset is allowed only when every resolved field using it is an explicit support field and evidence is complete.
9. Check PPAC: `MATCHES_THEMES`, `PURE_POWER_POOL_THEME`, `POWER_POOL_CORRELATION`, `POWER_POOL_DESCRIPTION_LENGTH`, and `POWER_POOL_DESCRIPTION_FORMAT`. Apply `power_pool_self_correlation_max`; missing numeric evidence is `PENDING`.
10. Check `unique_data_fields_max_excluding_support_fields` and `operators_max`.
11. Classify as `PPA_PASS`, `FAIL`, `PENDING`, `RULE_CONFLICT`, or `EXCLUDED`.

Every stage records `input`, `remaining`, `excluded`, and `pending`. Output every candidate surviving PPAC, including later `FAIL` and `PENDING` rows; do not output only `PPA_PASS`.
The exact `filter_alphas` contract is saved under `screening_records.json.api_query`.
For a query-only run it is saved as `api_query.json`, with raw candidate rows in `api_candidates.json`.

## Fixed neutralization mapping

Normalize labels before comparison:

| Scope label | Platform enum |
|---|---|
| `RAM` | `REVERSION_AND_MOMENTUM` |
| `SLOW` / `Slow Factors` | `SLOW_FACTORS` |
| `SLOW_AND_FAST` / `Slow + Fast Factors` | `SLOW_AND_FAST_FACTORS` |
| `Fast Factors` | `FAST_FACTORS` |
| `Crowding Factors` | `CROWDING_FACTORS` |

`NONE` plus expression-level `group_neutralize` is not an allowed theme neutralization.

## Default PPA gates

Use the selected standard when it supplies another value. Otherwise:

- Sharpe `>= 1.0`.
- Turnover `0.01 <= turnover <= 0.70`.
- Operators `<= 8`.
- Non-support unique fields `<= 3`.
- PPAC self-correlation `<= 0.5`; missing value is `PENDING`.
- Support fields: `country`, `industry`, `subindustry`, `currency`, `market`, `sector`, `exchange`.

Do not add Fitness, Prod Correlation, unrelated Self-Correlation, or IS Ladder gates unless the selected scope or user requests them.

## Flexible inputs and outputs

Vary only:

- `--scope`, `--start-date`, `--end-date`, and `--output`.
- Requested text, Markdown, JSON audit, or Excel columns/sheets.
- Output directory and naming.

Standard outputs:

- `filter_steps.txt`: simple stage counts.
- `screening_records.json`: detailed Alpha, resolved field lineage, checks, rules, and classification.
- `final_table.md`: all factors surviving PPAC with ID, expression, Sharpe, Fitness, Turnover, PPAC, and status.
- `.xlsx` when requested: `概览`, `全部候选`, `PPAC后全部因子`, `检查明细`, `字段归属`, `规则与来源`.

Missing, incomplete, timed-out, 429, or 5xx platform evidence remains `PENDING` where possible. Never claim live PPA success from fixtures or static checks.

## Safety and verification

This workflow is read-only. Never call `simulate`, `submit`, or `patch_properties`, and never modify Alpha attributes.

Run:

```powershell
python -m py_compile 代码/ppa_screening_v2/ppa_screen.py 代码/ppa_screening_v2/test_ppa_screen.py
python 代码/ppa_screening_v2/test_ppa_screen.py
```

Then run targeted JSON/whitespace checks and `git diff --check`. If Excel is produced, re-import it, inspect key ranges, scan formula errors, and render every sheet once.
