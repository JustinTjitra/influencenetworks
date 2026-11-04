# Step 2 findings (2026-10-19)

## Done
- **BTN 2025 annual report extracted** (data/primary/btn_ar2025_*.csv): the full board
  of commissioners before and after the March 2025 AGM, the January 2026 EGM appointee,
  shareholders, and the concurrent government posts the report itself discloses.
  An independent check against the PDF found 9 wrong start dates and 1 unsupported
  edge; all fixed. These are the project's first 26 high-confidence edges.
- **Provenance**: primary documents are registered with sha256 hashes in
  data/raw/documents.csv and cited as doc:<id>#p<page>. The loader rejects
  citations to unregistered documents.
- **Financing loader** for Forests & Finance (needs the download; see docs/RUNNING.md).
- **News crawler** (robots-respecting, sitemap or GDELT URL lists), article extraction
  with syndicated-copy flagging, and alias-based entity tagging. Tested offline.

## What the BTN report shows
Of BTN's seven commissioners after the January 2026 EGM, six hold a concurrent
government post or a documented party tie:

| Commissioner | Tie |
|---|---|
| Suryo Utomo (President Commissioner) | Ministry of Finance agency head |
| Dwi Ary Purnomo (VP, resigned Feb 2026) | BP BUMN deputy |
| Fahri Hamzah | Vice minister; Gelora deputy chair (news) |
| Pietra Paloh | Nephew of NasDem's chairman (news) |
| Panangian Simanungkalit | Housing ministry task force |
| Didyk Choiroel | Housing ministry secretary general |
| Ida Nuryanti | none disclosed |

Two caveats before reading anything into this. Civil-servant commissioners
representing the state shareholder are normal SOE governance, not patronage; the
interesting category is the party-linked seats (Fahri Hamzah, Pietra Paloh). And
the party ties come from news (medium confidence), because annual reports never
disclose party roles.

The report also shows timing worth using later: Fahri Hamzah was appointed at the
March 2025 AGM but only cleared OJK's fit-and-proper test on 2025-12-17, nine months
later. Pietra Paloh cleared it on 2025-08-15.

## Blocked
- **BNI**: the sustainability report you sent was truncated; the recoverable 231
  pages are low-resolution images (about 460 px wide), and OCR produced unusable
  text. Need BNI's 2025 annual report as a normal (text) PDF.
- **BRI, Mandiri, BSI**: no reports yet.
- **No web access from the build workspace**: Forests & Finance, GDELT and the news
  crawl must run on your machine (docs/RUNNING.md).
