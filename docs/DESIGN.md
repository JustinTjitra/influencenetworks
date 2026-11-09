# Design: Political Connections, Stakeholder Shocks and Firm Value in Indonesia

Version 1, 2026-11-09. Supersedes the media-bias framing in `HANDOFF.md` section 1 as the
project's primary goal. Everything else in `HANDOFF.md` (data rules, environment limits,
fact-check corrections) still applies. `HANDOFF_MODULES.md` Module B (board interlocks)
is now a feeder for this design; Module A (stock promotion) is a separate project.

Repo: https://github.com/JustinTjitra/influencenetworks (private).

---

## 1. Purpose

Two outputs from one codebase:

1. **The paper.** Do politically connected Indonesian firms gain or lose more value than
   comparable unconnected firms when the political ground shifts? A modern replication
   and extension of Fisman (1998), "Estimating the Value of Political Connections"
   (AER), which used Indonesian firms and Suharto health rumours. We use the 2021-2026
   Jokowi-to-Prabowo transition and the 2025 state-ownership restructuring (Danantara).
2. **The monitor.** A Streamlit application, the Stakeholder Exposure Monitor, that shows
   for any firm in scope its documented stakeholder network, the dated shocks it has
   lived through, and how its stock has historically responded to each shock type. Built
   for an investor or a public-affairs team, not for a journalist.

Course alignment: MGMT 2150 (map stakeholder power and relationships; model how political
developments affect value; mobilize support), STAT 4220/4300 (the empirical method),
LGST 2050 (the governance context). Concentration: Statistics + IVSB (SOGO).

## 2. Research question and hypotheses

**Question.** Conditional on sector and size, does a firm's connection to the governing
coalition change its abnormal return around events that strengthen or weaken that
coalition, and around sector policy shocks?

Pre-registered directions (write these down before computing any return):

- **H1 (coalition strength).** Events that strengthen the governing coalition raise
  connected firms' abnormal returns relative to unconnected peers; events that weaken
  it lower them.
- **H2 (ownership vs. people).** Connection through state ownership (Danantara/government
  stake) and connection through people (board members with party or ministry ties) have
  different sensitivities. We expect ownership ties to matter more for events about
  state-asset governance (Danantara, BP BUMN) and people ties to matter more for
  cabinet and party events.
- **H3 (policy shocks).** For sector policy shocks (export bans, biodiesel mandates,
  plantation seizures), connected firms are less negatively affected by adverse policy
  and more positively affected by favourable policy than unconnected peers.
- **H0 to take seriously.** In a market where state ownership is pervasive and
  liquidity is thin, connection may be priced in and show no event sensitivity.
  A null is a publishable result if the design is clean.

## 3. Scope

- **Universe.** IDX-listed firms. Phase 1: banks and palm oil groups already in the
  graph (about 30 listed tickers). Phase 2: all IDX, once Module B profile collection
  gives boards and shareholders for every listed company.
- **Window.** 2021-01-01 to 2026-12-31 for events; prices from 2019 for estimation
  windows.
- **Not in scope.** Causal claims about corruption or favouritism. Private companies
  (no prices). Intraday effects (no free intraday data for IDX).

## 4. Connection measures

All measures are computed from the graph at the event date with `graph.snapshot(date)`,
so a board member who left in March does not count in April. Each has a source chain
back to a filing, registry or dated news item.

| Measure | Definition | Source edges | Type |
|---|---|---|---|
| `state_own` | Share held by Republic of Indonesia, Danantara, Danantara Asset Management, or an SOE holding | `owns`, `controls` with `pct` | continuous 0-1 |
| `board_party` | Count of current commissioners/directors with a `party_role` edge | `board_seat` x `party_role` | count |
| `board_office` | Count of current board members holding a concurrent government post (`held_office` with no end date) | `board_seat` x `held_office` | count |
| `board_former` | Count of board members who held office in the last 5 years | same, ended | count |
| `board_family` | Count of board members with a `family_of` edge to a party chair, minister or president | `board_seat` x `family_of` | count |
| `group_conn` | Owner's business group has an owner with any of the above | `member_of_group`, `controls` | binary |
| `dist_gov` | Shortest undirected path from firm to any `govt_body` or `party` node | all | integer |

Composite: a connection index as the first principal component of the standardised
measures, reported alongside each component. Never report the composite alone.

**Which coalition.** Party ties are mapped to "governing coalition" or "outside" at each
date using `data/seed/coalition_events.csv`. NasDem is the key case: in coalition under
Jokowi, nominated Anies (2022-10-03), supported Prabowo after 2024 without ministers.
Code this as a time-varying party-level variable, not a fixed label.

## 5. Event set

Stored in `data/events/events.csv` with columns:
`event_id, date, type, subtype, description, expected_sign_connected, scope (market|sector),
sector, anticipation_flag, source_url, confidence, notes`.

Rules:
- Every event has a source and a date confirmed from a primary or two secondary sources.
- `expected_sign_connected` is filled before any return is computed and never changed
  afterwards; if a direction is debatable, record "ambiguous" and exclude from the main
  tests (keep for exploration).
- `anticipation_flag` marks events that were widely expected (scheduled elections, bills
  with long debate). Main tests use unanticipated events; anticipated ones are robustness.
- Confounded dates (two events within the window) are flagged and tested separately.

Candidate events to verify and classify (dates from the project's fact-checks where
noted; verify the rest):

| Date | Event | Type | Expected sign for connected |
|---|---|---|---|
| 2022-04-28 to 2022-05-23 | CPO export ban announced and lifted | sector policy (palm) | negative at ban for all; test whether connected lose less |
| 2022-10-03 | NasDem nominates Anies Baswedan | coalition | negative for NasDem-tied, neutral others |
| 2024-02-14 | General election (Prabowo win called by quick counts) | coalition | anticipated; positive for Gerindra/Prabowo-tied |
| 2024-10-20 | Prabowo inaugurated; cabinet announced 2024-10-21 | coalition | anticipated; by party of each new minister |
| 2025-02-24 | Danantara launched | state governance | positive for state_own firms? (ambiguous: write the argument before testing) |
| 2025-03-22 | Bank share transfers to Danantara operating holding (verified) | state governance | state banks treated; other banks control |
| 2025-08-28 | Constitutional Court bars deputy ministers from SOE boards, 2-year transition (verified) | governance | negative for firms with `board_office` > 0 |
| 2025-09-17 | Cabinet reshuffle (Erick Thohir to Sports; verified in seeds) | coalition | by connection to moved ministers |
| 2025-10-08 | SOE ministry becomes BP BUMN; Dony Oskaria head (verified) | state governance | state_own firms |
| 2025 (dates needed) | Agrinas plantation seizures incl. Duta Palma | sector policy (palm) | negative for targeted groups; test spillover to connected vs unconnected |
| various | B35/B40 biodiesel mandate announcements | sector policy (palm) | positive for palm; test heterogeneity |
| various | EUDR adoption and delays | sector policy (palm) | negative/positive for exporters |
| various | Presidential health or security rumours (Fisman's instrument) | coalition | if any occur: negative for connected |

Aim for 15-25 clean events. Fewer, well-classified events beat a long noisy list.

## 6. Empirical design

### 6.1 Returns
- Daily adjusted close and volume via `yfinance` (`TICKER.JK`), stored raw per download
  date in `data/raw/prices/`. Keep delisted tickers; note gaps.
- Market model: `R_it = a_i + b_i R_mt + e_it`, estimated on trading days [-250, -30]
  relative to each event. Market = `^JKSE`. Thin trading is common in small caps, so
  report three versions: market model, market-adjusted (`R_it - R_mt`), and Dimson
  (lead/lag betas). Results must agree in sign to count.
- Abnormal returns `AR_it`, cumulative over windows [-1,+1], [0,+2], [0,+5]; pre-window
  [-5,-2] as a leakage check. Abnormal volume as `log(V_it / mean V_i[-60,-11])`.

### 6.2 Cross-section
For each event `e`:
`CAR_ie = g_e + d_e * Connection_i(t_e) + X_i' k + sector FE + u_ie`
with `X` = log market cap, leverage, turnover (liquidity), SOE dummy. `d_e` is the
object of interest; its sign is compared to `expected_sign_connected`.

Stacked panel across events of the same type:
`CAR_ie = g_e + d * (Connection_i x Sign_e) + X_i' k + sector FE + firm FE + u_ie`
with standard errors clustered by firm and by event date. This is the headline table.

### 6.3 Identification cautions
- Connected firms are larger and more often state-owned. Always compare within sector,
  always include size and the SOE dummy, and report state-owned and privately connected
  firms separately (H2).
- Placebo: re-run with 200 random non-event dates per firm; the true `d` should sit in
  the tails.
- Anticipation: anticipated events (elections, inauguration) in robustness only.
- Multiple testing: report the stacked estimate as the main result, individual events
  as a forest plot.
- Confounders: flag any event within 5 trading days of another market-wide event.

### 6.4 Sample size reality
Phase 1 has about 30 tickers. That is enough for the stacked panel across 15-25 events
(hundreds of firm-events) but not for per-event cross-sections with many controls.
Phase 2 (all IDX, about 900 tickers, from Module B) is what makes per-event estimates
credible. Plan the paper's claims accordingly: Phase 1 = sector case study; Phase 2 =
market-wide test.

## 7. The Stakeholder Exposure Monitor

Streamlit app, one page per firm plus a sector overview.

**Firm page**
1. *Stakeholder map.* The firm's network within 3 hops, grouped by stakeholder type
   (owners, lenders, boards and their political roles, regulators, media groups with
   shared owners). Every node and edge shows its source on hover. Powered by
   `graph.linked_entities` and `snapshot` with a date slider.
2. *Exposure profile.* The connection measures from section 4 as of the selected date,
   with the edges that produce each number listed underneath. Labelled "exposure", not
   "risk". No composite score on this page.
3. *Event timeline.* Events from `events.csv` that apply to the firm (market-wide and
   its sector), with the firm's CAR for each, and the sector median for comparison.
4. *Measured sensitivity.* Average CAR by event type for this firm vs. its sector, with
   confidence intervals; shown only where at least 5 events exist.
5. *Lenders.* Forests & Finance credit edges (palm oil groups) with year and amount.

**Sector page**
- Connection measures across firms (table and distribution).
- Stacked-panel estimates by event type (the paper's headline table, live).
- Event forest plot.

**Design rules**
- Facts with sources only. The app never says "risky", "captured", "corrupt" or
  "favoured". It says "holds", "sits on", "lent", "returned".
- Every number clicks through to the rows that produced it.
- A visible "report an error" link (mailto or form) on every page.
- Private deployment (Streamlit Community Cloud with password, or local) until legal
  review. Forests & Finance data requires their permission before any public release.

## 8. Code changes

```
src/influence/connections/   measures.py (section 4), coalition.py (time-varying party status)
src/influence/events/        prices.py (yfinance download, cache), eventstudy.py (AR/CAR,
                             three models), crosssection.py (regressions, placebo), plots.py
src/influence/app/           streamlit_app.py, pages/firm.py, pages/sector.py, components/
data/events/events.csv       the event set (section 5)
data/mappings/tickers.csv    node_id -> IDX ticker(s); several groups map to several tickers
tests/                       measures on a toy graph; CAR arithmetic on a toy panel;
                             placebo machinery; coalition status at dates
docs/paper/                  outline.md, then sections as they are written
```

Existing code reused without change: `schema.py`, `graph.py`, `build_seed_graph.py`,
`validate.py`, `load_financing.py`. The news crawler and tagger stay; they become the
salience channel later (not in v1).

Relationship to the module handoff:
- Module B (IDX profiles, boards, shareholders, entity resolution) is **Phase 2's data**.
  Build its steps 1-4 as specified there.
- Module A (stock promotion) is unrelated to this design and should live in its own
  repo if pursued.

## 9. Milestones

1. **Event set and pre-registration** (1 week). `events.csv` complete with sources and
   signs; `docs/paper/prereg.md` committed before any price is downloaded.
2. **Prices and event-study engine** (1 week). Three AR models, tests on toy data,
   placebo machinery.
3. **Connection measures** (1 week). Section 4 implemented over the existing graph with
   `snapshot`; table of measures for the Phase 1 universe at each event date.
4. **Phase 1 results** (1 week). Stacked panel for banks and palm oil; forest plot;
   write-up of what holds and what doesn't.
5. **Monitor v1** (1-2 weeks). Firm and sector pages on Phase 1 data.
6. **Phase 2** (ongoing). Module B profile collection; rerun on all IDX.

Independent check before milestones 4 and 5: a separate session re-derives the event
classifications and spot-checks 20 CARs by hand.

## 10. Risks

- **Thin trading and small N in Phase 1.** Mitigated by three AR models, stacking, and
  honest scoping of claims.
- **Direction ambiguity.** Many events have no obvious sign for connected firms
  (Danantara's launch could be read either way). Pre-registration plus an "ambiguous"
  bucket keeps this honest.
- **Connection measurement error.** Party ties come from news (medium confidence);
  ownership from filings (high). Report results by confidence tier.
- **Legal.** The monitor displays real people's board seats and party roles. All of it is
  from public filings and reputable press, time-bound and sourced, with no judgement
  language. Still: lawyer review before anything leaves private deployment.
- **Scope creep.** This is the fourth framing of the project. Milestone 4 is the point
  where a result exists. Protect it.

## 11. Open decisions for the user

- Phase 1 universe: confirm the ticker list (banks and palm oil listed entities in the
  graph) or widen to include the media groups' listed entities (MNCN, BMTR, EMTK, etc.).
- Which Danantara-launch sign to pre-register, or to leave it ambiguous.
- Whether to add Erick Thohir-era SOE board appointments (2019-2024) as historical
  events, which would need older annual reports.
- Deployment: local only, or password-protected Streamlit Cloud.
