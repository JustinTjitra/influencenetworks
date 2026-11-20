"""Password gate for the private monitor. The app never runs open."""

from __future__ import annotations

import hmac

import streamlit as st

MISSING_MESSAGE = ("This app is not configured: no `app_password` secret is set, so it will "
                   "not start. Copy `.streamlit/secrets.toml.example` to "
                   "`.streamlit/secrets.toml` and set a password.")


def check_password(entered: str, expected: str) -> bool:
    """Constant-time comparison of the entered and expected passwords."""
    return hmac.compare_digest(str(entered).encode("utf-8"), str(expected).encode("utf-8"))


def _expected() -> str:
    try:
        value = st.secrets["app_password"]
    except (KeyError, FileNotFoundError):
        return ""
    return str(value or "")


def require_password() -> None:
    """Stop the app unless a configured password has been entered."""
    expected = _expected()
    if not expected:
        st.error(MISSING_MESSAGE)
        st.stop()
    if st.session_state.get("_authenticated"):
        return
    entered = st.text_input("Password", type="password", key="_password_box")
    if entered and check_password(entered, expected):
        st.session_state["_authenticated"] = True
        return
    if entered:
        st.error("Wrong password.")
    st.stop()
