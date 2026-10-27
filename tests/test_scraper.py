"""Fetch tests against a real local HTTP server (no mocks, no network)."""

import asyncio
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from tmobile_deals.scraper import ScraperError, fetch_deals, fetch_html

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "offers_sample.html").read_text(
    encoding="utf-8"
)


class _State:
    def __init__(self) -> None:
        self.requests = 0
        self.user_agents: list[str] = []
        self.mode = "ok"


def _make_server(state: _State) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib name
            state.requests += 1
            state.user_agents.append(self.headers.get("User-Agent", ""))
            if state.mode == "flaky" and state.requests == 1:
                self.send_response(429)
                self.send_header("Retry-After", "0")
                self.end_headers()
                return
            if state.mode == "server-error":
                self.send_response(500)
                self.end_headers()
                return
            body = FIXTURE_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            pass

    return ThreadingHTTPServer(("127.0.0.1", 0), Handler)


@pytest.fixture()
def server_url() -> Iterator[tuple[str, _State]]:
    state = _State()
    server = _make_server(state)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    yield f"http://{host}:{port}/offers", state
    server.shutdown()
    server.server_close()


def test_fetch_html_returns_page_and_sends_user_agent(
    server_url: tuple[str, _State],
) -> None:
    url, state = server_url
    html = asyncio.run(fetch_html(url, user_agent="test-agent/1.0"))
    assert "Galaxy S26+ On Us." in html
    assert state.user_agents == ["test-agent/1.0"]


def test_fetch_deals_parses_local_page(server_url: tuple[str, _State]) -> None:
    url, _ = server_url
    deals = asyncio.run(fetch_deals(url))
    assert [deal.title for deal in deals] == [
        "All-New Phone Duo. Yours for $1000 off.",
        "Galaxy S26+ On Us.",
        "Limited time: $99 Galaxy Watch Ultra2.",
        "Introducing the new moto pad.",
        "Buy 3 or more iPhone accessories and save 25% today.",
    ]


def test_fetch_retries_once_after_429(server_url: tuple[str, _State]) -> None:
    url, state = server_url
    state.mode = "flaky"
    html = asyncio.run(fetch_html(url))
    assert "Galaxy S26+ On Us." in html
    assert state.requests == 2


def test_persistent_500_raises_scraper_error(server_url: tuple[str, _State]) -> None:
    url, state = server_url
    state.mode = "server-error"
    with pytest.raises(ScraperError, match="failed after 2 attempt"):
        asyncio.run(fetch_html(url))
    assert state.requests == 2


def test_unreachable_host_raises_scraper_error() -> None:
    with pytest.raises(ScraperError):
        asyncio.run(fetch_html("http://127.0.0.1:9/offers", timeout_s=2.0))
