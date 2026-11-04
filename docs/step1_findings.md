# Step 1 findings (2026-10-19)

## What exists now
- Schema that rejects unsourced edges, low-confidence family ties, and convictions not citing a verdict.
- Seed data: 18 palm oil groups, 12 banks, 13 media groups, 62 people, 19 coalition events.
- Independent fact-check (data/seed/verification.csv): 62 confirmed, 19 partly confirmed,
  1 contradicted (fixed), 2 unverifiable (excluded).
- Graph: 150 nodes, 142 edges, all passing validation.

## Honest state of the data
- **No edge is rated high confidence.** Almost everything rests on news and Wikipedia.
  High confidence needs annual reports / exchange filings, which sit behind IDX's bot
  protection. Fixing this is the main job of step 2.
- 11 nodes have no edges yet: six private/foreign-owned banks, Astra Agro, PTPN, Agrinas,
  SSMS, and IDN's founder. They need controlling-shareholder data.
- Financing edges (bank -> palm oil group) are not loaded yet. Forests & Finance is the source.

## Early structural signal (not a finding yet)
Within 3 hops, party-linked outlets connect to their owner's party (MNC -> Perindo/NasDem/Hanura,
Media Group -> NasDem, Viva -> Golkar + Bakrie plantations, B-Universe -> NasDem), while Kompas,
Tempo, Kumparan, Detik and IDN connect to none. That is the treatment/comparison split the
coverage analysis needs. State bank boards are where parties show up most densely: NasDem
(BTN), Gelora (BTN), Demokrat (BNI), PKB and Gerindra (BRI), Golkar (Mandiri, until Dec 2025),
Gerindra (BSI).

## Publication cautions raised by the fact-check
- Do not attach ownership percentages to B-Universe; the 80% figure was a rumor.
- No direct Prabowo -> Arsari edge; the link is through Hashim (family).
- Never import news-site tags (e.g. "tersangka") as data.
- A source about a company's legal case does not make its chairman personally liable.

## Next (step 2)
1. Download Forests & Finance dataset; load bank -> group financing edges.
2. Get board/shareholder data from IDX annual reports (needs a real browser, or manual PDF pulls)
   to upgrade confidence to high and fill the isolated banks.
3. Download Trase Indonesian palm oil data for group-level company lists.
4. Start news ingestion: sitemap-based scrapers for detik, cnnindonesia, okezone, inews, viva,
   kumparan; manual check of kompas/tempo/metrotvnews/mediaindonesia robots rules.
