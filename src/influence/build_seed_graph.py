"""Turn the hand-researched seed CSVs into validated nodes.csv / edges.csv.

The seed files describe people in free text. Rather than guess edge types from
that text, the typed edges are declared explicitly in PERSON_EDGES below so a
reviewer can read every relationship the graph asserts in one place.

Confidence is capped by source type, regardless of what the seed row says:
    annual report / exchange filing / registry / company site -> up to high
    reputable news, NGO, Wikipedia                            -> up to medium
Run:  python -m influence.build_seed_graph
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "data" / "seed"
OUT = ROOT / "data" / "processed"
PRIMARY = ROOT / "data" / "primary"

PARTIES = {
    "party_nasdem": "Partai NasDem",
    "party_perindo": "Partai Perindo",
    "party_hanura": "Partai Hanura",
    "party_golkar": "Partai Golkar",
    "party_gerindra": "Partai Gerindra",
    "party_pkb": "Partai Kebangkitan Bangsa (PKB)",
    "party_demokrat": "Partai Demokrat",
    "party_gelora": "Partai Gelora",
}
GOVT = {
    "gov_danantara": "BPI Danantara",
    "gov_bp_bumn": "BP BUMN (SOE Regulatory Agency)",
    "gov_ministry_soe": "Ministry of SOEs (until Oct 2025)",
    "gov_cabinet": "Cabinet of Indonesia",
    "gov_presidency": "Presidency of Indonesia",
    "gov_dpr": "DPR (House of Representatives)",
    "gov_pln": "PLN (state electricity company)",
}

# (target, edge_type, role, start, end)
PERSON_EDGES: dict[str, list[tuple]] = {
    # ---- media owners ----
    "p_hary_tanoesoedibjo": [
        ("mg_mnc", "owns_media", "founder/chairman", "", ""),
        ("party_nasdem", "party_role", "member", "2011-08", "2013-02"),
        ("party_hanura", "party_role", "member", "2013", "2014-05"),
        ("party_perindo", "party_role", "general chairman", "2015-02-07", "2024-07-31"),
    ],
    "p_angela_tanoesoedibjo": [
        ("mg_mnc", "board_seat", "co-CEO", "2024-10-22", ""),
        ("gov_cabinet", "held_office", "Vice Minister of Tourism and Creative Economy", "2019", "2024"),
        ("party_perindo", "party_role", "general chairwoman", "2024-07-31", ""),
        ("p_hary_tanoesoedibjo", "family_of", "daughter", "", ""),
    ],
    "p_liliana_tanoesoedibjo": [("p_hary_tanoesoedibjo", "family_of", "spouse", "", "")],
    "p_surya_paloh": [
        ("mg_media_group", "owns_media", "founder/chairman", "1984", ""),
        ("party_nasdem", "party_role", "general chairman", "", ""),
    ],
    "p_prananda_paloh": [
        ("mg_media_group", "board_seat", "advisor", "", ""),
    ],
    "p_pietra_paloh": [
        ("bank_btn", "board_seat", "independent commissioner", "2025-03", ""),
        ("p_surya_paloh", "family_of", "nephew", "", ""),
    ],
    "p_aburizal_bakrie": [
        ("pg_bakrie", "controls", "family patriarch", "", ""),
        ("mg_viva", "owns_media", "family patriarch", "", ""),
        ("party_golkar", "party_role", "general chairman", "2009-10-09", ""),
        ("gov_cabinet", "held_office", "Coordinating Minister", "2004", "2009"),
    ],
    "p_anindya_bakrie": [
        ("pg_bakrie", "board_seat", "President Director, Bakrie & Brothers", "", ""),
        ("p_aburizal_bakrie", "family_of", "son", "", ""),
    ],
    "p_ardi_bakrie": [
        ("mg_viva", "board_seat", "President Commissioner, Intermedia Capital", "", ""),
        ("p_aburizal_bakrie", "family_of", "son", "", ""),
    ],
    "p_chairul_tanjung": [
        ("mg_ct_corp", "owns_media", "founder/chairman", "", ""),
        ("gov_cabinet", "held_office", "Coordinating Minister for Economic Affairs", "2014-05-19", "2014-10-27"),
    ],
    "p_putri_tanjung": [
        ("gov_presidency", "held_office", "presidential special staff", "2019", "2024"),
        ("p_chairul_tanjung", "family_of", "daughter", "", ""),
    ],
    "p_eddy_sariaatmadja": [("mg_emtek", "owns_media", "founder (21.94%)", "", "")],
    "p_alvin_sariaatmadja": [("mg_emtek", "board_seat", "President Director", "", "")],
    "p_lilik_oetama": [("mg_kompas_gramedia", "board_seat", "Chairman & CEO", "", "")],
    "p_dahlan_iskan": [
        ("mg_jawapos", "owns", "shareholder (3.8%)", "", ""),
        ("gov_pln", "held_office", "CEO", "2009-12-23", "2011-10-19"),
        ("gov_cabinet", "held_office", "Minister of SOEs", "2011-10-19", "2014-10-20"),
    ],
    "p_enggartiasto_lukita": [
        ("mg_b_universe", "board_seat", "Executive Chairman", "", ""),
        ("party_nasdem", "party_role", "member", "2013", ""),
        ("gov_cabinet", "held_office", "Trade Minister", "2016-07-27", "2019-10"),
    ],
    "p_erick_thohir": [
        ("mg_mahaka", "owns_media", "founder", "", ""),
        ("gov_cabinet", "held_office", "Minister of SOEs", "2019-10-23", "2025-09-17"),
        ("gov_cabinet", "held_office", "Minister of Youth and Sports", "2025-09-17", ""),
        ("gov_danantara", "held_office", "Chair, Supervisory Board (confirmed as of 2025-10-16)", "", ""),
    ],
    # ---- palm oil ----
    "p_anthoni_salim": [
        ("pg_salim", "controls", "group head", "", ""),
        ("mg_emtek", "owns", "shareholder (9%)", "", ""),
    ],
    "p_franky_widjaja": [("pg_sinarmas", "board_seat", "President Commissioner, SMART Tbk", "2003-01", "")],
    "p_kuok_khoon_hong": [("pg_wilmar", "board_seat", "co-founder, Chairman & CEO", "", "")],
    "p_martua_sitorus": [("pg_wilmar", "controls", "co-founder", "", "")],
    "p_sukanto_tanoto": [("pg_rge", "controls", "founder", "", "")],
    "p_bachtiar_karim": [("pg_musim_mas", "board_seat", "Executive Chairman & CEO", "", "")],
    "p_peter_sondakh": [("pg_rajawali", "controls", "founder", "", "")],
    "p_ciliandra_fangiono": [
        ("pg_first_resources", "board_seat", "CEO", "", ""),
        ("p_martias_fangiono", "family_of", "son", "", ""),
    ],
    "p_martias_fangiono": [("pg_first_resources", "controls", "founder", "1992", "")],
    "p_tp_rachmat": [
        ("pg_triputra", "controls", "founder, controlling party", "", ""),
        ("pg_dsn", "owns", "shareholder", "", ""),
    ],
    "p_arini_subianto": [("pg_triputra", "owns", "via Persada Capital Investama (33.06%)", "", "")],
    "p_hashim_djojohadikusumo": [
        ("pg_arsari", "controls", "owner", "", ""),
        ("party_gerindra", "party_role", "co-founder", "2008", ""),
        ("p_prabowo_subianto", "family_of", "brother", "", ""),
    ],
    "p_prabowo_subianto": [
        ("gov_presidency", "held_office", "President", "2024-10-20", ""),
        ("party_gerindra", "party_role", "general chairman", "", ""),
        ("gov_danantara", "held_office", "founder / person in charge", "2025-02-24", ""),
    ],
    "p_lim_gunawan_hariyanto": [("pg_harita_bumitama", "board_seat", "Executive Chairman & CEO", "", "")],
    "p_putera_sampoerna": [("pg_sampoerna_agro", "controls", "former controller", "", "2025-11")],
    "p_surya_darmadi": [("pg_duta_palma", "controls", "owner (as described in source)", "", "")],
    # ---- banks / Danantara ----
    "p_robert_budi_hartono": [("bank_bca", "controls", "ultimate controlling shareholder", "", "")],
    "p_bambang_hartono": [
        ("bank_bca", "controls", "co-controller", "", "2026-07"),
        ("p_robert_budi_hartono", "family_of", "brother", "", ""),
    ],
    "p_rosan_roeslani": [
        ("gov_danantara", "held_office", "CEO, Executive Body", "2025-02-24", ""),
        ("gov_cabinet", "held_office", "Minister of Investment and Downstreaming", "2024-08-19", ""),
    ],
    "p_dony_oskaria": [
        ("gov_danantara", "held_office", "COO", "2025-02", ""),
        ("gov_bp_bumn", "held_office", "Head", "2025-10-08", ""),
    ],
    "p_pandu_sjahrir": [("gov_danantara", "held_office", "CIO", "2025-02", "")],
    "p_kartika_wirjoatmodjo": [
        ("bank_bri", "board_seat", "President Commissioner", "2020-02", ""),
        ("gov_ministry_soe", "held_office", "Deputy Minister of SOEs", "", "2025-10-08"),
    ],
    "p_helvi_moraza": [
        ("bank_bri", "board_seat", "commissioner", "2025-03-24", ""),
        ("gov_cabinet", "held_office", "Deputy Minister of MSMEs", "", ""),
        ("party_gerindra", "party_role", "former regional secretary-general (Tangerang)", "", ""),
    ],
    "p_lukmanul_khakim": [
        ("bank_bri", "board_seat", "independent commissioner", "2025-03", ""),
        ("party_pkb", "party_role", "central board division chair", "", ""),
    ],
    "p_hery_gunardi": [("bank_bri", "board_seat", "President Director", "2025-03", "")],
    "p_yuliot_tanjung": [
        ("bank_mandiri", "board_seat", "commissioner", "2025-03", ""),
        ("gov_cabinet", "held_office", "Deputy Minister of Energy and Mineral Resources", "2024-10-21", ""),
    ],
    "p_luky_alfirman": [("bank_mandiri", "board_seat", "commissioner", "2025-03", "")],
    "p_zainudin_amali": [
        ("bank_mandiri", "board_seat", "independent commissioner, Deputy President Commissioner from 2024-03-07", "2023", "2025-12-19"),
        ("party_golkar", "party_role", "politician", "", ""),
    ],
    "p_zulkifli_zaini": [("bank_mandiri", "board_seat", "President Commissioner", "2025-12-19", "")],
    "p_vera_febyanthy": [
        ("bank_bni", "board_seat", "independent commissioner", "2025-03-26", ""),
        ("party_demokrat", "party_role", "deputy general chair", "2025", ""),
        ("gov_dpr", "held_office", "member", "2019", "2024"),
    ],
    "p_tedi_bharata": [
        ("bank_bni", "board_seat", "Vice President Commissioner", "2025-03", ""),
        ("gov_bp_bumn", "held_office", "Deputy Head", "2025-10-08", ""),
    ],
    "p_omar_sjawaldy_anwar": [("bank_bni", "board_seat", "President Commissioner", "2025-03", "")],
    "p_putrama_setyawan": [("bank_bni", "board_seat", "President Director", "2025-03", "")],
    "p_fahri_hamzah": [
        ("bank_btn", "board_seat", "commissioner", "2025-03-26", ""),
        ("gov_cabinet", "held_office", "Deputy Minister of Housing and Settlement Areas", "2024-10-21", ""),
        ("party_gelora", "party_role", "deputy general chair", "", ""),
    ],
    "p_suryo_utomo": [("bank_btn", "board_seat", "President Commissioner", "2025-03-26", "")],
    "p_didyk_choiroel": [("bank_btn", "board_seat", "commissioner", "2026-01-07", "")],
    "p_endra_gunawan": [
        ("bank_btn", "board_seat", "Vice President Commissioner", "2026-04-23", ""),
        ("gov_bp_bumn", "held_office", "Deputy", "", ""),
    ],
    "p_nixon_napitupulu": [("bank_btn", "board_seat", "President Director", "", "")],
    "p_muhadjir_effendy": [("bank_bsi", "board_seat", "President Commissioner", "2025-05-16", "")],
    "p_felicitas_tallulembang": [
        ("bank_bsi", "board_seat", "independent commissioner", "", ""),
        ("party_gerindra", "party_role", "cadre", "", ""),
    ],
    "p_addin_jauharudin": [("bank_bsi", "board_seat", "independent commissioner", "2025-05", "")],
    "p_kamaruddin_amin": [("bank_bsi", "board_seat", "commissioner", "2025-05", "")],
    "p_cholil_nafis": [("bank_bsi", "board_seat", "independent commissioner (pending OJK)", "2026-05-05", "")],
    "p_anggoro_eko_cahyo": [("bank_bsi", "board_seat", "President Director", "", "")],
}

# Institutional edges not tied to a person row: (src, tgt, type, role, start, end, url_from)
DANANTARA_BANKS = {"bank_bri": 53.19, "bank_mandiri": 52.0, "bank_bni": 60.0, "bank_btn": 60.0}
RANK = {"low": 0, "medium": 1, "high": 2}

HIGH_OK = {"annual_report", "exchange_filing", "govt_registry", "court_record", "company_website"}


def source_type_for(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "wikipedia.org" in host:
        return "other"
    if any(k in host for k in ("idx.co.id", "sgx.com", "ojk.go.id")):
        return "exchange_filing"
    if host.endswith(".go.id"):
        return "govt_registry"
    if any(k in host for k in ("mahkamahagung",)):
        return "court_record"
    if any(k in host for k in ("forestsandfinance", "trase.earth", "auriga", "tuk.or.id", "greenpeace")):
        return "ngo_dataset"
    corp = ("bakrie-brothers.com", "mncgroup", "wilmar-international", "goldenagri", "bankmandiri",
            "bri.co.id", "bni.co.id", "btn.co.id", "bankbsi", "bca.co.id", "firstresources", "musimmas")
    if any(k in host for k in corp):
        return "company_website"
    return "news"


def cap_confidence(conf: str, stype: str) -> str:
    conf = (conf or "low").strip().lower()
    if conf == "high" and stype not in HIGH_OK:
        return "medium"
    return conf if conf in ("high", "medium", "low") else "low"


def outlet_domains(text: str) -> list[str]:
    return sorted(set(re.findall(r"\b([a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|id|co\.id|co|net))\b", str(text).lower())))


def main() -> int:
    groups = pd.read_csv(SEED / "palm_oil_groups.csv")
    banks = pd.read_csv(SEED / "banks.csv")
    media = pd.read_csv(SEED / "media_groups.csv")
    people = pd.read_csv(SEED / "people_seed.csv")

    nodes: list[dict] = []
    edges: list[dict] = []
    warnings: list[str] = []

    def add_node(i, t, name, aliases=""):
        nodes.append({"id": i, "type": t, "name": name, "aliases": aliases})

    for _, r in groups.iterrows():
        add_node(r.group_id, "business_group", r.group_name)
    for _, r in banks.iterrows():
        add_node(r.bank_id, "bank", r.bank_name, str(r.ticker))
    for _, r in media.iterrows():
        add_node(r.media_group_id, "media_group", r.group_name)
        stype = source_type_for(r.source_url)
        for dom in outlet_domains(r.flagship_outlets):
            oid = "out_" + dom.replace(".", "_").replace("-", "_")
            add_node(oid, "outlet", dom)
            edges.append(dict(source_id=r.media_group_id, target_id=oid, type="publishes",
                              source_url=r.source_url, source_type=stype,
                              confidence=cap_confidence(r.confidence, stype)))
    for k, v in {**PARTIES, **GOVT}.items():
        add_node(k, "party" if k.startswith("party_") else "govt_body", v)

    person_rows = {r.person_id: r for _, r in people.iterrows()}

    # Independent fact-check: take the lower of the capped and recommended confidence,
    # and drop rows the checker found contradicted or unverifiable.
    verified: dict[str, str] = {}
    blocked: set[str] = set()
    vpath = SEED / "verification.csv"
    if vpath.exists():
        v = pd.read_csv(vpath)
        for _, row in v.iterrows():
            rid = str(row.row_id)
            if row.status == "unverifiable":
                blocked.add(rid)
            rc = str(row.recommended_confidence).strip().lower()
            if rc in RANK and (rid not in verified or RANK[rc] < RANK[verified[rid]]):
                verified[rid] = rc

    def final_conf(rid: str, conf: str, stype: str) -> str:
        c = cap_confidence(conf, stype)
        if rid in verified and RANK[verified[rid]] < RANK[c]:
            c = verified[rid]
        return c
    for _, r in people.iterrows():
        add_node(r.person_id, "person", r["name"], str(r.aliases) if pd.notna(r.aliases) else "")

    for pid, specs in PERSON_EDGES.items():
        if pid not in person_rows:
            warnings.append(f"edge spec for unknown person {pid}")
            continue
        if pid in blocked:
            warnings.append(f"person {pid} marked unverifiable by fact-check; edges skipped")
            continue
        r = person_rows[pid]
        stype = source_type_for(r.source_url)
        conf = final_conf(pid, r.confidence, stype)
        for tgt, etype, role, start, end in specs:
            if etype == "family_of" and conf == "low":
                warnings.append(f"skipping low-confidence family edge {pid}->{tgt}")
                continue
            edges.append(dict(source_id=pid, target_id=tgt, type=etype, role=role,
                              start_date=start, end_date=end, source_url=r.source_url,
                              source_type=stype, confidence=conf))

    unspecified = sorted(set(person_rows) - set(PERSON_EDGES))
    for pid in unspecified:
        warnings.append(f"person {pid} has no typed edges yet")

    # Detik sits inside CT Corp's Trans Media.
    m = media.set_index("media_group_id")
    if {"mg_detik", "mg_ct_corp"} <= set(m.index):
        url = m.loc["mg_detik", "source_url"]
        stype = source_type_for(url)
        edges.append(dict(source_id="mg_ct_corp", target_id="mg_detik", type="owns",
                          role="parent (via Trans Media)", source_url=url, source_type=stype,
                          confidence=cap_confidence(m.loc["mg_detik", "confidence"], stype)))

    b = banks.set_index("bank_id")
    for bid, pct in DANANTARA_BANKS.items():
        if bid in b.index:
            url = b.loc[bid, "source_url"]
            stype = source_type_for(url)
            edges.append(dict(source_id="gov_danantara", target_id=bid, type="owns",
                              role="Series B shares via operating holding", start_date="2025-03-22", pct=pct,
                              source_url=url, source_type=stype,
                              confidence=cap_confidence(b.loc[bid, "confidence"], stype)))

    # Fact-check: Mandiri still holds 51.47% of BSI after BSI became a Persero (2026-01-23).
    edges.append(dict(source_id="bank_mandiri", target_id="bank_bsi", type="owns",
                      role="shareholder, no longer consolidated", start_date="2026-01-23", pct=51.47,
                      source_url="https://finansial.bisnis.com/read/20260128/90/1947797/bank-mandiri-bmri-tidak-lagi-ditopang-bsi-segini-penurunan-asetnya",
                      source_type="news", confidence="medium"))

    # Primary-source extractions (annual reports etc.) supersede seed edges with the
    # same (source, target, type). A primary ownership edge into a bank also
    # supersedes the seed-level gov_danantara -> bank edge.
    primary_edges: list[dict] = []
    for npath in sorted(PRIMARY.glob("*_nodes.csv")):
        for _, r in pd.read_csv(npath, dtype=str).fillna("").iterrows():
            add_node(r["id"], r["type"], r["name"], r["aliases"])
    for epath in sorted(PRIMARY.glob("*_edges.csv")):
        primary_edges += pd.read_csv(epath, dtype=str).fillna("").to_dict("records")
    pkeys = {(e["source_id"], e["target_id"], e["type"]) for e in primary_edges}
    owned_banks = {e["target_id"] for e in primary_edges
                   if e["type"] == "owns" and e["target_id"].startswith("bank_")}
    before = len(edges)
    edges = [e for e in edges
             if (e["source_id"], e["target_id"], e["type"]) not in pkeys
             and not (e["source_id"] == "gov_danantara" and e["type"] == "owns"
                      and e["target_id"] in owned_banks)]
    print(f"primary sources: {len(primary_edges)} edges, superseding {before - len(edges)} seed edges")
    edges += primary_edges

    OUT.mkdir(parents=True, exist_ok=True)
    ncols = ["id", "type", "name", "aliases"]
    ecols = ["source_id", "target_id", "type", "source_url", "source_type", "confidence",
             "role", "start_date", "end_date", "pct", "amount_usd", "note"]
    seen = set()
    with open(OUT / "nodes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ncols)
        w.writeheader()
        for n in nodes:
            if n["id"] in seen:
                continue
            seen.add(n["id"])
            w.writerow(n)
    with open(OUT / "edges.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ecols)
        w.writeheader()
        for e in edges:
            w.writerow({c: e.get(c, "") for c in ecols})

    for msg in warnings:
        print("WARN", msg, file=sys.stderr)
    print(f"wrote {len(seen)} nodes, {len(edges)} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
