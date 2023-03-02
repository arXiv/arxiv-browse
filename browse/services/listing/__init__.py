"""Serves lists of articles for categories and time periods."""

from typing import cast, Any
from browse.services.listing.base_listing import ListingService


def get_listing_service() -> ListingService:
    """Get the listing service configured for the app context."""
    from browse.config import settings
    from flask import g
    if 'listing_service' not in g:
        g.listing_service = settings.DOCUMENT_LISTING_SERVICE(settings, g)  # pylint disable:E1102

    return cast(ListingService, g.listing_service)


def fs_listing(settings: Any, _: Any) -> ListingService:
    """Factory function for filesystem-based listing service."""
    from .fs_listings import FsListingFilesService
    return FsListingFilesService(settings.DOCUMENT_LISTING_PATH)

def db_listing(settings: Any, _: Any) -> ListingService:
    """Factory function for DB backed listing service."""
    from .db_listing_impl import DBListingService
    from browse.services.database import models
    #maybe pass in the specific classes for the tables we need?
    return DBListingService(models.db)

def fake(settings: Any, _: Any) -> ListingService:
    """Factory function for fake listing service."""
    from .fake_listings import FakeListingFilesService
    return FakeListingFilesService()
