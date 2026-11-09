# Pre-registration: political connections, stakeholder shocks and firm value in Indonesia (Phase 1)

Registration commit: `ba4db0fa9d9cf8ab82199db791d32f4823dd28a0`

The line above is filled in by a follow-up commit with the hash of the commit that
first added this file together with `data/mappings/tickers.csv`, `data/events/events.csv`
and the analysis code. Every file named here is fixed as of that commit.

**No price data was downloaded, read or looked at before that commit.** The code enforces
this: `influence.events.prices.download` and real runs of `influence.events.run` refuse to
start until the line above holds a commit hash that exists in the repository.

Written 2026-11-09. Design: `docs/DESIGN.md`. Build notes: `docs/HANDOFF_PHASE1.md`.

## 0. What a reader should know before trusting this document

1. **The events are in the past.** They happened between 2022 and 2025 and this document
   was written in November 2026. The authors follow Indonesian markets and remember how
   the market moved after several of them (section 11). Pre-registration here does not
   make the signs blind predictions. What it does fix, before any return is computed, is
   everything a researcher could otherwise tune: the event list, the day-0 rule, the
   models, the windows, the controls, the sample rules and the decision rule.
2. **Phase 1 is small.** Two events pass every rule for the confirmatory test (section 3).
   A simulation on synthetic prices (section 12) puts the smallest detectable gap at about
   4 percentage points of three-day abnormal return, and shows that the registered
   decision rule would almost never be met at that sample size. Phase 1 is a pilot of the
   method. Phase 2 (all IDX firms, with board data) is where the hypotheses can be tested.
3. **Dates were checked from search-result snippets, not from opened pages.** The
   workspace could not open news or government sites on 2026-11-09. Every event has two
   source URLs whose snippets showed the date; none was read in full. Section 13 lists
   what is still unverified.

## 1. Hypotheses

**Question.** Conditional on sector and size, does a firm's connection to the governing
coalition change its abnormal return around events that strengthen or weaken that
coalition, and around sector policy shocks?

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

**The Danantara sign.** Confirmed by the project owner on 2026-11-09: **negative for firms
with `state_own` > 0.** Reasoning: the launch moved dividend rights and control from the
Finance Ministry to a new fund with less parliamentary oversight, which minority
shareholders should price as a governance cost.
*Rejected alternative reading:* positive, on the grounds that the fund gives state-owned
firms cheaper capital and protection. It is recorded here so the choice can be audited.
The same reasoning fixes the sign of the other Danantara events: negative for the date
announcement and the share transfer, positive for the postponement.

**What the sign means.** `expected_sign_connected` is the sign of the gap between
connected and unconnected firms' abnormal returns. Under H3 that gap is positive for
adverse shocks (connected firms lose less) and for favourable ones (they gain more). The
independent check (section 3) pointed out that this makes H3 a test of whether a gap
exists, not of its direction, and that a shock and its reversal (the export ban and its
lifting) cannot both be informative. We keep H3 as the design states it and report that
limit with the results.

## 2. Universe

`data/mappings/tickers.csv` at the registration commit: 34 IDX-listed firms.

- Banks (12): BMRI, BBRI, BBCA, BBNI, BBTN, BRIS, BNGA, NISP, BNLI, BDMN, BNII, PNBN.
- Palm oil (11): SMAR, SIMP, LSIP, AALI, SGRO, TAPG, DSNG, BWPT, ANJT, UNSP, SSMS.
- Media (11): BMTR, MNCN, MSIN, IPTV, EMTK, SCMA, VIVA, MDIA, TMPO, ABBA, MARI.

Each ticker maps to a node of the graph, or to a company node with a sourced
`member_of_group` edge to one (`data/seed/supplement/listed_entities_*.csv`). A firm is in
an event's sample if it was listed on day 0. Singapore-listed parents are not in Phase 1.

Left out on purpose: CEKA (Wilmar's IDX entity is an oil processor, not a plantation
company, and a ban on exports moves processors and growers in opposite directions), BHIT
(the MNC holding company, with large non-media businesses), INDF and INRU (not palm oil
companies).

## 3. Event set

`data/events/events.csv` at the registration commit: 24 events. The sign and the
tested measure were written from the hypotheses, with the argument in the `notes` column,
before anything else. An independent agent then derived a sign for each event from a
neutral description that gave no direction; where it disagreed, the event is `ambiguous`.

| Date | Event | Type | Sign | Measure tested | Sample | Anticipated | Confounded | Treated firms / clusters | Main test | Independent check |
|---|---|---|---|---|---|---|---|---|---|---|
| 2022-04-22 | `ev_cpo_export_ban` | sector_policy | + | all | palm | no | no | 0 / 0 | no | +  |
| 2022-05-19 | `ev_cpo_export_ban_lifted` | sector_policy | + | all | palm | no | no | 0 / 0 | no | + (debatable) |
| 2022-07-16 | `ev_cpo_levy_zero` | sector_policy | + | all | palm | no | no | 0 / 0 | no | + (debatable) |
| 2022-10-03 | `ev_nasdem_anies` | coalition | - | all (party_nasdem) | market | no | no | 0 / 0 | no | - (debatable) |
| 2022-11-02 | `ev_aso_jabodetabek` | sector_policy | + | all | media | yes | no | 6 / 2 | no | + (debatable) |
| 2023-08-13 | `ev_golkar_pan_prabowo` | coalition | + | all (party_golkar) | market | no | no | 4 / 2 | no | +  |
| 2024-02-20 | `ev_publisher_rights` | sector_policy | + | all | media | no | yes | 6 / 2 | no | + (debatable) |
| 2024-08-11 | `ev_airlangga_resigns` | coalition | ambiguous | all (party_golkar) | market | no | yes | 4 / 2 | no | ambiguous (debatable) |
| 2024-08-15 | `ev_perindo_joins_prabowo` | coalition | + | all (party_perindo) | market | no | yes | 4 / 1 | no | +  |
| 2024-10-02 | `ev_eudr_delay_proposed` | sector_policy | 0 | all | palm | no | no | 0 / 0 | no | 0  |
| 2024-10-20 | `ev_inauguration_cabinet` | coalition | + | all | market | yes | yes | 11 / 7 | no | + (debatable) |
| 2024-11-06 | `ev_danantara_postponed` | state_governance | + | state_own | market | no | yes | 5 / 5 | no | +  |
| 2025-02-13 | `ev_danantara_date_announced` | state_governance | - | state_own | market | no | no | 5 / 5 | yes | -  |
| 2025-02-24 | `ev_danantara_launch` | state_governance | - | state_own | market | yes | yes | 5 / 5 | no | -  |
| 2025-03-03 | `ev_kopdes_himbara` | sector_policy | ambiguous | state_own | bank | no | yes | 5 / 5 | no | ambiguous (debatable) |
| 2025-03-24 | `ev_bank_shares_to_danantara` | state_governance | - | state_own | market | yes | yes | 5 / 5 | no | - (debatable) |
| 2025-05-14 | `ev_cpo_levy_10pct` | sector_policy | + | all | palm | no | no | 1 / 1 | no | + (debatable) |
| 2025-07-09 | `ev_agrinas_handover` | sector_policy | + | all | palm | no | no | 1 / 1 | no | +  |
| 2025-07-17 | `ev_mk_wamen_signal` | governance | - | board_office | market | no | no | 3 / 3 | yes | - (debatable) |
| 2025-08-28 | `ev_mk_wamen_ruling` | governance | - | board_office | market | no | yes | 3 / 3 | no | - (debatable) |
| 2025-09-08 | `ev_reshuffle_finance` | coalition | ambiguous | all | market | no | yes | 14 / 8 | no | ambiguous (debatable) |
| 2025-09-10 | `ev_state_cash_placement` | sector_policy | + | state_own | bank | no | yes | 5 / 5 | no | + (debatable) |
| 2025-09-17 | `ev_erick_thohir_moved` | coalition | ambiguous | group_conn | market | no | yes | 9 / 3 | no | - (debatable) |
| 2025-09-26 | `ev_soe_ministry_to_agency` | state_governance | ambiguous | state_own | market | no | no | 5 / 5 | no | ambiguous (debatable) |

Rules that produced the flags:

- **Day 0** is the first trading day on or after the event date; for news after the close
  (`after_close` = 1) it is the first trading day strictly after it.
- **Anticipated** (`anticipation_flag` = 1): the event was scheduled or legislated in
  advance. Robustness only. This includes the Danantara launch of 2025-02-24, which the
  president announced on 2025-02-13 and parliament legislated on 2025-02-04. Its
  unanticipated counterpart, the announcement of the launch date, is in the main test
  with the same sign.
- **Confounded** (`confounder_flag` = 1): another listed event with an overlapping sample
  has its day 0 within five trading days, or the notes name a major shock in that window
  that is not listed. Robustness only.
- **Enough clusters:** at least three treated and three untreated clusters in the event's
  sample, where firms controlled by the same person or belonging to the same group are one
  cluster. Computed by `influence.connections.build_measures` from the graph; no prices.
- **Main test** = not anticipated, not confounded, sign `+` or `-`, enough clusters.

**The main-test subset is exactly:**

- `ev_danantara_date_announced` (2025-02-13): President announces that Danantara will be launched on 24 February 2025. Measure `state_own`, sign -. Treated firms: BBNI BBRI BBTN BMRI BRIS.
- `ev_mk_wamen_signal` (2025-07-17): Constitutional Court ruling 21/PUU-XXIII/2025 states in its reasoning that the ban on concurrent posts also covers deputy ministers. Measure `board_office`, sign -. Treated firms: BBRI BBTN BMRI.

Every other signed event is reported as robustness or exploration, labelled as such.
`ev_eudr_delay_proposed` (sign `0`) is a falsification event: no gap is expected.

Outcome of the independent check: it agreed with every registered sign except two.
`ev_kopdes_himbara` was registered `-` and derived `ambiguous`; it is now `ambiguous`.
`ev_erick_thohir_moved` was already `ambiguous` (the check derived `-`). The check marked
16 of the 24 signs as debatable, including `ev_mk_wamen_signal`, whose sign rests on the
assumption that office-holding board members are valuable to the firm.

## 4. Connection measures

Definitions are those of DESIGN.md section 4 as implemented in
`src/influence/connections/measures.py` (the module docstring is the authoritative text).
Measures are computed on `graph.snapshot(d)`, where d is the last weekday before day 0.

| Measure | Definition |
|---|---|
| `state_own` | Sum of `pct` on active `owns`/`controls` edges into the firm from the Republic of Indonesia, Danantara or its holding company, plus the `pct` held by shareholders that are themselves majority state-owned. Between 0 and 1. |
| `board_party` | Board members (active `board_seat` on the firm or its group) with an active `party_role` in a governing party. |
| `board_office` | Board members with an active `held_office` at a government body. |
| `board_former` | Board members with no current office whose last office ended within five years. |
| `board_family` | Board members with a `family_of` edge to a governing party's general chair, a sitting minister or the president. |
| `group_conn` | 1 if a person who owns or controls the firm or its group has a governing-party role, a government office, or a family tie to someone who has either. |
| `dist_gov` | Shortest undirected path from the firm to a government body or governing party; `inf` if none. |

- **Governing party** on a date comes from `data/seed/coalition_events.csv` through
  `connections.coalition.party_status`. Flagged codings (a party that supports the
  government without ministers) count as governing. The measures can be rebuilt with
  those codings counted as outside (`build(..., count_flagged=False)`); the main-test
  events use ownership and office measures, which this does not touch.
- **Events about one party** (`target_party` filled) count ties to that party only,
  whatever its status.
- **Tested measure.** Each event names one measure. The main specification uses its 0/1
  indicator (measure > 0). For `all` the indicator is 1 if any of the six tie measures is
  positive. A secondary specification uses the measure's value, scaled within event.
- **Composite.** The first principal component of the standardised measures across the
  universe on each date, reported with its loadings and never alone.
- **Coverage.** The share of a firm's two board organs (commissioners, directors) for
  which a complete primary-source roster covers the date
  (`data/mappings/board_rosters.csv`). At registration it is 0 for 99% of firm-events:
  only Bank Tabungan Negara's commissioners are covered. A board measure of zero with
  coverage 0 is zero by absence of data. Results are reported for all firms and for
  firms with coverage above 0.
- **Graph freeze.** The measures are those built from the graph at the registration
  commit (`data/processed/connection_measures.parquet`). Adding board data before prices
  are downloaded requires an amendment (section 14); after that, it is a deviation.

## 5. Models of the normal return

Simple daily returns on adjusted close. Estimation window: trading days [-250, -30]
relative to day 0. Market index: `^JKSE`. Three models, all reported:

1. Market model: R_it = a_i + b_i R_mt + e_it.
2. Market-adjusted: AR_it = R_it - R_mt.
3. Dimson: R_it regressed on the market return at t-1, t and t+1; the abnormal return uses
   the summed beta, AR_it = R_it - a_i - (b1 + b2 + b3) R_mt.

A firm-event is dropped if the estimation window has fewer than 120 days on which the
stock has a return and traded. It is dropped from a window if any return in that window is
missing or if the stock did not trade on any day of it. The calendar is the set of dates
on which `^JKSE` has a price.

## 6. Windows

- Primary: [-1, +1].
- Secondary: [0, +2] and [0, +5].
- Leakage check: [-5, -2].
- Abnormal volume: mean over the window of log(V_t / mean V over [-60, -11]).

## 7. Cross-section and stacked panel

Per event e, as DESIGN.md 6.2:

    CAR_ie = g_e + d_e * Conn_i(t_e) + X_i'k + sector FE + u_ie

Stacked across events:

    CAR_ie = g_e + d * (Conn_i(t_e) x Sign_e) + X_ie'k + fixed effects + u_ie

with standard errors clustered by firm and by event date. d > 0 means connected firms
moved in the registered direction. Two sets of fixed effects are always reported:

- **A. Event and firm fixed effects**, as DESIGN.md 6.2 is written.
- **B. Event-by-sector fixed effects**, no firm effects.

**B is the specification the decision rule uses.** This is a change from DESIGN.md, made
before any price was seen, for a reason the data forced: with firm effects d is identified
only from within-firm variation in Conn x Sign. In the main-test set both signs are
negative and state ownership does not change, so A would be identified only by the
difference between the two measures for the same firm, which is not the comparison the
hypotheses are about. For a single event, or a set with one sign, A is not identified at
all. A is reported beside B in every table.

Controls, in priority order: log market capitalisation, SOE dummy, leverage, turnover
(definitions in `src/influence/events/controls.py`). Three rules, fixed now:

1. A regression keeps as many controls, in that order, as leave at least 10 identifying
   firm-events per coefficient (identifying = in an event-by-sector cell where the
   connection varies). The two-event main test has 24, so it carries one control.
2. A control collinear with the connection is dropped, not the connection. The SOE dummy
   is the treatment itself in a state-ownership event.
3. Shares outstanding, assets and liabilities come from `data/mappings/fundamentals.csv`,
   collected from annual reports after registration (it holds no prices). If any primary
   control is missing for more than 20% of firm-events, the fallback set is used: log mean
   daily traded value, SOE dummy, share of zero-volume days.

Per-event standard errors are HC3. Stacked standard errors are two-way clustered with t
inference on min(clusters) - 1 degrees of freedom; when the two-way variance is not
positive the larger one-way clustered standard error is used and the table says so. With
fewer than about ten clusters on either dimension these p-values are unreliable, which is
why the placebo is part of the decision rule.

Splits reported for the main test: H2 (ownership-tie events against people-tie events),
treated ties resting only on high-confidence edges against the rest, and firms with board
coverage above 0.

## 8. Placebo

200 draws, seed 20261109. In each draw every main-test event is moved to a random
trading day that has a full estimation window and is more than 10 trading days from every
listed event. **All firms share the pseudo-date within a draw.** Connection measures,
signs, sample and controls stay as at the real event; only the returns change. The stacked
estimate is recomputed for each draw. The placebo p-value is
(1 + number of draws with |d_b| >= |d|) / (201).

The build notes ask for random dates per firm. Shared dates are used because firms in an
event share a date and their returns are correlated that day; separate dates per firm
would remove that correlation and make the null distribution too narrow. The per-firm
variant is in the code (`mode="per_firm"`) and is not part of the decision.

## 9. Decision rule

A result **holds** only if, for the stacked estimate under specification B, window
[-1, +1], 0/1 connection:

1. d > 0 (the registered direction) under all three return models, and
2. p < 0.05 (two-sided, two-way clustered) under all three, and
3. the placebo p-value is below 0.05 under all three.

It is applied to the main-test set as a whole and to its subsets by event type and by H2
family. Anything that fails any part is reported as "does not hold". `results_summary.md`
is written by `python -m influence.events.run` and applies this rule mechanically.

## 10. Reported whatever the result

- The decision table, with every estimate, both p-values and the verdict.
- Both specifications and all three models, for all four windows with the 0/1
  connection and for the primary window with the scaled connection.
- Every event's own estimate with its interval (forest plot), main test or not.
- The anticipated, confounded and too-few-clusters sets as separate robustness stacks.
- The leakage window, the falsification event, abnormal volume.
- The splits of section 7, the composite index with its loadings.
- Counts of firm-events dropped by each rule, and the price coverage report per ticker.
- Null results in full.

## 11. What the authors already knew

- State-bank shares and the index were weak in February and March 2025, around the
  Danantara events. The Danantara sign was confirmed by the project owner with that
  general knowledge.
- The export ban of April 2022 and its lifting were widely covered, including sector
  share moves.
- A source in the seed data reports in its headline how the shares of two firms linked to
  Erick Thohir moved after his 2025-09-17 change of post. That event is `ambiguous` for
  this reason among others.
- The independent checker reported vague memories of price moves for five events and
  stated that none was used.
- Research agents were instructed not to search for or report prices or market
  reactions. Some cited URLs contain share-related wording in their address, including
  the seed source just mentioned, which is also the source of two group-membership edges.

No return, price series or abnormal return was computed, downloaded or read by anyone
working on this registration.

## 12. Power, from simulation

`python -m influence.events.power` plants a known gap on the main-test events in
simulated prices (daily idiosyncratic volatility 1.2% to 2.8%) and repeats 200 times.
At registration, with the one control the sample carries:

| Planted gap | Mean estimate | Spread (sd) | Share meeting clustered p < 0.05 |
|---|---|---|---|
| 0 pp | -0.02 pp | 1.39 pp | 1% |
| 2 pp | +2.00 pp | 1.39 pp | 6% |
| 8 pp | n/a | n/a | 30% |

The estimator is unbiased, and the smallest gap detectable with 80% power from that
spread is about 3.9 pp. The clustered test almost never rejects with two event clusters,
whatever the effect. So in Phase 1 the main test can show the direction and size of the
gap and its place in the placebo distribution; "holds" under section 9 is unlikely even
if the effect is real. This is stated now so that a null in Phase 1 is not later read as
evidence of no effect.

## 13. Known gaps at registration

Recorded, not filled silently. Closing any of them before prices are downloaded is an
amendment (section 14).

- **Party status before October 2024.** No sourced row yet for Golkar or Gerindra before
  2024-10-20, so both read as `unknown` earlier and ties to them do not count in the
  governing-party measures for 2022 to 2024 events. Events about one named party are not
  affected.
- **Aburizal Bakrie's Golkar role.** The graph has an open-ended "general chairman" edge
  from 2009. Sources differ on when it ended (2014 to 2016) and his later role was not
  verified. The Bakrie firms' ties to Golkar rest on this edge.
- **Board data.** Only Bank Tabungan Negara has a primary-source roster. Board measures
  for other firms come from a few news-sourced seats.
- **Events not listed for lack of a sourced date:** the general election of 2024-02-14,
  the nationwide protests of late August 2025, Presidential Instruction 1/2025, the first
  Agrinas handover. The first two are named in the notes of the events they confound.
- **Tickers:** SCMA's listing date is unverified (it predates the sample by two decades).
  Suspension histories were checked for only some tickers; the price coverage report
  will show them.
- **Times of day** are unconfirmed for several events (see each event's notes). The
  [-1, +1] window covers a one-day error.
- **Checks still owed:** an independent comparison of the supplement edges against their
  sources (the rule for extractions in HANDOFF.md).

## 14. Amendments

Before the first price download, a change to sections 1 to 9 or to the registered files
is made by a new commit that adds an entry here and a new registration hash. After the
first download nothing in sections 1 to 9 changes; anything done differently is reported
in the paper as a deviation, with the registered version beside it.

| Date | Commit | Change |
|---|---|---|
| | | none |

## 15. Changes from DESIGN.md and HANDOFF_PHASE1.md made at registration

1. Decision specification is event-by-sector fixed effects; the firm-effects
   specification is reported beside it (section 7).
2. Placebo uses shared pseudo-dates (section 8).
3. `events.csv` has two extra columns, `target_party` and `after_close`; `tickers.csv` has
   `source_url_2`.
4. The confounder flag requires overlapping samples and can also be set for a named shock
   that is not listed (section 3).
5. A cluster rule decides which events have enough treated firms (section 3).
6. Controls are capped by sample size and ordered by priority; a fallback set is defined
   (section 7).
7. The Danantara launch keeps the confirmed sign and is flagged anticipated under the
   build notes' own rule; the date announcement of 2025-02-13 is added (section 3).
8. `coverage` is defined by registered rosters (section 4).
9. The graph loader now reads a year-only or month-only end date as the last day of that
   period. Before, a financing edge dated 2015 to 2015 was active for one day.
10. Universe is 34 tickers, not 35 to 45 (section 2).
