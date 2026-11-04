# BTN AR 2025 transcription check

Source: data/raw/docs/btn_annual_report_2025.pdf (pdftotext -layout). Rows numbered 1-20 in CSV order (header excluded).
Fields not listed for a row were checked and are ok (or blank, which is fine).

| row | field | CSV value | document says (page) | verdict |
|---|---|---|---|---|
| 1 co_danantara_am owns bank_btn | pct | 60.00 | PT Danantara Asset Management 8,420,666,647 shares, 60.00% at 2025-12-31 (p205, p203) | ok |
| 1 | note: share count | 8420666647 | 8,420,666,647 (p205) | ok |
| 1 | note: RI 60.00% at 2025-01-01 | 60.00% | Republic of Indonesia 8,420,666,648, 60.00% (p205, p203) | ok |
| 1 | note: RI keeps 1 share | 1 share | RI 1 share, 0.00% at 2025-12-31 (p203, not p205) | ok (cite p203) |
| 1 | role | Series B shareholder | Majority Series B holder moved from Ministry of SOEs to the Operational Holding (p414) | ok |
| 1 | start_date | 2025 | Transfer happened in 2025; no exact date given (p203/p205/p414) | ok |
| 2 gov_danantara controls co_danantara_am | note | BKI renamed DAM, Operational Holding, GR 15/2025 | Same wording (p414, row 3 of table) | ok |
| 2 | edge (controls) | BPI Danantara controls DAM | p414 names BPI Danantara and the Operational Holding as new controlling shareholders/regulators of the Bank. It does not say BPI Danantara controls DAM | unsupported (inferred) |
| 3 Suryo Utomo | role, start, OJK date | President Commissioner; 2025-03-26; OJK 2025-06-26 | Same (p168, p150) | ok |
| 4 Dwi Ary Purnomo | role, start, end | Vice President Commissioner; 2025-03-26; 2026-02-25 | Same; resigned Feb 25, 2026 on appointment to BoD of PT Asuransi Kerugian Jasa Raharja (p168 footnote, p151) | ok |
| 4 | OJK date (not in note) | n/a | June 26, 2025 (p168) | ok (could add) |
| 5 Fahri Hamzah | role, start, OJK date, term | Commissioner; 2025-03-26; 2025-12-17; AGM 2030 | Same (p152, p168) | ok |
| 6 Ida Nuryanti | role, start, OJK date | Independent Commissioner; 2025-03-26; 2025-10-09 | Same (p168, p153) | ok |
| 7 Pietra Paloh | role, start, OJK date, Audit chair, term | Independent Commissioner; 2025-03-26; 2025-08-15; chairs Audit Committee from June 2025; AGM 2030 | Same; full name Pietra Machreza Paloh (p154, p168) | ok |
| 8 Panangian Simanungkalit | role, start, OJK date | Independent Commissioner; 2025-03-26; 2025-08-15 | Same (p168, p155) | ok |
| 9 Didyk Choiroel | role, start, note | Commissioner; 2026-01-07; fit and proper pending | Same (p168, p156, p208) | ok |
| 10 Chandra M. Hamzah | start_date | 2020-05-04 | First appointed EGMS Nov 27, 2019; FSA effective May 4, 2020 (p157, p167). CSV has the FSA date; rows 3-9 use the GMS date | wrong (use 2019-11-27, or note it is the FSA date) |
| 10 | role, end, note | President Commissioner/Independent; 2025-03-26; dismissed | Honorably dismissed at AGM 2025-03-26 (p167, p157) | ok |
| 11 Iqbal Latanro | start_date | 2021-09-06 | Appointed AGMS Mar 10, 2021; FSA effective Sep 6, 2021 (p158, p167) | wrong (2021-03-10) |
| 11 | role, end | Vice President Commissioner/Independent; 2025-03-26 | Same (p167) | ok |
| 12 Armand B. Arief | start_date | 2020-05-14 | First appointed EGMS Nov 27, 2019; FSA May 14, 2020 (p159, p167) | wrong (2019-11-27) |
| 13 Sentot A. Sentausa | start_date | 2022-08-08 | AGMS Mar 2, 2022; FSA Aug 8, 2022 (p160, p167) | wrong (2022-03-02) |
| 14 Adi Sulistyowati | start_date | 2024-10-07 | AGMS Mar 6, 2024; FSA Oct 7, 2024 (p161, p167) | wrong (2024-03-06) |
| 15 Bambang Widjanarko | start_date | 2024-10-07 | AGMS Mar 6, 2024; FSA Oct 7, 2024 (p162, p167) | wrong (2024-03-06) |
| 16 Andin Hadiyanto | start_date | 2020-07-10 | First appointed EGMS Nov 27, 2019; FSA Jul 10, 2020 (p163, p167) | wrong (2019-11-27) |
| 17 Herry Trisaputra Zuna | start_date | 2022-10-11 | AGMS Mar 2, 2022; FSA Oct 11, 2022 (p164, p167) | wrong (2022-03-02) |
| 18 Himawan Arief Sugoto | start_date | 2022-10-03 | AGMS Mar 2, 2022; FSA Oct 3, 2022 (p165, p167) | wrong (2022-03-02) |
| 11-18 | role, end_date, note, spelling | as CSV | Match p167 table and dismissal list | ok |
| 19 Fahri Hamzah held_office gov_cabinet | role, start | Vice Minister (housing portfolio); 2024-10 | "Vice Minister of Public Works and Public Housing ... (October 2024 - present)" (p152) | ok (confidence "high" is odd given the note says pending check) |
| 20 Fahri Hamzah held_office gov_dpr | role, start, end | Member; Vice Chairman 2014-2019; 2004; 2019 | Member 2004-2014; Vice Chairman 2014-2019 (p152) | ok |

Name spellings in btn_ar2025_nodes.csv all match the report. p_suryo_utomo, p_fahri_hamzah, p_pietra_paloh and p_didyk_choiroel are not in that file; they are defined in data/processed/nodes.csv with matching spellings.

Summary: 10 rows fully ok (1, 3-9, 19, 20). 9 rows have the wrong start_date: rows 10-18 use the FSA effective date, while current commissioners use the GMS appointment date. 1 row is unsupported: row 2, where the control link is inferred.

## Missing items

Current commissioners: none missing. All 7 on p168/p208 are in the CSV (Suryo, Dwi Ary, Fahri, Ida, Pietra, Panangian, Didyk).

Concurrent government and other positions the report gives that are not in the CSV:
- Suryo Utomo: Head of the Agency for Technology, Information, and Financial Intelligence, Ministry of Finance (May 2025 - present) (p150). Also Chairman of the Supervisory Board, RSUPN Dr. Cipto Mangunkusumo (Oct 2023 - present) (p150). Former roles: Director General of Taxes, MoF (Nov 2019 - May 2025) and Commissioner, PT Sarana Multi Infrastruktur (Nov 2019 - Apr 2025) (p150).
- Dwi Ary Purnomo: Deputy for Finance and Risk Management, State-Owned Enterprises Regulation Agency (May 2025 - present) (p151; the work-experience column calls it the Ministry of SOEs). After he left, he became a member of the BoD of PT Asuransi Kerugian Jasa Raharja (Feb 2026) (p151, p168).
- Panangian Simanungkalit: Member of the Housing Task Force Team, Ministry of Housing and Settlement Areas (May 2024 - present) (p155).
- Didyk Choiroel: Secretary General, Ministry of Housing and Settlement Areas (Jan 2025 - present) (p156). Former: Head of Regional Office, DG Treasury East Java, MoF (May 2024 - Jan 2025) (p156).
- Ida Nuryanti and Pietra Paloh: no external concurrent positions (p153, p154). Ida was at Bank Indonesia until Mar 2025 (p153).
- Former commissioners: Herry Trisaputra Zuna, Road and Bridge Management Expert, Ministry of Public Works and Public Housing (2024 - present) (p164). Armand B. Arief, Independent Commissioner, PT Cardig Aero Services Tbk (p159). Chandra M. Hamzah, Co-Founder and Senior Partner, Assegaf Hamzah & Partners (2012 - present) (p157).
