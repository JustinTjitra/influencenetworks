# Paper outline

Written 2026-11-21, before any price was downloaded and before any result exists, so
that results cannot shape the story. It follows `docs/paper/prereg.md` (registration
commit `ba4db0fa`); where the two differ, the pre-registration governs. File names under
`data/processed/results/` are those written by `python -m influence.events.run`. Citation
keys refer to `docs/paper/references.bib` and are annotated in `docs/paper/literature.md`.

## 1. Introduction

- The question: conditional on sector and size, does a listed firm's connection to the
  governing coalition change its abnormal return around events that strengthen or weaken
  that coalition, and around sector policy shocks?
- Why Indonesia now: a change of government in October 2024, the transfer of state
  shareholdings to a new fund in 2025, and a court ruling on concurrent posts give dated
  events that bear on ownership ties and on people ties separately.
- What is new: every tie is a dated, sourced edge in a graph, so connection is measured
  on the day before each event; and the event list, signs, models and decision rule were
  fixed before any return was computed.
- What the paper is and is not: a pilot of the method on 34 firms. It reports direction,
  size and placement in a placebo distribution. It is not a powered test.
- Leans on: `fisman2001estimating`, `faccio2006politically`, `johnson2003cronyism`,
  `leuz2006political`, `acemoglu2016value`, `olken2015promises`.

## 2. Setting: Indonesia 2021 to 2026 and Danantara

- The coalition timeline: which parties were in government on which dates, from
  `data/seed/coalition_events.csv`, with the 2024 handover.
- State ownership of listed banks, and the 2025 sequence: postponement, announcement of
  the launch date, launch, transfer of bank shares, and the later change from ministry
  to agency.
- Board members who also hold government office, and the 2025 Constitutional Court
  reasoning and ruling on deputy ministers.
- Sector policy in palm oil and media during the sample, described from the event notes
  only (dates and instruments; no market reaction).
- Uses: `event_sample.csv` (the event list with samples and flags); a timeline figure
  built from `data/events/events.csv`.
- Leans on: `claessens2000separation`, `carney2013changes`, `mobarak2005political`.

## 3. Data

- The graph: node and edge types, and the evidence rules (every relationship has a
  source and dates; family ties need medium or high confidence; no fuzzy name matching;
  relationships are recorded, conduct is not inferred).
- The universe: 34 firms (12 banks, 11 palm oil, 11 media), the mapping of tickers to
  graph nodes, and the firms left out on purpose with the reason for each.
- The event set: 24 events with two sources each, the day-0 rule, and the anticipated,
  confounded and cluster flags; the independent sign check and its 16 "debatable" marks.
- Board roster coverage per firm and date, before and after the roster amendment.
- Uses: `event_sample.csv`, `price_coverage.csv`; a table of graph counts by edge type
  and source kind (from `data/processed/nodes.csv` and `edges.csv`).
- Leans on: `faccio2006politically` (definition of a connected firm), `indonesia1999undang`.

## 4. Measuring connection

- The seven measures as registered (`state_own`, `board_party`, `board_office`,
  `board_former`, `board_family`, `group_conn`, `dist_gov`), each computed on the graph
  snapshot of the last weekday before day 0.
- The tested measure per event and its 0/1 indicator; the scaled value as a secondary
  specification; the composite reported with its loadings and never alone.
- Coverage: a board measure of zero with no roster is zero by absence of data. Results
  are shown for all firms and for firms with coverage above 0.
- Clusters (firms under one controlling person or group count once); a descriptive
  table of the measures by sector on the two main-test dates.
- Uses: `data/processed/connection_measures.parquet`, `connection_event_summary.csv`,
  `connection_pca_loadings.csv` (no prices in any of them).
- Leans on: `faccio2006politically`, `faccio2006political`, `azar2018anticompetitive`,
  `dennis2022common`, `azar2022refutation` (for the ownership-path discussion).

## 5. Empirical design (as registered)

- Normal-return models: market model, market-adjusted, Dimson; estimation window
  [-250, -30]; drop rules for thin trading.
- Windows: primary [-1, +1]; secondary [0, +2] and [0, +5]; leakage [-5, -2]; abnormal
  volume.
- Cross-section per event and the stacked panel; specification B (event-by-sector fixed
  effects) decides, specification A (event and firm effects) is reported beside it, and
  why.
- Controls in priority order, capped by sample size; the fallback set.
- Inference: two-way clustered errors, and the placebo with 200 shared pseudo-dates.
- The decision rule exactly as in force at the time of the price download (section 9 of
  the pre-registration, with amendment 1 if approved), quoted in full.
- Uses: `controls.csv`, `event_sample.csv`.
- Leans on: `mackinlay1997event`, `brown1985using`, `dimson1979risk`,
  `scholes1977estimating`, `kolari2010event`, `boehmer1991event`, `cameron2011robust`.

## 6. Results (placeholders only)

- Table 1, the decision table: every estimate, both p-values and the verdict, for the
  main-test set and its subsets. Source: `decisions.csv`, `results_summary.md`.
- Table 2, stacked estimates: both specifications, three models, four windows, 0/1 and
  scaled connection. Source: `stacked.csv`.
- Figure 1, each event's own estimate with its interval. Source: `per_event.csv`,
  `figures/forest_per_event`.
- Figure 2, the real estimate within the placebo distribution. Source: `placebo.csv`,
  `placebo_draws.csv`, `figures/placebo_main`.
- Figure 3, stacked estimates by event type. Source: `figures/stacked_by_type`.
- The text of this section is written only after the run, from those files, in the
  order above, with nulls reported in full.

## 7. Robustness

- The anticipated, confounded and too-few-clusters sets as separate stacks, labelled as
  robustness. Source: `stacked.csv`.
- The leakage window, the falsification event (no gap expected) and abnormal volume.
  Source: `falsification.csv`, `per_event.csv`.
- Splits: ownership-tie against people-tie events (H2), high-confidence edges against
  the rest, firms with board coverage above 0. Source: `splits.csv`.
- Flagged coalition codings counted as outside government; the per-firm placebo variant.
- Counts of firm-events dropped by each rule. Source: `cars.csv`, `price_coverage.csv`.
- Leans on: `cameron2008bootstrap`, `conley2011inference`, `mackinnon2017wild`,
  `mackinnon2018wild`, `gelbach2013valid`.

## 8. Limits

- **Two events are in the main test** before the roster amendment, both about banks.
  The count after the amendment is whatever the registered rule then produces.
- **Power is low.** The registered simulation puts the smallest detectable gap near four
  percentage points, and with two event dates the clustered test almost never rejects.
- **Dates were verified from search-result snippets**, not from opened pages, unless the
  owner has since opened them; the paper says which.
- **The signs are not blind.** The events are in the past and the authors recall how the
  market moved after several of them (section 11 of the pre-registration).
- Board coverage is partial (a zero can mean "none recorded"); H3 as registered tests
  whether a gap exists, not its direction; three sectors do not stand for the exchange.
- Leans on: `olken2015promises`, `burlig2018improving`.

## 9. Conclusion

- One paragraph per hypothesis saying what the registered test showed, in the words of
  the table below.
- What Phase 2 (all listed firms, with board data) would need in order to be a powered
  test, taken from the power simulation.
- The data and code release, and what cannot be released (licensed lending data).

## What we will say under each outcome

Written now. "Holds" means the decision rule in force at the price download is met.

| Outcome of the main test | What the paper says |
|---|---|
| Holds | "In this pre-registered pilot, firms with the tested tie moved in the registered direction relative to their peers around the main-test events, and the estimate lies in the tail of the placebo distribution; with so few events this is evidence of direction, to be tested at scale in Phase 2." |
| Does not hold, estimate has the registered sign | "The estimate has the registered sign but does not meet the decision rule; given the stated power, the pilot cannot tell a real gap of this size from none, and we report the estimate and its placebo position without further reading." |
| Does not hold, estimate has the opposite sign | "The estimate has the opposite sign to the one registered and does not meet the decision rule; we report it as it is, do not reinterpret the hypothesis after the fact, and note that the rejected alternative reading recorded in the pre-registration predicted this sign." |

In all three cases the abstract leads with the sample size and the power statement, no
result or number about returns enters this file or any section before the run, the paper
makes no claim about any named person's conduct, and anything done differently from the
pre-registration is reported as a deviation with the registered version beside it.
