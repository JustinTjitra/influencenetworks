# Supplement edges: independent source check (T26)

Files checked (read only): `data/seed/supplement/state_ownership_edges.csv` (13 edges, rows S1-S13 in CSV order, header excluded) and `data/seed/supplement/listed_entities_edges.csv` (19 edges, rows L1-L19 in CSV order).

## Method

- Date of check: 2026-11-21.
- Web searches used: 26 of the allowed 30, one per distinct cited source (state edges: 9 searches, because the two bisnis.com and kontan.co.id articles on the 2021 bank-syariah merger and rights issue each serve three edges; listed entities: 17 searches, because the SIMP and LSIP rows share one page and the ABBA and MARI rows share one article).
- No page could be opened in this session. Every judgement rests on the search result's title, URL and the summary text returned with it. Every row is therefore "snippet only". No row claims a page was read.
- Queries were worded around ownership, shareholding percentage, group membership or the cited article title. Nothing about share prices or market reactions was searched, read or recorded.
- The cited page itself was often not returned by the search. Where a row relies on a different result, the note says so. A value that the result did not show is `unsupported` or `could not check`, never `ok`.
- Dates in the file that the snippets do not show are marked `could not check`, even where the percentage is `ok`.
- Verdict kinds: `ok` (the result shows the value), `wrong` (the result shows a different value), `unsupported` (the result is on topic but does not show the claim), `could not check` (the cited source was not reached within the limits).
- Where a result URL is not reproduced, the reason is given in the row. Those slugs describe a share movement, which this project does not record.

## Searches and the URL relied on

| q | rows served | query used | URL of the result relied on |
|---|---|---|---|
| Q1 | S1 | pemerintah alihkan saham Bank Mandiri ke Indonesia Investment Authority kepemilikan Seri B 60% bisnis.com | https://finansial.bisnis.com/read/20211224/90/1481590/pemerintah-alihkan-373-miliar-saham-bank-mandiri-bmri-ke-indonesia-investment-authority |
| Q2 | S2 | pemerintah alihkan 8 persen saham Bank Mandiri ke INA kontan kepemilikan pemerintah 52 persen | https://finansial.bisnis.com/read/20211224/90/1481590/pemerintah-alihkan-373-miliar-saham-bank-mandiri-bmri-ke-indonesia-investment-authority (the cited kontan article was listed by title only: https://insight.kontan.co.id/news/pemerintah-alihkan-8-persen-saham-bank-mandiri-bmri-senilai-rp-2267-triliun-ke-ina) |
| Q3 | S3 | BRI rights issue skenario perubahan porsi kepemilikan pemerintah 56,75% bisnis.com | https://finansial.bisnis.com/read/20210615/90/1405557/bri-bbri-mau-rights-issue-begini-skenario-perubahan-porsi-kepemilikan-saham |
| Q4 | S4 | penuhi PP pemerintah alihkan 5,49 miliar saham BRI ke Indonesia Investment Authority kepemilikan pemerintah 56,82% | https://finansial.bisnis.com/read/20211224/90/1481605/penuhi-pp-pemerintah-alihkan-549-miliar-saham-bri-ke-indonesia-investment-authority |
| Q5 | S5 | pasca inbreng porsi kepemilikan saham INA di Bank Mandiri BMRI dan BRI BBRI pemerintah 53,19% | https://finansial.bisnis.com/read/20211227/90/1482040/pasca-inbreng-begini-porsi-kepemilikan-saham-ina-di-bank-mandiri-bmri-dan-bri-bbri |
| Q6 | S6 | pemerintah dividen BNI BBNI 2023 kepemilikan Negara Republik Indonesia 60% saham seri B | https://finansial.bisnis.com/read/20230315/90/1637745/pemerintah-cuan-rp439-triliun-dari-dividen-bni-bbni (class of share seen only in the title of https://keuangan.kontan.co.id/news/60-saham-seri-b-dan-c-bbni-beralih-ke-pt-biro-klasifikasi-indonesia, listed by Q7) |
| Q7 | S7 | 60% saham seri B Bank BTN BBTN dialihkan ke Biro Klasifikasi Indonesia kepemilikan pemerintah | https://keuangan.kontan.co.id/news/sebanyak-60-saham-seri-b-bank-btn-bbtn-dialihkan-ke-biro-klasifikasi-indonesia |
| Q8 | S8, S10, S12 | resmi jadi BRIS 1 Februari merger Bank Syariah BUMN kepemilikan Mandiri 50,95% BNI 24,91% BRI 17,29% | https://finansial.bisnis.com/read/20210201/231/1350470/bismillah-hari-ini-presiden-jokowi-resmikan-bank-syariah-indonesia-bris (merger date only; the cited kontan page was not returned) |
| Q9 | S9, S11, S13 (and the 50.83% in S8) | rights issue BSI BRIS pembagian pemilikan BRI BNI Mandiri Mandiri 51,47% BNI 23,24% BRI 15,38% | https://finansial.bisnis.com/read/20230108/90/1616053/rights-issue-bsi-bris-begini-pembagian-pemilikan-bri-bbri-bni-bbni-dan-mandiri-bmri |
| Q10 | L1 | daftar 12 raja kelapa sawit RI kekayaan Sinar Mas SMAR pemegang saham Purimas Sasmita cnbcindonesia | https://www.cnbcindonesia.com/market/20250807075238-17-655799/daftar-12-raja-kelapa-sawit-ri-segini-harta-kekayaannya |
| Q11 | L2, L3 | Salim Ivomas Pratama SIMP shareholders Indofood Agri Resources 72% Lonsum 59.5% indonesia-investments | https://www.indonesia-investments.com/business/indonesian-companies/salim-ivomas-pratama/item570 ; also https://investor.indofoodagri.com/misc/ar2024/120/ and https://londonsumatra.com/Contents/shareholders-composition |
| Q12 | L4 | Astra Agro Lestari AALI Astra International ownership 79.68% indonesia-investments | https://www.indonesia-investments.com/business/indonesian-companies/agro-astari-lestari/item196 |
| Q13 | L5 | POSCO mandatory tender offer SGRO Sampoerna Agro AGPA ownership idnfinancials | https://investortrust.id/market/86024/posco-akuisisi-65-72-sampoerna-agro-sgro-putera-sampoerna-lepas-pengendalian (the cited idnfinancials page was not returned) |
| Q14 | L6 | TP Rachmat tambah koleksi saham Triputra Agro TAPG kepemilikan persentase bisnis.com | https://market.bisnis.com/read/20250212/192/1838961/tp-rachmat-tambah-koleksi-saham-triputra-agro-tapg-jadi-103-miliar |
| Q15 | L7 | Dharma Satya Nusantara DSNG shareholders Triputra Investindo Arya ownership indonesia-investments | https://www.indonesia-investments.com/business/indonesian-companies/dharma-satya-nusantara/item1120 |
| Q16 | L8 | Eagle High Plantations BWPT pemegang saham Rajawali Capital International 37,7% FIC Properties 37% investortrust | https://investortrust.id/market/66304/didukung-kuat-pemegang-saham-eagle-high-bwpt-alokasikan-keuntungan-2024-untuk-ini |
| Q17 | L9 | First Resources ANJT mandatory tender offer 100% Fangionos ownership completed idnfinancials | https://market.bisnis.com/read/20251006/192/1917671/perusahaan-ciliandra-fangiono-tuntaskan-tender-offer-anjt-rp28869-miliar (the cited idnfinancials page was not returned) |
| Q18 | L10 | UNSP Bakrie Sumatera Plantations private placement 14,51 billion shares largest shareholder Bakrie Capital Indonesia idnfinancials | https://investasi.kontan.co.id/news/bakrie-sumatera-unsp-private-placement-1450-miliar-saham-seri-b-ini-rinciannya (the cited idnfinancials page was not returned) |
| Q19 | L11 | SSMS Sawit Sumbermas Sarana expansion SML acquisition Citra Borneo Indah ownership 62.30% | https://market.bisnis.com/read/20251124/192/1931283/sawit-sumbermas-ssms-akuisisi-perusahaan-afiliasi-rp16-triliun |
| Q20 | L12 | Lo Kheng Hong BMTR struktur kepemilikan MNC Asia Holding 45,99% Hary Tanoesoedibjo stockwatch | https://market.bisnis.com/read/20250704/7/1890469/data-terbaru-saham-bmtr-yang-dipegang-lo-kheng-hong-awal-juli-2025 (the cited stockwatch page was not returned) |
| Q21 | L13 | Lo Kheng Hong BMTR kepemilikan MNCN Global Mediacom 39,80% pemegang saham bisnis.com | https://market.bisnis.com/read/20250805/7/1899495/emiten-jagoan-lo-kheng-hong-bmtr-borong-saham-mncn |
| Q22 | L14 | MNCN Media Nusantara Citra kepemilikan MSIN MNC Studios International 72,81% kabarbursa | https://www.kabarbursa.com/market-hari-ini/mncn-borong-saham-msin-hingga-579-700-lembar.md |
| Q23 | L15 | IPO MNC Vision Networks IPTV Global Mediacom anak usaha dana Rp856 miliar bisnis.com | https://market.bisnis.com/read/20190617/192/934688/ipo-mnc-vision-networks-targetkan-dana-hingga-rp856-miliar ; also https://www.indotelko.com/amp/read/1562640149/MNC-Play-1-5 |
| Q24 | L16 | Emtek EMTK kepemilikan Surya Citra Media SCMA 66,11% pembelian saham bisnis.com | https://market.bisnis.com/read/20250805/192/1899390/emtek-emtk-borong-325-juta-saham-surya-citra-media-scma |
| Q25 | L17 | media landscape in Indonesia Visi Media Asia VIVA owns Intermedia Capital MDIA 89.99% fulcrum.sg | https://www.cnbcindonesia.com/market/20190319075543-17-61451/mdia-viva-private-placement-erick-thohir-akan-masuk (the cited fulcrum.sg page was not returned) |
| Q26 | L18, L19 | grup Mahaka MARI ABBA Erick Thohir Menpora Beyond Media pemegang saham 40,35% Mahaka Media 16,37% | The article cited in the CSV for co_abba and co_mari (its date code in the URL is 20250917). Its URL is not reproduced because the slug names a share movement. |

## Table: state-ownership edges (S1-S13)

All rows: snippet only.

| row | edge | field | value in file | what the source shows | verdict | read | q | note |
|---|---|---|---|---|---|---|---|---|
| S1 | gov_republic owns bank_mandiri | pct | 60.00 | Government held 27.99 billion Series B shares, 60 percent, before the transfer | ok | snippet only | Q1 | |
| S1 | | end_date | 2021-12-22 | Transfer to the Indonesia Investment Authority on 2021-12-23 | ok | snippet only | Q1 | |
| S2 | gov_republic owns bank_mandiri | pct | 52.00 | Government stake went from 60 to 52 percent, 24.27 billion shares; INA holds 8 percent | ok | snippet only | Q2 | Value taken from the bisnis.com result; the cited kontan article was listed by title only |
| S2 | | start_date | 2021-12-23 | Transfer on 2021-12-23 | ok | snippet only | Q2 | |
| S2 | | end_date | 2025-03-21 | Cited 2021 article cannot show a 2025 date. A result on the 2025 transfer to the Danantara operating holding gives 2025-03-22 for BTN only | could not check | snippet only | Q2 | Consistent with the file but not shown for Mandiri |
| S3 | gov_republic owns bank_bri | pct | 56.75 | Government share before the 2021 rights issue 56.75% | ok | snippet only | Q3 | |
| S3 | | end_date | 2021-09-28 | Article is dated June 2021 and gives scenarios only | could not check | snippet only | Q3 | The file itself says the date is approximate |
| S4 | gov_republic owns bank_bri | pct | 56.82 | Before the transfer to INA the government held 86.1 billion Series B shares, 56.82% | ok | snippet only | Q4 | |
| S4 | | start_date | 2021-09-29 | Not in the result | could not check | snippet only | Q4 | |
| S4 | | end_date | 2021-12-22 | Transfer on 2021-12-23 | ok | snippet only | Q4 | |
| S5 | gov_republic owns bank_bri | pct | 53.19 | After the transfer 80.61 billion shares, 53.19%; INA 3.63% | ok | snippet only | Q4, Q5 | |
| S5 | | start_date | 2021-12-23 | Transfer on 2021-12-23 | ok | snippet only | Q4, Q5 | |
| S5 | | end_date | 2025-03-21 | Not shown for BRI by the cited 2021 article | could not check | snippet only | Q5 | |
| S6 | gov_republic owns bank_bni | pct | 60.00 | Government holds 60 percent of BBNI (11.18 billion shares per the result; another source gives 11.89 billion) | ok | snippet only | Q6 | Share count differs between sources; the file does not use it |
| S6 | | role | Series B shareholder | The result does not name the share class. A different result's title refers to 60% of Series B and C shares of BBNI moving to the Biro Klasifikasi Indonesia | unsupported | snippet only | Q6 | Probably right; confirm in the BNI annual report. See Proposed corrections |
| S6 | | end_date | 2025-03-21 | Not in the cited 2023 article | could not check | snippet only | Q6 | |
| S7 | gov_republic owns bank_btn | pct | 60.00 | 60% of Series B shares (8.42 billion) moved to the Biro Klasifikasi Indonesia on 2025-03-22 | ok | snippet only | Q7 | |
| S7 | | role | Series B shareholder | Title: 60 percent of Series B shares of Bank BTN | ok | snippet only | Q7 | |
| S7 | | end_date | 2024-12-31 | The source shows 60% until 2025-03-22. 2024-12-31 is a modelling choice explained in the file note | ok | snippet only | Q7 | The note in the file describes the choice accurately |
| S8 | bank_mandiri owns bank_bsi | pct | 50.95 | The cited kontan article was not returned; no result shows 50.95 | could not check | snippet only | Q8 | |
| S8 | | start_date | 2021-02-01 | Merger effective 2021-02-01 | ok | snippet only | Q8 | |
| S8 | | note: 50.83% | 50.83% | Mandiri stake before the 2022 rights issue was 50.83% (date of that figure not shown) | ok | snippet only | Q9 | Value only; "February 2022" not confirmed |
| S9 | bank_mandiri owns bank_bsi | pct | 51.47 | Stake rose from 50.83% to 51.47% after the rights issue | ok | snippet only | Q9 | |
| S9 | | start_date | 2022-12-23 | Rights issue ran 19-23 December 2022 | ok | snippet only | Q9 | |
| S9 | | end_date | 2026-01-22 | Not in the 2023 article | could not check | snippet only | Q9 | |
| S10 | bank_bni owns bank_bsi | pct | 24.91 | Cited page not returned. A result gives BNI at 24.85% before the 2022 rights issue, which differs slightly from 24.91 and may be a later date | could not check | snippet only | Q8, Q9 | Needs the merger-date register |
| S10 | | start_date | 2021-02-01 | Merger effective 2021-02-01 | ok | snippet only | Q8 | |
| S11 | bank_bni owns bank_bsi | pct | 23.24 | Stake went from 24.85% to 23.24%; BNI took up 500 million of 1.24 billion new shares | ok | snippet only | Q9 | |
| S11 | | start_date | 2022-12-23 | Rights issue ran 19-23 December 2022 | ok | snippet only | Q9 | |
| S12 | bank_bri owns bank_bsi | pct | 17.29 | Cited page not returned. A result gives BRI at 17.25% before the 2022 rights issue | could not check | snippet only | Q8, Q9 | Small difference; date of the figure unknown |
| S12 | | start_date | 2021-02-01 | Merger effective 2021-02-01 | ok | snippet only | Q8 | |
| S13 | bank_bri owns bank_bsi | pct | 15.38 | Stake fell from 17.25% to 15.38% | ok | snippet only | Q9 | The result notes the same share count is shown before and after, which looks like a reporting slip in the article; the percentage is the part relied on |
| S13 | | start_date | 2022-12-23 | Rights issue ran 19-23 December 2022 | ok | snippet only | Q9 | |
| S13 | | note: last seen June 2025 | June 2025 | Not in the result | could not check | snippet only | Q9 | |

## Table: listed-entity edges (L1-L19)

All rows: snippet only. The field checked for these edges is the group membership and the figures in the note.

| row | edge | field | value in file | what the source shows | verdict | read | q | note |
|---|---|---|---|---|---|---|---|---|
| L1 | co_smar member_of_group pg_sinarmas | member_of_group | listed entity of the group | The result lists the Widjaja family as owners of the Sinar Mas Group and names Golden Agri-Resources under the group, but does not name SMAR | unsupported | snippet only | Q10 | |
| L1 | | note: parent PT Purimas Sasmita | direct parent reported | No result mentions Purimas Sasmita | could not check | snippet only | Q10 | |
| L2 | co_simp member_of_group pg_salim | note: IndoAgri holds 72.00% | 72.00% | Profile lists Indofood Agri Resources at 72.00% | ok | snippet only | Q11 | |
| L2 | | note: 73.46% April 2026 | 73.46% | The IndoAgri annual report page shows 73.46% effective holding; a second result also gives 73.46% for April 2026 but its URL slug names a share movement and is not reproduced | ok | snippet only | Q11 | Date "April 2026" rests on the unrecorded second result |
| L3 | co_lsip member_of_group pg_salim | note: SIMP holds 59.5% of Lonsum | 59.5% | Profile says 59.5%; Lonsum's own table shows 59.51% | ok | snippet only | Q11 | |
| L4 | co_aali member_of_group pg_astra_agro | note: Astra International 79.68% | 79.68% | Profile and company page show 79.68% | ok | snippet only | Q12 | |
| L5 | co_sgro member_of_group pg_sampoerna_agro | note: Sampoerna until 2025-11-19, then AGPA | control change 2025-11-19 | A Sampoerna-linked seller (Twinwood Family Holdings) sold 65.72% to AGPA Pte Ltd, a POSCO International subsidiary, completed 2025-11-19 | ok | snippet only | Q13 | |
| L5 | | note: renamed 2026-01-13 | 2026-01-13 | Result says the company was renamed Prime Agri Resources; no date | could not check | snippet only | Q13 | |
| L6 | co_tapg member_of_group pg_triputra | member_of_group | listed entity of the group | The result shows an individual (TP Rachmat) holding about 5.2% of TAPG. It does not show the group, a parent company or a group holding | unsupported | snippet only | Q14 | See Proposed corrections |
| L7 | co_dsng member_of_group pg_dsn | note: Triputra Investindo Arya largest holder | largest holder | Profile lists Triputra Investindo Arya at 27.04%, then Krishna Kapital Investama 14.46%; another result gives 28.33% for end April 2026 | ok | snippet only | Q15 | The profile itself cites the 2015 annual report |
| L8 | co_bwpt member_of_group pg_rajawali | note: RCI 37.7% and FIC Properties 37% | 37.7% and 37% | Same figures: RCI as controller 37.7%, FIC Properties 37%, public 23.98% | ok | snippet only | Q16 | |
| L9 | co_anjt member_of_group pg_first_resources | note: 91.17% purchase | 91.17% | 91.17% is the direct stake before the later tender offer, which took it to 95.92% | ok | snippet only | Q17 | The file does not mention the later 95.92% (3 October 2025); the cited page's title speaks of 100%, which the results do not support |
| L9 | | start_date | 2025-05-06 | Date of completion not shown | could not check | snippet only | Q17 | |
| L10 | co_unsp member_of_group pg_bakrie | note: placement completed 2026-08-04 | 2026-08-04 | Placement of 14,505,112,734 Series B shares was scheduled for 2026-08-04; completion is not shown | could not check | snippet only | Q18 | |
| L10 | | note: non-Bakrie entity largest holder; control stays with Bakrie Capital Indonesia | as stated | No result names the largest holder after the placement or the Bakrie Capital Indonesia stake | unsupported | snippet only | Q18 | The file already marks this as not verified |
| L11 | co_ssms member_of_group pg_ssms | note: Citra Borneo Indah 62.30% | 62.30% | Citra Borneo Indah is the controlling shareholder with 62.30% (62.3% in other reports) | ok | snippet only | Q19 | |
| L12 | co_bmtr member_of_group mg_mnc | note: MNC Asia Holding 45.99% (end April 2026) | 45.99% | No result shows 45.99. Figures seen: 45.75% (mid-2023) and 33.98% (July 2025) | unsupported | snippet only | Q20 | See Proposed corrections |
| L12 | | note: other report gives 33.98% | 33.98% | July 2025 report gives MNC Asia Holding 33.98% | ok | snippet only | Q20 | |
| L13 | co_mncn member_of_group mg_mnc | note: Global Mediacom 39.80% (2025-08-01) | 39.80% | Global Mediacom held 5.98 billion MNCN shares, 39.80%, early August 2025 | ok | snippet only | Q21 | |
| L14 | co_msin member_of_group mg_mnc | note: Media Nusantara Citra 72.81% (August 2024) | 72.81% | MNCN's stake rose to 72.813% in August 2024 | ok | snippet only | Q22 | A March 2023 report in the results gives 73.77%, a higher earlier figure; not resolved here |
| L15 | co_iptv member_of_group mg_mnc | note: Global Mediacom subsidiary at 2019 IPO | subsidiary | IPO of MNC Vision Networks in 2019; the parent Global Mediacom kept 90% after the offer | ok | snippet only | Q23 | The 90% comes from the indotelko result, not the cited page |
| L16 | co_scma member_of_group mg_emtek | note: Elang Mahkota Teknologi 66.11% (August 2025) | 66.11% | Stake raised to 66.11% by the purchase reported 2025-08-05 | ok | snippet only | Q24 | Later reports give higher figures; the file dates its value to August 2025 |
| L17 | co_mdia member_of_group mg_viva | note: 89.99% owned by Visi Media Asia | 89.99% | Cited fulcrum.sg page not returned; no result shows 89.99 | could not check | snippet only | Q25 | |
| L17 | | member_of_group | listed entity of the group | A 2019 CNBC Indonesia article refers to MDIA as a subsidiary of VIVA (Visi Media Asia) | ok | snippet only | Q25 | Relation only, from a different page than the cited one |
| L18 | co_abba member_of_group mg_mahaka | note: Beyond Media 40.47% | 40.47% | Beyond Media is reported as controller with 1,592,831,618 shares, 40.47% | ok | snippet only | Q26 | The result dates the 40.47% figure to a 2023 article |
| L18 | | note: 57.81% in 2019 | 57.81% | Results show 57.81% in 2019-2020 reporting | ok | snippet only | Q26 | |
| L18 | | note: "40.47% in September 2026" | September 2026 | The cited article carries the date 2025-09-17 (date code in its URL), so it cannot support a figure dated September 2026. No source seen is dated September 2026 | unsupported | snippet only | Q26 | Either the date in the note is a slip, or a later source is missing; see Proposed corrections |
| L19 | co_mari member_of_group mg_mahaka | note: Beyond Media 40.35% | 40.35% | Beyond Media holds about 40.35% of MARI | ok | snippet only | Q26 | |
| L19 | | note: Mahaka Media 16.37% | 16.37% | Mahaka Media holds 16.37% (860,034,567 shares) | ok | snippet only | Q26 | |

## Proposed corrections

The CSV files are protected and are not edited here. These are proposals for the owner's amendment process.

1. S6 (bank_bni, role "Series B shareholder", `unsupported`): no replacement value. Keep the role, and attach a source that names the share class: the BNI annual report share register, or the article whose title refers to 60% of Series B and C shares of BBNI (https://keuangan.kontan.co.id/news/60-saham-seri-b-dan-c-bbni-beralih-ke-pt-biro-klasifikasi-indonesia, title seen only).
2. L1 (co_smar, group membership, `unsupported`): no replacement value found. Replace the cited page with a source that names SMAR and its direct parent, for example the SMAR annual report shareholder table. Until then the row should stay at confidence medium or lower.
3. L6 (co_tapg, group membership, `unsupported`): no replacement value found. The cited article shows an individual's holding of about 5.2%, not group membership. A source naming the Triputra holding company and its stake in TAPG is needed.
4. L10 (co_unsp, post-placement holder statement, `unsupported`): no replacement value. Keep the "not verified" wording and add the KSEI register or the company's disclosure after 2026-08-04 once the owner has it.
5. L12 (co_bmtr, 45.99%, `unsupported`): no replacement for 45.99. Dated figures seen: 33.98% (July 2025), source https://market.bisnis.com/read/20250704/7/1890469/data-terbaru-saham-bmtr-yang-dipegang-lo-kheng-hong-awal-juli-2025 (snippet only). The owner should confirm the end-April 2026 figure from the stockwatch page or the KSEI register.
6. L18 (co_abba, "40.47% in September 2026", `unsupported`): the cited 2025 article (date code 20250917 in the URL given in the CSV for co_abba) cannot support a figure dated September 2026. Either the date in the note is a slip, or a later source is missing. The owner should confirm the date the 40.47% belongs to and cite a source of that date. No replacement value is offered; the search dated the 40.47% figure to a 2023 article.

Rows marked `could not check` need a page opened on the owner's machine: S2, S3, S4, S5, S6, S8, S9, S10, S12, S13 (dates and the merger-date percentages), L1, L5, L9, L10 and L17.

## Count of verdicts

63 rows (34 state-ownership rows, 29 listed-entity rows).

| verdict | state-ownership | listed entities | total |
|---|---|---|---|
| ok | 23 | 19 | 42 |
| wrong | 0 | 0 | 0 |
| unsupported | 1 | 5 | 6 |
| could not check | 10 | 5 | 15 |

Searches used: 26 of 30.
