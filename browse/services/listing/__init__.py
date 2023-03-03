"""Serves lists of articles for categories and time periods."""

from abc import ABC, abstractmethod
from typing import cast, Any

from typing import Optional

from .base_listing import NewResponse, ListingResponse, ListingItem, \
    ListingCountResponse


def get_listing_service() -> "ListingService":
    """Get the listing service configured for the app context."""
    from browse.config import settings
    from flask import g
    if 'listing_service' not in g:
        g.listing_service = settings.DOCUMENT_LISTING_SERVICE(settings, g)  # pylint disable:E1102

    return cast(ListingService, g.listing_service)


def fs_listing(settings: Any, _: Any) -> "ListingService":
    """Factory function for filesystem-based listing service."""
    from .fs_listings import FsListingFilesService
    return FsListingFilesService(settings.DOCUMENT_LISTING_PATH)

def db_listing(settings: Any, _: Any) -> "ListingService":
    """Factory function for DB backed listing service."""
    from .db_listing_impl import DBListingService
    from browse.services.database import models
    #maybe pass in the specific classes for the tables we need?
    return DBListingService(models.db)

def fake(settings: Any, _: Any) -> "ListingService":
    """Factory function for fake listing service."""
    from .fake_listings import FakeListingFilesService
    return FakeListingFilesService()


class ListingService(ABC):
    """Abstract Base Class for arXiv document listings."""

    @abstractmethod
    def list_articles_by_year(self,
                              archiveOrCategory: str,
                              year: int,
                              skip: int,
                              show: int,
                              if_modified_since: Optional[str] = None) -> ListingResponse:
        """Get listing items for a whole year.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.
        """

    @abstractmethod
    def list_articles_by_month(self,
                               archiveOrCategory: str,
                               year: int,
                               month: int,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None) -> ListingResponse:
        """Get listings for a month.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.
        """

    @abstractmethod
    def list_new_articles(self,
                          archiveOrCategory: str,
                          skip: int,
                          show: int,
                          if_modified_since: Optional[str] = None) -> NewResponse:
        """Gets listings for the most recent announcement/publish.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.
        """

    @abstractmethod
    def list_pastweek_articles(self,
                               archiveOrCategory: str,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None) -> ListingResponse:
        """Gets listings for the 5 most recent announcement/publish.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.
        """

    @abstractmethod
    def monthly_counts(self,
                       archive: str,
                       year: int) -> ListingCountResponse:
        """Gets monthly listing counts for the year."""
