# Changelog

## 2.0.0 — 2026-10-27

Rewrite of the original `ss-t-mo` sketch as an installable package. Breaking changes throughout; the v1 code is not API-compatible with this release.

### Added

- Installable package `tmobile_deals` with a `tmobile-deals` CLI: `--url`, `--fixture`, `--output`, `--format table|csv|json`, `--timeout`, `--user-agent`.
- Parser for the real offers page, verified against live HTML on 2026-10-27: `.xpr-promoCard` cards, section headings, hero offers, and the "Explore T-Mobile" navigation tiles excluded (see `RECON.md`).
- Deduplication by cleaned URL; tracking query strings (`icid`, `INTNAV`) stripped.
- CSV and JSON output; the table summary groups by section and no longer crashes on an empty result.
- Tests: fixture-based parser tests, model tests, CLI tests, and fetch tests against a local HTTP server (retry-on-429, persistent-500, unreachable host).
- GitHub Actions CI (Python 3.10–3.13): ruff, mypy strict, pytest. MIT LICENSE.

### Changed

- Python floor raised from 3.8 to 3.10.
- `aiohttp`/`beautifulsoup4` version ranges replace the pinned 2023 versions that no longer build on current Python. The `pandas` dependency is gone — output is plain CSV/JSON now. `python-dotenv` is gone too; the URL and User-Agent are set with flags or the `TMOBILE_DEALS_URL` / `TMOBILE_DEALS_USER_AGENT` environment variables.
- Fetching is fail-loud: timeout, `raise_for_status`, one retry on 429/5xx honouring `Retry-After`, and `ScraperError` instead of a partial result.

### Removed

- The placeholder selectors (`.deals-container .deal-item`) that never matched the live page.
- `microsoft-visual-cpp-build-tools` from the dependency list (a Windows toolchain, not a Python package).
- The broken `src/main.py` entry point (absolute import vs. relative import, no package markers).

## 1.0.0 — 2026-07-19

Original `ss-t-mo`: async scraper sketch, `Deal` model, and README. Never ran end-to-end as documented.
