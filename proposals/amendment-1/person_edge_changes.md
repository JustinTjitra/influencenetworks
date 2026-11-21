# Proposed change: Aburizal Bakrie's roles in Golkar

A proposal for amendment 1. Not applied. The edge is defined in the seed data and loaded
by `src/influence/build_seed_graph.py`; neither is changed here. Evidence level for every
row: search-result titles, URLs and the search tool's summary of result pages
(`research_notes/Influence network project sources/cabinet_party_facts.md`, section 4).
No page was opened. URLs are copied from those notes.

## Before (as in `data/processed/edges.csv` today)

| source | target | type | role | start | end | source_url | confidence |
|---|---|---|---|---|---|---|---|
| `p_aburizal_bakrie` | `party_golkar` | `party_role` | general chairman | 2009-10-09 | (open) | https://en.wikipedia.org/wiki/Aburizal_Bakrie | medium |

## After (three edges in place of one)

| source | target | type | role | start | end | source_url | confidence |
|---|---|---|---|---|---|---|---|
| `p_aburizal_bakrie` | `party_golkar` | `party_role` | general chairman | 2009-10-09 | 2016-05-17 | https://news.republika.co.id/berita/o7aq82366/setya-novanto-terpilih-secara-aklamasi | medium |
| `p_aburizal_bakrie` | `party_golkar` | `party_role` | chair of the Dewan Pembina (advisory board) | 2016-05-17 | 2024-08-22 | https://www.suara.com/news/2016/05/17/040600/munaslub-tunjuk-aburizal-ketua-dewan-pembina-golkar | medium |
| `p_aburizal_bakrie` | `party_golkar` | `party_role` | chair of the Dewan Kehormatan (honorary council) | 2024-11-07 | (open) | https://rm.id/baca-berita/parpol/242427/bahlil-umumkan-ical-ketua-dewan-kehormatan-agus-gumiwang-ketua-dewan-pembina | medium |

Second sources, for the owner to open before approving:

- End of the general chairmanship, 2016-05-17 (the extraordinary congress in Nusa Dua
  elected Setya Novanto): https://tirto.id/novanto-resmi-ditetapkan-sebagai-ketum-golkar-8Yd
  and https://setkab.go.id/setya-novanto-ketua-umum-presiden-jokowi-kita-hormati-pilihan-pemilik-suara-partai-golkar/
- Dewan Pembina chair confirmed again on 2019-12-05 for 2019 to 2024:
  https://news.detik.com/berita/d-4811657/kursi-baru-di-kabinet-airlangga
- End of the Dewan Pembina chairmanship, 2024-08-22 (Agus Gumiwang Kartasasmita named
  to it): https://www.medcom.id/nasional/politik/Obz5YReN-bukan-jokowi-bahlil-umumkan-agus-gumiwang-ketua-dewan-pembina-golkar
- Dewan Kehormatan chair from 2024-11-07, board term 2024 to 2029:
  https://news.republika.co.id/berita/smkzi3487/bahlil-umumkan-150an-pengurus-dpp-golkar-20242029-ini-susunan-lengkapnya

## What the change does to the measures

- The start date 2009-10-09 is kept as it is; the notes did not verify it.
- Between 2024-08-22 and 2024-11-07 no formal Golkar post is documented for him. On
  snapshots in that interval the edge is not active, so ties that rest on it (the
  `board_party` and `group_conn` measures of the firms linked to the Bakrie group) are
  not counted. Two registered events have their snapshot in that interval:
  `ev_inauguration_cabinet` (2024-10-20) and `ev_danantara_postponed` (2024-11-06).
  Neither is in the main test.
- From 2016 on the role is a council chair, not the general chair. The registered
  measures count any active `party_role` in a governing party, so the tie still counts
  where the edge is active. `board_family` counts ties to a governing party's *general
  chair*; after this change he is no longer one, so family ties that count through him
  on that ground stop counting from 2016-05-17. Whether a council chair should count as
  a party role at all is the owner's decision; the registered text says "an active
  `party_role`" without a rank.
- The roles for 2025 and 2026 are presumed from the 2024 to 2029 term; no result dated
  in those years names him with the title.

## Not proposed

The dates of the 2014 to 2016 dual-leadership dispute are not turned into edges: the
notes say outlets differ on them and they do not affect the 2016-05-17 end date.
