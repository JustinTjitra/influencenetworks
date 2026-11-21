# Amendment 1: how to apply it

A draft for the owner. Nothing in this folder changes the pre-registration. It is applied
only in a session the owner attends, in one commit, and only if no price has been
downloaded.

## What must NOT have happened before it

- No run of `python -m influence.events.prices download`, on any machine.
- No run of `python -m influence.events.run` without `--synthetic`.
- No price file under `data/raw/prices/`, and no `data/processed/results/` folder.
- Nobody working on the amendment has looked up how any share or index moved around any
  listed or proposed event.

If any of these has happened, stop: the changes below are then deviations to be reported
in the paper, not an amendment.

## Files in this folder

| File | What it is |
|---|---|
| `prereg_changes.md` | Replacement text for the pre-registration, section by section, with `TO FILL AFTER ROSTERS` placeholders |
| `coalition_rows.csv`, `person_edge_changes.md`, `event_rows.csv`, `evidence_notes.md` | Proposed data rows and their sources (board task T25), if present |

## Order of operations in the attended session

1. **Check the starting point.** `git status` clean, `pytest -q` and
   `python tools/guard.py` pass, and the four conditions above hold.
2. **Extract and check the rosters.** For each annual report received
   (`data/intake/annual_reports.csv`), follow `docs/intake/ROSTER_PROTOCOL.md`: register
   the document, transcribe, validate, independent check, record what is not covered.
   Finish every firm that can be finished before going on; the amendment is made once.
3. **Decide the open questions** at the end of `prereg_changes.md` (the graph's edge
   key, lending in `dist_gov`) and the proposed rows from T25. Write the decisions down
   before any rebuild, so that they cannot depend on what the rebuild shows.
4. **Apply the data changes.** Rosters into `data/primary/` and
   `data/mappings/board_rosters.csv`; approved party-status, person-edge and event rows
   into `data/seed/` and `data/events/events.csv`; any approved code change, with a test.
5. **Rebuild.** `python -m influence.build_seed_graph && python -m influence.validate`,
   then `python -m influence.connections.build_measures`. The graph must have 0 rejected
   edges.
6. **Fill the placeholders** in `prereg_changes.md` from the rebuild's output, paste the
   text into `docs/paper/prereg.md`, and rerun `python -m influence.events.power` for
   section 12. Paste values unchanged; do not round, reorder or drop anything by hand.
   `grep -c "TO FILL AFTER ROSTERS" docs/paper/prereg.md` must print 0.
7. **Run the checks.** `pytest -q`, `python tools/taskboard.py validate`,
   `python -m influence.events.run --synthetic` (simulated prices only).
8. **Commit once**, as the owner, with `[amendment]` in the subject, for example
   `[amendment] Amendment 1: board rosters, placebo decision rule`. Continuous
   integration lets the guard pass protected-file changes only for such a commit;
   locally, run `python tools/guard.py --allow-protected "amendment 1"` before it.
9. **Record the new registration hash.** A follow-up commit puts the amendment commit's
   hash on the "Registration commit" line and in the section 14 row, as was done at
   registration. Push both commits.
10. **Only then** may prices be downloaded (board item U03).

## What the amendment may and may not change

- May change: the board data and what follows from it mechanically (measures, cluster
  counts, the main-test subset, coverage, the power table); the decision rule's wording
  as decided on 2026-11-13; the gaps it closes; items the owner decides under step 3.
- May not change: the hypotheses, the signs or tested measures of existing events, the
  day-0 rule, the return models, the windows, the placebo design, or the conditions that
  define the main test. A wish to change any of these is a separate amendment with its
  own reason, made before the price download or not at all.
