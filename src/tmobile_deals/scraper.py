"""Fetch the offers page over HTTP and hand it to the parser.

Exactly one polite request per run, with a total timeout and a single
retry on transient failures. A fetch that is still failing after the
retry raises :class:`ScraperError` instead of returning a partial or
empty result -- zero deals from a failed fetch must never look like
zero deals on the page.

The default User-Agent is a browser string, deliberately and openly:
T-Mobile's edge returns HTTP 403 Access Denied to any non-browser
User-Agent (verified 2026-10-27; see RECON.md). Pass ``--user-agent``
with an identifying string if you prefer one, and expect a 403.
"""

import asyncio

import aiohttp

from tmobile_deals.models import Deal
from tmobile_deals.parser import DEFAULT_URL, parse_deals

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
DEFAULT_TIMEOUT_S = 30.0
MAX_ATTEMPTS = 2
_RETRY_DELAY_S = 2.0


class ScraperError(Exception):
    """Raised when the offers page cannot be fetched."""


async def fetch_html(
    url: str = DEFAULT_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    user_agent: str = DEFAULT_USER_AGENT,
    max_attempts: int = MAX_ATTEMPTS,
) -> str:
    """Return the raw HTML of ``url``.

    Retries once on connection errors, timeouts, HTTP 429, and 5xx
    responses, honouring a ``Retry-After`` header (capped at 30s) when
    the server sends one.
    """
    last_error: Exception | None = None
    timeout = aiohttp.ClientTimeout(total=timeout_s)
    for attempt in range(1, max_attempts + 1):
        try:
            async with aiohttp.ClientSession(
                timeout=timeout, headers={"User-Agent": user_agent}
            ) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.text()
        except aiohttp.ClientResponseError as exc:
            last_error = exc
            retryable = exc.status == 429 or exc.status >= 500
            if not retryable or attempt == max_attempts:
                break
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            delay = _RETRY_DELAY_S
            if retry_after is not None:
                try:
                    delay = min(float(retry_after), 30.0)
                except ValueError:
                    pass
            await asyncio.sleep(delay)
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            last_error = exc
            if attempt == max_attempts:
                break
            await asyncio.sleep(_RETRY_DELAY_S)
    raise ScraperError(f"GET {url} failed after {max_attempts} attempt(s): {last_error}")


async def fetch_deals(
    url: str = DEFAULT_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    user_agent: str = DEFAULT_USER_AGENT,
    max_attempts: int = MAX_ATTEMPTS,
) -> list[Deal]:
    """Fetch ``url`` and parse its offers into deals."""
    html = await fetch_html(
        url, timeout_s=timeout_s, user_agent=user_agent, max_attempts=max_attempts
    )
    return parse_deals(html, base_url=url)
