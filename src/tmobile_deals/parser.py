"""Parse T-Mobile's offers page HTML into :class:`Deal` objects.

Verified against the live page on 2026-10-27 (see ``RECON.md``). The
page renders its offers server-side as ``.xpr-promoCard`` components:

* title: ``.xpr-promoCard__title`` (an ``h2``/``h3``)
* description: paragraphs inside ``.xpr-promoCard__body`` (absent on
  most cards, so the description is often empty -- that is the real
  shape of the page, not a parse failure)
* link: the first ``a[href]`` inside ``.xpr-promoCard__ctas``
* section: the nearest preceding ``.xpr-cardContainer__headline``
  ("Phone deals.", "Smartwatch deals.", ...); cards before the first
  headline are the hero offers and get section ``"Featured"``

Cards after the "Explore T-Mobile" heading are site-navigation tiles
(HOME INTERNET, BUSINESS, ...), not offers, so parsing stops there.
(The heading's markup is ``Explore <nobr>T-Mobile</nobr>.``, so the
comparison strips its trailing period.)
These selectors are a snapshot of the page as it looked on
2026-10-27 and will drift when T-Mobile redesigns the page; when the
parser starts returning zero deals, re-check the live markup before
assuming the site is down.
"""

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from tmobile_deals.models import Deal, DealCategory

DEFAULT_URL = "https://www.t-mobile.com/offers"

_EXPLORE_HEADING = "Explore T-Mobile"


def _clean(text: str) -> str:
    # Joining inline elements with a space restores word breaks the
    # markup omits ("new< span>Galaxy"), then drop the space that
    # joining puts before trailing punctuation ("Duo .").
    collapsed = " ".join(text.split())
    return re.sub(r"\s+([.,;:!?%])", r"\1", collapsed)


def _determine_category(title: str, url: str, section: str) -> DealCategory:
    haystack = f"{section} {title} {url}".lower()
    url_lower = url.lower()
    # Device-type URL segments win over brand keywords: a Galaxy Watch
    # is a watch, not a phone, and a moto tablet is a tablet.
    if any(
        segment in url_lower
        for segment in ("/smart-watch/", "/tablet/", "/hotspot-iot-connected-devices/", "/devices/")
    ):
        return DealCategory.SERVICE
    if "accessor" in haystack:
        return DealCategory.ACCESSORY
    if "plan" in haystack or "/switch/" in url_lower:
        return DealCategory.PLAN
    if (
        "phone" in haystack
        or "cell-phone" in url_lower
        or "iphone" in haystack
        or "galaxy" in haystack
        or "pixel" in haystack
        or "motorola" in haystack
        or "razr" in haystack
    ):
        return DealCategory.PHONE
    return DealCategory.SERVICE


def _card_url(card: Tag, base_url: str) -> str | None:
    ctas = card.select_one(".xpr-promoCard__ctas")
    if ctas is None:
        return None
    link = ctas.select_one("a[href]")
    if link is None:
        return None
    href_value = link.get("href")
    href = href_value.strip() if isinstance(href_value, str) else ""
    if not href:
        return None
    resolved = urljoin(base_url, href)
    parsed = urlparse(resolved)
    # Strip tracking query strings (icid/INTNAV) and fragments so the
    # same offer always yields the same URL.
    return str(parsed._replace(query="", fragment="").geturl())


def parse_deals(html: str, base_url: str = DEFAULT_URL) -> list[Deal]:
    """Parse offers HTML into deals, in page order, deduplicated by URL.

    Cards without a title or without a call-to-action link are skipped:
    a card with neither is a navigation tile or a markup fragment, not
    an offer. Cards without a description body are kept with an empty
    description.
    """
    soup = BeautifulSoup(html, "html.parser")
    deals: list[Deal] = []
    seen_urls: set[str] = set()
    section = "Featured"

    for element in soup.find_all(True):
        if not isinstance(element, Tag):
            continue
        raw_classes = element.get("class")
        classes: list[str] = list(raw_classes) if isinstance(raw_classes, list) else []
        if "xpr-cardContainer__headline" in classes:
            section = _clean(element.get_text(" ")).rstrip(".")
            continue
        # The heading is "Explore <nobr>T-Mobile</nobr>." in the markup,
        # which cleans to "Explore T-Mobile ." -- strip the trailing
        # period before comparing.
        if (
            element.name == "h2"
            and _clean(element.get_text(" ")).rstrip(".").strip() == _EXPLORE_HEADING
        ):
            break
        if "xpr-promoCard" not in classes:
            continue
        if any("xpr-promoCard" in (parent.get("class") or []) for parent in element.parents):
            continue

        title_el = element.select_one(".xpr-promoCard__title")
        title = _clean(title_el.get_text(" ")) if title_el is not None else ""
        if not title:
            continue
        url = _card_url(element, base_url)
        if url is None or url in seen_urls:
            continue
        seen_urls.add(url)

        body = element.select_one(".xpr-promoCard__body")
        description = ""
        if body is not None:
            description = " ".join(
                _clean(p.get_text(" ")) for p in body.select("p") if _clean(p.get_text(" "))
            )

        deals.append(
            Deal(
                title=title,
                description=description,
                category=_determine_category(title, url, section),
                url=url,
                section=section,
            )
        )
    return deals
