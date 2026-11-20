# T08: Roster extraction protocol

## Goal
A one-page procedure a session follows to turn one annual report into a checked roster
file, the same way every time.

## Read first
- `CLAUDE.md`
- `docs/RUNNING.md` section 4
- `data/primary/btn_ar2025_check.md`
- `src/influence/intake/documents.py`, `rosters.py`, `pdf_pages.py` (command-line help)
- `docs/PROJECT_PLAN.md` section "Phase 1b"

## Files you may create or edit
- `docs/intake/ROSTER_PROTOCOL.md` (new)

## Specification
Write the procedure as numbered steps with the exact commands:
1. Put the PDF in `data/raw/docs/`, register it (document registry command).
2. Check it has a text layer; if scanned, stop and ask the owner for a text PDF.
3. Locate pages (page locator command).
4. Transcribe every commissioner and director who served in the report year into
   `data/intake/rosters/<doc_id>.csv`: name exactly as printed, role, appointment date
   (the general-meeting date; the regulator's effective date goes in `note`), end date
   and reason if they left, page number; concurrent government posts only when the
   report itself states them, with their page.
5. Validate the file (roster validator command).
6. Independent check: a second agent that has not seen the transcription re-reads the
   cited pages and writes `data/intake/rosters/<doc_id>_check.md` as a table of
   row, field, CSV value, what the document says (page), verdict. Fix every "wrong".
7. Record what the report does not cover (for example directors missing, earlier years).
Also state: party roles are never in annual reports and are not added here; names are
not matched to existing people in this step; nothing is written to `data/primary/` or
`data/seed/` until the owner approves the pre-registration amendment.
Keep it under 90 lines, plain language, no judgemental wording.

## Acceptance
`test -s docs/intake/ROSTER_PROTOCOL.md && grep -c "influence.intake" docs/intake/ROSTER_PROTOCOL.md`

## Out of scope
Running the procedure, changing any code.
