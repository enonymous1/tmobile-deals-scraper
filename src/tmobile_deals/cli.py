"""Command line: ``tmobile-deals``.

Fetches T-Mobile's offers page (or parses a saved HTML file with
``--fixture``) and prints or writes the deals as a table, CSV, or
JSON. The original script printed a pandas summary and crashed on an
empty result; this one reports "no deals found" and still writes a
well-formed empty output.
"""

import argparse
import asyncio
import csv
import io
import json
import os
import sys
from collections import Counter
from pathlib import Path

from tmobile_deals import __version__
from tmobile_deals.models import Deal
from tmobile_deals.parser import DEFAULT_URL, parse_deals
from tmobile_deals.scraper import DEFAULT_TIMEOUT_S, DEFAULT_USER_AGENT, ScraperError, fetch_deals

_CSV_FIELDS = [
    "title",
    "description",
    "category",
    "url",
    "price",
    "original_price",
    "valid_until",
    "section",
]


def render_table(deals: list[Deal]) -> str:
    """Render deals grouped by section, as plain text."""
    lines = [f"Found deals: {len(deals)}", ""]
    counts = Counter(deal.section for deal in deals)
    lines.append("Deals by section:")
    for section, count in counts.most_common():
        lines.append(f"  {section}: {count}")
    lines.append("")
    lines.append("Detailed deals:")
    for deal in deals:
        lines.append(f"\nTitle: {deal.title}")
        lines.append(f"Category: {deal.category.value}")
        if deal.section:
            lines.append(f"Section: {deal.section}")
        if deal.description:
            lines.append(f"Description: {deal.description}")
        lines.append(f"URL: {deal.url}")
    return "\n".join(lines) + "\n"


def render_csv(deals: list[Deal]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_CSV_FIELDS)
    writer.writeheader()
    for deal in deals:
        writer.writerow(deal.as_dict())
    return buffer.getvalue()


def render_json(deals: list[Deal]) -> str:
    return json.dumps([deal.as_dict() for deal in deals], indent=2) + "\n"


def _render(deals: list[Deal], fmt: str) -> str:
    if fmt == "csv":
        return render_csv(deals)
    if fmt == "json":
        return render_json(deals)
    return render_table(deals)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tmobile-deals",
        description="Fetch and list special offers from t-mobile.com/offers.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--url",
        default=os.environ.get("TMOBILE_DEALS_URL", DEFAULT_URL),
        help="Offers page URL (default: %(default)s; override with TMOBILE_DEALS_URL).",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=None,
        help="Parse a saved HTML file instead of fetching the live page.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write output to this file instead of stdout.",
    )
    parser.add_argument(
        "--format",
        choices=["table", "csv", "json"],
        default="table",
        help="Output format (default: %(default)s).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_S,
        help="Total request timeout in seconds (default: %(default)s).",
    )
    parser.add_argument(
        "--user-agent",
        default=os.environ.get("TMOBILE_DEALS_USER_AGENT", DEFAULT_USER_AGENT),
        help="User-Agent sent with the request.",
    )
    return parser


async def _load_deals(args: argparse.Namespace) -> list[Deal]:
    if args.fixture is not None:
        html = args.fixture.read_text(encoding="utf-8")
        return parse_deals(html, base_url=args.url)
    return await fetch_deals(args.url, timeout_s=args.timeout, user_agent=args.user_agent)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        deals = asyncio.run(_load_deals(args))
    except ScraperError as exc:
        print(f"tmobile-deals: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"tmobile-deals: {exc}", file=sys.stderr)
        return 1
    if not deals:
        print(f"tmobile-deals: no deals found at {args.url}", file=sys.stderr)
    output = _render(deals, args.format)
    if args.output is not None:
        args.output.write_text(output, encoding="utf-8")
        print(f"Wrote {len(deals)} deal(s) to {args.output}")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
