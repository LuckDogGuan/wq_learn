# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the label strings used in `Status:` lines of local tickets (`.scratch/**/issues/*.md`).

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on the user (authorization, budget, decision) |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation or manual platform action |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.

## Not the same vocabulary

These are **ticket** labels. They are unrelated to **Alpha** tags on the BRAIN platform (`Useful`, `SC_PASS`, `PPA_Useful`) and to internal batch markers (`PC_STUCK_DORMANT`, `STALLED_DORMANT_AFTER_3_ROUNDS`, ...). Never apply an Alpha tag to a ticket or a ticket label to an Alpha. Alpha-side vocabulary is defined in `GLOSSARY.md`.
