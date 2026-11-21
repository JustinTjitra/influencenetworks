# Evidence notes for the proposed rows (amendment 1)

Written 2026-11-21 by the task loop from
`research_notes/Influence network project sources/cabinet_party_facts.md` and
`event_dates.md`. No web search was made for this task, and nothing about share prices,
index levels or market reaction was looked up or recorded.

## Evidence level, stated once

The notes opened no page. Their strongest labels are a search summary quoting the cited
page, a search summary attributing a statement to it, and a headline or URL that carries
the date. Rows here use only facts with one of those labels and at least one URL; they
are given `medium` confidence for that reason, although registered events with the same
level of evidence carry `high`. The owner should open the cited pages before approving,
and may then raise the confidence.

## `coalition_rows.csv` (4 rows)

| Row | Relation to the registered file | Basis in the notes |
|---|---|---|
| `st_golkar_2019` | New baseline row, 2019-10-23. Precedes every existing Golkar row. | Section 1: Airlangga Hartarto and Agus Gumiwang Kartasasmita appointed 2019-10-23; both carried into the October 2024 cabinet. |
| `st_gerindra_2019` | New baseline row, 2019-10-23. Precedes `st_gerindra_2024`. | Section 2: Prabowo Subianto Minister of Defence from 2019-10-23 while Gerindra general chairman; two seats. |
| `st_golkar_2024` | Replaces the existing row of the same id, which has no source URL and says "NO SOURCED ROW YET". Status unchanged (governing). | Section 1, October 2024: eight minister and three deputy-minister seats. |
| `st_pkb_2024` | Replaces the existing row of the same id and removes its flag `support_declared_ministers_not_verified`. Status unchanged (governing). | Section 3: Muhaimin Iskandar, PKB chair, sworn in as a coordinating minister on 2024-10-21. |

Effect: Golkar and Gerindra read as `governing` from 2019-10-23, so ties to them count
in the governing-party measures for the 2022 to 2024 events, which closes the first gap
in section 13 of the pre-registration. Removing the PKB flag changes the sensitivity run
with flagged codings counted as outside. Which firm-events change is known only after
the rebuild; it is not computed here.

## `event_rows.csv` (2 rows)

- `ev_election_quick_count` (2024-02-14): no sign (`ambiguous`), flagged anticipated
  and confounded, so it cannot enter the main test under the registered rules.
- `ev_protests_escalation` (2025-08-28, after the close): sign `-` under H1, flagged
  confounded, so it cannot enter the main test either.

**The signs still need the independent sign check** that every registered event went
through (a second agent derives a sign from a neutral description that gives no
direction; where it disagrees, the event becomes `ambiguous`).

**Confounder flags of neighbouring events.** Under the registered five-trading-day rule
with overlapping samples:

| Neighbour | Flag today | Flag after | What changes |
|---|---|---|---|
| `ev_publisher_rights` (day 0 2024-02-20) | 1 | 1 | The reason: the election becomes a listed event instead of a shock named in the notes. |
| `ev_mk_wamen_ruling` (day 0 2025-08-29) | 1 | 1 | The reason: the protests become a listed event instead of a recalled shock. |
| `ev_reshuffle_finance` (day 0 2025-09-09) | 1 | 1 | Nothing: it is at least six trading days after 2025-08-29 and is confounded by `ev_state_cash_placement`. Count the days on the real calendar in the attended session. |

No flag changes value, and the main-test subset is not affected by these two rows. The
notes of the two neighbours should be reworded to cite the listed events.

## Still open (not turned into rows)

- **Gerindra's posts in the Red and White Cabinet.** The existing `st_gerindra_2024` row
  has no source URL. The notes state that Gerindra held minister posts throughout only
  as an inference and give no URL that names Gerindra ministers in October 2024, so no
  replacement row is proposed. One targeted search would settle it.
- **Perindo, October 2024.** No minister found; the deputy-minister post rests on a
  search summary of Wikipedia only, and whether the person was a party member when
  appointed is not verified. The existing flagged row stays.
- **Hanura.** "None" rests on absence from seat lists, not on a statement.
- **Party status after the cabinet changes of 2026-10-01 and 2026-10-15**: not verified
  for any party. It is outside the event window.
- **Other ministers' party membership**: Bahlil Lahadalia's Golkar membership in 2021
  and Supratman Andi Agtas's Gerindra affiliation in August 2024 are not verified. They
  are not needed for the baseline rows.
- **Sandiaga Uno** left Gerindra on 2023-04-23 while remaining a minister. This does not
  change Gerindra's status, because Prabowo Subianto remained a minister.
- **Election row.** The hour of the first quick-count figures is not verified; it does
  not matter for day 0 because the exchange was closed. No original Reuters URL was
  found, only republished copies.
- **Protest row.** The hour of the incident on 2025-08-28 is not verified; sources say
  "Thursday evening". There is no established end date. Other candidate dates in the
  notes, not proposed as rows: the start on 2025-08-25, and the presidential statements
  of 2025-08-29 and 2025-08-31.
- **Presidential Instruction 1/2025 and the first Agrinas handover** (sections 3 and 4
  of the event notes) were outside this task's brief and are not proposed.
- **Aburizal Bakrie**: his original election date in 2009, the day of his re-election in
  December 2014, and direct evidence of his title in 2025 and 2026 are not verified.
