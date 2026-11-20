# Roster extraction protocol

Turns one annual report into a checked roster file, the same way each time. Run commands from the repository root; nothing here touches price data.

## Who may do what

- Step 1 writes `data/raw/documents.csv`, a protected file. Only the owner, or a session
  the owner attends, registers a document. An unattended session never runs `register`; it
  stops and notes it for the owner unless the document is already listed in
  `data/raw/documents.csv` and `python -m influence.intake.documents verify` prints no `missing` for it.
- Steps 2 to 7 can be done by any session that has the PDF.
- Nothing is written to `data/primary/` or `data/seed/` until the owner approves the
  pre-registration amendment.

## Steps

**1. Register the document.** Put the PDF in `data/raw/docs/` (never committed). Then,
as owner or attended session:

```
python -m influence.intake.documents register --pdf data/raw/docs/<file>.pdf --id <doc_id> --title "<title>" --publisher "<publisher>" --year <YYYY> --from "<where obtained>"
python -m influence.intake.documents verify
```

`<doc_id>` uses lower-case letters, digits and underscores only. `--note "<text>"` is optional.

**2. Check the text layer.**

```
python -m influence.intake.pdf_pages data/raw/docs/<file>.pdf
```

If the output starts with `WARNING: this file looks scanned`, stop and ask the owner for
a text PDF. Do not run OCR.

**3. Locate pages.** The same command lists likely pages for commissioners, directors and
shareholders (`--top <N>` for a longer list). These are candidates only. Read each page:

```
pdftotext -layout -f <page> -l <page> data/raw/docs/<file>.pdf -
```

**4. Transcribe.** Create the file, then fill it in:

```
mkdir -p data/intake/rosters
python -m influence.intake.rosters template --doc <doc_id> --ticker <TICKER> > data/intake/rosters/<doc_id>.csv
```

Delete the two example lines starting with `#`. Write one row per person per organ
(`commissioners` or `directors`) who served in the report year:

- `person_name`, `role`: exactly as printed.
- `start_date`: the general-meeting date that appointed the person (`YYYY`, `YYYY-MM` or
  `YYYY-MM-DD`).
- `end_date`: if the person left in the report year. The reason goes in `note`.
- `note`: the regulator's effective date, if the report gives one, and any reason for leaving.
- `page`: the page where the person appears.
- Concurrent government posts only when the report itself states them, with their page,
  in `government_post`, `government_body`, `post_start`, `post_end`, `post_page`.

Party roles are never in annual reports and are not added here. Do not match names
against existing people. Leave cells blank when the report does not state them.

**5. Validate.**

```
python -m influence.intake.rosters validate data/intake/rosters/<doc_id>.csv
```

No output and exit code 0 means the file passed. Otherwise fix each line printed and rerun.

**6. Independent check.** A second agent, which did not do step 4, re-reads the cited pages
with the step 3 command and checks the CSV. It writes `data/intake/rosters/<doc_id>_check.md`:
a table of row, field, CSV value, what the document says (page), verdict (ok, wrong or
unsupported), plus any person on the cited pages missing from the CSV. Fix every "wrong"
row, rerun step 5, and update the check file.

**7. Record what the report does not cover.** Add a "Not covered" section to the check
file: omitted directors or commissioners, years outside the report, and pages not reached.

## Rules

- Every row cites a page; every relationship has a source and dates (see README.md
  "Data rules").
- Names are copied as printed. No fuzzy matching and no merging with existing people.
- Write the report's facts in neutral wording.
- Owner approval of the pre-registration amendment is needed before anything reaches
  `data/primary/` or `data/seed/` (see `tasks/PROTECTED.txt`).
