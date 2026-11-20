# T07: Locate roster pages in an annual report

## Goal
Given an annual report PDF with a text layer, list the pages most likely to hold the
board of commissioners, the board of directors and the shareholder table, so a person
(or a model) transcribing the roster starts on the right pages.

## Read first
- `CLAUDE.md`
- `data/primary/btn_ar2025_check.md` (shows which kinds of page were used for BTN)

## Files you may create or edit
- `src/influence/intake/__init__.py` (create with a one-line docstring if missing)
- `src/influence/intake/pdf_pages.py` (new)
- `tests/test_intake_pdf_pages.py` (new)

## Specification
- `page_texts(pdf_path) -> list[str]` runs `pdftotext -layout` once and splits on the
  form-feed character; raises `RuntimeError` with a clear message if `pdftotext` is not
  installed.
- `score_pages(texts) -> DataFrame` with columns `page` (1-based), `chars`,
  `commissioners`, `directors`, `shareholders`, `appointment`: counts of
  case-insensitive keyword hits per page. Keyword lists (English and Indonesian), kept
  as module constants:
  commissioners: "board of commissioners", "dewan komisaris", "komisaris independen",
  "independent commissioner", "president commissioner", "komisaris utama";
  directors: "board of directors", "direksi", "president director", "direktur utama";
  shareholders: "shareholder", "pemegang saham", "share ownership", "kepemilikan saham";
  appointment: "appointed", "diangkat", "general meeting", "rups", "term of office",
  "masa jabatan", "fit and proper", "effective".
- `likely_pages(scores, kind, top=10) -> list[int]` returns pages ranked by the hits for
  `kind` plus half the `appointment` hits, ties broken by page number.
- `is_scanned(texts) -> bool` is True when the median page has fewer than 100 characters.
- `python -m influence.intake.pdf_pages PATH [--top 10]` prints the three lists and a
  warning if the file looks scanned.
- Tests work on lists of strings (no PDF needed) for scoring, ranking and the scanned
  check. One extra test builds a two-page PDF only if both `pdftotext` and a way to make
  a PDF are available; otherwise it is skipped. Do not add dependencies.

## Acceptance
`pytest -q tests/test_intake_pdf_pages.py`

## Out of scope
Extracting names, OCR, any network access, new dependencies.
