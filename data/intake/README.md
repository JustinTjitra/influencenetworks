# data/intake

Checklist for downloading the 2024 and 2025 annual reports of the 34 firms in
`data/mappings/tickers.csv` (12 banks, 11 palm oil, 11 media). Two rows per firm, 68 in all.

- `annual_reports.csv`: one row per ticker and `report_year`. Banks first (BBRI, BMRI,
  BBNI, BRIS, then the rest), then palm oil, then media. 2025 comes before 2024.
- `archive_page_url`: the firm's own page that lists its reports.
- `pdf_url`: a direct PDF link. Both URLs are copied from the files in
  `research_notes/Influence network project sources/`. They were not opened or checked.
- `url_status`: `pdf_found` (a direct PDF is listed), `archive_only` (only the archive
  page), `not_found` (neither).
- `note`: why a link is missing, which language or version was chosen, and what to
  check on opening. Read it before downloading.
- `doc_id`: the name the file will be registered under in `data/raw/documents.csv`.
  Use `btn_ar_2025` for BBTN 2025, which is already registered.
- Owner fills in: `received` (yes once the file is saved), `sha256` (of the saved file),
  `text_layer` (yes or no, once checked).
- Downloads happen on the owner's machine (see `docs/RUNNING.md`). Raw PDFs are never
  committed (CLAUDE.md, rule 5).
- If a link is broken, correct the cell from the firm's own page and say so in `note`.
