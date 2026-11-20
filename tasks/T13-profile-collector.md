# T13: Exchange profile collector for the owner's machine

## Goal
A script the owner runs on his own computer to save the Indonesia Stock Exchange's
company profile for each ticker, raw and dated. It cannot be run from cloud sessions
(the exchange site is behind Cloudflare), so it must be simple and safe to run blind.

## Read first
- `CLAUDE.md`
- `docs/HANDOFF_MODULES.md`, Module B, "Data" table and pipeline step 1
- `research_notes/Influence network project sources/annual_reports_palm_media.md`
  (section on the exchange's profile endpoint, if present)
- `src/influence/news/crawl.py` (read only: the project's polite-crawling conventions)

## Files you may create or edit
- `src/influence/interlocks/__init__.py` (create with a one-line docstring if missing)
- `src/influence/interlocks/collect_profiles.py` (new)
- `tests/test_interlocks_collect.py` (new)
- `docs/intake/PROFILES.md` (new, under 40 lines: how the owner runs it)

## Specification
- Pure, tested helpers: `profile_url(ticker, base=...)` building
  `<base>/primary/ListedCompany/GetCompanyProfilesDetail?KodeEmiten=<TICKER>&language=en-us`
  (the endpoint is reported, not confirmed: keep `base` and the path as module constants
  with a comment saying so); `out_path(root, day, ticker)` ->
  `<root>/<YYYY-MM-DD>/<TICKER>.json`; `load_tickers(csv_path)`; `plan(tickers, root,
  day)` listing which tickers still need fetching (skip files that exist and are
  non-empty).
- `fetch_all(tickers, root, day, fetch, sleep, min_delay=3.0, max_delay=6.0)` takes the
  `fetch(url) -> (status, bytes)` and `sleep` functions as arguments so tests can pass
  fakes. It writes the raw bytes unchanged, waits a random delay between requests, stops
  after 3 consecutive failures, and returns a list of `(ticker, status, bytes_written)`.
- A `--browser` mode builds `fetch` with Playwright (import inside the function; say in
  the docs how to install it) because plain HTTP is blocked; a `--http` mode uses
  `httpx` with a User-Agent that names the project and the `CONTACT_EMAIL` environment
  variable (never a hard-coded address).
- Default output root `data/raw/idx_profiles/` (not committed). `--limit N` for a trial
  run; `--tickers-file` defaults to `data/mappings/tickers.csv`.
- Tests: URL building, output paths, skip-existing, stop after 3 failures, delays called
  between requests, raw bytes preserved. No network in tests.
- `docs/intake/PROFILES.md`: the three commands to run (install, trial with
  `--limit 2`, full run), what to send back (one sample JSON first), and that the
  endpoint is unconfirmed.

## Acceptance
`pytest -q tests/test_interlocks_collect.py && python -m influence.interlocks.collect_profiles --help | head -5`

## Out of scope
Parsing the responses (T14), running the collector, adding Playwright to the required
dependencies.
