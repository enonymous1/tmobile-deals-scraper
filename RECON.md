# Recon: t-mobile.com/offers, 2026-10-27

How the parser's selectors were verified, so the next person to touch them can tell what was observed vs. assumed. All observations are from a single fetch of the live page on 2026-10-27; no HTML from that fetch is shipped in this repo (the tests use a small hand-written fixture instead).

## Endpoint

- `GET https://www.t-mobile.com/offers` → HTTP 200, ~802 KB of HTML, with a browser User-Agent. No login, no API key.
- User-Agent gating (verified with curl and aiohttp, three variants): a browser UA gets 200; an identifying UA (`tmobile-deals-scraper/2.0.0`, with or without browser `Accept` headers) and a bare default UA both get HTTP 403 Access Denied from the edge. The shipped default UA is therefore a browser string, documented as such in the README. No other bot mitigation was encountered — no CAPTCHA, no redirect loop — and none is worked around.
- The page is an Adobe Experience Manager / Helix site. Offers are in the static HTML — no JavaScript rendering is needed to see them, and there is no `__NEXT_DATA__` payload or offers JSON API to consume instead.
- `robots.txt`: `User-agent: *` does not disallow `/offers` (it disallows account/checkout/search paths). That covers polite crawling only; see the README's "Be polite" section.

## Observed shape

- 35 `.xpr-promoCard` elements in the fetched HTML, each with a unique call-to-action URL (after stripping query strings).
- Title: `.xpr-promoCard__title` (`h2`/`h3`). Titles contain inline spans, so text must be joined with spaces — naive concatenation produces "newGalaxy Tab" from the real markup.
- Description: paragraphs inside `.xpr-promoCard__body`. Only the 4 hero cards have a body; the other section cards have none, so most descriptions are legitimately empty.
- Link: the first `a[href]` inside `.xpr-promoCard__ctas`. Hrefs are absolute with `icid=`/`INTNAV=` tracking parameters; stripping query + fragment yields stable URLs and is what makes deduplication work.
- Sections: `.xpr-cardContainer__headline` elements in document order — "Phone deals.", "Smartwatch deals.", "Tablet, hotspot deals and more.", "Accessories deals." Cards before the first headline are hero offers (section `Featured`).
- The last 6 promo cards sit after an `h2` reading "Explore T-Mobile" and are navigation tiles (HOME INTERNET, BUSINESS, COVERAGE MAP, T-MOBILE TRAVEL, MAGENTA STATUS, FREE TRIAL). Parsing stops at that heading, leaving 29 offers. If T-Mobile reorders the page, this rule is the first thing to re-check. Caution: the heading's markup is `Explore <nobr>T-Mobile</nobr>.`, which cleans to "Explore T-Mobile ." — an exact-equality check misses it, and a live smoke run on 2026-10-27 returned all 35 cards (including the 6 tiles) before this was fixed. The comparison now strips the trailing period.
- Category is derived from the URL path first for device types (`/smart-watch/`, `/tablet/`, `/hotspot-iot-connected-devices/`, `/devices/` → service), because brand keywords misclassify: a Galaxy Watch or moto tablet is not a phone. Section and title keywords then handle accessories, plans, and phones.
- No structured price, original price, or expiry anywhere in the markup — no `data-*` price attributes, no JSON-LD offer data (the single JSON-LD block is empty). Savings language lives only in titles/descriptions and is deliberately not parsed into price fields.
- Ordering: page order, top to bottom. No pagination.
- Throttling: none observed (no 429, no retry needed on the probe fetch). The fetcher still retries once on 429/5xx and honours `Retry-After`, and a throttled run that keeps failing raises instead of reporting a partial count as a measurement.

## What was NOT verified

- How the page behaves from other regions/locales or with different query parameters.
- Whether the selectors survive the next T-Mobile redesign (they will not, eventually — see the snapshot warning in the README).
