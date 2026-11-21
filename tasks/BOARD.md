# Task board

Status of every task. Edit with `python tools/taskboard.py set <id> <status>` once that
tool exists. Rules are in `tasks/README.md`; the plan is `docs/PROJECT_PLAN.md`.

| id | title | tier | depends | status |
|---|---|---|---|---|
| T01 | Task board tool | sonnet | - | done |
| T02 | Guard against protected-file and price-data changes | sonnet | - | done |
| T03 | Continuous integration workflow | haiku | T01 T02 | done |
| T04 | Fundamentals file schema and validator | sonnet | - | done |
| T05 | Document registry command | sonnet | - | done |
| T06 | Board roster CSV templates and validator | sonnet | - | done |
| T07 | Locate roster pages in an annual report | sonnet | - | done |
| T08 | Roster extraction protocol | haiku | T05 T06 T07 | done |
| T09 | Annual report manifest | haiku | - | done |
| T10 | Indonesian name normalisation | sonnet | - | done |
| T11 | Person merge candidates and review file | sonnet | T10 | done |
| T12 | Board interlock graph and classification | sonnet | - | done |
| T13 | Exchange profile collector for the owner's machine | sonnet | - | done |
| T14 | Exchange profile parser | sonnet | U04 | blocked:U04 |
| T15 | Monitor data layer | sonnet | - | done |
| T16 | Monitor exposure profile tables | sonnet | T15 | done |
| T17 | Monitor event timeline table | sonnet | T15 | done |
| T18 | Monitor lenders table | sonnet | T15 | done |
| T19 | Monitor firm page | sonnet | T16 T17 T18 | done |
| T20 | Monitor sector page | sonnet | T19 | done |
| T21 | Neutral-language check | haiku | - | todo |
| T22 | Bibliography from the research notes | haiku | - | todo |
| T23 | Paper outline | planner | T22 | todo |
| T24 | Draft of pre-registration amendment 1 | planner | - | todo |
| T25 | Proposed party-status and event rows for amendment 1 | planner | - | todo |
| T26 | Source check of the supplement edges | sonnet | - | todo |
| U01 | Download 2024 and 2025 annual reports for the 34 firms | owner | T09 | blocked:owner |
| U02 | Approve amendment 1 in an attended session | owner | U01 T24 T25 | blocked:owner |
| U03 | Download prices and run the event study locally | owner | U02 | blocked:owner |
| U04 | Save one exchange profile response as a sample | owner | T13 | blocked:owner |
| U05 | Deploy the monitor privately with a password | owner | T20 | blocked:owner |
