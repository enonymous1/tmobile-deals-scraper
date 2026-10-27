# T-Mobile Deals Scraper

Fetch and list the special offers on [T-Mobile's deals page](https://www.t-mobile.com/offers) from the command line — as a readable table, CSV, or JSON.

```bash
tmobile-deals
```

```text
Found deals: 29

Deals by section:
  Phone deals: 9
  Smartwatch deals: 7
  ...
```

The original project (2026, `ss-t-mo`) was an 86-line sketch whose parser only matched placeholder HTML and whose entry point crashed on import. This is a rewrite around the page as it actually looks: offers are parsed from the server-rendered promo cards, with section headings, empty descriptions where the page has none, and no invented prices. See [CHANGELOG.md](CHANGELOG.md) for what changed and [RECON.md](RECON.md) for how the page was verified.

> **Snapshot warning.** The selectors in `src/tmobile_deals/parser.py` describe the page as it looked on 2026-10-27. T-Mobile redesigns this page regularly; if the tool suddenly reports zero deals, check the live markup first — the selectors have probably drifted, not the network. The `--fixture` mode and the tests exist so a new snapshot can be verified without hitting the live site.

## Quick start

Requires Python 3.10+.

```bash
pip install .
tmobile-deals
```

Or, without installing:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
tmobile-deals
```

## Usage

```bash
# Print the deals table (default)
tmobile-deals

# Save as CSV / JSON
tmobile-deals --format csv --output deals.csv
tmobile-deals --format json --output deals.json

# Parse a saved copy of the page instead of fetching it (offline, repeatable)
tmobile-deals --fixture tests/fixtures/offers_sample.html

# Point at a different page, e.g. a regional variant
tmobile-deals --url https://www.t-mobile.com/offers/apple-iphone-deals

# Environment overrides
TMOBILE_DEALS_URL=https://www.t-mobile.com/offers tmobile-deals
```

Options: `--url`, `--fixture`, `--output`, `--format table|csv|json`, `--timeout` (seconds, default 30), `--user-agent`.

Each run makes exactly one request to the page, with a timeout and one retry on transient failures. A fetch that keeps failing exits with an error instead of printing an empty result as if the page had no offers.

## What a deal looks like

| Field | Source |
|---|---|
| `title` | The promo card heading |
| `description` | Paragraphs in the card body — empty on most cards, because the page has none there |
| `category` | `phone`, `plan`, `accessory`, or `service`, from the section heading and link |
| `url` | The card's call-to-action link, with tracking query strings removed |
| `section` | The section heading the card sits under (`Phone deals`, `Smartwatch deals`, …), or `Featured` for the hero offers |
| `price`, `original_price`, `valid_until` | Always empty: the page carries no structured price or expiry. Prose like "$1000 off" in a title is savings copy, not a price, and is not parsed into one. |

## Be polite

This tool fetches a public marketing page once per run, respects `Retry-After`, and does not crawl. T-Mobile's `robots.txt` does not disallow `/offers` for generic crawlers (checked 2026-10-27), but that is not permission to hammer the site: use `--fixture` with a saved copy for development and testing, and check T-Mobile's terms before any automated or commercial use. This project is not affiliated with or endorsed by T-Mobile.

One deliberate choice to know about: the default User-Agent is a browser string, because T-Mobile's edge returns HTTP 403 Access Denied to any non-browser User-Agent — verified on 2026-10-27 with three request variants (see `RECON.md`). Pass `--user-agent` with an identifying string if you prefer one, and expect a 403. The tool does not log in, solve challenges, or bypass any other access control.

## Development

```bash
pip install -e ".[dev]"
ruff check src tests
ruff format --check src tests
mypy src
pytest
```

## License

MIT — see [LICENSE](LICENSE).
