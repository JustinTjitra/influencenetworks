# Source Access Report

Tested 2026-10-19 using WebFetch and WebSearch only. No curl, no browser, no login.

**Evidence labels**
- **[F]**: I fetched the page and saw this.
- **[3P]**: a third-party page (news, law firm, GitHub, docs) says this. I have not verified it directly.
- **[X]**: the fetch failed. `CLIENT_ERROR` usually means a block, a JS-only page or a timeout. `ROBOTS_DISALLOWED` means the fetch tool refused because of the site's robots.txt.

**Caveat:** WebFetch is not a real browser. A failure here does not prove that a Python scraper running from an Indonesian IP will fail, and a success does not prove it will work at scale.

---

## 1. AHU (Ditjen AHU, company and beneficial-owner registry)

| Source | Reachable? | What's available | Access method | Cost/limits | Terms/robots notes | Verdict | Evidence URL |
|---|---|---|---|---|---|---|---|
| AHU company search (`ahu.go.id/pencarian/profil-pt`) | Yes [F] | Company name search ("Pencarian Perseroan", "Cari" button). It covers companies registered under UU 40/2007; for others the page says "permohonan data perseroan dapat dimohonkan secara manual". [F] The free result is a "General Profile" with name, address and phone. [3P Mondaq] | Web form only. No API was seen. | Basic search appears free [3P]. Complete Profile costs Rp 500,000 and Latest Profile Rp 50,000 per company, paid in advance as PNBP [3P Mondaq]. The official PP 28/2019 tariff matrix lists "Pencarian/unduh data Perseroan Secara Online" at Rp 50,000 per search and "Informasi Tentang Data Perseroan dalam Daftar Perseroan" at Rp 500,000 per request [F, PDF on portal.ahu.go.id]. | The fetched HTML did not show a captcha or login; the form is JS-driven, so a captcha at submit time cannot be ruled out. I found no public bulk "AHU Unduh Data" product with pricing. "Data Download AHU" seems to be the per-company paid download [3P Mondaq]. | **Use with caution.** Use it for targeted lookups of named groups. The paid profiles (Rp 50k–500k each) are what list directors, commissioners and shareholders. Budget for this, and do not plan a bulk scrape. | https://ahu.go.id/pencarian/profil-pt ; https://portal.ahu.go.id/uploads/324489_Matriks%20Jenis%20dan%20Tarif%20PNBP%20Ditjen%20AHU%20PP%2028%202019.pdf ; https://www.mondaq.com/corporate-and-company-law/1299998/company-profile-information-in-indonesia |
| AHU beneficial owner (`ahu.go.id/pencarian/profil-pemilik-manfaat`) | Yes [F] | Search by corporation type and name. The page notes that BO data is "disampaikan baik oleh Kementerian/Lembaga, Korporasi, Notaris maupun PIC", meaning it is self-reported. [F] | Web form | No fee was shown [F]. I could not see what fields a result returns. | The HTML did not mention a captcha or login [F]. | **Use with caution.** BO data is self-declared, so treat it as a claim, not proof. | https://ahu.go.id/pencarian/profil-pemilik-manfaat |
| `bo.ahu.go.id` | Yes [F] | A login page for reporting parties. It also has public links to "Keterbukaan Informasi Publik Pemilik Manfaat" (which goes back to the search above), "Daftar Korporasi Yang Belum Melaporkan Pemilik Manfaat" and "Daftar Korporasi Nonaktif". [F] | Login for filers. The non-filer lists are public. | No fee was shown. | | **Use** the non-reporting-corporation list as a red-flag feature. **Skip** the login area. | https://bo.ahu.go.id |

## 2. IDX (Indonesia Stock Exchange)

| Source | Reachable? | What's available | Access method | Cost/limits | Terms/robots notes | Verdict | Evidence URL |
|---|---|---|---|---|---|---|---|
| IDX company profiles, annual reports, JSON | **No [X]**. Every fetch returned CLIENT_ERROR: the profile page, `/en/...`, `/id`, `/robots.txt`, the annual-report page and `primary/ListedCompany/GetCompanyProfilesDetail?KodeEmiten=BBCA`. | A dev.to tutorial scrapes `/id/perusahaan-tercatat/profil-perusahaan-tercatat/{code}` with Selenium and gets name, address, sector and registrar, but **not** directors or commissioners [3P]. The `GetCompanyProfilesDetail` JSON endpoint is widely used in community scrapers but **unverified by me**. | Headless browser. GitHub `noczero/idx-fundamental-analysis` says it uses "Camoufox (stealth Firefox) to scrape stock data from IDX past Cloudflare" [3P]. | Free if you can get through. | **Cloudflare bot protection is likely**: every plain fetch failed, including robots.txt, and a third party says so explicitly. | **Use with caution.** Plan on a real browser such as Playwright with polite rate limits, or parse board data from the annual-report PDFs. Fallback for board names: AHU paid profiles. | https://dev.to/zororaka/how-to-scrape-indonesian-public-company-profiles-hd9 ; https://github.com/noczero/idx-fundamental-analysis |

## 3. Forests & Finance

| Source | Reachable? | What's available | Access method | Cost/limits | Terms/robots notes | Verdict | Evidence URL |
|---|---|---|---|---|---|---|---|
| forestsandfinance.org | Yes [F] (home, data, FAQ, soft-commodities pages). `/explore-the-data/` itself returned CLIENT_ERROR. | Bank-to-company financing for beef, soy, **palm oil**, pulp and paper, rubber and timber. Loans and underwriting cover **2013 to Sept 2026**; bonds and shares are as of Sept 2026. More than 300 companies; the Southeast Asia region is covered [F]. The soft-commodities page has a **"Download full dataset"** button and a financial-institution filter, and lists "318 financial institutions… 27,418 operations" [F]. Indonesian banks are named: TuK and F&F report that Mandiri, BRI, BCA and BNI gave about USD 30.5bn to forest-risk companies in Indonesia, with Sinar Mas taking 38% [F, news page]. | Web download. The file format was not stated. | Free | The site's Terms link points to RAN's general T&Cs: "limited license for personal use", "excludes the download or collection of… text", and no commercial exploitation without written approval [F, ran.org]. These may not have been written for the dataset. The contact form has a "Data inquiry" option. | **Use**, but email for written permission before you republish derived data. Amounts are adjusted down to the forest-risk share, so read the methodology. | https://forestsandfinance.org ; https://forestsandfinance.org/explore-the-data/soft-commodities/ ; https://www.ran.org/terms_and_conditions/ ; https://forestsandfinance.org/news/major-banks-in-indonesia-financing-forest-destruction-biodiversity-loss-climate-chaos-and-human-rights-violations/ |

## 4. TuK Indonesia

| Source | Reachable? | What's available | Access method | Cost/limits | Terms/robots notes | Verdict | Evidence URL |
|---|---|---|---|---|---|---|---|
| tuk.or.id | Yes [F]. The site is live with October 2026 news, but some template placeholder text is still visible. | Publications: "Taipan Kelapa Sawit" (tycoon control of plantations), an Exclusion List for palm oil (Nov 2025, with IPB), a Greenwash Index, and a link to Fires and Finance [F]. The 2015 "Tycoon-controlled oil palm groups in Indonesia" report covers 25 groups [3P farmlandgrab/GRAIN]. | PDF reports. I saw **no structured dataset download**. | Free | Not stated | **Use with caution.** It is a good seed list of tycoon to group mappings, but you will have to transcribe it from PDFs. | https://www.tuk.or.id ; https://farmlandgrab.org/post/24562 |
| firesandfinance.tuk.or.id | Yes [F] | A map plus a visual report linking concessions (Sinar Mas, APRIL) to fires and to banks. Bank financing covers 2014–2018 and the fires are from 2019 [F]. | Interactive map. No download link was seen. | Free | | **Use with caution** for older context only. | https://firesandfinance.tuk.or.id |

## 5. Trase

| Source | Reachable? | What's available | Access method | Cost/limits | Terms/robots notes | Verdict | Evidence URL |
|---|---|---|---|---|---|---|---|
| trase.earth | Yes [F]. `/data` failed, but `/`, `/open-data`, the dataset page and the terms page loaded. | "Indonesia palm oil – Supply chain data", **2018–2024**, "free-to-download". Variables include year, mill_trase_id, refinery_trase_id and province_of_production [F]. A 2026 explainer covers 2023–24 supply chains and 2025 deforestation [F]. | Download button on the dataset page | Free. Older versions are available by email. | "Licensing is determined for each individual data set". Website charts are CC BY 4.0. Attribution is required, and commercial use needs contact with info@trase.earth [F]. | **Use.** It gives mill/refinery-to-exporter links that you can join to groups. Check the license text on the dataset itself. | https://trase.earth/open-data/datasets/supply-chains-indonesia-palm-oil ; https://trase.earth/terms-of-use |

## 6. Auriga Nusantara and Greenpeace Kepo Hutan

| Source | Reachable? | What's available | Access method | Cost/limits | Terms/robots notes | Verdict | Evidence URL |
|---|---|---|---|---|---|---|---|
| Auriga (auriga.or.id) | Yes [F] | No ownership dataset is listed on the homepage. It links to **Simontini** (land cover and license maps; "Access land cover or license maps and data" [F]), Sawit.info, MapBiomas Indonesia and Pasopati [F]. | Map and data portal | Free | Not reviewed | **Use with caution.** Simontini has license and concession geodata. For group ownership, email info@auriga.or.id. | https://auriga.or.id ; https://simontini.id/en |
| Greenpeace Kepo Hutan (kepohutan.greenpeace.org) | Partially [F]. The page loaded, but only a short description came back: an interactive map of plantations and fires. | The 2016 launch press says it identifies the companies that own concessions, with shapefiles downloadable [3P Eco-Business, Mar 2016]. The greenpeace.org/indonesia homepage no longer links to it [F]. | JS map | Free | | **Use with caution.** It looks legacy and its data is probably from 2016–2019. Confirm the shapefile download still works. | https://kepohutan.greenpeace.org ; https://www.eco-business.com/news/new-map-launched-on-company-concessions-in-indonesia/ |

## 7. KPK e-LHKPN

| Source | Reachable? | What's available | Access method | Cost/limits | Terms/robots notes | Verdict | Evidence URL |
|---|---|---|---|---|---|---|---|
| elhkpn.kpk.go.id | **Blocked to my tool [X]**: ROBOTS_DISALLOWED on `/`, `/robots.txt` and the announcement page. | Per Bisnis.com (2023): the public "e-Announcement" lets you search by name, year and institution; you **tick a captcha**, the results show **total wealth**, and you get the itemised breakdown by entering your name, age and profession, then downloading. **No account login** is needed. [3P] | Manual web form | Free | The captcha plus identity form plus robots disallow make automated scraping both inappropriate and impractical. | **Use with caution.** Do manual, targeted lookups for named officials only, and keep a log. Do not automate. | https://kabar24.bisnis.com/read/20230225/15/1631673/bisa-diakses-umum-ini-cara-cek-harta-kekayaan-pejabat-di-lhkpn-kpk |

## 8. KPU campaign finance (2024)

| Source | Reachable? | What's available | Access method | Cost/limits | Terms/robots notes | Verdict | Evidence URL |
|---|---|---|---|---|---|---|---|
| infopemilu.kpu.go.id / Sidakam / Sikadeka | **Blocked to my tool [X]** (ROBOTS_DISALLOWED). | **LPSDK (donation report) was abolished for 2024.** Donations are folded into LADK and LPPDK, and KPU said Sidakam would give public views of donor identities [3P rm.id]. Published figures in the press are **totals per party or ticket**, for example Ganjar–Mahfud receipts of Rp 506.9bn and Prabowo–Gibran Rp 208.2bn [3P NU Online, Mar 2024]. I found no evidence of a downloadable donor-level dataset. KAP audit results were announced, including at regional KPUs [3P]. | Web portal, and PPID information requests | Free | robots.txt disallows my fetcher | **Use with caution.** Expect totals only. For donor-level data, file a PPID request to KPU or use Bawaslu, ICW or Perludem compilations. | https://rm.id/baca-berita/pemilu/175029/kpu-hapus-lpsdk-laporan-sumbangan-dana-kampanye-tetap-wajib-kok ; https://nu.or.id/nasional/kpu-publikasi-pengeluaran-dana-kampanye-tiap-paslon-pada-pilpres-2024-wOp2R |

## 9. Supreme Court decision directory

| Source | Reachable? | What's available | Access method | Cost/limits | Terms/robots notes | Verdict | Evidence URL |
|---|---|---|---|---|---|---|---|
| putusan3.mahkamahagung.go.id | The homepage, a listing page and a decision page all returned CLIENT_ERROR [X]. **robots.txt was fetched [F].** | Search results show indexed listings by court and category, for example `/direktori/index/pengadilan/pn-tarakan/kategori/ite-1.html`, and decision pages `/direktori/putusan/{id}.html` [3P search index]. | HTML listings plus per-decision PDF (from search snippets, not verified) | Free | robots.txt [F] carries a Cloudflare-managed header `Content-Signal: search=yes,ai-train=no,use=reference`. It blocks AI and training bots (ClaudeBot, GPTBot, CCBot and others) site-wide, and gives Googlebot and Bing a 10–15 s crawl-delay. **There are two conflicting `User-agent: *` groups (Allow / and Disallow /).** | **Use with caution.** Run slow, targeted queries on named entities (for example the defendants in corruption cases). Do not bulk crawl: robots is ambiguous and probably restrictive, and Cloudflare is in front. | https://putusan3.mahkamahagung.go.id/robots.txt |

## 10. Procurement (LPSE, INAPROC, opentender)

| Source | Reachable? | What's available | Access method | Cost/limits | Terms/robots notes | Verdict | Evidence URL |
|---|---|---|---|---|---|---|---|
| spse.inaproc.id | Yes [F] | The root is a directory of agency SPSE instances. `/lkpp/lelang` shows a public "CARI PAKET" search with columns Kode, Nama Paket, Instansi, Tahapan, HPS and Jadwal, without a login. "Pemenang Berkontrak" is a filter, not a column [F]. Rows load by JS, so none were captured. | Web, with a JS/AJAX table | Free | No captcha was seen in the HTML | **Use with caution.** Winners are on per-package pages; there are many instances to scrape. | https://spse.inaproc.id/lkpp/lelang |
| lpse.lkpp.go.id | **Blocked [X]** (ROBOTS_DISALLOWED) | | | | robots disallows | **Skip** (use INAPROC or opentender instead) | — |
| opentender.net (ICW) | Site **blocked to my tool [X]** (ROBOTS_DISALLOWED) | **The OCP Data Registry mirrors ICW's data [F]**: OCDS, 1,303,374 tenders and 1,086,425 awards, valid from 2008 to **July 2025**, last retrieved 3 Aug 2026, refreshed monthly. Formats: JSONL.gz (211 MB), CSV tar.gz (308 MB) and per-year XLSX. **License ODbL.** | Bulk download from data.open-contracting.org | Free | ODbL is share-alike for derived databases you publish | **Use.** This is the best structured source on the list. | https://data.open-contracting.org/ru/publication/101 |

## 11. GDELT

| Source | Reachable? | What's available | Access method | Cost/limits | Terms/robots notes | Verdict | Evidence URL |
|---|---|---|---|---|---|---|---|
| GDELT 2.0 DOC API | **Could not verify [X].** Five API calls (domain:kompas.com, domain:detik.com, domainis:tempo.co, sourcelang:indonesian, "kelapa sawit") returned CLIENT_ERROR or SERVER_ERROR, or an empty HTML shell. | The DOC API officially covers only the **last ~3 months**, with at most **250 records** per call [3P gdeltdoc PyPI]. Indonesian is one of the **65 Translingual languages** [F, GDELT blog]. A third-party GDELT analysis says 23 of the 25 largest publishers of Indonesia coverage are Indonesian outlets, but names none [F, demolab]. **I could not confirm per-domain coverage** for the 9 outlets. | REST API (no key) | Free; low per-call cap | | **Use with caution.** Good for discovering URLs and dates. Test `domainis:` per outlet from your own machine first. For anything older than 3 months, use BigQuery. | https://blog.gdeltproject.org/gdelt-translingual-translating-the-planet/ ; https://pypi.org/project/gdeltdoc/ |
| GDELT BigQuery (`gdelt-bq.gdeltv2`) | gdeltproject.org loaded [F]. It says the Event DB is in BigQuery, updated daily. | The GKG and Events tables carry DocumentIdentifier/SOURCEURL, so you can filter by domain. | BigQuery SQL | The BigQuery **sandbox** needs **no credit card**, gives **1 TiB of queries a month**, 10 GiB of lifetime storage, and expires tables after 60 days [F, Google docs]. Full-table GKG scans are many TB. Partitioned tables (`*_partitioned`) and narrow columns keep a query under 1 TiB. | | **Use.** This is the primary way to discover article URLs historically. The `bq` CLI is preconfigured in this environment. | https://docs.cloud.google.com/bigquery/docs/sandbox |

## 12. News sites: robots.txt, sitemaps, date indexes

| Site | Reachable? | Article paths disallowed? | Sitemaps | AI-bot rules | Date index | Verdict |
|---|---|---|---|---|---|---|
| detik.com | Yes [F] | No. Only `*/komentar$`, `/main`, `/search/*`, `/tag/news/*`, `/ajax/`, `/api/`, `/video/` and query strings (Googlebot group) | `/sitemap.xml`. The index [F] has hundreds of per-channel `sitemap_news.xml` and `sitemap_web.xml` files, with lastmod from 2013 to 2026-10-11. | None blocked; `*` Allow / | `news.detik.com/indeks` [F], paginated `?page=` up to 500, plus a "by date" control (parameter not seen) | **Use** |
| kompas.com | **ROBOTS_DISALLOWED [X]**. My fetcher was refused on robots.txt, the homepage and indeks.kompas.com | Unknown. The refusal suggests AI or generic agents are blocked. | Unknown | Likely blocks AI agents | indeks.kompas.com exists [3P/old snapshot] | **Use with caution.** Check robots.txt manually with your own UA before crawling. |
| tempo.co | **ROBOTS_DISALLOWED [X]** on robots.txt and /indeks. The homepage returned content. | Unknown | Unknown | Likely blocks AI agents | `/indeks` exists (blocked to me) | **Use with caution.** Check manually; Tempo has paywalled content. |
| cnnindonesia.com | Yes [F] | No. Only params, embeds, `/search`, `/api/`, `/ucnews` and similar (Googlebot) | `/sitemap.xml`, 27 child sitemaps by section × news/web/video, not by date [F] | `*` and Google-Extended Allow / | `/indeks/{section}?page=N` up to 1000 [F]. Article URLs embed `YYYYMMDDhhmmss` | **Use** |
| metrotvnews.com | Yes [F] | No (`/moadmin/`, `/search`, `/embed/`, `/vmap`, `/hit/`) | `/sitemap/sitemap.xml`, 7 children (news, nasional, ekonomi…), no lastmod [F] | **Blocks GPTBot, ChatGPT-User, OpenAI, CCBot** | Not tested | **Use** (with a non-AI research UA; respect the AI blocks if your UA is AI-identified) |
| mediaindonesia.com | Yes [F] | No | `/sitemap.xml` [F] | **Blocks GPTBot, Google-Extended, ClaudeBot, CCBot, Bytespider, Amazonbot, Applebot-Extended, meta-externalagent** | `/indeks` CLIENT_ERROR | **Use with caution.** It explicitly opts out of AI crawling, so don't feed articles to LLM training. Metadata and coverage counts are fine. |
| okezone.com | Yes [F] | No (`/tag/`, `/jadwalsholat/*`, cookie handlers) | `/sitemap.xml` (72 children) and `/news/sitemap.xml` [F] | None | Not tested | **Use** |
| inews.id | Yes [F] | No (`/getwidget`, `/getnews`, `/debug-page-source`) | `/sitemap.xml` [F] | None | `/indeks` has a channel and date dropdown and "Load More" (JS) [F] | **Use** |
| viva.co.id | Yes [F] | No. Disallows `/indeks_tahun/all/2008–2010`, `/urindeks/*`, `/enindeks/*`, `/anindeks/*`, `/listmp/*` | `/sitemap.xml` [F] | None | `/indeks` has "Muat Lainnya" (JS), no date parameter [F] | **Use** (avoid the disallowed index paths) |
| kumparan.com | Yes [F] | No Disallow at all | **18 sitemaps** (channel-level news, basic, collection…) [F] | ClaudeBot, GPTBot, PerplexityBot and others explicitly allowed | Not tested | **Use** |

## 13. Indonesian legal constraints

| Law | Status as of Oct 2026 | Relevance | Evidence |
|---|---|---|---|
| **UU 27/2022 (PDP)** | Fully applicable since Oct 2024. **PP 33/2026** (the implementing regulation) is reportedly issued, but the **independent PDP Agency is still not formed**; the Perpres was sent to the President on 20 May 2026 and is reportedly signed, but the body has not been set up. Interim oversight sits with Komdigi [3P Bisnis.com, 13 Sep 2026; CNBC Indonesia, 4 Feb 2026]. | Officials' names, positions and declared assets are personal data. Rely on the legitimate-interest and public-interest bases, minimise what you collect (no NIK, home addresses or family members unless they are relevant and already public), and document purpose and retention. | https://teknologi.bisnis.com/read/20260913/84/2003698/pembentukan-badan-pdp-dipercepat-implementasi-uu-pdp-dinilai-belum-efektif ; https://www.cnbcindonesia.com/tech/20260204144446-37-708158/telat-2-tahun-komdigi-janji-badan-penjaga-data-warga-ri-berdiri-2026 |
| **New KUHP (UU 1/2023)** | **In force since 2 January 2026**, together with the new KUHAP [3P Bisnis.com, Republika] | It contains defamation and insult provisions, including insulting the President or state institutions, separate from the ITE law. Published network claims need careful sourcing. | https://kabar24.bisnis.com/read/20260102/16/1941064/kejagung-siap-laksanakan-aturan-kuhp-dan-kuhap-baru-yang-berlaku-hari-ini |
| **ITE 2nd amendment (UU 1/2024), Art. 27A defamation** | It narrowed online defamation to attacks on a person's honour by alleging a matter. **MK Decision 105/PUU-XXII/2024 (29 Apr 2025)** held that "orang lain" means **individuals only**: government institutions, corporations, groups, professions and positions cannot be complainants, and a legal entity "tidak dapat menjadi pihak pengadu" [F, mkri.id]. | It lowers the risk from corporations (palm oil groups, banks) but not from the **individual** tycoons or officials you name. Stick to documented, cited facts. | https://www.mkri.id/berita/mk-mempertegas-pemaknaan-unsur-unsur-pencemaran-nama-baik-dalam-uu-ite--23133 |

*This is not legal advice. Get an Indonesian lawyer's review before you publish named political-business links.*

---

## Recommended pipeline order

1. **Bulk open datasets first** (no scraping risk): opentender/ICW OCDS dump (ODbL), Trase Indonesia palm oil 2018–2024, and the Forests & Finance full dataset (send the data-use request email at the same time).
2. **Build the entity spine:** seed palm oil groups and tycoons from TuK reports and F&F; seed banks from F&F. Add listed-company boards from IDX annual reports, using a headless browser or PDF parsing, at low volume.
3. **Targeted registry enrichment:** buy AHU profiles (Rp 50k–500k each) only for entities that matter for the network; check the AHU BO search and the non-reporting list.
4. **Political side:** compile KPU 2024 campaign totals and file a PPID request for donor detail. Do manual LHKPN lookups for named officials only.
5. **Court records:** run slow, targeted putusan3 queries on entity names.
6. **News corpus:** discover URLs with GDELT via BigQuery (sandbox, partitioned tables), then fill gaps from sitemaps for detik, cnnindonesia, okezone, kumparan, inews, viva and metrotvnews. Check kompas and tempo robots manually before including them. Respect the AI opt-outs at mediaindonesia and metrotvnews. Store metadata and extracted features, and avoid redistributing full text.
7. **Legal review** under UU PDP, the new KUHP and the ITE law before you publish any named relationship.
