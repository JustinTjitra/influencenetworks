# Handoff: two new modules for the influence network

Written 2026-11-05 for a fresh Claude Code session. Read `docs/HANDOFF.md` first: it has
the project context, the data rules the code enforces, the environment limits, and the
errors earlier fact-checks caught. Everything there still applies. This file adds two
modules and says how they fit the existing code.

Repo: https://github.com/JustinTjitra/influencenetworks (private).

Both modules are meant to end as **one paper each with a clear result**, for a Wharton
transfer application (Statistics + Impact, Value and Sustainable Business concentration)
and as course projects: the pump module alongside STAT 4220 (fall 2026) and STAT 4300
(spring 2027); the interlocks module alongside LGST 2050 Antitrust and Big Tech
(Hovenkamp, spring 2027).

---

## Module A: Coordinated stock promotion on Indonesian social media ("saham gorengan")

### Question
Can coordinated pump campaigns be detected in Telegram, X and Stockbit chatter, and do
they predict abnormal returns and volume in small-cap IDX stocks?

### Why this one
- IDX publishes Unusual Market Activity (UMA) notices and trading suspensions. Those are
  free, dated labels.
- The detector reuses the coordination methods from the user's election bot research:
  synchronized posting, near-duplicate text, account clusters.
- Retail participation in Indonesia surged after 2020, the pump groups are well known,
  and the phenomenon is under-studied academically.

### Ground rules specific to this module
1. **UMA is not a finding of manipulation.** IDX issues UMA when price or volume moves
   unusually; it says so explicitly. Treat UMA and suspensions as labels for
   "unusual activity", never as proof of a pump. Say this in every output.
2. **Never publish account handles, channel names tied to people, or lists of
   "pumpers".** All reporting is aggregate (campaign counts, cluster sizes, effect sizes).
   Defamation exposure under ITE/KUHP applies to individuals; UU PDP applies to storing
   personal data. Store the minimum: hashed account ids, timestamps, text, ticker.
3. **Collect only from public channels and public posts.** Check Stockbit's terms before
   touching it; if scraping is prohibited, drop it and say so. X's API is expensive;
   treat X as optional.
4. **Do all collection on the user's machine.** The cloud workspace has no general web
   access (see HANDOFF.md section 7).

### Data
| Data | Source | How | Notes |
|---|---|---|---|
| UMA notices, suspensions | idx.co.id announcements ("Pengumuman", filter UMA / Suspensi) | user's browser or a Playwright script on user's machine; IDX is behind Cloudflare | Save raw HTML/PDF under `data/raw/idx_announcements/`; register in `documents.csv` |
| Daily prices, volume | Yahoo Finance via `yfinance`, tickers as `XXXX.JK` | script on user's machine | Free. No free intraday for IDX; daily granularity only |
| Index and sector returns | `^JKSE`, IDX sector indices via yfinance | same | For the market model |
| Listed company list, IDX-IC sector, free float, market cap | IDX company profiles | user's machine | Also needed by Module B |
| Telegram chatter | public "saham" channels and groups via Telethon (public entities only) | user's machine, user's own Telegram account | Seed list: ask the user; he knows the circuit. Store message id, channel id (hashed), sender id (hashed), timestamp, text, forwarded-from flag |
| Stockbit stream | per-ticker stream | only if terms allow | Optional |
| X | API | optional | Skip unless budget appears |

### Pipeline (new package `src/influence/pump/`)
1. `tickers.py`: build `data/processed/tickers.parquet` (ticker, name, IDX-IC sector,
   listing date, free float, market cap bucket). Small-cap = bottom tercile by market cap,
   or free float below a threshold; justify the cut once and keep it.
2. `labels.py`: parse UMA and suspension announcements into `events_idx.parquet`
   (ticker, date, type, announcement doc_id). Ticker extraction from announcement text
   must be exact-match against the ticker list; no fuzzy matching.
3. `collect_telegram.py`: Telethon collector with a channel seed list in
   `data/mappings/telegram_channels.csv` (channel id hashed, label, added-by, date).
   Writes `data/raw/chatter/telegram/*.parquet`. Rate-limit politely.
4. `mentions.py`: cashtag and name matching of posts to tickers. Reuse the alias
   approach from `news/tag_entities.py` (exact, auditable aliases in a CSV). Short
   tickers like `AALI` match case-sensitively on word boundaries.
5. `coordination.py`: per ticker and day, compute
   - burst score (posts vs trailing 30-day baseline; Kleinberg burst detection or a
     simple z-score of log counts),
   - near-duplicate share (MinHash/simhash on normalised text, Jaccard above 0.8),
   - synchrony (share of posts within 5-minute windows across distinct accounts),
   - account-cluster concentration (user–ticker bipartite graph, Louvain on the user
     projection, share of posts from the top cluster),
   - forward share (share of messages that are forwards).
   Output `campaign_candidates.parquet` with a `campaign_start` date per ticker when
   the composite crosses a threshold. Keep the threshold explicit and sweep it.
6. `eventstudy.py`:
   - Market model estimated on days [-250, -30] before `campaign_start`; thin trading
     is a problem for small caps, so also report raw and market-adjusted returns and
     use Dimson-style lagged betas as a robustness check.
   - CAR windows [-5,-1], [0,+1], [0,+5], [+6,+20]. Abnormal volume as log(volume /
     trailing 60-day mean).
   - Matched controls: same sector and market-cap bucket, no campaign flag within
     ±30 days.
   - **Direction:** lead-lag tests at daily granularity (Granger on chatter counts vs
     returns/volume; and whether the chatter burst day precedes the first abnormal
     volume day). Intraday timing is not available free; say so.
   - Validation against IDX labels: precision/recall of detector flags vs UMA within
     ±5 days, as a sanity check, not as ground truth.
7. `report.py`: tables and figures; aggregate only.

### Statistics to report
- Number of campaigns detected, by month and sector.
- Mean CAR and abnormal volume by window, with bootstrap CIs, vs matched controls.
- Post-campaign reversal (the [+6,+20] window is the tell for a pump).
- Lead-lag results.
- Sensitivity to the detection threshold.

### Known risks
- Chatter-follows-price: handled by lead-lag and the reversal window, but state the
  limit plainly; daily data can't settle intraday causality.
- Survivorship: delisted tickers must stay in the universe; yfinance drops some.
  Note any gap.
- Channel seed bias: the seed list is hand-picked; report how results change when
  the largest channel is dropped.
- Telegram deleted messages are gone; collection should run forward continuously,
  not only backward.

### Acceptance for "done"
- Detector + event study run end-to-end from raw files with one command.
- Tests cover: ticker matching, duplicate detection, burst scoring on a synthetic
  series, CAR arithmetic on a toy panel.
- A `docs/pump_findings.md` with the tables above and a limitations section.

---

## Module B: Board interlocks and common ownership across IDX (antitrust)

### Question
How concentrated is corporate control in Indonesia; which conglomerates share
directors or commissioners with their nominal competitors; and did the 2025 Danantara
consolidation create common ownership across firms that compete (the state banks
compete for deposits and loans and now share one controlling shareholder)?

### Why this one
- The pipeline exists: document registry, people nodes, `board_seat` and `owns` edges,
  entity ids, independent checking. This module scales it from one bank to the
  whole exchange (about 900 companies).
- Law 5/1999 (Indonesia's competition law) Article 26 restricts a person from holding
  director or commissioner seats concurrently in companies that are in the same
  relevant market, are closely linked, or could jointly control market share; Article 27
  restricts majority shareholdings across similar companies in the same market. KPPU
  rarely enforces either. "Here is how much of the exchange the law technically covers"
  is a finding on its own. Verify the article text against the statute before citing.
- The causal claim (interlocks reduce competition) is hard and the US common-ownership
  literature (Azar, Schmalz and Tecu on airlines; critics including Hovenkamp) is
  contested. **The descriptive map is the deliverable.** Do not promise causal results.

### Ground rules specific to this module
1. Every edge still needs a primary source and a page or URL (`doc:` or `http`).
   For 900 companies that means a structured source, not 900 PDFs.
2. A board seat is a fact; "interlock" is a derived relationship with a stated
   definition. Keep the definition in code and in the write-up.
3. Entity resolution of Indonesian names is the hardest part (single names,
   honorifics, variants). Use `splink` or `dedupe` with blocking on exact name tokens,
   and **a human review file for every merge below a high threshold**. Never merge
   two people silently.

### Data
| Data | Source | Notes |
|---|---|---|
| Boards (commissioners, directors) and shareholders above 5% for all listed companies | IDX company profile pages ("Profil Perusahaan Tercatat"). There is a reported JSON endpoint behind them (`/primary/ListedCompany/GetCompanyProfilesDetail?KodeEmiten=XXXX`); the source-access report could not confirm it. Test it from the user's machine first | Behind Cloudflare; Playwright on user's machine. One snapshot per quarter, stored raw with date, registered in `documents.csv` as a `govt_registry`/`exchange_filing` source |
| IDX-IC sector and sub-industry per company | IDX | Defines "nominal competitors" |
| Conglomerate membership | seed `business_group` nodes already in the graph, extended by hand with sources | Group assignment needs a source per company |
| Danantara transfers 2025 | annual reports (BTN already done), IDX disclosures | Before/after dates: 2025-03-22 (BRI, Mandiri, BNI, BTN transfers), later moves per fact-check notes in HANDOFF.md |
| Historical boards (for before/after) | annual reports 2023-2025 of the companies in affected sectors | PDFs from the user; extract as BTN was extracted |

### Pipeline (new package `src/influence/interlocks/`)
1. `collect_profiles.py` (runs on user's machine): fetch and store profiles for all
   tickers; politely, with delays; raw JSON/HTML to `data/raw/idx_profiles/<date>/`.
2. `parse_profiles.py`: to `people_raw.parquet` (name as printed, role, company, date)
   and `holders_raw.parquet` (holder name, pct, company, date).
3. `resolve_people.py`: normalise names (strip titles like H., Hj., Ir., Dr., Drs.,
   S.E., M.B.A.; unify spacing and case), block, score, write
   `data/mappings/person_merges.csv` for review, then assign person ids. Reuse the
   `p_` id scheme and existing person nodes where names match reviewed aliases.
4. `build_edges.py`: `board_seat` edges with `doc:` sources into `data/primary/`,
   `owns` edges for holders above 5% (holder may be a person, a company, or a
   custodian; custodians are not owners, flag them).
5. `interlocks.py`:
   - Company–company interlock graph: edge when a person sits on both boards
     at the same date (`snapshot()` in `graph.py` already handles dates).
   - Classify each interlock: same IDX-IC sub-industry ("horizontal"), same business
     group ("intra-group"), other.
   - Article 26 exposure: count of horizontal interlocks not explained by group
     membership, by sector.
   - Concentration: share of listed market cap controlled by the top 10, 20, 50
     ultimate owners (via `controls`/`owns` chains in the graph).
   - Common ownership: for each sub-industry, compute the overlap in top holders
     and a modified HHI (MHHI delta) using the standard profit-weight formula;
     report with and without Danantara as a single owner, before and after
     2025-03-22.
6. `report.py`: network figures (pyvis or Cytoscape export), tables, and a
   sector-by-sector appendix.

### Statistics to report
- Interlock density overall and by sector; share of companies with at least one
  horizontal interlock outside their group.
- Top 20 people by number of board seats, **with sources**, reported as counts, not
  as accusations.
- Concentration curve of control.
- MHHI delta by sub-industry, before and after Danantara, with the banking sector
  as the headline case.
- Comparison with what Article 26/27 would cover if enforced.

### Known risks
- Profile snapshots are current-state only; history needs annual reports. Scope the
  before/after to the sectors Danantara touched (banks, energy, telecoms, mining),
  not the whole exchange.
- Nominee and custodian holdings hide ultimate owners; report the share of holdings
  that could not be traced.
- Name collisions in a country with many shared names: expect false merges; the
  review file is mandatory.

### Acceptance for "done"
- A reproducible build from raw profile snapshots to the interlock graph.
- Tests cover: name normalisation, a toy interlock classification, MHHI delta on a
  worked example with known answer.
- `docs/interlocks_findings.md` with the tables above, the Article 26/27 framing, and
  a limitations section that says the map is descriptive.

---

## How the modules connect to the existing graph

- Both reuse `schema.py`, `graph.py` (`snapshot`, `linked_entities`), the document
  registry and the alias-matching pattern. Do not fork these; extend them.
- Module B's people and `board_seat` edges flow into the same `nodes.csv`/`edges.csv`,
  so the media-coverage analysis gains a far larger owner network.
- Module A's campaign list can later be joined to the graph: are pumped tickers more
  often group-affiliated, and do group-owned outlets cover them? That is a v2 question;
  don't start there.

## Suggested order
1. Module B steps 1-2 first (profile collection and parsing), because they also give
   Module A its ticker universe and sectors.
2. Module A labels and price data, then the detector, then the event study.
3. Module B entity resolution and interlock analysis.
4. Independent checks on each extraction before any findings are written.

## Open items for the user
- Telegram channel seed list and whether he is comfortable collecting with his own
  account.
- Stockbit terms of service check.
- Confirm the IDX profile endpoint works from his machine.
- Whether to keep Danantara before/after limited to banks for the first pass (recommended).
