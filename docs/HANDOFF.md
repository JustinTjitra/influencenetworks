# Handoff: Indonesian Influence Network

Status as of 2026-11-05. Read this file first. Then read `README.md`, `docs/RUNNING.md`
and `docs/step2_findings.md`.

## 1. What the project is

Repo: https://github.com/JustinTjitra/influencenetworks (private, owner Justin Tjitra).

The project maps **documented** relationships between Indonesian politicians, parties,
palm oil groups, banks and media owners. It then tests one question:

> Do Indonesian news outlets cover companies and politicians inside their owner's
> business or political network differently from comparable entities outside it?

The project is a mix of political communication, data science and business/finance.

### How the scope got here

1. The first idea was a media bias tracker plus a hoax/misinformation module.
2. The user then asked to add "funding sources of politicians and parties". That was
   reframed as a relationship network, because Indonesian campaign-finance data is
   unusable. KPU removed the donor-receipts report (LPSDK) for 2024, and donor details
   are not public.
3. The hoax module was **dropped**.
4. Sectors were narrowed to **palm oil and banking** for the MVP. **Tech is planned
   for v2**: its links run through regulation and state-linked investors, which need
   their own edge types. A contained Nadiem/GoTo case study is possible later.

## 2. The user

- Justin, a Penn freshman from Jakarta studying math and economics. He knows
  Indonesian business and politics well and is fluent in finance and PE concepts.
- He wants to be challenged and disagreed with when warranted, and spoken to as an
  equal. Don't use em-dashes in replies.
- He can download files the workspace can't reach: IDX PDFs, NGO datasets, GDELT exports.

## 3. Non-negotiable data rules

These are enforced in `src/influence/schema.py` and `graph.py`. Keep them.

1. **Every edge needs a source.** That means an `http(s)` URL, or `doc:<doc_id>#p<page>`
   pointing at a document registered in `data/raw/documents.csv` with its sha256.
   The loader rejects anything else.
2. **Relationships, not accusations.** There is no edge type for suspicion or
   wrongdoing. `convicted_in` requires the court record itself.
3. **`family_of` edges need medium or high confidence.**
4. **Confidence follows the source type:**
   - **high:** an annual report, exchange filing, registry, or a company's own site.
   - **medium at most:** news, NGO data, or Wikipedia.
   - The builder caps confidence automatically.
5. **Every edge is time-bound** (`start_date` / `end_date`). This lets coverage be
   matched to the links that existed when an article was published.
6. **Name matching is never fuzzy and never silent.** Unmapped names go to a file
   for a human to map.
7. **Have an independent agent check extractions against the source** before relying
   on them. This has caught real errors every time (see section 6).
8. **Legal context:**
   - Defamation exposure exists under the ITE Law and the new KUHP (in force since
     2 Jan 2026).
   - UU PDP covers personal data. Its implementing regulation is PP 33/2026; the data
     protection agency is not set up yet.
   - A Constitutional Court ruling (105/PUU-XXII/2024) limits ITE defamation
     complaints to individuals.
   - Before anything goes public: sourced edges only, a correction channel, and review
     by an Indonesian lawyer. The repo stays private until then.

## 4. Repo layout and pipeline

```
data/seed/        hand-researched seed CSVs + verification.csv (fact-check results)
data/primary/     primary-source extractions; these OVERRIDE seed edges with same (src,tgt,type)
data/mappings/    entity_aliases.csv (news tagging), financing_names.csv (+ _unmapped.csv)
data/raw/         documents.csv is committed; docs/, financing/, news/ are gitignored
data/processed/   nodes.csv / edges.csv built from the above
src/influence/    schema.py, graph.py, build_seed_graph.py, validate.py,
                  load_financing.py, news/{outlets,crawl,tag_entities}.py
tests/            19 tests, all passing
docs/             source_access_report.md, step1/2 findings, RUNNING.md, gdelt_urls.sql
```

Build and check:
```
pip install -e ".[dev]"   # or: pip install --break-system-packages networkx pandas httpx trafilatura pyarrow pytest openpyxl
pytest
PYTHONPATH=src python3 -m influence.build_seed_graph
PYTHONPATH=src python3 -m influence.validate
PYTHONPATH=src python3 -m influence.load_financing   # needs data/raw/financing/forests_and_finance.xlsx (~2 min to read)
```

How the parts fit:
- **`build_seed_graph.py`** declares every person's typed edges explicitly in
  `PERSON_EDGES`, so a reviewer can read all asserted relationships in one place.
- It applies `verification.csv`: confidence is lowered to the fact-checker's
  recommendation, and rows marked unverifiable are skipped.
- It then merges `data/primary/*_edges.csv` and `*_nodes.csv`.

## 5. Current state of the graph

- 166 nodes and 342 edges, with 0 rejected.
- 26 edges are high confidence (BTN annual report). 314 are medium; 2 are low.
- Edge counts by type:

| Type | Count |
|---|---|
| finances | 180 |
| board_seat | 48 |
| held_office | 31 |
| publishes | 30 |
| party_role | 15 |
| controls | 13 |
| owns | 10 |
| family_of | 9 |
| owns_media | 6 |

- **Seeds:** 18 palm oil groups, 12 banks, 13 media groups (30 outlet domains),
  62 people, and 19 coalition events from 2021 to 2026.
- **Isolated nodes (8):**
  - CIMB Niaga, Danamon, Maybank Indonesia, OCBC NISP, Permata. Forests & Finance books
    their deals under the foreign parent; do NOT map parent deals to the Indonesian
    subsidiary.
  - p_winston_utomo, pg_agrinas, pg_ssms.

### Primary sources ingested

1. **BTN 2025 Annual Report** (`doc:btn_ar_2025`, 432 pages, English, text layer intact).
   - Covers the full board of commissioners before and after the 2025-03-26 AGM, plus
     Didyk Choiroel (EGM 2026-01-07).
   - Shareholders: PT Danantara Asset Management holds 60.00% (p205); the Republic of
     Indonesia keeps 1 share (p203).
   - Includes the concurrent government posts disclosed in the profiles (p150-165).
   - The independent check is in `data/primary/btn_ar2025_check.md`.
   - Start dates use the GMS appointment date; the OJK effective date is in `note`.
2. **Forests & Finance, soft commodities 2026 export** (752,844 rows, 2010-2026).
   - Columns: Type, Bank, Country, Region, Group, Client, AmountUSDMillions, Year,
     Sector, ForestRiskClientCountry, ForestRiskClientRegion.
   - Filtered to Sector = Palm oil and ForestRiskClientCountry = Indonesia
     (34,579 rows, US$94bn).
   - **Credit vs holdings:** Bondholding and Shareholding are snapshot stocks, all booked
     in 2026 (about US$19.5bn). The loader tags each edge `role` as `credit:` or
     `holding:` and never sums them together. A test enforces this.
   - Licence: personal use. Ask Rainforest Action Network before publishing derived data.
3. A **hard commodities** F&F file was also provided. It covers mining only, with no
   palm oil, and is not loaded. Notable: Indonesian banks lend to ANTAM, Amman and
   nickel firms there; Harita Group is a borrower; CT Corpora (Chairul Tanjung, who
   owns Detik, CNN Indonesia and Trans TV) appears as a financier. Useful if mining is
   added later.

### Rejected inputs

- The BNI 2025 sustainability report arrived truncated.
- qpdf recovered 231 pages, but they are images about 460 px wide, so OCR was unusable.
- No names were taken from it, by design. BNI needs its **annual report** as a text PDF.

## 6. Findings so far (all provisional)

- **Owner networks split cleanly into treatment and comparison** (within 3 hops):

| Outlet group | Party / interests linked |
|---|---|
| MNC (okezone, inews, sindonews, idxchannel) | Perindo, plus Hanura/NasDem historically |
| Media Group (metrotvnews, mediaindonesia, medcom) | NasDem |
| Viva (viva.co.id, tvonenews) | Golkar, plus Bakrie plantations |
| B-Universe (beritasatu, investor.id, jakartaglobe) | NasDem |
| Kompas, Tempo, Kumparan, Detik, IDN | none |

- **State bank boards are where party ties concentrate.**
  - BTN: Fahri Hamzah (vice minister; Gelora deputy chair) and Pietra Paloh
    (nephew of Surya Paloh).
  - BNI: Vera Febyanthy (Demokrat deputy chair).
  - BRI: Helvi Moraza (Gerindra-linked, deputy minister) and Lukmanul Khakim (PKB).
  - BSI: Felicitas Tallulembang (Gerindra).
  - Party ties come from news (medium confidence); annual reports never disclose them.
  - Most other state-bank commissioners are civil servants representing the shareholder.
    That is normal SOE governance, not patronage. Don't conflate the two.
- **Natural experiment:** a 2025-08-28 Constitutional Court ruling bars deputy ministers
  from SOE commissioner seats, with a 2-year transition. That makes 2027 a before/after
  point.
- **OJK fit-and-proper lag:** Fahri Hamzah was appointed 2025-03-26 and cleared
  2025-12-17. Pietra Paloh cleared 2025-08-15.
- **Palm oil credit from Indonesian banks, 2010-2026 (US$m):**

| Bank | Credit |
|---|---|
| Mandiri | 5,330 |
| BNI | 3,609 |
| BCA | 3,219 |
| Panin | 2,780 |
| BRI | 2,254 |
| BTN | 113 |
| BSI | 0 |

- **Top credit pairs:**
  - Mandiri to PTPN: 2,538
  - Panin to Sinar Mas: 2,438
  - BCA to Salim: 1,734
  - BNI to Sinar Mas: 1,661
- Indonesian banks supply about 26.5% of financing for Indonesian palm oil.
- **State-bank palm credit by year (US$m):** 1,081 in 2019, 452 in 2021, 261 in 2022,
  431 in 2023, 994 in 2024, 1,522 in 2025.
  - The 2025 jump is mostly 957 to PTPN, i.e. state bank to state plantation company.
  - This is NOT a finding yet. First check that 2025 data is complete, and compare with
    lending to private groups.
- **Seed corrections made by the fact-checker. Do not reintroduce these errors:**
  - Enggartiasto's 80% B-Universe stake was a rumour. No ownership percentage is recorded.
  - There is no Prabowo-to-Arsari edge. The link is Hashim (brother) to Arsari.
  - No Zulkifli Zaini-to-PTPN edge.
  - Never import news-site tags (e.g. "tersangka") as data.
  - A company's legal case does not make its chairman liable.
  - Mandiri still holds 51.47% of BSI after BSI became a Persero (2026-01-23); it just
    no longer consolidates it.
  - First Resources holds about 95.9% of ANJT (plus about 2.6% via PT Ciliandra Perkasa),
    not 100%.

## 7. Environment constraints (cloud workspace)

- **No general web access from the shell.** curl to news sites and NGOs fails.
  WebSearch and WebFetch work. Anything bulk (crawl, GDELT, downloads) runs on the
  user's machine per `docs/RUNNING.md`.
- **IDX has Cloudflare protection.** kompas, tempo, KPU, LHKPN and the Supreme Court
  site refused or failed for automated fetchers. AHU full company profiles cost
  Rp50k-500k each.
- **GitHub pushes from the session have failed:**
  - a 403 because the Claude GitHub app isn't installed on the account;
  - the session's permission classifier also blocked a push once.
- The user has been pushing himself, squashing into a single "Initial commit".
- Workaround: commit locally, then hand over a `git bundle` or zip. Ask the user to
  install the app at https://github.com/apps/claude/installations/select_target if
  direct pushes are wanted.
- **Crawler User-Agent:** reads the CONTACT_EMAIL env var. Do not hardcode the user's
  email anywhere.

## 8. Next steps, in priority order

1. **Add the palm groups that received large state-bank credit but aren't nodes yet.**
   - Groups: Sungai Budi, Tanjung Lingga, Provident Agro.
   - Also add Bank Sinar Mas: it lends to its own group (US$117m), a related-party pattern.
   - Source owners and controllers carefully (filings first), add to the seed and
     `financing_names.csv`, then rebuild.
   - This was offered to the user and is awaiting his go-ahead.
2. **State-bank annual reports for 2025** (BNI, BRI, Mandiri, BSI) as text PDFs from the
   user.
   - Extract them like BTN: register each in `documents.csv`, transcribe into
     `data/primary/`, cite pages, then run an independent check.
3. **News corpus.**
   - The user runs `docs/gdelt_urls.sql` in the BigQuery sandbox, one year at a time,
     then `crawl urls`, `crawl extract` and `tag_entities`.
   - Kompas and Tempo robots rules are unverified; check them manually.
4. **Stance model.**
   - Have an LLM label about 1-2k article-entity pairs, hand-validate 200, then
     fine-tune IndoBERT.
   - If validated accuracy is below about 75%, the coverage analysis is noise.
   - Measure entity-level stance, not document sentiment.
5. **Coverage analysis.**
   - Compare coverage share and stance toward network-linked vs unlinked entities, by
     outlet, using `snapshot()` to match the links active on each publish date.
   - Then a diff-in-diff around coalition events (`data/seed/coalition_events.csv`);
     NasDem nominating Anies on 2022-10-03 is the cleanest.
   - Caveat: only about 4 treated media groups, so results are suggestive.
6. **Dashboard:** Streamlit, with a graph explorer (pyvis or Cytoscape).
7. **Later:** primary-source board data for the palm oil groups (IDX annual reports),
   the tech sector (v2), and mining (hard-commodities file already in hand).

## 9. Open decisions for the user

- Publication mode: public, anonymous, or private research tool. This is undecided;
  the repo is private for now.
- Whether to request Forests & Finance republication permission.
- Whether to install the Claude GitHub app.
