"""Serves lists of articles for categories and time periods."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from time import mktime
from typing import Any, List, Literal, Optional, Protocol, Tuple, Union, cast
from wsgiref.handlers import format_date_time

from browse.domain.identifier import Identifier
from browse.domain.metadata import Archive, DocMetadata


def get_listing_service() -> "ListingService":
    """Get the listing service configured for the app context."""
    from browse.config import settings
    from flask import g

    if "listing_service" not in g:
        g.listing_service = settings.DOCUMENT_LISTING_SERVICE(
            settings, g
        )  # pylint disable:E1102

    return cast(ListingService, g.listing_service)


def fs_listing(settings: Any, _: Any) -> "ListingService":
    """Factory function for filesystem-based listing service."""
    from .fs_listings import FsListingFilesService

    return FsListingFilesService(settings.DOCUMENT_LISTING_PATH)


def db_listing(settings: Any, _: Any) -> "ListingService":
    """Factory function for DB backed listing service."""
    from browse.services.database import models

    from .db_listing_impl import DBListingService

    # maybe pass in the specific classes for the tables we need?
    return DBListingService(models.db)


def fake(settings: Any, _: Any) -> "ListingService":
    """Factory function for fake listing service."""
    from .fake_listings import FakeListingFilesService

    return FakeListingFilesService()


AnnounceTypes = Literal["new", "cross", "rep"]
"""The types that announces can be in the listings."""


class ListingArticle(Protocol):
    arxiv_identifier: Identifier
    title: str
    abstract: str
    comments: str
    journal_ref: str
    arxiv_id: str
    arxiv_id_v: str
    primary_archive: Archive



class ListingItem:
    """A single item for a listing.

    The id is the arXiv ID and may be an idv.

    The listing type is one of 'new,'rep','cross','wdr','jref'. These
    would be extended with any new types of actions/events that can happen
    in the arXiv system.

    primary is the primary category of the article.
    """

    def __init__(self, id: str,
                 listingType: AnnounceTypes,
                 primary: str,
                 article: Optional[DocMetadata] = None):
        self.id = id
        self.listingType = listingType
        self.primary = primary
        self.article = article

    def __repr__(self) -> str:
        return f"<ListingItem {self.id} {self.listingType}>"


@dataclass
class Listing:
    """A list of items in time period.

    listings is the list of items for the time period.

    pubdates are the dates of publications. The int is the number of items
    published on the associated date.

    count is the count of all the items in the listing for the query.

    expires is the time at which this data may no longer be cached. It
    should be the sort of datetime that could go in an HTTP Expires response
    header. It must be in rfc-1123 format ex. Wed, 22 Oct 2008 10:55:46 GMT
    The timezone for this expires should be when the cache expires and does not need
    to be the timezone of the listing service, listing client or web client.

    Why not just do listing: List[Tuple[date,List[ListingItem]}} ?
    Because pastweek needs to support counts for the days and needs to be
    able to support skip/show.
    """

    listings: List[ListingItem]
    pubdates: List[Tuple[date, int]]
    count: int
    expires: str


@dataclass
class ListingNew:
    """
    A listing from the list_new_articles method.

    listings is the list of items for the most recent publish cycle.

    announced is the date of the most recent publish cycle.

    new_count is the count of new the items in the listing for the query.
    rep_count is the count of rep the items in the listing for the query.
    cross_count is the count of cross the items in the listing for the query.

    submitted is the start date of when these items were submitted and the end date.

    expires is the time at which this data may no longer be cached. It
    should be the sort of datetime that could go in an HTTP Expires response
    header. It must be in rfc-1123 format ex. Wed, 22 Oct 2008 10:55:46 GMT
    The timezone for this expires should be when the cache expires and does not need
    to be the timezone of the listing service, listing client or web client."""

    listings: List[ListingItem]
    new_count: int
    cross_count: int
    rep_count: int
    announced: date
    submitted: Tuple[date, date]
    expires: str


@dataclass
class ListingPastweek:
    """
    A listing for the pastweek of articles.

    """
    listings: List[ListingItem]
    pubdates: List[Tuple[str, int]]
    count: int
    expires: str


@dataclass
class NotModifiedResponse:
    """
    Listing response that indicates that the listing has not been modified since
    the date in the if-modified-since parameter.

    expires must be in rfc-1123 format ex. Wed, 22 Oct 2008 10:55:46 GMT
    The timezone for this expires should be when the cache expires and does not need
    to be the timezone of the listing service, listing client or web client.

    """

    not_modified: bool
    expires: str


@dataclass
class MonthCount:
    """A single month's count for an archive.

    year is the year the listing is for.

    month is the month the listing is for.

    new is the count of new listings for that month.

    cross is the count of crosses for that month.

    rep is the count of replaced for that month.

    """

    year: int
    month: int
    new: int
    cross: int
    expires: str
    listings: List[ListingItem]


@dataclass
class ListingCountResponse:
    """Response with the counts for an archive for a given year.

    month_counts are counts for individual months.

    new_count is the count of new articles for the year.

    cross_count is the count of cross articles for the year.

    rep_count is the count of replaced articles for the year.
    """

    month_counts: List[MonthCount]
    new_count: int
    cross_count: int


class ListingService(ABC):
    """Abstract Base Class for arXiv document listings."""

    @abstractmethod
    def list_articles_by_year(
        self,
        archiveOrCategory: str,
        year: int,
        skip: int,
        show: int,
        if_modified_since: Optional[str] = None,
    ) -> Union[Listing, NotModifiedResponse]:
        """Get listing items for a whole year.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.
        """

    @abstractmethod
    def list_articles_by_month(
        self,
        archiveOrCategory: str,
        year: int,
        month: int,
        skip: int,
        show: int,
        if_modified_since: Optional[str] = None,
    ) -> Union[Listing, NotModifiedResponse]:
        """Get listings for a month.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.
        """

    @abstractmethod
    def list_new_articles(
        self,
        archiveOrCategory: str,
        skip: int,
        show: int,
        if_modified_since: Optional[str] = None,
    ) -> Union[ListingNew, NotModifiedResponse]:
        """Gets listings for the most recent announcement/publish.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.
        """

    @abstractmethod
    def list_pastweek_articles(
        self,
        archiveOrCategory: str,
        skip: int,
        show: int,
        if_modified_since: Optional[str] = None,
    ) -> ListingPastweek:
        """Gets listings for the 5 most recent announcement/publish.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.
        """

    @abstractmethod
    def monthly_counts(self, archive: str, year: int) -> ListingCountResponse:
        """Gets monthly listing counts for the year."""




def gen_expires() -> str:
    """Generate expires in RFC 1123 format.

       What is optimal value for the expires value? Next publish?
       RFC 1123 format ex 'Wed, 21 Oct 2015 07:28:00 GMT'
    """
    now = datetime.now()
    future = timedelta(days=1)
    expire = now + future
    stamp = mktime(expire.timetuple())
    expires = format_date_time(stamp)
    return expires
