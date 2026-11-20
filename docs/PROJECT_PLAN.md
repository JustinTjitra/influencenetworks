# Project plan: Indonesian political influence network

Last revised 2026-11-20. This is the guiding document. It says what the project is, how
it works, what it will deliver, and the steps to get there, including who does each step.
Details live in the documents it points to; where they disagree, the pre-registration
(`docs/paper/prereg.md`) wins on anything about the event study.

| If you want | Read |
|---|---|
| The rules every session follows | `CLAUDE.md` |
| The empirical design in full | `docs/DESIGN.md`, `docs/paper/prereg.md` |
| What exists today and what is decided | `docs/phase1_status.md` |
| The task list and how the loop runs | `tasks/BOARD.md`, `tasks/README.md` |
| Commands | `docs/RUNNING.md` |
| Sources found by web research | `reports/`, `research_notes/`, `docs/research/` |

## 1. What the project is

A sourced, dated map of documented relationships between Indonesian politicians, parties,
state bodies and listed firms, and an event study that uses the map to answer one
question:

> Do politically connected Indonesian firms gain or lose more value than comparable
> unconnected firms when the political ground shifts?

It follows Fisman (2001), who measured the value of connections to Suharto, and applies
the idea to the transition from Jokowi to Prabowo (2021-2026) and the 2025 restructuring
of state ownership under Danantara. The map records positions, shareholdings, board
seats, family ties and lending. It records no allegation about anyone.

## 2. Deliverables

| # | Deliverable | Done when |
|---|---|---|
| D1 | **Relationship graph**: nodes and edges with source, dates and confidence | Every edge passes the loader; extractions from primary documents have an independent check on file |
| D2 | **Pre-registered event study** (Phase 1: 34 firms; Phase 2: all listed firms) | `results_summary.md` is produced by one command from frozen inputs, and the registered decision rule has been applied mechanically |
| D3 | **Paper** | Draft with the registered tables and figures, limits stated, nulls reported |
| D4 | **Stakeholder Exposure Monitor**: a private Streamlit app, one page per firm and one per sector | Runs behind a password, every number links to its source rows, wording is neutral |
| D5 | **Board interlock and control map** (feeds Phase 2) | Reproducible build from exchange profiles; every person merge reviewed by a human |
| D6 | **Media coverage module** (the original framing; later) | Out of scope until D2 to D4 are done |

## 3. Methodology

### 3.1 The graph
- **Evidence rules** (enforced in `src/influence/schema.py` and `graph.py`): every edge
  has a source (a URL, or `doc:<id>#p<page>` for a registered document with its sha256),
  a source type and a confidence level; annual reports, filings and registries can be
  high, press and NGO data are capped at medium; family ties need medium or better; there
  is no edge type for suspicion or wrongdoing.
- **Time.** Every edge has start and end dates, so `graph.snapshot(date)` returns only
  the relationships in effect that day.
- **Build.** Hand-researched seeds (`data/seed/`) plus extractions from primary
  documents (`data/primary/`, which override seeds) become `data/processed/nodes.csv`
  and `edges.csv`.
- **Checking.** Whoever extracts does not check. A second agent re-reads the cited pages
  and writes a check table. This has caught errors every time it has been used.

### 3.2 Connection measures
For a firm on a date (`src/influence/connections/measures.py`): state shareholding;
board members with a governing-party role, a current government office, a recent former
office, or a family tie to a party chair or minister; owner ties at group level; graph
distance to the state. Party status is itself dated (`coalition.py`), so a party can be
governing, outside or unknown on different days. Each number carries the edges behind it
and the weakest confidence among them. A composite index (first principal component) is
reported with its loadings and never alone.

### 3.3 Events
`data/events/events.csv`: 24 dated political and policy events, each with two sources, a
pre-registered direction argued in one sentence from the hypotheses, the measure it
tests, and flags for "anticipated" and "confounded". An independent agent re-derived
every sign from a neutral description; disagreements became "ambiguous".

### 3.4 Event study
- Daily returns; day 0 is the first trading day on or after the news (the next one for
  news after the close); all windows count trading days on the exchange calendar.
- Three models of the normal return (market, market-adjusted, Dimson for thin trading),
  estimated on days [-250, -30]. Windows [-1,+1] (primary), [0,+2], [0,+5], and [-5,-2]
  as a leakage check.
- Stacked regression of abnormal returns on connection x registered sign. **Primary
  specification: event-by-sector fixed effects** (connected against unconnected firms in
  the same sector on the same day); the firm-fixed-effects version is reported beside it.
- **Inference by placebo:** the same estimate on 200 sets of pseudo-event dates shared
  by all firms. A result holds only if it has the registered sign and beats the placebo
  distribution under all three models (wording to be fixed in amendment 1).

### 3.5 Pre-registration
The event set, signs, models, windows, controls, sample rules and decision rule were
fixed in `docs/paper/prereg.md` before any price was downloaded, and the code refuses to
download prices without the registration hash. Changes before the first download are
logged amendments; after it, nothing registered changes. The events are in the past and
some outcomes are known to the authors, so this fixes the method, not blind predictions.
The document says so.

## 4. Main features of the codebase

| Area | What it does | State |
|---|---|---|
| `influence.schema`, `graph`, `build_seed_graph`, `validate` | Typed, sourced, dated graph; rejects unsourced edges | Built, tested |
| `influence.load_financing` | Bank lending to palm oil groups from Forests & Finance | Built (data under a personal-use licence) |
| `influence.connections` | Party status by date; the seven measures with evidence; per-event tables | Built, tested, registered |
| `influence.events` | Prices (owner's machine), event study, regressions, placebo, plots, one-command runner, power simulation | Built, tested on synthetic prices, registered |
| `influence.intake` | Register documents, validate rosters and fundamentals, find roster pages | Tasks T04 to T08 |
| `influence.interlocks` | Name normalisation, merge review, interlock graph, exchange profile collector and parser | Tasks T10 to T14 |
| `influence.app` | Stakeholder Exposure Monitor | Tasks T15 to T20 |
| `influence.news` | Crawler and entity tagger for the media module | Built, parked |
| `tools/` | Task board, guard against protected-file and price-data changes | T01, T02 done; CI is T03 |

## 5. Where things stand (2026-11-20)

- Graph: 186 nodes, 374 edges, none rejected. Universe: 34 listed firms (12 banks, 11
  palm oil, 11 media). 24 events.
- Pre-registered at commit `ba4db0f`. **No price data has been downloaded or looked at.**
- Two events pass every rule for the main test, both about state banks. A simulation
  puts the smallest detectable gap near 4 percentage points. Phase 1 as it stands is a
  pilot.
- Decided on 2026-11-13: keep event-by-sector effects as primary; add board rosters for
  all 34 firms before any price download; rest the decision rule on the placebo. The
  last two go into one amendment.
- Only one firm (BTN) has a complete, primary-source board roster. This is the binding
  constraint on what Phase 1 can test.

## 6. Plan of action

Who: **You** (the owner; anything that needs your machine, a download, or a decision),
**Loop** (the unattended task loop), **Attended** (a session with you present, for
anything that touches registered files).

### Phase 1a. Guard rails and tooling. Now; Loop
1. Task board tool and guard (T01, T02: done). Continuous integration (T03).
2. Intake tooling so rosters and fundamentals arrive in a checked format (T04 to T08).
3. Annual report checklist with the download links found by research (T09).
4. Neutral-language check (T21).

### Phase 1b. Board rosters and amendment 1. Blocked on you
1. **You:** download the 2024 and 2025 annual reports for the 34 firms as text PDFs,
   using `data/intake/annual_reports.csv` (U01). Order: BBRI, BMRI, BBNI, BRIS, then the
   other banks, palm oil, media. Send them with their sha256 values.
2. **Attended:** for each report, follow `docs/intake/ROSTER_PROTOCOL.md`: register,
   locate pages, transcribe commissioners and directors with page citations, validate,
   independent check. The same reports give shares, assets and liabilities for
   `data/mappings/fundamentals.csv`.
3. **Loop, meanwhile:** draft the amendment text (T24); turn verified research into
   proposed party-status rows, the corrected Bakrie party role and candidate events
   (T25); source-check the supplement edges (T26). All of it stays under `proposals/`.
4. **Attended (U02):** apply the rosters and approved proposals, rebuild graph and
   measures, recompute the main-test subset mechanically, rerun the power simulation,
   independent sign check for any new event, write amendment 1 into the pre-registration,
   record the new registration hash.

### Phase 1c. Prices and results. You, then Attended
1. **You (U03):** `python -m influence.events.prices download`, then
   `python -m influence.events.run`. Send back `data/processed/results/`.
2. **Attended:** read the price coverage report, write up what held and what did not,
   exactly as the decision rule says. A separate session spot-checks 20 abnormal returns
   by hand.

### Phase 1d. Monitor v1. Loop builds; you deploy
1. Data layer, exposure profile, event timeline, lenders (T15 to T18). None of this
   needs prices.
2. Firm page with password gate, then sector page (T19, T20).
3. **You (U05):** deploy privately on Streamlit Community Cloud with a password. Before
   that: confirm no raw Forests & Finance rows and no personal data beyond public filings
   are in the repository the deploy pulls from, or keep the lenders table switched off.

### Phase 2. All listed firms. After Phase 1 results
1. Exchange profile collector for your machine (T13). **You (U04):** run it for two
   tickers and send one sample response. Then the parser (T14).
2. Name normalisation, merge candidates with a human review file, interlock graph (T10
   to T12). No person is ever merged automatically.
3. Extend tickers, measures and the event study to the whole exchange. This is a new
   pre-registration (Phase 2), written before Phase 2 prices are downloaded.

### Paper. Alongside
1. Bibliography from verified references (T22). Outline written before results (T23).
2. Sections drafted as results arrive; limits and nulls stated in full.

### Later
Media coverage module; Singapore-listed parents as a robustness check; legal review by an
Indonesian lawyer before anything leaves private use; the decision on publication mode;
permission from Rainforest Action Network before any Forests & Finance-derived output is
shown outside private use.

## 7. How the work is organised

- **Small tasks.** Each task in `tasks/` is sized for one commit and names the files it
  may touch and the command that proves it done. A fault traces to one task id in the
  commit subject.
- **Two tiers of model.** A more capable model plans, reviews and solves problems. A
  cheaper model writes the code for one task from its brief. The planner never accepts a
  task on the coder's word: it reruns the acceptance command, the full tests and the
  guard itself.
- **The loop.** A scheduled task starts a fresh session every few hours. It follows
  `tasks/README.md`: pull, test, take the next unblocked task, delegate, verify, commit,
  push, log; at most three tasks a run; pause itself when nothing is unblocked. Its log
  is `tasks/log/<date>.md`.
- **What the loop can never do:** touch a registered file (`tasks/PROTECTED.txt`),
  download or look at prices, merge people automatically, force-push, or commit raw
  documents. `tools/guard.py` and continuous integration enforce the first two
  mechanically. Changes to registered files are written under `proposals/` for you.
- **What needs you:** downloads (annual reports, prices, exchange profiles), approving
  amendments, deployment, and the open decisions below.

## 8. Decisions

**Made:** universe of 34 firms on IDX only; Danantara sign negative for state-owned
firms; event-by-sector effects as primary; rosters before prices; placebo-based decision
rule; private deployment behind a password.

**Open:**
- Publication mode (public, anonymous or private tool). Private until decided.
- Forests & Finance republication permission. Needed before the lenders table is shown
  to anyone else.
- Whether Phase 2 gets its own paper or extends this one.
- Whether older board appointments (2019-2024) are added as events; needs older reports.

## 9. Risks

| Risk | What limits it |
|---|---|
| Too few treated firms and events to detect anything | Rosters for all 34 firms (Phase 1b); Phase 2; power stated before results |
| A date or tie is wrong | Two sources per event; independent checks; pages still to be opened from your machine; evidence tier reported with every result |
| The loop breaks something while you are away | One task per commit, tests and guard before every push, continuous integration, protected paths, self-pausing schedule |
| The design drifts after results are seen | Pre-registration, amendment log, mechanical results summary |
| Legal exposure (defamation under the ITE Law and KUHP; personal data under UU PDP) | Sourced relationships only, neutral wording, private repository and app, lawyer review before any release |
| Scope creep (this is the fourth framing) | D6 is parked; new work enters only as a task on the board |

## 10. Sources

Web research is kept with the repository so a later session can see what was found and
what was not:
- `reports/Influence network project sources.md`: annual-report locations for the 34
  firms, sourced party and cabinet facts, dates for events not yet listed, the exchange's
  profile endpoint, and the verified literature list.
- `research_notes/Influence network project sources/`: the working notes behind it.
- `docs/research/2026-11-09/`: the evidence trail for the registered event set.

All of it was gathered from search results. The cloud workspace cannot open pages, so
nothing has been read in full; each note says so, and anything unverified is labelled.
