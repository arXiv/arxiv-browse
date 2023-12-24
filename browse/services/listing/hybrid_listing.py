import logging

from browse.services.listing.fs_listings import FsListingFilesService
from browse.services.listing import YearCount
from browse.services.database.listings import get_yearly_article_counts

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG

class HybridListingService(FsListingFilesService):

    def monthly_counts(self, archive: str, year: int) -> YearCount:
        return get_yearly_article_counts(archive,year)
