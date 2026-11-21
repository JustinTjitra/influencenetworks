# Amendment 1: replacement text for `docs/paper/prereg.md`

Draft written 2026-11-21 by the task loop. Not applied. It becomes part of the
pre-registration only when the owner approves it in an attended session (see
`README.md` in this folder). Section numbers are those of the pre-registration at
registration commit `ba4db0fa9d9cf8ab82199db791d32f4823dd28a0`.

Text between `>>>` and `<<<` is the exact replacement. `TO FILL AFTER ROSTERS` marks a
value that must be produced mechanically by the named command and pasted in unchanged.
Nothing here may be filled, adjusted or reworded after a price has been downloaded.

## Section 9 (decision rule)

Replace the numbered list and the sentence that introduces it. The wording is the one
decided on 2026-11-13 (`docs/phase1_status.md`, "Decided 2026-11-13", item 3).

>>>
A result **holds** only if the stacked estimate under specification B, window [-1,+1],
0/1 connection (1) has the registered sign under all three return models, and
(2) has a placebo p-value below 0.05 under all three. The two-way clustered p-value
is reported but plays no part in the decision, because with few event dates it is
unreliable.

With 200 draws the smallest possible placebo p-value is 1/201, so "below 0.05" means
the real estimate beats at least 191 of the 200 pseudo-dates.
<<<

The two sentences that follow in section 9 (the rule applies to the main-test set and to
its subsets; anything that fails any part is "does not hold"; `results_summary.md`
applies the rule mechanically) stay as they are.

Consequences to carry through in the same commit:

- Section 0, point 2: replace "shows that the registered decision rule would almost
  never be met at that sample size" by `TO FILL AFTER ROSTERS` (one sentence stating
  what the rerun power simulation shows under the amended rule; see section 12 below).
- Section 7, last sentence of the paragraph on standard errors ("which is why the
  placebo is part of the decision rule"): replace by "which is why the decision rule
  rests on the placebo (section 9)".
- The code that writes `decisions.csv` and `results_summary.md`
  (`src/influence/events/`) must apply the amended rule. That code is a registered
  file: the change is made in the attended session, with a test, in the same commit.

## Section 4 (coverage)

Replace the "Coverage" bullet's second and third sentences.

>>>
After amendment 1 the registered rosters cover TO FILL AFTER ROSTERS of the 34 firms
(commissioners: TO FILL AFTER ROSTERS; directors: TO FILL AFTER ROSTERS), from the
annual reports listed in `data/raw/documents.csv`, each row cited by page and checked
independently (`docs/intake/ROSTER_PROTOCOL.md`). Coverage is above 0 for
TO FILL AFTER ROSTERS % of firm-events. A board measure of zero with coverage 0 is zero
by absence of data.
<<<

Replace the "Graph freeze" bullet.

>>>
- **Graph freeze.** The measures are those built from the graph at the amendment 1
  commit (`data/processed/connection_measures.parquet`). Any later change to the graph
  is a deviation, reported as such.
<<<

Rule for filling: the numbers come from `python -m influence.connections.build_measures`
run on the amended graph, read from its printed coverage summary. Firms whose report
could not be obtained or was a scan are named in section 13, not silently left out.

## Section 3 (main-test subset)

Replace the event table's last four columns for every row, and the block that begins
"**The main-test subset is exactly:**", with the output of
`python -m influence.connections.build_measures` on the amended graph, pasted unchanged
from `data/processed/connection_event_summary.csv`.

>>>
**The main-test subset is exactly:**

TO FILL AFTER ROSTERS (one bullet per event: id, date, description, measure, sign,
treated firms; in date order; no event added, removed or reordered by hand)
<<<

Rules, fixed now:

- The four conditions for the main test do not change: not anticipated, not confounded,
  sign `+` or `-`, at least three treated and three untreated clusters.
- No sign, flag, date or tested measure of an existing event changes in this amendment
  on account of the rosters. Only `n_treated`, the cluster counts, `enough_clusters` and
  `main_test` can change, and only because board data changed the measures.
- If the proposed event rows and party-status rows (`event_rows.csv`,
  `coalition_rows.csv` in this folder) are approved, they are applied before the
  rebuild, and the confounder flags of neighbouring events are recomputed by the
  registered five-trading-day rule. Each flag that changes is listed in section 14.
- The sentence in section 0, point 2 ("Two events pass every rule") is replaced by the
  count the rebuild gives: TO FILL AFTER ROSTERS.

## Section 12 (power)

After the rebuild, rerun `python -m influence.events.power` (simulated prices only; it
reads no real price) and replace the table and the paragraph under it.

>>>
At amendment 1, with TO FILL AFTER ROSTERS main-test events and the controls the sample
carries:

| Planted gap | Mean estimate | Spread (sd) | Share meeting the decision rule |
|---|---|---|---|
| TO FILL AFTER ROSTERS | | | |

TO FILL AFTER ROSTERS (two sentences: the smallest gap detectable with 80% power, and
how often the amended rule is met when no gap is planted)
<<<

If the power script reports only the clustered test, the attended session extends it to
report the share meeting the amended rule before the table is filled; the script is a
registered file.

## Section 13 (known gaps)

Replace the bullets this amendment closes; keep the others word for word.

>>>
- **Board data.** Closed by amendment 1 for TO FILL AFTER ROSTERS firms. Still without a
  primary-source roster: TO FILL AFTER ROSTERS (tickers, with the reason for each).
- **Party status before October 2024.** TO FILL AFTER ROSTERS (closed, if the baseline
  rows for Golkar and Gerindra in `proposals/amendment-1/coalition_rows.csv` are
  approved; otherwise this bullet stays as registered).
- **Aburizal Bakrie's Golkar role.** TO FILL AFTER ROSTERS (closed, if the change in
  `proposals/amendment-1/person_edge_changes.md` is approved; otherwise as registered).
- **Events not listed for lack of a sourced date:** TO FILL AFTER ROSTERS (which of the
  general election of 2024-02-14 and the protests of late August 2025 are now listed;
  Presidential Instruction 1/2025 and the first Agrinas handover remain unlisted).
- **Checks still owed:** TO FILL AFTER ROSTERS (the outcome of the independent
  comparison of the supplement edges, board task T26, or "still owed").
<<<

Unchanged by this amendment: tickers (SCMA's listing date, suspension histories), times
of day, and the statement that dates rest on search-result snippets unless the owner has
opened the pages, in which case say which.

## Section 14 (amendment log)

Replace the row `| | | none |`.

>>>
| TO FILL AFTER ROSTERS (date) | TO FILL AFTER ROSTERS (commit) | Amendment 1, before any price download. (a) Board rosters for TO FILL AFTER ROSTERS firms added from annual reports; measures, cluster counts and the main-test subset recomputed mechanically (sections 3, 4). (b) Decision rule rests on the placebo; the clustered p-value is reported only (section 9). (c) Power table rerun (section 12). (d) TO FILL AFTER ROSTERS: party-status rows, the Bakrie edge, added events and the confounder flags they change, each listed, or "not included". (e) TO FILL AFTER ROSTERS: graph changes from the items under "Open questions" below, or "none". |
<<<

Also replace the first line of the document, `Registration commit: ...`, by the hash of
the amendment commit, and keep the original hash in section 14's row for the record.

## Open questions the owner should settle in the same amendment

These were found by the task loop and are not part of the wording decided on 2026-11-13.
Each either goes into amendment 1 or is written into section 13 as a known gap. Leaving
them for after the price download would make them deviations.

1. **Parallel edges overwrite each other in the graph**
   (`proposals/2026-11-20-graph-edge-key-collision.md`). The graph holds 80 of the 180
   lending edges. Scope, checked against section 4: the two registered main-test events
   test `state_own` and `board_office`, which do not use lending edges, and the 0/1
   indicator for `all` uses the six tie measures, not `dist_gov`. What is affected is
   `dist_gov`, and through it the composite and the scaled value for events whose tested
   measure is `all`. If fixed, section 4 gains one sentence and section 15 one item.
2. **Should lending count as a path in `dist_gov`?** As registered it does ("shortest
   undirected path"), so a private bank can be three steps from the state by lending to
   the same group as a state bank. Either keep it and say so in section 4, or restrict
   the path to ownership, board, office, party and family edges.
3. **Title-like name tokens** (log of 2026-11-20, run 3): relevant only if person
   matching across companies is used for the rosters. The roster protocol does not
   merge names, so this can stay outside amendment 1.
