# T19: Monitor firm page

## Goal
The Streamlit page for one firm, wiring together the tested data functions. Private use
only; password gate included.

## Read first
- `CLAUDE.md` (hard rules 1, 4, 5)
- `docs/DESIGN.md` section 7 (firm page and design rules)
- `src/influence/app/data.py`, `exposure.py`, `timeline.py`, `lenders.py`

## Files you may create or edit
- `src/influence/app/streamlit_app.py` (new)
- `src/influence/app/auth.py` (new)
- `tests/test_app_firm_page.py` (new)
- `.streamlit/secrets.toml.example` (new: `app_password = "change-me"` and a comment)
- `.gitignore` (append one line: `.streamlit/secrets.toml`)

## Specification
- `auth.check_password(entered, expected) -> bool` uses `hmac.compare_digest`;
  `auth.require_password()` reads `st.secrets["app_password"]`, shows a password box,
  and stops the app until it matches. If no secret is configured the app refuses to
  start with a clear message (never run open).
- Page: title; firm selector (ticker and name, grouped by sector); date slider within
  `data.date_bounds`; then four sections in this order:
  1. "Stakeholder map": the `network` nodes grouped by `stakeholder_group` in tables
     (a graph drawing is not required), each edge row showing its source link.
  2. "Exposure profile": the `profile` table; under each measure an expander with its
     `evidence` rows; the `data_note`. The word is "exposure". No composite score.
  3. "Event timeline": the `timeline` table. If `has_results()` is False show
     "Returns appear here after the event study has been run." and hide the CAR columns.
  4. "Lenders": the `lenders` tables with `licence_note()` (palm oil firms only).
- Footer on every page: "Every item links to its source. Report an error:" followed by
  a mailto link built from `st.secrets.get("contact_email", "")`; if empty, show
  "contact the project owner". Never hard-code an address.
- Keep all text neutral: no "risk", "risky", "captured", "corrupt", "favoured", "crony".
- Put page-building code in functions (`render_firm(bundle, ticker, on)`) so that the
  test can call them.
- Tests: `check_password` true and false cases; if `streamlit` is importable, use
  `streamlit.testing.v1.AppTest` to run the app with a secret set and assert it renders
  without exception and shows the four section headers; otherwise skip that test with
  `pytest.importorskip`.

## Acceptance
`pytest -q tests/test_app_firm_page.py && python -c "import ast,sys; ast.parse(open('src/influence/app/streamlit_app.py').read()); print('parses')"`

## Out of scope
Deployment, the sector page (T20), charts of returns, any price data.
