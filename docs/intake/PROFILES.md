# Collecting exchange company profiles (owner's machine)

The collector saves the exchange's company profile for each ticker as raw JSON, one file
per ticker, in a dated folder. It cannot run from cloud sessions (the exchange site is
behind Cloudflare). Output goes to `data/raw/idx_profiles/<YYYY-MM-DD>/<TICKER>.json`
and is not committed.

The endpoint (`/primary/ListedCompany/GetCompanyProfilesDetail?KodeEmiten=<TICKER>&language=en-us`)
is **unconfirmed**: it was reported by third-party scrapers, not by the exchange. If the
trial returns errors, send back the printed status codes rather than guessing.

## Commands
1. Install (browser mode needs Playwright; it is not a project dependency):
   ```
   pip install -e ".[dev]" playwright && playwright install chromium
   ```

2. Trial run on two tickers (a browser window opens; wait for it to finish):

   ```
   python -m influence.interlocks.collect_profiles --browser --limit 2
   ```

3. Full run (safe to repeat: tickers already saved today are skipped; it stops after
   3 failures in a row and waits 3 to 6 seconds between requests):

   ```
   python -m influence.interlocks.collect_profiles --browser
   ```

Plain HTTP mode (`--http`) usually gets blocked. If you try it, set `CONTACT_EMAIL`
first; it goes into the User-Agent and the script refuses to start without it.
A status of 200 with 0 bytes saved means a block page came back, not a profile.

## What to send back
After the trial, send **one sample JSON file** first (for example
`data/raw/idx_profiles/<date>/<TICKER>.json`) so the parser can be written against the
real field names. Send the rest only after that is confirmed.
