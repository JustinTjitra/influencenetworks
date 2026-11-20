"""Stakeholder exposure monitor: the page for one firm. Private use, password protected."""

from __future__ import annotations

from datetime import date
from urllib.parse import quote

import pandas as pd
import streamlit as st

from influence.app import auth, data, exposure, lenders, timeline

NO_RESULTS_TEXT = "Returns appear here after the event study has been run."
CAR_COLUMNS = ["car", "sector_median_car"]
SECTIONS = ("Stakeholder map", "Exposure profile", "Event timeline", "Lenders")


def _link_config(df: pd.DataFrame) -> dict:
    return {c: st.column_config.LinkColumn(c) for c in df.columns if c.startswith("source_url")}


def render_stakeholder_map(bundle, ticker: str, on: date) -> None:
    st.header("Stakeholder map")
    nodes, edges = data.network(bundle, ticker, on)
    names = dict(zip(nodes["id"], nodes["name"]))
    for group, part in nodes.groupby("stakeholder_group", sort=True):
        st.subheader(group)
        st.dataframe(part[["name", "type", "hop"]], hide_index=True, use_container_width=True)
    st.subheader("Relationships")
    if edges.empty:
        st.write("No relationships recorded for this firm on this date.")
        return
    shown = edges.copy()
    shown.insert(0, "from_name", shown["source"].map(names))
    shown.insert(1, "to_name", shown["target"].map(names))
    shown = shown.drop(columns=["source", "target"])
    st.dataframe(shown, hide_index=True, use_container_width=True,
                 column_config=_link_config(shown))


def render_exposure(bundle, ticker: str, on: date) -> None:
    st.header("Exposure profile")
    prof = exposure.profile(bundle, ticker, on)
    st.dataframe(prof[["label", "display", "n_edges"]], hide_index=True,
                 use_container_width=True)
    for row in prof.itertuples(index=False):
        with st.expander(f"{row.label}: evidence ({row.n_edges})"):
            ev = exposure.evidence(bundle, ticker, on, row.measure)
            if ev.empty:
                st.write("No relationships recorded for this measure.")
            else:
                st.dataframe(ev, hide_index=True, use_container_width=True,
                             column_config=_link_config(ev))
    st.caption(exposure.data_note(bundle, ticker, on))


def timeline_view(bundle, ticker: str, results_dir=None) -> tuple[pd.DataFrame, bool]:
    """Timeline table as displayed. `firm_value` is blank for composite ('all') rows."""
    tl = timeline.timeline(bundle, ticker, results_dir)
    tl["firm_value"] = tl["firm_value"].astype(float).where(tl["tested_measure"] != "all")
    has = timeline.has_results(results_dir)
    if not has:
        tl = tl.drop(columns=CAR_COLUMNS)
    return tl, has


def render_timeline(bundle, ticker: str) -> None:
    st.header("Event timeline")
    tl, has = timeline_view(bundle, ticker)
    if not has:
        st.write(NO_RESULTS_TEXT)
    st.dataframe(tl, hide_index=True, use_container_width=True,
                 column_config=_link_config(tl))


def render_lenders(bundle, ticker: str) -> None:
    st.header("Lenders")
    df = lenders.lenders(bundle, ticker)
    if df.empty:
        st.write("No financing records for this firm (palm oil firms only).")
        return
    st.subheader("Credit by bank (USD millions)")
    st.dataframe(lenders.credit_by_bank(df), hide_index=True, use_container_width=True)
    for kind, part in df.groupby("kind", sort=True):
        st.subheader(f"Records: {kind}")
        st.dataframe(part, hide_index=True, use_container_width=True,
                     column_config=_link_config(part))
    st.caption(lenders.licence_note())


def render_footer() -> None:
    try:
        email = str(st.secrets.get("contact_email", "") or "")
    except FileNotFoundError:
        email = ""
    if email:
        link = f"[{email}](mailto:{quote(email, safe='@')})"
    else:
        link = "contact the project owner"
    st.markdown("---")
    st.markdown(f"Every item links to its source. Report an error: {link}")


def render_firm(bundle, ticker: str, on: date) -> None:
    st.subheader(f"{ticker}: {data.firm_label(bundle, ticker)}")
    render_stakeholder_map(bundle, ticker, on)
    render_exposure(bundle, ticker, on)
    render_timeline(bundle, ticker)
    render_lenders(bundle, ticker)


def main() -> None:
    st.set_page_config(page_title="Stakeholder exposure monitor", layout="wide")
    st.title("Stakeholder exposure monitor")
    auth.require_password()
    bundle = data.load()
    tk = bundle.tickers.sort_values(["sector_bucket", "ticker"])
    sector = st.selectbox("Sector", sorted(tk["sector_bucket"].unique()))
    firms = tk[tk["sector_bucket"] == sector]
    ticker = st.selectbox("Firm", list(firms["ticker"]),
                          format_func=lambda t: f"{t}: {data.firm_label(bundle, t)}")
    lo, hi = data.date_bounds(bundle)
    on = st.slider("Date", min_value=lo, max_value=hi, value=hi)
    render_firm(bundle, ticker, on)
    render_footer()


if __name__ == "__main__":
    main()
