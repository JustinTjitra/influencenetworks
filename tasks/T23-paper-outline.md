# T23: Paper outline

## Goal
The skeleton of the paper: sections, the claim each makes, and the table or figure that
supports it, written before results exist so that results cannot shape the story.

## Read first
- `CLAUDE.md`
- `docs/DESIGN.md`, `docs/paper/prereg.md`, `docs/phase1_status.md`
- `docs/paper/literature.md`

## Files you may create or edit
- `docs/paper/outline.md` (new)

## Specification
- Sections: Introduction; Setting (Indonesia 2021-2026, Danantara); Data (the graph and
  its evidence rules, the universe, the event set); Measuring connection; Empirical
  design (as registered); Results (placeholders only); Robustness; Limits; Conclusion.
- For each section: 3 to 6 bullet points of content, the registered table or figure it
  uses (name the file under `data/processed/results/` that will hold it), and the
  references from `literature.md` it leans on.
- A "What we will say under each outcome" table: the main test holds, does not hold
  with the registered sign, does not hold with the opposite sign. One sentence each,
  written now.
- State the limits plainly: two main-test events before the roster amendment, low
  power, dates verified from snippets, signs not blind.
- No result, no number about returns, no claim about any named person's conduct.
- Under 150 lines.

## Acceptance
`test -s docs/paper/outline.md && grep -c "^## " docs/paper/outline.md`

## Out of scope
Writing prose sections, any result, changing the pre-registration.
