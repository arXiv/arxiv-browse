"""arXiv listing backed by files.

Can be either local file or GCP storage.
"""

import logging
import re
from datetime import date, datetime
from typing import List, Literal, Optional, Tuple, Union
from zoneinfo import ZoneInfo

from google.cloud import storage

from arxiv.taxonomy.definitions import ARCHIVES, CATEGORIES
from arxiv.base.globals import get_application_config
from browse.services.listing import (Listing, YearCount, MonthCount,
                                     ListingItem, ListingNew, ListingService,
                                     MonthTotal, NotModifiedResponse,
                                     gen_expires)
from arxiv.files import FileObj
from arxiv.files.object_store import ObjectStore, GsObjectStore, LocalObjectStore
from werkzeug.exceptions import BadRequest

from .parse_listing_file import ParsingMode, get_updates_from_list_file
from .parse_listing_pastweek import parse_listing_pastweek
from .parse_new_listing_file import parse_new_listing_file

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG

ListingFileType = Literal["new", "pastweek", "month"]
"""These are the listing file types."""


class FsListingFilesService(ListingService):
    """arXiv document listings via Filesystem.

    The source of the files can be either the local file system
    or a GCP storage bucket.
    """

    def __init__(self, document_listing_path: str):
        self.document_listing_path = document_listing_path
        self.obj_store: ObjectStore = LocalObjectStore(document_listing_path)
        self.listing_files_root = "./"
        
        if document_listing_path.startswith("gs://"):
            parts = document_listing_path.replace("gs://","").split("/")
            gs_client = storage.Client()
            bucket = gs_client.bucket(parts[0])
            self.obj_store = GsObjectStore(bucket)
            path = "/".join(parts[1:]) if len(parts)>0 else ""
            if path.endswith("/"):
                path = path[:-1]
            self.listing_files_root = path

    def _generate_listing_path(self, fileMode: ListingFileType, archiveOrCategory: str,
                               year: int, month: int) -> FileObj:
        """Create `Path` to a listing file.

        This just formats the string file name and returns a `Path`. It does
        not check if the file exists."""
        categorySuffix = ''
        archive_id = ''
        if archiveOrCategory in ARCHIVES:
            # Create listing file path with archive as <archive>/new
            archive_id = archiveOrCategory
        elif archiveOrCategory in CATEGORIES:
            # Get archive and create path - <archive>/new.<category>
            res = re.match('([^\\.]*)(?P<suffix>\\.[^\\.]*)$', archiveOrCategory)
            if res:
                suffix = res.group('suffix')
                categorySuffix = suffix
            archive_id = CATEGORIES[archiveOrCategory].in_archive
        else:
            raise BadRequest(f"Archive or category doesn't exist: {archiveOrCategory}")

        listingRoot = f'{self.listing_files_root}/{archive_id}/listings/'
        if fileMode == 'month':
            if len(str(year)) >= 4:
                if year < 2090:
                    yy = str(year)[2:]
                    listingFilePath = f'{listingRoot}{yy}{month:02d}'
                else:
                    listingFilePath = f'{listingRoot}{year}{month:02d}'
            elif len(str(year)) <= 2:
                listingFilePath = f'{listingRoot}{year:02d}{month:02d}'
            else:
                raise BadRequest(f"Bad year value: year: {year} month: {month:02d}")
        else:
            listingFilePath = f'{listingRoot}{fileMode}{categorySuffix}'

        return self.obj_store.to_obj(listingFilePath)


    def _current_y_m_em(self, year:int) -> Tuple[str,int,int]:
        """Gets `(currentYear, currentMonth, end_month)`"""
        # If current year, limit range to available months
        currentYear = str(datetime.now().year)[2:]
        currentMonth = datetime.now().month
        end_month = 12
        if currentYear == str(year):
            end_month = currentMonth
        return (currentYear, currentMonth, end_month)

    def _modified_since(self, if_modified_since: str, listingFile: FileObj) -> bool:
        """Returns whether data has been modified since `if_modified_since`."""
        if not listingFile.exists():
            return False
        parsed = datetime.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT')
        modTime = listingFile.updated
        return modTime > parsed

    def _list_articles_by_period(self,
                                 archiveOrCategory: str,
                                 yymmfiles: List[Tuple[int,int, FileObj]],
                                 skip: int,
                                 show: int,
                                 if_modified_since: Optional[str] = None,
                                 mode: ParsingMode = 'month')\
                                 -> Union[Listing, MonthTotal, NotModifiedResponse]:
        """Gets listing for a list of `months`.

        This gets the listings for all the months in `months`. It works fine for
        getting just one month. Creating an archive listing for the year involves
        combining the listing files for all available months for the specified
        year.

        A category listing requires filtering these monthly listing files by the
        category.

        `if_modified_since` is the if_modified_since header value passed by the
        web client It should be in RFC 1123 format. This will return
        NotModifiedResponse if `if_modified_since` is not empty and any of the
        files related to `months` have been modified since then.

        Existing production year list links use two digit year.

        Parameters
        ----------
        archiveOrCategory : str
            A valid arxiv archive or category to get the listing for. Must not
            be empty.
        months : List[Tuple[int,int,FileObj]]
            The months to get the listings for. Tuple of (yy, mm, FileObj_to_listing_file)
            where both yy and mm are `int`. If yy or mm are 0 the
            result may lack pubdates.
        # tuple of (yy,mm) skip : int
        show : int
            The quantity of listings that need to be shown.
        if_modified_since : Optional[str]
            RFC 1123 format date of an if_modified_since header.
        mode: ParsingMode        
            Which type if listing is requested. One of ['new', 'month',
            'monthly_counts', 'year', 'pastweek']'month' works with a yymmfiles
            list greater than length 1. 'new' works only with a list of length 1.

        Returns
        -------
        Listing
            Combined listing response for all `months`

        Raises
        ------
        Exception
            If any listing file is missing. The only acceptable mising listing
            file is the one for the current year and month. That might not
            have been created yet if there has not yet been an announcement.

        """
        if mode == 'new' and len(yymmfiles) > 1:
            raise ValueError("When listing type  is 'new' yymmfiles must be size 1")

        currentYear, currentMonth, end_month = self._current_y_m_em(
            max([yy for yy,_,_ in yymmfiles]))
        
        if if_modified_since: # Check if-modified-since for months of interest
            if all([not self._modified_since(if_modified_since, lf)
                    for _,_, lf in yymmfiles]):
                return NotModifiedResponse(True, gen_expires())

        # Collect updates for each month
        all_listings: List[ListingItem] = []
        all_pubdates: List[Tuple[date,int]] = []
        for year, month, listingFile in yymmfiles:
            if not listingFile.exists() and currentYear != str(year)\
               and currentMonth != str(month):
                # This is fine if new month and no announce has happened yet.
                raise Exception(f"Missing monthly listing file {listingFile}")

            response = get_updates_from_list_file(year, month, listingFile,
                                                  mode, archiveOrCategory)
            if not isinstance(response, Listing):
                return response
            
            all_listings.extend(response.listings)            
            if response.pubdates:
                all_pubdates.extend(response.pubdates)
            # else:
            #     pub_date = date(year, month, 1).strftime('%a, %d %b %Y')
            #     all_pubdates.append((pub_date, len(response.listings)))

        return Listing(listings=all_listings[skip:skip + show], # Adjust for skip/show
                       pubdates=all_pubdates,
                       count=len(all_listings),
                       expires= gen_expires())


    
    def list_articles_by_year(self,
                              archiveOrCategory: str,
                              year: int,
                              skip: int,
                              show: int,
                              if_modified_since: Optional[str] = None) -> Listing:
        """Get listing items for a whole year.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.

        Creating a archive listing for the year involves combining
        the listing files for all available months for the specified
        year. A category listing requires filtering these monthly
        listing files by the category.

        Existing production year list links use two digit year.
        """
        _, _, end_month = self._current_y_m_em(year)
        months = [(year, month) for month in range(1, end_month + 1)]
        possible = (
            (year, month, self._generate_listing_path('month', archiveOrCategory,
                                                      year, month))
            for year, month in months)
        yymmfiles = [(year, month, fobj) for (year, month, fobj) in possible
                     if fobj.exists()]
        return self._list_articles_by_period(archiveOrCategory, yymmfiles, skip,
                                             show, if_modified_since) # type: ignore


    def list_articles_by_month(self,
                               archiveOrCategory: str,
                               year: int,
                               month: int,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None) -> Listing:
        """Get listings for a month.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.

        The monthly listing for an archive maps to a single file. The monthly
        listing for categories is more work since all updates are
        included in the same montly listing file.
        """
        yymmfiles= [(year,month, self._generate_listing_path('month', archiveOrCategory,
                                                             year, month))]
        return self._list_articles_by_period(archiveOrCategory, yymmfiles, skip,
                                             show, if_modified_since) # type: ignore


    def list_new_articles(self,
                          archiveOrCategory: str,
                          skip: int,
                          show: int,
                          if_modified_since: Optional[str] = None)\
                          -> Union[ListingNew, NotModifiedResponse]:
        """Gets listings for the most recent announcement/publish.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.

        The 'new' listing maps to a single file. The filename depends on whether
        the archiveOrCategory value is an archive or category listing.
        """
        file= self._generate_listing_path('new', archiveOrCategory, 0, 0)
        if if_modified_since and self._modified_since(if_modified_since, file):
            return NotModifiedResponse(True, gen_expires())
        else:
            rv =  parse_new_listing_file(file)
            rv.listings = rv.listings[skip:skip + show] # Adjust for skip/show
            return rv

    def list_pastweek_articles(self,
                               archiveOrCategory: str,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None)\
                               -> Union[Listing, NotModifiedResponse]:
        """Gets listings for the 5 most recent announcement/publish.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.

        The 'pastweek' listing maps to a single file. The filename depends on whether
        the archiveOrCategory value is an archive or category listing.
        """
        file = self._generate_listing_path('pastweek', archiveOrCategory, 0, 0)
        if if_modified_since and self._modified_since(if_modified_since, file):
            return NotModifiedResponse(True, gen_expires())
        else:
            rv = parse_listing_pastweek(file)
            rv.listings = rv.listings[skip:skip + show] # Adjust for skip/show
            return rv

    def monthly_counts(self, archive: str, year: int) -> YearCount:
        """Gets monthly listing counts for the year."""
        monthly_counts: List[MonthTotal] = []
        new_cnt, cross_cnt = 0, 0
        currentYear, currentMonth, end_month = self._current_y_m_em(year)

        files = []
        for month in range(1, end_month + 1):
            file = self._generate_listing_path('month', archive, year, month)
            files.append((month, file, file.exists()))
        month_totals=[]
        for month, file, exists in files:
            if not exists:
                continue
            response = get_updates_from_list_file(year, month, file, 'monthly_counts'
                                                  # archive TODO Does this need archive?
                                                  )
            if isinstance(response, MonthTotal):
                monthly_counts.append(response)
                new_cnt += response.new
                cross_cnt += response.cross
                month_totals.append(MonthCount(year,month,response.new,response.cross))

        year_resp=YearCount(year, new_cnt, cross_cnt,month_totals)

        return year_resp



    def service_status(self)->List[str]:
        try:
            stat, msg = self.obj_store.status()
            if stat != "GOOD":
                return [f"{__name__} Supporting ObjectStore not good: {msg}"]
            if not any(self.obj_store.list(self.listing_files_root)):
                return [f"{__name__} No files under '{self.document_listing_path}' or not exist"]
            else:
                return []
        except Exception as ex:
            return [f"{__name__} Could not access '{self.document_listing_path}' due to {ex}"]
