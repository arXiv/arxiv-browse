import logging
from typing import Optional, List, Union
from datetime import datetime

from browse.services.listing import YearCount, Listing, ListingNew, ListingItem, NotModifiedResponse, gen_expires, ListingService
from browse.services.database.listings import (
    get_yearly_article_counts,
    get_articles_for_month,
    get_recent_listing,
    get_new_listing,
    check_service
)
from browse.services.documents.config.deleted_papers import DELETED_PAPERS, intentionally_blank


logger = logging.getLogger(__name__)
logger.level = logging.DEBUG


class DBListingService(ListingService):

    def monthly_counts(self, archive: str, year: int) -> YearCount:
        return get_yearly_article_counts(archive, year)

    def list_articles_by_year(self,
                              archiveOrCategory: str,
                              year: int,
                              skip: int,
                              show: int,
                              if_modified_since: Optional[str] = None
                              ) -> Union[Listing, NotModifiedResponse]:
        """Get listings for a month. if_modified_since is ignored"""

        if year<91: #in 2000s
            year+=2000
        elif year<1900: #90s articles
            year+=1900

        items=get_articles_for_month(archive_or_cat=archiveOrCategory, year=year, month=None, skip=skip, show=show)
        items.listings = _without_deleted(items.listings)
        if _check_modified(items.listings,if_modified_since):
            return NotModifiedResponse(True,gen_expires())
        return items

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

        if_modified_since is ignored
        """
        if year<91: #in 2000s
            year+=2000
        elif year<1900: #90s articles
            year+=1900

        items=get_articles_for_month(archiveOrCategory, year, month, skip, show)
        items.listings = _without_deleted(items.listings)
        if _check_modified(items.listings,if_modified_since):
            return NotModifiedResponse(True,gen_expires())
        return items

    def list_pastweek_articles(self,
                               archiveOrCategory: str,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None)\
                               -> Union[Listing, NotModifiedResponse]:
        """Gets listings for the 5 most recent announcement/publish.
        """
        items=get_recent_listing(archiveOrCategory,skip,show)
        items.listings = _without_deleted(items.listings)
        if _check_modified(items.listings,if_modified_since):
            return NotModifiedResponse(True,gen_expires())
        return items

    def list_new_articles(self,
                          archiveOrCategory: str,
                          skip: int,
                          show: int,
                          if_modified_since: Optional[str] = None)\
                          -> Union[ListingNew, NotModifiedResponse]:
        items=get_new_listing(archiveOrCategory,skip,show)
        items.listings = _without_deleted(items.listings)
        if _check_modified(items.listings,if_modified_since):
            return NotModifiedResponse(True,gen_expires())
        return items
    
    def service_status(self)->List[str]:
        try:
            result=check_service()
            if result != "GOOD":
                return [f"{__name__} Could not retrieve data from database"]
            else:
                return []
        except Exception as ex:
            return [f"{__name__} Could not access database due to {ex}"]
    
def _check_modified(items: List[ListingItem], if_modified_since: Optional[str] = None)->bool:
    if if_modified_since:
        parsed = datetime.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT')
        for item in items:
            if item.article and item.article.modified >=parsed:
                return True
    return False


def _without_deleted(listings: List[ListingItem] ) -> List[ListingItem]:
    """Removes `intentionally_blank` deleted items from the listing items."""
    return [item for item in listings
            if item.id not in DELETED_PAPERS or
            DELETED_PAPERS[item.id] != intentionally_blank]
