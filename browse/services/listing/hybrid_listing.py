import logging
from typing import Optional

from browse.services.listing.fs_listings import FsListingFilesService
from browse.services.listing import YearCount, Listing
from browse.services.database.listings import (
    get_yearly_article_counts,
    get_articles_for_month,
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

        return get_articles_for_month(archiveOrCategory, year, month, skip, show)
