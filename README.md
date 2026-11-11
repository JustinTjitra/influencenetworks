# Indonesian Influence Network

A sourced, time-bound map of **documented** relationships between Indonesian
politicians, parties, state bodies and listed firms (banks, palm oil groups and media
groups), and an event study that uses it to measure what political connections are
worth to those firms.

Private research project. Nothing here is published, and nothing here alleges
wrongdoing: the graph records positions, shareholdings, board seats, family ties and
lending, each with its source and dates.

## The question

Do politically connected Indonesian firms gain or lose more value than comparable
unconnected firms when the political ground shifts?

It is a modern replication and extension of Fisman (2001), "Estimating the Value of
Political Connections", which used Indonesian firms and rumours about Suharto's health.
This version uses the 2021-2026 transition from Jokowi to Prabowo and the 2025
restructuring of state ownership under Danantara. Connections are measured two ways,
through state ownership and through people (board members with party, ministry or family
ties), because the two may respond to different kinds of event.

## Three outputs from one codebase

1. **The paper.** An event study across 24 dated political and policy events, with the
   design pre-registered before any price was downloaded.
2. **The Stakeholder Exposure Monitor** (planned). A private Streamlit app showing, for
   each firm, its documented network, the shocks it has lived through and how its stock
   responded. Written for an investor or a public-affairs team.
3. **Media coverage** (later module, the project's original framing). Do outlets cover
   firms and politicians inside their owner's network differently from those outside it?

## Where it stands

**Phase 1 is registered and waiting for prices.** The pre-registration
(`docs/paper/prereg.md`) was fixed at commit `66209bc`, before any price data was
downloaded, read or looked at. The code refuses to download prices without that hash.

| | |
|---|---|
| Universe | 34 IDX-listed firms: 12 banks, 11 palm oil, 11 media |
| Events | 24, from the 2022 palm oil export ban to the 2025 SOE ministry change |
| Main test | 2 events that are unanticipated, unconfounded and have enough treated firms: the Danantara launch-date announcement (2025-02-13) and the first Constitutional Court signal on deputy ministers as SOE commissioners (2025-07-17) |
| Graph | 186 nodes, 374 sourced edges, 0 rejected |
| Tests | 51 passing |

Phase 1 is a pilot. A simulation on synthetic prices puts the smallest detectable gap at
about 4 percentage points of three-day abnormal return, so a null result here is weak
evidence. The hypotheses about people ties and palm oil policy need board data for every
firm, which Phase 2 adds by scaling to all IDX companies.

`docs/phase1_status.md` has the details, the open items and the decisions to take
before prices are downloaded.

## How it works

```
seed CSVs + primary documents ──► validated graph (nodes.csv, edges.csv)
                                        │
                     graph.snapshot(date): only links in effect that day
                                        │
tickers.csv + events.csv ──► connection measures per firm and event
                                        │
daily prices (^JKSE calendar) ──► abnormal returns: market, market-adjusted, Dimson
                                        │
                     stacked regressions, placebo dates, decision rule
                                        │
                              results_summary.md
```

Connection measures (`src/influence/connections/measures.py`): state shareholding,
board members with a governing-party role, a current government office, a recent former
office or a family tie to a party chair or minister; owner ties at group level; and
graph distance to the state. Party status is time-varying, so NasDem counts as governing
under Jokowi until it nominated Anies, outside through 2024, and governing again under
Prabowo.

## Data rules

Enforced in `src/influence/schema.py` and `graph.py`. Keep them.

1. **Every edge needs a source**: an `http(s)` URL, or `doc:<doc_id>#p<page>` pointing at
   a document registered in `data/raw/documents.csv` with its sha256. The loader rejects
   anything else.
2. **Relationships, not accusations.** There is no edge type for suspicion or wrongdoing.
   A conviction is recorded only with the court record itself.
3. **Family ties need medium or high confidence.**
4. **Confidence follows the source.** Annual reports, exchange filings, registries and a
   company's own site can be high; news, NGO data and Wikipedia are capped at medium.
5. **Every edge is time-bound**, so measures use only the links that existed on the date.
6. **Name matching is never fuzzy and never silent.** Unmapped names go to a file for a
   person to map.
7. **Extractions are checked independently** against the source before they are used.
8. **No judgemental language** in code, column names or docs: "holds", "sits on",
   "lent", not "captured" or "cronies".

## Layout

```
data/seed/            hand-researched seeds; supplement/ holds listed entities and state holdings
data/primary/         extractions from primary documents (override seed edges)
data/mappings/        tickers.csv, board_rosters.csv, name aliases, financing names
data/events/          events.csv: the registered event set
data/raw/             documents.csv is committed; documents, prices, news are not
data/processed/       graph and connection measures built from the above
src/influence/        schema, graph, seed builder, validation, financing loader
  connections/        party status by date, connection measures
  events/             prices, event study, regressions, placebo, plots, one-command runner
  news/               crawler and entity tagger (media module)
docs/                 DESIGN.md, HANDOFF*.md, RUNNING.md, phase1_status.md
  paper/prereg.md     the pre-registration
  research/           evidence trail for the event dates and tickers
tests/
```

## Running

```
pip install -e ".[dev]"
pytest
python -m influence.build_seed_graph
python -m influence.validate
python -m influence.connections.build_measures
python -m influence.events.run --synthetic    # engine check on simulated prices
```

Price download, controls and the real run happen on your own machine (the cloud
workspace has no general internet access). `docs/RUNNING.md` section 5 has the steps.

## Sources and licences

- Company filings and annual reports (IDX, company sites); the BTN 2025 annual report is
  the first primary-source extraction.
- Reputable Indonesian and international press for party roles, offices and events.
- [Forests & Finance](https://forestsandfinance.org/data/) for bank lending to palm oil
  groups. Personal-use licence: ask Rainforest Action Network before publishing anything
  derived from it.
- Daily prices from Yahoo Finance via `yfinance`. Never committed.

## Legal note

Publishing this involves defamation exposure under the ITE Law and the new KUHP (in force
since 2 January 2026), and personal data obligations under UU PDP. Before anything
leaves private use: sourced edges only, a visible correction channel, and review by an
Indonesian lawyer. The repository stays private until then.
