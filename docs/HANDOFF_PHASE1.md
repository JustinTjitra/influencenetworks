# Handoff: Phase 1 build (event set, connection measures, event-study engine)

Written 2026-11-09 for a fresh Claude Code session. Read in this order:
1. `docs/HANDOFF.md` (project context, data rules, environment limits, past fact-check
   corrections). Section 1's media-bias framing is superseded by `DESIGN.md`; the rest
   stands.
2. `docs/DESIGN.md` (what we are building and why; the empirical design).
3. This file (what to build now, with the user's decisions filled in).

Repo: https://github.com/JustinTjitra/influencenetworks. Pushes from a session now work.
Commit after each task; small commits with the source of every fact in the message or
the data row.

## Decisions already made by the user (do not reopen)

1. **Universe is widened.** Phase 1 = IDX-listed entities of the banks, palm oil groups
   AND media groups already in the graph. IDX only; Singapore-listed parents (Golden
   Agri, Wilmar, First Resources, Bumitama) are a later robustness check with `^STI`,
   not part of Phase 1.
2. **Danantara's launch (2025-02-24) gets a pre-registered sign**, not the ambiguous
   bucket. **Confirmed by the user on 2026-11-09: negative for firms with
   `state_own` > 0**, on the reasoning that the launch moved dividend rights and
   control from the Finance Ministry to a new fund with less parliamentary oversight,
   which minority shareholders should price as a governance cost. Record the
   alternative (positive: cheaper capital, protection) in `prereg.md` as the rejected
   reading, so the choice is auditable. This is fixed; do not ask again.
3. **Monitor deployment: password-protected Streamlit Community Cloud.** Not part of
   this handoff's tasks, but it means no secrets, no raw Forests & Finance rows, and no
   personal data beyond public filings may ever be committed, because the deploy pulls
   from the repo.

## The one hard rule for this phase

**No price data is downloaded, read or looked at until `docs/paper/prereg.md` is
committed and pushed.** The event set, the signs, the models, the windows, the controls
and the exclusion rules are all fixed first. If anyone (including the user) asks to
"just check one stock" before that commit exists, say no and point to this paragraph.
Pre-registration is the paper's main credibility claim.

## Task 1: Event set and pre-registration

### 1a. Ticker mapping: `data/mappings/tickers.csv`
Columns: `node_id, ticker, exchange, listed_name, sector_bucket (bank|palm|media),
listing_date, delisting_date, source_url, note`.
- One row per listed entity; a business group may map to several tickers (Salim ->
  SIMP, LSIP; Sinar Mas -> SMAR; MNC -> MNCN, BMTR, MSIN; Emtek -> EMTK, SCMA; etc.).
- Only entities that are nodes in the graph or direct subsidiaries of them with a
  sourced `owns`/`member_of_group` edge. If a subsidiary edge is missing, add it to the
  seed with a source before adding the ticker.
- Expect 35-45 tickers. Verify each ticker exists and its listing date (IDX company
  profile or a reliable aggregator; two sources where cheap).

### 1b. Events: `data/events/events.csv`
Columns (from DESIGN.md section 5):
`event_id, date, type (coalition|state_governance|sector_policy|governance), subtype,
description, expected_sign_connected (+|-|0|ambiguous), connection_measure_tested
(state_own|board_party|board_office|board_family|group_conn|all), scope (market|sector),
sector (bank|palm|media|all), anticipation_flag (0|1), confounder_flag (0|1),
source_url_1, source_url_2, confidence, notes`.

Rules:
- 15-25 events, 2021-01-01 to 2026-11-01. Start from the candidate table in DESIGN.md
  section 5; verify every date with two sources (WebSearch/WebFetch work from the
  workspace). Dates already verified by earlier fact-checks are marked in that table.
- `expected_sign_connected` and `connection_measure_tested` are filled from theory,
  written in a sentence in `notes`, before anything else. An event whose sign you
  cannot argue in one sentence is `ambiguous`.
- Scheduled events (election day, inauguration, announced AGMs) get
  `anticipation_flag = 1`. These are robustness only.
- Set `confounder_flag = 1` when another listed event falls within 5 trading days.
- Add the sector-policy events for media too (e.g. broadcasting/digital regulation,
  KPI decisions) if they can be dated and sourced; otherwise media firms enter through
  coalition and governance events only.

### 1c. `docs/paper/prereg.md`
Must contain, in this order:
1. Hypotheses H0-H3 exactly as in DESIGN.md section 2, plus the Danantara sign and its
   rejected alternative.
2. Universe: the ticker list by reference to `tickers.csv` at a commit hash.
3. Event set: by reference to `events.csv` at a commit hash; the main-test subset
   (unanticipated, unconfounded, non-ambiguous) listed explicitly.
4. Connection measures: definitions from DESIGN.md section 4; the snapshot date is the
   trading day before the event.
5. Models: market model on [-250, -30]; market-adjusted; Dimson with one lead and one
   lag. Market index `^JKSE`. Minimum 120 valid estimation days or the firm-event is
   dropped.
6. Windows: [-1,+1] primary; [0,+2] and [0,+5] secondary; [-5,-2] leakage check.
7. Cross-section and stacked panel exactly as DESIGN.md 6.2, with controls (log market
   cap, leverage, turnover, SOE dummy) and clustering (firm and event date).
8. Placebo: 200 random non-event dates per firm, same pipeline.
9. Decision rules: a result "holds" only if the stacked estimate has the pre-registered
   sign at p < 0.05 under all three AR models and survives the placebo.
10. What will be reported regardless of result (all of the above, nulls included).

Commit `prereg.md` with the two CSVs, push, and record the commit hash at the top of
the file in a follow-up commit. Tell the user it is done and give the price-download
command.

## Task 2: Connection measures (`src/influence/connections/`)

- `coalition.py`: `party_status(party_id, date) -> "governing" | "outside" | "unknown"`
  from `data/seed/coalition_events.csv`. Time-varying. NasDem is the test case
  (governing under Jokowi until the Anies nomination 2022-10-03 made it ambiguous;
  outside through 2024; supporting Prabowo without ministers from Oct 2024; treat
  "supporting without ministers" as `governing` but flag it as a sensitivity).
- `measures.py`: the seven measures from DESIGN.md section 4, each a function
  `(graph, firm_node_id, date) -> value`, using `graph.snapshot(date)` and
  `linked_entities`. Firm node = the ticker's node (or its parent group node when the
  listed entity itself is not a node; record which was used).
  - `state_own`: sum of `pct` on `owns`/`controls` edges from government-type nodes
    (`gov_*`, `co_danantara_am`) into the firm or its parent, capped at 1.
  - `board_*`: count board members (active `board_seat` edges) with the relevant
    active edge to a party (status "governing") or govt body.
  - `group_conn`: any owner/controller of the firm's business group has an active
    party_role/held_office/family_of edge to a governing-party figure.
  - `dist_gov`: shortest undirected path length to any `party` (governing) or
    `govt_body` node; `inf` if none.
  - Composite: first principal component over the standardised measures across the
    universe at each date; report loadings.
- `build_measures.py`: writes `data/processed/connection_measures.parquet` with one row
  per (ticker, event_date) for all events in `events.csv`, plus a column
  `confidence_tier` = lowest confidence among the edges that produced a non-zero
  measure (so results can be split by evidence quality).
- Tests on a toy graph: a board member who leaves before the date does not count; a
  party's status flips at the right date; `dist_gov` through an owner chain; PCA runs
  on a 5-firm toy.

Known data gaps to record, not to fill silently: several palm groups have no board
data yet (only BTN has primary-source boards); `board_*` measures for them will be
zero-by-absence, not zero-by-evidence. Add a `coverage` column (fraction of the
firm's board with any sourced edge) and carry it into the regressions as a control
and as a sample split.

## Task 3: Event-study engine (`src/influence/events/`)

Build and test on synthetic data only. The real download happens on the user's
machine after Task 1 is committed.

- `prices.py`: `download(tickers, start, end)` via `yfinance` into
  `data/raw/prices/<download_date>/<ticker>.parquet` (gitignored), plus `load()` that
  returns a tidy panel (date, ticker, adj_close, volume) and a coverage report
  (missing days, zero-volume days, delisted gaps). Include `^JKSE`.
- `eventstudy.py`:
  - `estimate(panel, ticker, event_date, model)` returning alpha/beta (or nothing for
    market-adjusted), estimation-window stats, and the valid-day count.
  - `abnormal_returns(...)` and `car(window)` for the three models.
  - `abnormal_volume(...)` as in DESIGN.md 6.1.
  - Trading-day arithmetic must use the exchange calendar derived from `^JKSE` dates,
    not calendar days.
- `crosssection.py`: per-event OLS with sector FE and the controls; stacked panel with
  firm and event FE and two-way clustering (use `linearmodels` or `statsmodels` with
  cluster-robust SE; document which); `placebo(n=200, seed=...)`.
- `plots.py`: forest plot of per-event `d_e` with CIs; stacked estimates by event type;
  placebo distribution with the true estimate marked.
- `run.py`: one command from raw prices + `events.csv` + `connection_measures.parquet`
  to `data/processed/results/` (tables as CSV, figures as PNG/SVG) and a
  `results_summary.md` that applies the decision rules from `prereg.md` mechanically.
- Tests: CAR on a toy panel with known betas reproduces hand-computed numbers; the
  three models agree when there is no thin trading; the stacked estimator recovers a
  planted effect of known size; the placebo returns a centred distribution when no
  effect is planted; trading-day windows skip holidays correctly.

## Environment reminders

- Workspace has WebSearch/WebFetch but no shell internet. `yfinance`, IDX and Streamlit
  Cloud all run on the user's machine. Write scripts so they run there with one command
  (see `docs/RUNNING.md` style).
- Everything that identifies a person must keep its source and dates; nothing judgemental
  in code, comments, column names or docs ("connected", "holds", "sits on", not
  "captured", "cronies").
- Have an independent agent re-derive the event signs from the `notes` sentences before
  Task 1 is committed; disagreements are resolved by moving the event to `ambiguous`.

## Done when

- `tickers.csv`, `events.csv`, `prereg.md` committed and pushed, hash recorded.
- `connection_measures.parquet` builds from the current graph; tests pass.
- `python -m influence.events.run` works end to end on a synthetic price panel; tests pass.
- A short `docs/phase1_status.md` saying what exists, what the user must run locally
  (price download command), and the Danantara sign as confirmed.
