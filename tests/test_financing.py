import pandas as pd

from influence.load_financing import build_edges, find_columns

# Fictional rows shaped like the Forests & Finance export.
DF = pd.DataFrame({
    "Bank": ["Bank A", "Bank A", "Bank A", "Bank B", "Bank A"],
    "Group": ["Group X", "Group X", "Group X", "Group X", "Group X"],
    "Year": [2021, 2021, 2022, 2021, 2021],
    "Amount (US$ mln)": [10.0, 5.0, 7.0, 3.0, 99.0],
    "Sector": ["Palm Oil", "Palm Oil", "Palm Oil", "Palm Oil", "Pulp & Paper"],
    "Country of operation": ["Indonesia"] * 5,
    "Finance type": ["Corporate loan", "Bond issuance", "Corporate loan", "Corporate loan", "Corporate loan"],
})
NAMES = {("bank", "bank a"): "bank_a", ("group", "group x"): "pg_x"}


def test_columns_found():
    cols = find_columns(DF)
    assert cols["amount"] == "Amount (US$ mln)"


def test_aggregates_palm_only_and_reports_unmapped():
    edges, unmapped = build_edges(DF, find_columns(DF), NAMES)
    e21 = edges[(edges.start_date == "2021")]
    assert len(edges) == 2                       # 2021 and 2022 for bank_a -> pg_x
    assert e21.amount_usd.iloc[0] == 15_000_000  # pulp row excluded, loan + bond summed
    assert "Bank B" in set(unmapped.raw_name)


def test_holdings_never_summed_with_credit():
    df = DF.copy()
    df.loc[1, "Finance type"] = "Shareholding"
    edges, _ = build_edges(df, find_columns(df), NAMES)
    e21 = edges[edges.start_date == "2021"].set_index(edges[edges.start_date == "2021"].role.str.split(":").str[0])
    assert e21.loc["credit", "amount_usd"] == 10_000_000
    assert e21.loc["holding", "amount_usd"] == 5_000_000
