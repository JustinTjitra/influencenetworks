# T24: Draft of pre-registration amendment 1

## Goal
The text of amendment 1, ready for the owner to approve once the board rosters are in.
It is a draft under `proposals/`; it does not change the pre-registration.

## Read first
- `CLAUDE.md` (hard rule 2)
- `docs/paper/prereg.md` (all of it, especially sections 3, 4, 7, 9, 13, 14)
- `docs/phase1_status.md` section "Decided 2026-11-13"

## Files you may create or edit
- `proposals/amendment-1/README.md` (new)
- `proposals/amendment-1/prereg_changes.md` (new)

## Specification
- `prereg_changes.md` gives, section by section, the exact replacement text:
  - Section 9 (decision rule): the placebo-only wording decided on 2026-11-13, quoted
    from `docs/phase1_status.md`, plus the note that with 200 draws the smallest
    possible placebo p-value is 1/201.
  - Section 4 (coverage) and section 3 (main-test subset): placeholders marked
    `TO FILL AFTER ROSTERS`, with the rule that the subset is recomputed mechanically by
    `influence.connections.build_measures` and pasted in unchanged.
  - Section 13 (known gaps): which gaps the amendment closes, with placeholders.
  - Section 14 (amendment log): the row to add.
  - Section 12 (power): rerun `python -m influence.events.power` after the rosters and
    replace the table.
- `README.md`: the order of operations for the attended session (extract and check
  rosters, apply data changes, rebuild graph and measures, fill placeholders, run
  tests, commit with `[amendment]` in the subject, record the new registration hash),
  and what must NOT have happened before it (any price download).
- Do not edit `docs/paper/prereg.md`.

## Acceptance
`test -s proposals/amendment-1/prereg_changes.md && grep -c "TO FILL AFTER ROSTERS" proposals/amendment-1/prereg_changes.md && python tools/guard.py`

## Out of scope
Applying the amendment, changing any protected file.
