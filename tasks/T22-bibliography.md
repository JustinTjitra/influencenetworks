# T22: Bibliography from the research notes

## Goal
A BibTeX file and a short annotated bibliography for the paper, built only from
references that the research notes verified.

## Read first
- `CLAUDE.md`
- `research_notes/Influence network project sources/methodology_literature.md`
- `reports/Influence network project sources.md` (if present)

## Files you may create or edit
- `docs/paper/references.bib` (new)
- `docs/paper/literature.md` (new)

## Specification
- One BibTeX entry per reference the notes mark as verified, with key
  `<firstauthor><year><firstword>` (for example `fisman2001estimating`), and fields
  author, title, journal or booktitle, year, volume, number, pages, doi or url. Copy
  DOIs and URLs exactly from the notes. Never type one from memory.
- References the notes mark as not verified go in a final section of `literature.md`
  titled "Not yet verified" as plain text, and NOT into the `.bib` file.
- `literature.md`: grouped under "Political connections and firm value", "Ownership in
  East Asia", "Event-study method", "Inference with few events or few treated firms",
  "Common ownership and interlocks", "Pre-registration"; one or two sentences per
  reference on method and finding, taken from the notes, citing the BibTeX key.
- Under 200 lines for `literature.md`.

## Acceptance
`python - <<'PY'
import re
bib = open('docs/paper/references.bib').read()
keys = re.findall(r'@\w+\{([^,]+),', bib)
assert len(keys) >= 8 and len(keys) == len(set(keys)), keys
lit = open('docs/paper/literature.md').read()
missing = [k for k in keys if k not in lit]
assert not missing, missing
print(len(keys), 'entries, all cited in literature.md')
PY`

## Out of scope
Web searches, adding references that are not in the notes, writing the paper.
