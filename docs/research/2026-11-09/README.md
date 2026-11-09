# Research notes behind the Phase 1 event set (2026-11-09)

Working files from the agents that checked tickers, event dates and ownership facts
before registration. They are kept as the evidence trail for `data/mappings/tickers.csv`,
`data/events/events.csv`, `data/seed/coalition_events.csv` and `data/seed/supplement/`.

Read them with these limits in mind:

- **Snippet-level only.** The workspace could not open news or government sites, so every
  fact rests on a search-result snippet. No page was read in full.
- **The shared search budget ran out part-way.** Rows marked UNVERIFIED, MEMORY-ONLY or
  "recalled" are leads, not facts. Nothing so marked was entered in the data files as a
  fact; where such an item matters it appears in an event's notes with that label.
- **No prices.** The agents were told not to search for or report prices, returns or
  market reactions.

| File | Content |
|---|---|
| `tickers_bank_palm.csv`, `tickers_media.csv` | Listing dates, renames, suspensions, controlling shareholders |
| `events_palm.csv`, `events_coalition.csv`, `events_state_bank_media.csv` | Candidate events: announcement date, time of day, pre-signalling, nearby news, two sources |
| `graph_facts.csv` | State shareholdings 2019-2025, BSI ownership, cabinet posts by party |
| `sign_check_input.csv` | Neutral event descriptions given to the independent checker (no directions) |
| `sign_check_output.csv` | The checker's signs, arguments and "debatable" flags |
