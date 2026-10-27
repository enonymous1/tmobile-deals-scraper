from datetime import datetime, timezone

from tmobile_deals.models import Deal, DealCategory


def test_as_dict_is_json_safe() -> None:
    deal = Deal(
        title="Galaxy S26+ On Us.",
        description="",
        category=DealCategory.PHONE,
        url="https://www.t-mobile.com/cell-phone/samsung-galaxy-s26-plus",
        valid_until=datetime(2026, 12, 31, tzinfo=timezone.utc),
        section="Phone deals",
    )
    assert deal.as_dict() == {
        "title": "Galaxy S26+ On Us.",
        "description": "",
        "category": "phone",
        "url": "https://www.t-mobile.com/cell-phone/samsung-galaxy-s26-plus",
        "price": None,
        "original_price": None,
        "valid_until": "2026-12-31T00:00:00+00:00",
        "section": "Phone deals",
    }


def test_defaults_keep_price_fields_empty() -> None:
    deal = Deal(
        title="T", description="", category=DealCategory.SERVICE, url="https://example.test/"
    )
    assert deal.price is None
    assert deal.original_price is None
    assert deal.valid_until is None
    assert deal.section == ""
