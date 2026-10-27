from pathlib import Path

from tmobile_deals.models import DealCategory
from tmobile_deals.parser import DEFAULT_URL, parse_deals

FIXTURE = Path(__file__).parent / "fixtures" / "offers_sample.html"


def test_parse_fixture_returns_deals_in_page_order() -> None:
    deals = parse_deals(FIXTURE.read_text(encoding="utf-8"))
    assert [deal.title for deal in deals] == [
        "All-New Phone Duo. Yours for $1000 off.",
        "Galaxy S26+ On Us.",
        "Limited time: $99 Galaxy Watch Ultra2.",
        "Introducing the new moto pad.",
        "Buy 3 or more iPhone accessories and save 25% today.",
    ]


def test_hero_card_keeps_description_and_featured_section() -> None:
    (deal,) = parse_deals(FIXTURE.read_text(encoding="utf-8"))[:1]
    assert deal.description == (
        "Save $1000 when you switch and bring your number. With up to 36 monthly bill credits."
    )
    assert deal.section == "Featured"
    assert deal.category is DealCategory.PHONE


def test_section_cards_have_empty_description_and_section_category() -> None:
    deals = parse_deals(FIXTURE.read_text(encoding="utf-8"))
    phone, accessory = deals[1], deals[4]
    assert phone.description == ""
    assert phone.section == "Phone deals"
    assert phone.category is DealCategory.PHONE
    assert accessory.section == "Accessories deals"
    assert accessory.category is DealCategory.ACCESSORY


def test_tracking_params_stripped_and_relative_urls_resolved() -> None:
    deals = parse_deals(FIXTURE.read_text(encoding="utf-8"))
    assert deals[0].url == "https://www.t-mobile.com/cell-phone/phone-duo"
    assert deals[1].url == "https://www.t-mobile.com/cell-phone/samsung-galaxy-s26-plus"


def test_duplicate_url_deduped_and_explore_tiles_excluded() -> None:
    deals = parse_deals(FIXTURE.read_text(encoding="utf-8"))
    assert len(deals) == 5
    assert all("HOME INTERNET" not in deal.title for deal in deals)
    assert len({deal.url for deal in deals}) == 5


def test_watch_and_tablet_urls_are_service_not_phone() -> None:
    deals = parse_deals(FIXTURE.read_text(encoding="utf-8"))
    watch, tablet = deals[2], deals[3]
    assert watch.category is DealCategory.SERVICE
    assert tablet.category is DealCategory.SERVICE
    assert watch.section == "Smartwatch deals"


def test_cards_without_title_or_link_are_skipped() -> None:
    deals = parse_deals(FIXTURE.read_text(encoding="utf-8"))
    assert all(deal.title for deal in deals)
    assert all(deal.url for deal in deals)
    assert all("ghost" not in deal.url and "No link" not in deal.title for deal in deals)


def test_empty_page_yields_no_deals_instead_of_crashing() -> None:
    assert parse_deals("<html><body><h1>Deals</h1></body></html>") == []


def test_price_fields_stay_unpopulated() -> None:
    deals = parse_deals(FIXTURE.read_text(encoding="utf-8"))
    assert all(deal.price is None for deal in deals)
    assert all(deal.original_price is None for deal in deals)
    assert all(deal.valid_until is None for deal in deals)


def test_default_base_url_is_the_offers_page() -> None:
    assert DEFAULT_URL == "https://www.t-mobile.com/offers"
