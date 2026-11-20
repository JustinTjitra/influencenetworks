# T09: Annual report manifest

## Goal
A checklist file the owner uses to download the annual reports: one row per firm and
year, with where to find it and whether it has arrived.

## Read first
- `CLAUDE.md`
- `data/mappings/tickers.csv`
- `research_notes/Influence network project sources/annual_reports_banks.md` and
  `annual_reports_palm_media.md` (URLs found by web research; some are missing)

## Files you may create or edit
- `data/intake/annual_reports.csv` (new)
- `data/intake/README.md` (new, under 25 lines: what the folder is and how to use the file)

## Specification
- Columns: `ticker, listed_name, sector_bucket, report_year, archive_page_url,
  pdf_url, url_status, doc_id, received, sha256, text_layer, note`.
- One row per ticker in `tickers.csv` for each `report_year` in 2024 and 2025
  (68 rows), ordered: BBRI, BMRI, BBNI, BRIS first, then the other banks, then palm oil,
  then media; within a ticker 2025 before 2024.
- `archive_page_url` and `pdf_url` are copied exactly from the research notes. Never
  type or guess a URL. Where the notes have none, leave the cell empty.
- `url_status` is `pdf_found`, `archive_only` or `not_found`.
- `doc_id` is `<ticker lower-case>_ar_<year>`, for example `bbri_ar_2025`.
- `received`, `sha256`, `text_layer` are empty (the owner fills them).
- BTN's 2025 report is already registered as `btn_ar_2025`: mark that row
  `received = yes` and copy its sha256 from `data/raw/documents.csv`.

## Acceptance
`python - <<'PY'
import pandas as pd
d = pd.read_csv('data/intake/annual_reports.csv', dtype=str, keep_default_na=False)
t = pd.read_csv('data/mappings/tickers.csv', dtype=str)
assert len(d) == 68 and set(d.ticker) == set(t.ticker), (len(d), set(t.ticker) - set(d.ticker))
assert set(d.url_status) <= {'pdf_found', 'archive_only', 'not_found'}
assert (d.loc[d.pdf_url != '', 'pdf_url'].str.startswith('http')).all()
print(d.url_status.value_counts().to_dict())
PY`

## Out of scope
Downloading anything, web searches, guessing URLs.
