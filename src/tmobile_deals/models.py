"""Deal data model, carried over from the original ss-t-mo project."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class DealCategory(Enum):
    """Broad category for a deal, derived from its page section or link."""

    PHONE = "phone"
    PLAN = "plan"
    ACCESSORY = "accessory"
    SERVICE = "service"


@dataclass
class Deal:
    """One offer from the deals page.

    ``price``, ``original_price`` and ``valid_until`` stay ``None``: the
    live page carries no structured price or expiry, only prose such as
    "$1000 off" in the title. They are kept so callers that relied on the
    original model keep working, and so a future structured source can
    populate them without changing the shape.
    """

    title: str
    description: str
    category: DealCategory
    url: str
    price: float | None = None
    original_price: float | None = None
    valid_until: datetime | None = None
    section: str = ""

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON/CSV-safe mapping of this deal."""
        return {
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "url": self.url,
            "price": self.price,
            "original_price": self.original_price,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "section": self.section,
        }
