# Phase 1 status (2026-11-09)

Read `docs/paper/prereg.md` first; this file says what exists and what to do next.

## What exists

| Piece | Where | State |
|---|---|---|
| Ticker mapping | `data/mappings/tickers.csv` | 34 IDX tickers: 12 banks, 11 palm oil, 11 media |
| Event set | `data/events/events.csv` | 24 events, 2022-04-22 to 2025-09-26, two sources each |
| Pre-registration | `docs/paper/prereg.md` | Registered at commit `ba4db0fa9d9cf8ab82199db791d32f4823dd28a0`, pushed |
| Connection measures | `src/influence/connections/` | Built: `data/processed/connection_measures.parquet` (816 firm-events) |
| Event-study engine | `src/influence/events/` | Runs end to end on synthetic prices |
| Tests | `tests/` | 51 passing |
| Research notes | `docs/research/2026-11-09/` | Agents' working files, with what is unverified marked |

Graph after this phase: 186 nodes, 374 edges, 0 rejected.


## What you run locally

```
pip install -e ".[dev,prices]"
python -m influence.events.prices download     # all 34 tickers + ^JKSE from 2019
python -m influence.events.prices report
python -m influence.events.run                 # -> data/processed/results/
```

`docs/RUNNING.md` section 5 has the full sequence, including the controls file
(`data/mappings/fundamentals.csv`) to fill from annual reports.

**Before you run the download, decide on the items under "Decide first" below.** Once
prices are on your disk the registered files cannot change.

## What the registered design can and cannot show

- **Two events are in the confirmatory test:** the announcement of the Danantara launch
  date (2025-02-13, five state banks treated) and the first Constitutional Court signal
  on deputy ministers as commissioners (2025-07-17, three banks treated). Both are bank
  events. Every other signed event is robustness or exploration.
- **The Danantara launch (2025-02-24) is robustness only.** It keeps your sign. It is
  flagged anticipated because the president announced the date on 2025-02-13 and the law
  passed on 2025-02-04, and the build notes send scheduled events to robustness. The
  2025-02-13 announcement carries the same sign and is the unanticipated version.
- **Power is low.** A simulation on synthetic prices puts the smallest detectable gap at
  about 3.9 percentage points of three-day abnormal return, and the clustered test met
  p < 0.05 in 6% of runs with a true 2-point gap and 30% with an 8-point gap. With two
  event clusters the registered decision rule will almost never say "holds".
- **H1 (people ties) and H3 (palm policy) cannot be tested in Phase 1.** The graph has
  one palm group with any tie and one or two clusters per party. Those events need board
  data for all 34 firms, which is Module B work.

## Decided 2026-11-13

1. **Primary specification: B, event-by-sector fixed effects**, with A (event and firm
   fixed effects, as DESIGN.md is written) reported beside it in every table. This is
   what the pre-registration already says (section 7); no amendment needed.
2. **Board rosters will be added before any price is downloaded.** Commissioners and
   directors for the 34 firms, from the 2024 and 2025 annual reports, extracted with page
   citations and checked independently. This changes which events are in the main test,
   so it goes into a pre-registration amendment (section 14) with a new registration
   hash.
3. **The decision rule rests on the placebo.** Wording for the same amendment:

   > A result holds only if the stacked estimate under specification B, window [-1,+1],
   > 0/1 connection (1) has the registered sign under all three return models, and
   > (2) has a placebo p-value below 0.05 under all three. The two-way clustered p-value
   > is reported but plays no part in the decision, because with few event dates it is
   > unreliable.

   With 200 draws the smallest possible placebo p-value is 1/201, so "below 0.05" means
   the real estimate beats at least 191 of the 200 pseudo-dates.

Items 2 and 3 are one amendment, written once the rosters are extracted, so the
registration hash changes once. **Do not download prices until that amendment is
committed and its hash recorded.**

### What is needed for item 2

The 2024 and 2025 annual reports of the 34 tickers in `data/mappings/tickers.csv`, as
text PDFs (not scans), each with its sha256 (`sha256sum *.pdf`). Order: BBRI, BMRI, BBNI,
BRIS first, then palm oil, then media. The same reports give shares outstanding, total
assets and total liabilities for `data/mappings/fundamentals.csv`.

## Open items (also in section 13 of the pre-registration)

- Sources for Golkar's and Gerindra's cabinet posts before October 2024. Until then both
  read as `unknown` before 2024-10-20 and ties to them do not count for 2022-2024 events.
- Aburizal Bakrie's Golkar role after 2014-2016. The Bakrie firms' party tie rests on an
  open-ended seed edge.
- Sourced dates for the 2024-02-14 election and the late-August 2025 protests, so they
  can be listed as events instead of named in notes.
- SCMA's listing date; suspension histories for most tickers.
- An independent check of `data/seed/supplement/` against its sources.
- All dates rest on search-result snippets. Opening the cited pages from your machine
  would raise them to verified.

## Changes to existing behaviour

- `graph._parse_date`: a year-only or month-only **end** date is now the last day of
  that period. Financing edges dated to one year are active for that whole year.
- `build_seed_graph`: also loads `data/seed/supplement/`.
- `coalition_events.csv`: three new columns and 12 baseline rows.
