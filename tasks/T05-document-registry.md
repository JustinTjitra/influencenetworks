# T05: Document registry command

## Goal
One command that registers a downloaded primary document (an annual report PDF) in
`data/raw/documents.csv` with its sha256, so every `doc:<id>#p<page>` citation can be
traced to an exact file.

## Read first
- `CLAUDE.md`
- `data/raw/documents.csv` (columns: `doc_id, filename, sha256, title, publisher, year,
  obtained_from, note`)
- `docs/RUNNING.md` section 4

## Files you may create or edit
- `src/influence/intake/__init__.py` (create with a one-line docstring if missing)
- `src/influence/intake/documents.py` (new)
- `tests/test_intake_documents.py` (new)

## Specification
- `sha256_of(path) -> str` streams the file in chunks.
- `page_count(path) -> int | None` uses `pdfinfo` if it is installed, else `None`.
- `has_text_layer(path, sample_pages=5) -> bool | None` runs `pdftotext` on the first
  pages and returns True if at least 200 non-space characters come back; `None` if
  `pdftotext` is missing.
- `register(registry_csv, pdf_path, doc_id, title, publisher, year, obtained_from,
  note="") -> dict` appends a row. It refuses (ValueError) when: `doc_id` does not match
  `^[a-z0-9_]+$`; the id already exists with a different sha256; the same sha256 is
  already registered under another id; the file does not exist. Registering the same
  file under the same id again is a no-op. `filename` is stored relative to `data/raw/`
  (for example `docs/bbri_ar_2025.pdf`). The page count and "text layer: yes/no/unknown"
  go into `note`.
- Command line: `python -m influence.intake.documents register --pdf PATH --id ID
  --title T --publisher P --year Y --from "..." [--registry PATH]` and
  `python -m influence.intake.documents verify [--registry PATH] [--root data/raw]`,
  which recomputes hashes of files that are present and reports mismatches and missing
  files (missing is a warning, not an error: raw documents are not committed).
- Tests use `tmp_path` and small fake files written as bytes; they must not need
  `pdfinfo` or `pdftotext` (skip those two functions' tests if the binaries are absent).
  Tests never write to the real `data/raw/documents.csv`.

## Acceptance
`pytest -q tests/test_intake_documents.py && python -m influence.intake.documents verify | tail -5`

## Out of scope
Changing `data/raw/documents.csv` (it is protected), downloading anything.
