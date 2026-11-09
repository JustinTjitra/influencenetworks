# Running the pipeline on your own machine

The build workspace has no general internet access, so data collection runs locally.

```
pip install -e ".[dev]"
pytest
```

## 1. Rebuild the graph
```
python -m influence.build_seed_graph     # seeds + data/primary/*.csv -> data/processed
python -m influence.validate             # rejects unsourced / invalid edges, prints owner networks
```
Primary-source files in `data/primary/` (annual report extractions, financing data)
override seed edges with the same source, target and type.

## 2. Financing edges (Forests & Finance)
1. Download the full dataset from https://forestsandfinance.org/data/
2. Save it as `data/raw/financing/forests_and_finance.xlsx`
3. `python -m influence.load_financing`
4. Open `data/mappings/financing_unmapped.csv`. For each bank or group name that
   belongs to a node in the graph, add a row to `data/mappings/financing_names.csv`.
   Re-run step 3. Nothing is matched automatically, on purpose.
5. Rebuild the graph (step 1).

Licence: personal-use terms. Ask Rainforest Action Network before publishing derived data.

## 3. Articles
Recent articles via sitemaps:
```
export CONTACT_EMAIL=you@example.com
python -m influence.news.crawl sitemaps --outlet detik.com --since 2025-01-01 --max 500
```
Historical articles (2021-2025): run `docs/gdelt_urls.sql` in the BigQuery sandbox one
year at a time, export as CSV, then:
```
python -m influence.news.crawl urls --file gdelt_urls_2024.csv --max 5000
```
Then:
```
python -m influence.news.crawl extract    # -> data/processed/articles.parquet
python -m influence.news.tag_entities     # -> data/processed/mentions.parquet
```
The crawler checks robots.txt per URL, waits 2-5 s between requests to the same
domain, and identifies itself with your contact email. Keep it that way.

## 4. Adding a primary document
1. Put the PDF in `data/raw/docs/` (not committed to git).
2. Add a row to `data/raw/documents.csv` with its sha256 (`sha256sum file.pdf`).
3. Transcribe into `data/primary/<doc>_nodes.csv` and `<doc>_edges.csv`, citing
   `doc:<doc_id>#p<page>` as the source.
4. Have someone else check it against the pages before relying on it.

## 5. Phase 1 event study

Read `docs/paper/prereg.md` first. Nothing below touches prices until step 3, and step 3
refuses to run until the pre-registration records its commit hash.

```
pip install -e ".[dev,prices]"
```

1. Graph and connection measures (no prices):
```
python -m influence.build_seed_graph
python -m influence.validate
python -m influence.connections.build_measures   # -> data/processed/connection_measures.parquet
```
   The last command prints, per event, how many firms and clusters are treated and
   whether the event is in the main test. Those numbers must match section 3 of the
   pre-registration; if they do not, the graph has changed and the pre-registration needs
   an amendment before any price is downloaded.

2. Engine check on simulated prices (still no real prices):
```
python -m influence.events.run --synthetic       # -> data/processed/results_synthetic/
python -m influence.events.power                 # what size of gap the main test could detect
```

3. Prices (your machine only; needs internet):
```
python -m influence.events.prices download       # all tickers + ^JKSE from 2019 -> data/raw/prices/<date>/
python -m influence.events.prices report         # missing days, zero-volume days, gaps per ticker
```
   Raw price files are never committed. Each download is a new dated folder.

4. Controls. Fill `data/mappings/fundamentals.csv` from annual reports, one row per ticker
   and fiscal year: `ticker, fiscal_year_end, shares_outstanding, total_assets,
   total_liabilities, source_url`. It holds no prices and can be committed. If it is
   missing for more than 20% of firm-events the run falls back to price-based controls, as
   the pre-registration says, and reports that it did.

5. Results:
```
python -m influence.events.run                   # -> data/processed/results/
```
   `results_summary.md` in that folder applies the decision rule mechanically. Do not edit
   it by hand. The placebo (200 draws per model and event set) takes a few minutes.

To change anything in the registered files before step 3, follow section 14 of the
pre-registration (amend, commit, record the new hash). After step 3 the registered files
do not change.
