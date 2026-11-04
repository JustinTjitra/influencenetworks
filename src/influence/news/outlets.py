"""Outlets in the coverage analysis.

`group` links each outlet to its media_group node so the analysis can compute the
owner network. `crawl` is our starting assumption from the robots.txt review
(docs/source_access_report.md); robots.txt is still checked at runtime and wins.
"""

OUTLETS = {
    # party-linked owners (treatment)
    "okezone.com":        {"group": "mg_mnc",          "crawl": True},
    "inews.id":           {"group": "mg_mnc",          "crawl": True},
    "sindonews.com":      {"group": "mg_mnc",          "crawl": True},
    "metrotvnews.com":    {"group": "mg_media_group",  "crawl": True},
    "mediaindonesia.com": {"group": "mg_media_group",  "crawl": True},
    "viva.co.id":         {"group": "mg_viva",         "crawl": True},
    "tvonenews.com":      {"group": "mg_viva",         "crawl": True},
    "beritasatu.com":     {"group": "mg_b_universe",   "crawl": True},
    # comparison
    "kompas.com":         {"group": "mg_kompas_gramedia", "crawl": True},
    "tempo.co":           {"group": "mg_tempo",        "crawl": True},
    "detik.com":          {"group": "mg_detik",        "crawl": True},
    "cnnindonesia.com":   {"group": "mg_ct_corp",      "crawl": True},
    "kumparan.com":       {"group": "mg_kumparan",     "crawl": True},
    "idntimes.com":       {"group": "mg_idn",          "crawl": True},
}

USER_AGENT = (
    "id-influence-network-research/0.1 (academic media research; "
    "respects robots.txt; contact: set CONTACT_EMAIL env var)"
)
