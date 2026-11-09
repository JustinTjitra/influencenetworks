# Indonesian Influence Network (MVP: palm oil + banking)

Maps **documented** relationships between Indonesian politicians, parties, palm oil
groups, banks and media owners, then tests whether outlets cover entities in their
owner's network differently from unlinked entities.

> **Current design.** The project's primary goal is now an event study of political
> connections and firm value, with a stakeholder exposure monitor on top; see
> `docs/DESIGN.md`. The pre-registration is `docs/paper/prereg.md`, the current state is
> `docs/phase1_status.md`, and `docs/RUNNING.md` section 5 has the commands. The
> media-coverage question below is the original framing and remains a later module.

## Research question

Do Indonesian news outlets cover companies and politicians inside their owner's
business/political network more favourably (or less often, on negative topics)
than comparable entities outside it?

## Scope (MVP)

- Sectors: palm oil groups (~12-15) and banks (~10-12, all state banks included)
- Media: party-linked groups (MNC, Media Group, Viva) vs. comparison outlets
- Window: 2021-2025 coverage
- Out of scope for v1: tech sector, hoax/misinformation module

## Layout

```
data/seed/        hand-curated seed lists (groups, banks, media, people, events)
data/raw/         downloaded source material (never edited)
data/processed/   nodes.csv / edges.csv that pass validation
docs/             source access report, methodology, legal notes
src/influence/    schema, graph loading, (later) scrapers, NLP, analysis
tests/
```

## Data rules

1. **Every edge has a source URL, a source type and a confidence level.**
   The loader rejects edges without one.
2. **Relationships, not accusations.** There is no edge type for suspicion or
   wrongdoing. Convictions are recorded only with a link to the verdict.
3. **Family ties need medium or high confidence.**
4. **Everything is time-bound** so coverage can be matched to the relationships
   that existed when an article was published.
5. Raw downloads are kept unmodified; all cleaning happens in code.

## Legal note

Publishing this involves defamation exposure (ITE Law, KUHP) and personal data
obligations (UU PDP). Before any public release: sourced edges only, a visible
correction channel, and review by an Indonesian lawyer. See docs/.

## Running

```
pip install -e ".[dev]"
pytest
```
