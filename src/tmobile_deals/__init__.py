"""T-Mobile deals scraper: fetch and parse offers from t-mobile.com/offers."""

from tmobile_deals.models import Deal, DealCategory

__version__ = "2.0.0"

__all__ = ["Deal", "DealCategory", "__version__"]
