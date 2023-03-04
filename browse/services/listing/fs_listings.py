"""arXiv listing backed by files.

Due to use of CloudPathLib these can be either local files or cloud object
stores.

"""

import codecs
import logging
import re
from datetime import date, datetime, timedelta
from time import mktime
from typing import Dict, List, Optional, Tuple, Union, Literal
from wsgiref.handlers import format_date_time
from zoneinfo import ZoneInfo

from arxiv import taxonomy
from arxiv.base.globals import get_application_config
from browse.services import APath
from browse.services.listing import (Listing, ListingCountResponse,
                                     ListingService,
                                     MonthCount, ListingNew, ListingItem, NotModifiedResponse)
from cloudpathlib.anypath import to_anypath
from werkzeug.exceptions import BadRequest

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG

app_config = get_application_config()

debug_parser = False

FS_TZ = ZoneInfo(app_config["ARXIV_BUSINESS_TZ"])
"""Time used on the FS with the listing files."""

DATE     = re.compile(r'^Date:\s+')
SUBJECT  = re.compile(r'^Subject:\s+')
RECEIVED = re.compile(r'^\s*received from\s+(?P<date_range>.*)')

RULES_NORMAL     = re.compile(r'^------------')
RULES_CROSSES    = re.compile(r'^%-%-%-%-%-%-')
RULES_REPLACESES = re.compile(r'^%%--%%--%%--')
RULES_END        = re.compile(r'^%%%---%%%---')

PAPER_FORM = re.compile(r'^(Paper)(\s*\(\*cross-listing\*\))?:\s?(\S+)')
ARXIV_FORM = re.compile(r'^arXiv:(\S+)(\s*\(\*cross-listing\*\))?')
REPLACED_FORM = re.compile(r'^(replaced with revised version)|^((figures|part) added)', re.IGNORECASE)
PASTWEEK_DATE = re.compile(r'/\*\s+(.*)\s+\*/')
PRIMARY_CATEGORY = re.compile(r'^Categories:\s+(\S+)')
SECONDARY_CATEGORIES = re.compile(r'\s+([^\s]+)\s*(.*)$')

class FsListingFilesService(ListingService):
    """arXiv document listings via Filesystem."""

    def __init__(self, document_listing_path: str):
        self.listing_files_root = document_listing_path

    def _is_rule(self, line: str, type: str) -> Tuple[int, Literal['','cross','rep','end']]:
        """Scan listing file for special rules markup.

        Returns whether line is a rule and the item type, [is_rule, type]

        Change types to follow
        Comments copied from original Perl module.

            True if the input value is a 'rule', false otherwise.

            $$typeref is set to the rule type if not a plain old
             rule. Rule types are either a plain old rule
               -----------------
             or a special 'rule' denoting change of type for updates
               %-%-%-%-%-%-  => start of crosses
               %%--%%--%%--  => start of replaces and then replaced crosses
               %%%---%%%---  => end
        """
        if RULES_NORMAL.match(line):
            return (1, '')
        elif RULES_CROSSES.match(line):
            return (1, 'cross')
        elif RULES_REPLACESES.match(line):
            return (1, 'rep')
        elif RULES_END.match(line):
            return (1, 'end')

        return (0, '')

    def _get_updates_from_list_file(self, listingFilePath: APath,
                                    listingType: str, listingFilter: str='')-> Union[Listing, ListingNew, Dict]:
        """Read the paperids that have been updated from a listings file.

        There are three forms of listing file: new, pastweek, and monthly.
        The new listing contains the updates for the latest publish, pastweek
        contains updates for the last five publish days, and month contains
        the accumulated updates for the entire month (to date).

        The new, pastweek, and current month listings are dynamic and
        are updated after each publish. The monthly listing file is the only
        permanent record of older announcements. The current month's listing
        will be updated during the month it is active.

        An archive with sub categories will have a combined new and pastweek
        listing for the time period in addition to a new/pastweek listing
        file each category. new, new.CL, new.DF, etc.

        Listing file markup is used to identify new and cross submissions.

        Comments from original code:

          Ideas is that the code will be able to handle old format and then
          work with just a list of paperids later.

          Does not read the metadata from the listings file.
        """

        # pastweek and
        #
        #    Skip forward to first publish date
        #
        # month
        #
        #    Skip forward to first \\
        #
        # Process entries.
        #     Identify type change -> replacements
        #
        #    - Read articleid
        #    - Identify type: new, cross
        #
        format = ''
        if listingType == 'monthly_counts':
            format = 'monthly_counts'
            listingType = 'month'

        extras = {}

        new_items:List[ListingItem] = []
        cross_items:List[ListingItem] = []
        rep_items:List[ListingItem] = []

        # new
        announce_date: Optional[date] = None
        submit_start_date: Optional[date] = None
        submit_end_date: Optional[date] = None

        # pastweek
        pub_dates:List[date] = []
        pub_counts:List[int] = []
        pub_count_previous = 0

        with listingFilePath.open('rb') as fh:
            data = fh.read()

        lines = codecs.decode(data, encoding='utf-8',errors='ignore').split("\n")

        if listingType == 'new':
            # Process selected information from header
            #   Expect these lines:
            #       Date: (date)
            #       Subject: (subject)
            #       ...
            #       received from

            # First line is always the date.
            # Date: Tue, 20 Jul 21 00:51:12 GMT
            dateline = lines.pop(0)
            dateline = dateline.replace('\n', '')

            if DATE.match(dateline):
                date = re.sub(r'^Date:\s+', '', dateline)
                short_date = re.sub(r'\s+\d\d:\d\d:\d\d\s+\w\w\w', '', date)
                extras['Date'] = date
                extras['short_date'] = short_date
                announce_date = datetime.strptime(short_date, '%a, %d %b %y')

            # Subject: cs daily 346 new + 55 crosses received
            line = lines.pop(0)
            if SUBJECT.match(line):
                subject = line
                extras['Subject'] = subject

            # received from  Fri 16 Jul 21 18:00:00 GMT  to  Mon 19 Jul 21 18:00:00 GMT
            # Skip forward to first \\
            line = lines.pop(0)
            while (not re.match(r'^\\', line)):
                received = RECEIVED.match(line)
                if received:
                    date_from_to = str(received.group('date_range'))
                    date_short_from_to = re.sub(r'\s+\d\d:\d\d:\d\d\s+\w\w\w', '', date_from_to)
                    extras['date_from_to'] = date_from_to
                    extras['date_short_from_to'] = date_short_from_to
                    res = re.match(r'(.*)\s+to\s+(.*)$', date_short_from_to)
                    if res:
                        submit_start_date = datetime.strptime(res.group(1), '%a %d %b %y ')
                        submit_end_date = datetime.strptime(res.group(2), '%a %d %b %y')

                line = lines.pop(0)

        elif listingType == 'pastweek' or listingType == 'month':
            # Skip forward to first \\,
            #   which brings us to first publish date for pastweek
            # \\
            # /*Tue, 20 Jul 2021 */
            #\\
            #   or first update entry for monthly listing
            line = lines.pop(0)
            while (line and not re.match(r'^\\', line)):
                line = lines.pop(0)
                line = line.replace('\n', '')
        else:
            pass

        # Now cycle through and process update entries in file
        type = 'new'

        lasttype = ''
        line = lines.pop(0)
        line = line.replace('\n', '')
        while (line):
            # check for special markup
            (is_rule, type_change) = self._is_rule(line, type)
            while (is_rule):
                if is_rule and type_change:
                    type = type_change
                if len(lines):
                    line = lines.pop(0)
                else:
                    break
                (is_rule, type_change) = self._is_rule(line, type)
                if type == 'end':
                    break

            # Read up to the next \\
            while (len(lines) and re.match(r'^\\', line)):
                if len(lines):
                    line = lines.pop(0)

            # Now process all fields up to the next \\
            id = None
            nb = None
            primary_category = None
            secondary_categories = None
            is_preamble = 1
            is_cross = 0

            while (len(lines) and not re.match(r'^\\', line)):

                # Read article identifier and determine whether a cross
                #   Paper: quant-ph/9901070
                #   Paper (*cross-listing*): quant-ph/9901070
                #   arXiv:quant-ph/9901070 (*cross-listing*)
                #
                paper = PAPER_FORM.match(line)
                arxiv = ARXIV_FORM.match(line)

                # Replaced
                replaced = REPLACED_FORM.match(line)
                # Pastweek handling
                pastweek = PASTWEEK_DATE.match(line)
                # Category (primary/secondary)
                primary_match = PRIMARY_CATEGORY.match(line)

                if arxiv or paper:
                    if paper:
                        is_cross = bool(paper.group(2))
                        id = paper.group(3)
                    elif arxiv:
                        is_cross = bool(arxiv.group(2))
                        id = arxiv.group(1)

                    # Notes from original module:
                    # For month listings, there is no rule for start or crosses
                    # so we infer from Paper line. For pastweek we infer
                    # both new and cross from Paper line as the file switches
                    # back and forth.
                    if listingType == 'pastweek':
                        if is_cross:
                            type = 'cross'
                        else:
                            type = 'new'
                    elif listingType != 'new' and is_cross:
                        type = 'cross'

                elif replaced:
                    nb = line

                elif listingType == 'pastweek' and pastweek:
                    pub_date = pastweek.group(1)
                    pub_date = datetime.strptime(pub_date, '%a, %d %b %Y')
                    # Put together current updates and crosses
                    count = len(cross_items)
                    # Merge and clear crosses
                    new_items = new_items + cross_items

                    if pub_dates:
                        # We already have processed a pub date
                        # store update count for pub date we are
                        # finishing
                        pub_count = len(new_items) - pub_count_previous
                        pub_counts.append(pub_count)
                        pub_count_previous = len(new_items)
                        pub_dates.append(pub_date)
                    else:
                        pub_dates.append(pub_date)

                    cross_items = []
                    # anchors

                elif primary_match:
                    primary_category = primary_match.group(1)
                    secondaries = SECONDARY_CATEGORIES.search(line)
                    if secondaries:
                        secondary_categories = secondaries.group(2)

                    if debug_parser:
                        print(f"Categories: Primary: {primary_category}  Secondaries: {secondary_categories}")

                if len(lines):
                    line = lines.pop(0)
                    line = line.replace('\n', '')
                else:
                    break
                # End inner while

            # Outer while

            # If we have id, register the update
            #   apply filtering (if we are dealing with monthly listing)
            if id:
                filter = f'^{listingFilter}'
                if not listingFilter or (re.match(filter, primary_category)
                                         and type == 'new' ):
                    # push update
                    lasttype = type
                    item = ListingItem(id=id, listingType=type, primary=primary_category)
                    if type == 'new':
                        new_items.append(item)
                    elif type == 'cross':
                        cross_items.append(item)
                    elif type =='rep':
                        rep_items.append(item)

                elif listingFilter and re.search(listingFilter, secondary_categories):
                    item = ListingItem(id=id, listingType=type, primary=primary_category)
                    cross_items.append(item)

            # From original parser
            #  Now complete the reading of this entry by reading everything up to the
            #  next rule. If this is a 'new' listing then we will read past the
            #  abstract and discard.
            (rule, new_type) = self._is_rule(line, type)
            if new_type:
                type = new_type
            while len(lines) and not rule:
                line = lines.pop(0)
                line = line.replace('\n', '')
                (rule, new_type) = self._is_rule(line, type)
                if new_type:
                    type = new_type

            # Read the next line for while loop
            if len(lines):
                line = lines.pop(0)
                line = line.replace('\n', '')
            else:
                break

        # Combine the new and cross updates for pastweek
        #   if there are crosses, add them to updates.
        if listingType == 'pastweek':
            if len(cross_items):
                new_items = new_items + cross_items

            # Complete the last count for pastweek
            pub_count = len(new_items) - pub_count_previous
            pub_counts.append(pub_count)

        count = len(new_items)

        pub_dates_with_count:List[Tuple[date,int]] = []
        index = 0
        for date in pub_dates:
            pub_dates_with_count.append((date, pub_counts[index]))
            index = index + 1

        for pd in pub_dates_with_count:
            (date, count) = pd

        if format == 'monthly_counts':
            # We need the new and cross counts for the monthly count summary
            return MonthCount(pubdates=pub_dates_with_count,
                    new=len(new_items),
                    cross=len(cross_items),
                    expires=self._gen_expires(),
                    listings=new_items + cross_items + rep_items, # debugging
                    )
        elif listingType == 'new':
            return ListingNew(listings= new_items + cross_items + rep_items,
                              announced= announce_date,
                              submitted= (submit_start_date, submit_end_date),
                              new_count= len(new_items),
                              cross_count= len(cross_items),
                              rep_count= len(rep_items),
                              expires= self._gen_expires())
        elif listingType == 'pastweek' or listingType == 'month' \
                or listingType == 'year':
            #{'listings': List[ListingItem],
            # 'pubdates': List[Tuple[date, int]],
            # 'count': int,
            # 'expires': str}

            # There are no pubdates for month, so we will create one and add count
            # to be consistent with API
            if listingType == 'month':
                date = re.search(r'(?P<date>\d{4})$', str(listingFilePath))
                if date:
                    yymm_string = date.group('date')
                    pub_date = datetime.strptime(yymm_string, '%y%m')
                    pub_dates_with_count.append((pub_date, len(new_items + cross_items)))

            return Listing(listings=new_items + cross_items,
                           pubdates=pub_dates_with_count,
                           count=len(new_items + cross_items),
                           expires=self._gen_expires())


    def _generate_listing_path(self, listingType: str, archiveOrCategory: str,
                               year: int, month: int) -> APath:
        """Create `Path` to a listing file.

        This just formats the string file name and returns a `Path`. It does
        not check if the file exists."""
        categorySuffix = ''
        archive = ''

        if archiveOrCategory in taxonomy.ARCHIVES:
            # Create listing file path with archive as <archive>/new
            archive = archiveOrCategory
        elif archiveOrCategory in taxonomy.CATEGORIES:
            # Get archive and create path - <archive>/new.<category>
            res = re.match('([^\\.]*)(?P<suffix>\\.[^\\.]*)$', archiveOrCategory)
            if res:
                suffix = res.group('suffix')
                categorySuffix = suffix
            archive = taxonomy.CATEGORIES[archiveOrCategory]['in_archive']
        else:
            raise BadRequest(f"Archive or category doesn't exist: {archiveOrCategory}")

        listingRoot = f'{self.listing_files_root}/{archive}/listings/'
        if listingType == 'month':
            yymm = "%02d%02d" % (year, month)
            listingFilePath = f'{listingRoot}{yymm}'
        else:
            listingFilePath = f'{listingRoot}{listingType}{categorySuffix}'

        return to_anypath(listingFilePath)


    def _get_mtime(self, listingFilePath: APath) -> datetime:
        """Get the modify time fot specified file."""
        return datetime.fromtimestamp(listingFilePath.stat().st_mtime, tz=FS_TZ)


    def _gen_expires(self) -> str:
        """Generate expires.

           What is optimal value for the expires value? Next publish?

            # RFC 1123 format
            # 'Wed, 21 Oct 2015 07:28:00 GMT'
        """
        now = datetime.now()
        future = timedelta(days=1)
        expire = now + future
        stamp = mktime(expire.timetuple())
        expires = format_date_time(stamp)
        return expires

    def _current_y_m_em(self, year) -> Tuple[int,int,int]:
        """Gets `(currentYear, currentMonth, end_month)`"""
        # If current year, limit range to available months
        currentYear = str(datetime.now().year)[2:]
        currentMonth = datetime.now().month
        end_month = 12
        if currentYear == str(year):
            end_month = currentMonth
        return (currentYear, currentMonth, end_month)
    
    def _modified_since(self, if_modified_since: str, listingFile: APath) -> bool:
        """Returns whether data has been modified since `if_modified_since`."""
        if not listingFile.is_file():
            return False
        parsed = datetime.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT')
        modTime = self._get_mtime(listingFile)
        return modTime > parsed


    def _list_articles_by_period(self,
                                 archiveOrCategory: str,
                                 yymmfiles: List[Tuple[int,int, APath]],
                                 skip: int,
                                 show: int,
                                 if_modified_since: Optional[str] = None,
                                 listingType: Literal['new','month'] = 'month') -> Listing:
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
        months : List[Tuple[int,int,APath]]
            The months to get the listings for. Tuple of (yy, mm, APath_to_listing_file)
            where both yy and mm are `int`.
        # tuple of (yy,mm) skip : int
        show : int
            The quantity of listings that need to be shown.
        if_modified_since : Optional[str]
            RFC 1123 format date of an if_modified_since header.
        listingType: Literal['new','month']       
            Which type if listing is requested. 'month' works with a yymmfiles
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
        if listingType == 'new' and len(yymmfiles) > 1:
            raise ValueError("when listing type  is 'new' yymmfiles must be size 1")

        currentYear, currentMonth, end_month = self._current_y_m_em(max([yy for yy,_,_ in yymmfiles]))
        
        if if_modified_since: # Check if-modified-since for months of interest
            if all([not self._modified_since(if_modified_since, lf)
                    for _,_, lf in yymmfiles]):
                return NotModifiedResponse(True, self._gen_expires())

        # Collect updates for each month
        all_listings: List[ListingItem] = []
        all_pubdates: List[Tuple[date,int]] = []
        for year, month, listingFile in yymmfiles:
            if not listingFile.is_file() and currentYear != str(year) and currentMonth != str(month):
                # This is fine if new month and no announce has happened yet.
                raise Exception("Missing monthly listing file {listingFile}")

            response = self._get_updates_from_list_file(listingFile, listingType, archiveOrCategory)
            if listingType == 'new':
                return response
            
            all_listings.extend(response.listings)            
            if response.pubdates:
                all_pubdates.extend(response.pubdates)
            else:
                pub_date = date(year, month, 1).strftime('%a, %d %b %Y')
                all_pubdates.append((pub_date, len(response.listings)))

        return Listing(listings=all_listings[skip:skip + show], # Adjust for skip/show
                       pubdates=all_pubdates,
                       count=len(all_listings),
                       expires= self._gen_expires())


    
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
        yymmfiles = [
            (year, month, self._generate_listing_path('month', archiveOrCategory, year, month))
            for year, month in months]
        return self._list_articles_by_period(archiveOrCategory, yymmfiles, skip, show, if_modified_since)


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
        yymmfiles= [(year,month, self._generate_listing_path('month', archiveOrCategory, year, month))]
        return self._list_articles_by_period(archiveOrCategory, yymmfiles, skip, show, if_modified_since)


    def list_new_articles(self,
                          archiveOrCategory: str,
                          skip: int,
                          show: int,
                          if_modified_since: Optional[str] = None) -> ListingNew:
        """Gets listings for the most recent announcement/publish.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.

        The 'new' listing maps to a single file. The filename depends on whether
        the archiveOrCategory value is an archive or category listing.
        """
        yymmfiles= [(0,0, self._generate_listing_path('new', archiveOrCategory, 0, 0))]
        return self._list_articles_by_period(archiveOrCategory, yymmfiles, skip, show, if_modified_since, 'new')


    def list_pastweek_articles(self,
                               archiveOrCategory: str,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None) -> Listing:
        """Gets listings for the 5 most recent announcement/publish.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.

        The 'pastweek' listing maps to a single file. The filename depends on whether the
        archiveOrCategory value is an archive or category listing.
        """
        yymmfiles= [(0,0, self._generate_listing_path('pastweek', archiveOrCategory, 0, 0))]
        return self._list_articles_by_period(archiveOrCategory, yymmfiles, skip, show, if_modified_since)

    
    def monthly_counts(self, archive: str, year: int) -> ListingCountResponse:
        """Gets monthly listing counts for the year."""
        monthly_counts: List[MonthCount] = []
        new_cnt, cross_cnt = 0, 0

        currentYear = str(datetime.now().year)[2:]
        end_month = 12
        if currentYear == str(year):
            end_month = datetime.now().month  # limit range to available months

        for month in range(1, end_month + 1):
            listingFile = to_anypath(self._generate_listing_path(
                'month', archive, year, month))
            if not listingFile.is_file():
                if currentYear == str(year):
                    # This may be possible if new month and no announce has happened
                    # yet. Ignore it until we come up with logic to check whether
                    # announce has happened.
                    logger.debug("Listing file not found for current month. "
                                 "List file path is %s", listingFile)
                    continue
                else:
                    raise Exception(f"Missing monthly listing file at {listingFile}")

            response = self._get_updates_from_list_file(listingFile, 'monthly_counts')
            monthly_counts.append(MonthCount(year=year, month= month,
                                             new=response['new_count'],
                                             cross=response['cross_count']))
            new_cnt += response['new_count']
            cross_cnt += response['cross_count']

        return ListingCountResponse(month_counts=monthly_counts,
                                    new_count=new_cnt,
                                    cross_count= cross_cnt)
