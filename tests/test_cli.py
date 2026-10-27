import csv
import io
import json
from pathlib import Path

import pytest

from tmobile_deals.cli import main, render_csv, render_json, render_table
from tmobile_deals.models import Deal, DealCategory
from tmobile_deals.parser import parse_deals

FIXTURE = "tests/fixtures/offers_sample.html"

DEALS = [
    Deal(
        title="Galaxy S26+ On Us.",
        description="",
        category=DealCategory.PHONE,
        url="https://www.t-mobile.com/cell-phone/samsung-galaxy-s26-plus",
        section="Phone deals",
    ),
    Deal(
        title="Save 40% on the Onyx Studio 9 speaker.",
        description="For a limited time.",
        category=DealCategory.ACCESSORY,
        url="https://www.t-mobile.com/accessory/onyx-studio-9",
        section="Accessories deals",
    ),
]


def test_render_table_groups_by_section() -> None:
    table = render_table(DEALS)
    assert "Found deals: 2" in table
    assert "Phone deals: 1" in table
    assert "Galaxy S26+ On Us." in table
    assert "URL: https://www.t-mobile.com/cell-phone/samsung-galaxy-s26-plus" in table


def test_render_csv_has_header_and_rows() -> None:
    rows = list(csv.DictReader(io.StringIO(render_csv(DEALS))))
    assert len(rows) == 2
    assert rows[0]["category"] == "phone"
    assert rows[1]["section"] == "Accessories deals"


def test_render_json_round_trips() -> None:
    assert json.loads(render_json(DEALS))[0]["title"] == "Galaxy S26+ On Us."


def test_render_empty_table_does_not_crash() -> None:
    assert "Found deals: 0" in render_table([])


def test_cli_fixture_table_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--fixture", FIXTURE]) == 0
    out = capsys.readouterr().out
    assert "Found deals: 5" in out
    assert "Galaxy S26+ On Us." in out


def test_cli_fixture_json_to_file(tmp_path: Path) -> None:
    out_file = tmp_path / "deals.json"
    assert main(["--fixture", FIXTURE, "--format", "json", "--output", str(out_file)]) == 0
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert len(data) == 5
    assert data[0]["url"] == "https://www.t-mobile.com/cell-phone/phone-duo"


def test_cli_fixture_csv_to_file(tmp_path: Path) -> None:
    out_file = tmp_path / "deals.csv"
    assert main(["--fixture", FIXTURE, "--format", "csv", "--output", str(out_file)]) == 0
    rows = list(csv.DictReader(out_file.read_text(encoding="utf-8").splitlines()))
    assert len(rows) == 5
    assert rows[4]["category"] == "accessory"


def test_cli_missing_fixture_returns_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--fixture", "tests/fixtures/does-not-exist.html"]) == 1
    assert "tmobile-deals:" in capsys.readouterr().err


def test_parser_and_cli_agree_on_fixture_count() -> None:
    assert len(parse_deals(Path(FIXTURE).read_text(encoding="utf-8"))) == 5
