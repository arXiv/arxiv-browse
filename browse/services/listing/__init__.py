"""Serves lists of articles for categories and time periods."""

from typing import cast, Any
from browse.services.listing.base_listing import ListingService
from browse.config import Settings


def get_listing_service() -> ListingService:
    """Get the listing service configured for the app context."""
    from browse.config import settings
    from flask import g
    if 'listing_service' not in g:
        g.listing_service = settings.DOCUMENT_LISTING_SERVICE(settings, g)  # pylint disable:E1102

    return cast(ListingService, g.listing_service)


def fake(settings: Settings, _: Any) -> ListingService:
    """Integration for fake listing service."""
    from .fake_listings import FakeListingFilesService
    return FakeListingFilesService()
