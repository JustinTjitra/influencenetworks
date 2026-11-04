"""Load the Forests & Finance dataset into bank -> palm oil group `finances` edges.

Get the data:  download the full dataset from https://forestsandfinance.org/data/
(the "Download full dataset" button) and save it as
    data/raw/financing/forests_and_finance.xlsx   (or .csv)
Their terms are personal-use; ask Rainforest Action Network before publishing.

Run:  python -m influence.load_financing [path]

The dataset's exact column names have changed between releases, so columns are
found by matching candidate names (case-insensitive). Bank and company-group
names are mapped to graph ids through data/mappings/financing_names.csv;
anything unmapped is written to data/mappings/financing_unmapped.csv so a human
decides each match. Nothing is fuzzy-matched silently.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "financing"
MAPS = ROOT / "data" / "mappings"
OUT = ROOT / "data" / "primary" / "forests_finance_edges.csv"
SOURCE_URL = "https://forestsandfinance.org/data/"

COLUMN_CANDIDATES = {
    "bank": ["bank", "financier", "financier group", "bank group", "financier parent", "parent financier"],
    "group": ["group", "company group", "forest-risk group", "forest risk company group", "recipient group",
              "client group", "company"],
    "year": ["year", "deal year", "financial year"],
    "amount": ["amountusdmillions", "amount (us$ mln)", "amount (usd mln)", "amount usd m", "amount (usd m)", "value (us$ mln)",
               "amount", "value", "usd mln", "us$ mln"],
    "sector": ["sector", "forest-risk sector", "commodity", "subsector"],
    "country": ["forestriskclientcountry", "country of operation", "region of operation", "operation country"],
    "finance_type": ["finance type", "type of finance", "financing type", "deal type", "type"],
}
REQUIRED = ("bank", "group", "year", "amount")

# Credit = money provided in that year. Holdings = investor positions at a snapshot
# date (the 2026 file books them all in 2026), so they must never be summed with credit.
CREDIT = {"corporate loan", "revolving credit facility", "bond issuance", "share issuance",
          "project finance", "trade finance", "loan"}
HOLDING = {"bondholding", "shareholding"}


def categorise(t: str) -> str:
    t = (t or "").strip().lower()
    if t in CREDIT:
        return "credit"
    if t in HOLDING:
        return "holding"
    return "other"


def find_columns(df: pd.DataFrame) -> dict[str, str]:
    lower = {c.strip().lower(): c for c in df.columns}
    found = {}
    for key, cands in COLUMN_CANDIDATES.items():
        for c in cands:
            if c in lower:
                found[key] = lower[c]
                break
    missing = [k for k in REQUIRED if k not in found]
    if missing:
        raise SystemExit(f"could not find columns for {missing}; columns are: {list(df.columns)}")
    return found


def read_any(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        sheets = pd.read_excel(path, sheet_name=None)
        # take the largest sheet; the download has a readme sheet plus data
        return max(sheets.values(), key=len)
    return pd.read_csv(path)


def load_name_map() -> dict[tuple[str, str], str]:
    """(kind, raw_name_lower) -> node id, where kind is 'bank' or 'group'."""
    path = MAPS / "financing_names.csv"
    if not path.exists():
        return {}
    m = pd.read_csv(path, dtype=str).fillna("")
    return {(r.kind, r.raw_name.strip().lower()): r.node_id.strip()
            for r in m.itertuples() if r.node_id.strip()}


def build_edges(df: pd.DataFrame, cols: dict[str, str], name_map: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = pd.DataFrame({
        "bank": df[cols["bank"]].astype(str).str.strip(),
        "group": df[cols["group"]].astype(str).str.strip(),
        "year": pd.to_numeric(df[cols["year"]], errors="coerce"),
        "amount_musd": pd.to_numeric(df[cols["amount"]], errors="coerce"),
    })
    for opt in ("sector", "country", "finance_type"):
        d[opt] = df[cols[opt]].astype(str).str.strip() if opt in cols else ""

    if "sector" in cols:
        d = d[d.sector.str.contains("palm", case=False, na=False)]
    if "country" in cols:
        d = d[d.country.str.contains("indonesia", case=False, na=False)]
    d = d.dropna(subset=["year", "amount_musd"])

    d["bank_id"] = [name_map.get(("bank", b.lower()), "") for b in d.bank]
    d["group_id"] = [name_map.get(("group", g.lower()), "") for g in d.group]

    unmapped = pd.concat([
        d.loc[d.bank_id == "", ["bank"]].rename(columns={"bank": "raw_name"}).assign(kind="bank"),
        d.loc[d.group_id == "", ["group"]].rename(columns={"group": "raw_name"}).assign(kind="group"),
    ]).value_counts().reset_index(name="rows")

    ok = d[(d.bank_id != "") & (d.group_id != "")].copy()
    ok["category"] = ok.finance_type.map(categorise)
    agg = (ok.groupby(["bank_id", "group_id", "year", "category"])
             .agg(amount_musd=("amount_musd", "sum"),
                  types=("finance_type", lambda s: "; ".join(sorted({x.capitalize() for x in s if x and x != "nan"}))))
             .reset_index())
    notes = {
        "credit": "Forests & Finance attribution; Indonesia palm oil; loans, credit facilities and underwriting summed per bank-group-year",
        "holding": "Forests & Finance attribution; Indonesia palm oil; value of bonds/shares held at the dataset's snapshot date. A stock, not a flow: never add it to credit",
        "other": "Forests & Finance attribution; Indonesia palm oil; unclassified deal type",
    }
    edges = pd.DataFrame({
        "source_id": agg.bank_id,
        "target_id": agg.group_id,
        "type": "finances",
        "source_url": SOURCE_URL,
        "source_type": "ngo_dataset",
        "confidence": "medium",   # NGO estimates of deal attribution, not bank disclosures
        "role": agg.category + ": " + agg.types,
        "start_date": agg.year.astype(int).astype(str),
        "end_date": agg.year.astype(int).astype(str),
        "pct": "",
        "amount_usd": (agg.amount_musd * 1_000_000).round(0),
        "note": agg.category.map(notes),
    })
    return edges, unmapped


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        path = Path(argv[1])
    else:
        cands = sorted(RAW.glob("forests_and_finance.*"))
        if not cands:
            print(__doc__)
            return 2
        path = cands[0]
    df = read_any(path)
    cols = find_columns(df)
    print("columns used:", cols)
    edges, unmapped = build_edges(df, cols, load_name_map())
    MAPS.mkdir(parents=True, exist_ok=True)
    unmapped.to_csv(MAPS / "financing_unmapped.csv", index=False)
    edges.to_csv(OUT, index=False)
    print(f"wrote {len(edges)} finances edges to {OUT.relative_to(ROOT)}; "
          f"{len(unmapped)} unmapped names in data/mappings/financing_unmapped.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
