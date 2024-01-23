import logging
from typing import Optional
import time

from browse.services.listing.fs_listings import FsListingFilesService
from browse.services.listing import YearCount, Listing, ListingNew
from browse.services.database.listings import (
    get_yearly_article_counts,
    get_articles_for_month,
    get_new_listing
)

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG


class HybridListingService(FsListingFilesService):
    def monthly_counts(self, archive: str, year: int) -> YearCount:
        return get_yearly_article_counts(archive, year)

    def list_articles_by_year(self,
                              archiveOrCategory: str,
                              year: int,
                              skip: int,
                              show: int,
                              if_modified_since: Optional[str] = None) -> Listing:
        """Get listings for a month. if_modified_since is ignored"""

        if year<91: #in 2000s
            year+=2000
        elif year<1900: #90s articles
            year+=1900
        
        return get_articles_for_month(archive_or_cat=archiveOrCategory, year=year, month=None, skip=skip, show=show)

    def list_articles_by_month(
        self,
        archiveOrCategory: str,
        year: int,
        month: int,
        skip: int,
        show: int,
        if_modified_since: Optional[str] = None,
    ) -> Listing:
        """Get listings for a month.

        if_modified_since is ignored
        """
        if year<91: #in 2000s
            year+=2000
        elif year<1900: #90s articles
            year+=1900

        return get_articles_for_month(archiveOrCategory, year, month, skip, show)

    def list_new_articles(self,
                          archiveOrCategory: str,
                          skip: int,
                          show: int,
                          if_modified_since: Optional[str] = None)\
                          -> ListingNew:
        items=get_new_listing(archiveOrCategory,skip,show)
        return items