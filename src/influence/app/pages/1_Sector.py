"""Stakeholder exposure monitor: firms within one sector. Private use, password protected."""

from __future__ import annotations

import streamlit as st

from influence.app import auth, data, sector, streamlit_app

NO_RESULTS_TEXT = "Results appear here after the event study has been run."


def _link_config(df):
    return {c: st.column_config.LinkColumn(c) for c in df.columns if c.startswith("source_url")}


def main() -> None:
    st.set_page_config(page_title="Sector comparison", layout="wide")
    st.title("Sector comparison")
    auth.require_password()
    bundle = data.load()
    name = st.selectbox("Sector", sorted(bundle.tickers["sector_bucket"].unique()))
    lo, hi = data.date_bounds(bundle)
    on = st.slider("Date", min_value=lo, max_value=hi, value=hi)

    st.header("Connection measures")
    st.dataframe(sector.measures_table(bundle, name, on), hide_index=True,
                 use_container_width=True)

    st.header("Events in this sector's sample")
    events = sector.event_table(bundle, name)
    st.dataframe(events, hide_index=True, use_container_width=True,
                 column_config=_link_config(events))

    st.header("Stacked estimates")
    stacked = sector.stacked_results()
    if stacked is None:
        st.write(NO_RESULTS_TEXT)
    else:
        st.dataframe(stacked, hide_index=True, use_container_width=True)
    streamlit_app.render_footer()


if __name__ == "__main__":
    main()
