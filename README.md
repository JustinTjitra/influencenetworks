# WIP - Indonesian Political Influence Network

A sourced, time-bound map of **documented** relationships between Indonesian
politicians, parties, state bodies and listed firms (banks, palm oil groups and media
groups), and an event study that uses it to measure what political connections are
worth to those firms.

## The question

Do politically connected Indonesian firms gain or lose more value than comparable
unconnected firms when the political ground shifts?

modern replication and extension of Fisman (2001), "Estimating the Value of
Political Connections", which used Indonesian firms and rumours about Suharto's health.
This version uses the 2021-2026 transition from Jokowi to Prabowo and the 2025
restructuring of state ownership under Danantara. Connections are measured two ways,
through state ownership and through people (board members with party, ministry or family
ties), because the two may respond to different kinds of event.

## Three outputs from one codebase

1. **Study** An event study across 24 dated political and policy events, with the
   design pre-registered before any price was downloaded.
2. **The Stakeholder Exposure Monitor** A private Streamlit app showing, for
   each firm, its documented network, the shocks it has lived through and how its stock
   responded. 


| | |
|---|---|
| Universe | 34 IDX-listed firms: 12 banks, 11 palm oil, 11 media |
| Events | 24, from the 2022 palm oil export ban to the 2025 SOE ministry change |
| Main test | 2 events that are unanticipated, unconfounded and have enough treated firms: the Danantara launch-date announcement (2025-02-13) and the first Constitutional Court signal on deputy ministers as SOE commissioners (2025-07-17) |
| Graph | 186 nodes, 374 sourced edges, 0 rejected |
| Tests | 51 passing |





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
  groups
- Daily prices from Yahoo Finance via `yfinance`
