"""arXiv listing backed by filesystem"""

# will need to check errors at some point
# mypy: ignore-errors

import logging
import re
import os
import codecs

from werkzeug.exceptions import BadRequest
from wsgiref.handlers import format_date_time
from datetime import datetime, date, timedelta
from time import mktime

from typing import Optional, Tuple, Dict
from arxiv import taxonomy

from cloudpathlib.anypath import to_anypath

from arxiv.base.globals import get_application_config
app_config = get_application_config()

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG

from browse.services.listing import ListingService
from browse.services.listing.base_listing import NewResponse, \
    ListingResponse, ListingCountResponse, ListingItem

debug_parser = False

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

    def _is_rule(self, line: str, type: str) -> Tuple[int, str]:
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

    def _get_updates_from_list_file(self, listingFilePath: str,
                                    listingType: str, listingFilter: str)-> Dict:
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

        new_items:Dict = []
        cross_items:Dict = []
        rep_items:Dict = []

        # new
        announce_date = ''
        submit_start_date = ''
        submit_end_date = ''

        # pastweek
        pub_dates:Dict = []
        pub_counts:int = []
        pub_count_previous = 0

        with to_anypath(listingFilePath).open('rb') as fh:
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
                announce_date = short_date
                announce_date = datetime.strptime(announce_date, '%a, %d %b %y')

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
                        submit_start_date = res.group(1)
                        submit_start_date = datetime.strptime(submit_start_date, '%a %d %b %y ')
                        submit_end_date = res.group(2)
                        submit_end_date = datetime.strptime(submit_end_date, '%a %d %b %y')

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
                        is_cross = paper.group(2)
                        id = paper.group(3)
                    elif arxiv:
                        is_cross = arxiv.group(2)
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

                    item = {'id': id, 'listingType': type, 'primary': primary_category}
                    if type == 'new':
                        new_items.append(item)
                    elif type == 'cross':
                        cross_items.append(item)
                    elif type =='rep':
                        rep_items.append(item)

                elif listingFilter and re.search(listingFilter, secondary_categories):
                    item = {'id': id, 'listingType': type, 'primary': primary_category}
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

        pub_dates_with_count = []
        index = 0
        for date in pub_dates:
            pub_dates_with_count.append((date, pub_counts[index]))
            index = index + 1

        for pd in pub_dates_with_count:
            (date, count) = pd

        if format == 'monthly_counts':
            # We need the new and cross counts for the monthly count summary
            return {'pubdates': pub_dates_with_count,
                    'new_count': len(new_items),
                    'cross_count': len(cross_items),
                    'expires': self._gen_expires(),
                    'listings': new_items + cross_items + rep_items, # debugging
                    }
        elif listingType == 'new':
            return {'listings': new_items + cross_items + rep_items,
                    'announced': announce_date,
                    'submitted': (submit_start_date, submit_end_date),
                    'new_count': len(new_items),
                    'cross_count': len(cross_items),
                    'rep_count': len(rep_items),
                    'expires': self._gen_expires()
                    }
        elif listingType == 'pastweek' or listingType == 'month' \
                or listingType == 'year':
            #{'listings': List[ListingItem],
            # 'pubdates': List[Tuple[date, int]],
            # 'count': int,
            # 'expires': str}

            # There are no pubdates for month, so we will create one and add count
            # to be consistent with API
            if listingType == 'month':
                date = re.search(r'(?P<date>\d{4})$', listingFilePath)
                if date:
                    yymm_string = date.group('date')
                    pub_date = datetime.strptime(yymm_string, '%y%m')
                    pub_dates_with_count.append((pub_date, len(new_items + cross_items)))

            updates = new_items + cross_items
            return {'listings': updates,
                    'pubdates': pub_dates_with_count,
                    'count': len(new_items + cross_items),
                    'expires': self._gen_expires()
                    }

    def _generate_listing_path(self, listingType: str, archiveOrCategory: str,
                               year: int, month: int) -> str:
        """Create path to listing file"""
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

        # Check listing file
        # if not os.path.exists(listingFilePath):
        #     raise BadRequest("Archive or category listing file doesn't exist:"
        #                      f"{listingFilePath}")

        return listingFilePath

    def _get_mtime(self, listingFilePath: str) -> str:
        """Get the modify time fot specified file."""
        modTime = os.path.getmtime(listingFilePath)
        modTime = datetime.fromtimestamp(modTime)
        return modTime

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

    def _check_if_modified_since(self, if_modified_since: str, listingFilePath: str) -> bool:
        """Indicate whether data has been modified since specified date."""
        parsed = datetime.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT')
        modTime = self._get_mtime(listingFilePath)
        if modTime > parsed:
            # continue and return modified data
            return True
        else:
            # not modified relative to specified date
            return False

    def list_articles_by_year(self,
                              archiveOrCategory: str,
                              year: int,
                              skip: int,
                              show: int,
                              if_modified_since: Optional[str] = None) -> ListingResponse:
        """Get listing items for a whole year.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.

        Creating a archive listing for the year involves combining
        the listing files for all available months for the specified
        year. A category listing requires filtering these monthly
        listing files by the category.

        Existing production year list links use two digit year.
        """
        listingType = 'month'
        listingFilePath = ''
        listingFilter = archiveOrCategory

        all_listings = []
        all_pubdates = []
        monthly_count = 0

        # If current year, limit range to available months
        currentYear = datetime.now().year
        match = re.match(r'\d\d(?P<yy>\d\d)$', str(currentYear))
        currentYear = match.group('yy')
        currentMonth = datetime.now().month

        end_month = 12
        if currentYear == str(year):
            end_month = currentMonth

        # Check if-modified-since for months we will be processing.
        if if_modified_since:
            updates = 0

            for month in range(1, end_month + 1):
                listingFilePath = self._generate_listing_path(listingType,
                                                              archiveOrCategory, year, month)
                if not os.path.exists(listingFilePath):
                    continue
                if self._check_if_modified_since(if_modified_since, listingFilePath):
                    updates = 1

            if updates != 1:
                expires = self._gen_expires()
                return {'not_modified': True, 'expires': expires}

        # Collect updates for each month
        for month in range(1, end_month + 1):
            yymm = "%02d%02d" % (year, month)

            # Create pubdate for each month. Classic code does not generate
            # pubdates and classic UI does not delimit updates by month.
            pub_date = date(year, month, 1).strftime('%a, %d %b %Y')

            listingFilePath = self._generate_listing_path(listingType,
                                                          archiveOrCategory, year, month)
            # Make sure listing file exists
            if not os.path.exists(listingFilePath):
                if currentYear == str(year):
                    # This may be possible if new month and no announce has happened
                    # yet. Ignore it until we come up with logic to check whether
                    # announce has happened.
                    print("Skipping current month")
                    continue
                else:
                    raise Exception("Missing monthly listing file {year}{month}")

            # Parse listing file
            response = self._get_updates_from_list_file(listingFilePath, listingType, listingFilter)

            # These are monthly listings
            #   {'listings': List[ListingItem],
            #   'pubdates': List[Tuple[date, int]],
            #   'count': int,
            #   'expires': str}

            for item in response['listings']:
                all_listings.append(item)
            if response['pubdates']:
                for pub_date in response['pubdates']:
                    all_pubdates.append(pub_date)
            else:
                all_pubdates.append((pub_date, len(response['listings'])))
            monthly_count = monthly_count + response['count']

        total_count = len(all_listings)

        # Adjust listing according to skip and show
        all_listings = all_listings[skip:skip + show]

        return {'listings': all_listings,
                'pubdates': all_pubdates,
                'count': total_count,
                'expires': self._gen_expires()
                }

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

        The monthly listing for an archive maps to a single file. The monthly
        listing for categories is more work since all updates are
        included in the same montly listing file.
        """
        listingType = 'month'
        listingFilePath = ''
        listingFilter = archiveOrCategory

        listingFilePath = self._generate_listing_path(listingType,
                                                      archiveOrCategory, year, month)

        # Check if-modified-since
        if if_modified_since:
            # Return if file has not been updated
            if not self._check_if_modified_since(if_modified_since, listingFilePath):
                # return not modified instead of data
                expires = self._gen_expires()
                return {'not_modified': True, 'expires': expires}

        response = self._get_updates_from_list_file(listingFilePath, listingType, listingFilter)

        # Adjust listing according to skip and show
        response['listings'] = response['listings'][skip:skip + show]

        return response


    def list_new_articles(self,
                          archiveOrCategory: str,
                          skip: int,
                          show: int,
                          if_modified_since: Optional[str] = None) -> NewResponse:
        """Gets listings for the most recent announcement/publish.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.

        The 'new' listing maps to a single file. The filename depends on whether
        the archiveOrCategory value is an archive or category listing.
        """
        listingType = 'new'
        listingFilePath = ''
        listingFilter = archiveOrCategory

        listingFilePath = self._generate_listing_path(listingType, archiveOrCategory, 0, 0)

        # Check if-modified-since
        if if_modified_since:
            # Return if file has not been updated
            if not self._check_if_modified_since(if_modified_since, listingFilePath):
                # return not modified instead of data
                expires = self._gen_expires()
                return {'not_modified': True, 'expires': expires}

        response = self._get_updates_from_list_file(listingFilePath, listingType, listingFilter)

        # Adjust listing according to skip and show
        response['listings'] = response['listings'][skip:skip + show]

        return response


    def list_pastweek_articles(self,
                               archiveOrCategory: str,
                               skip: int,
                               show: int,
                               if_modified_since: Optional[str] = None) -> ListingResponse:
        """Gets listings for the 5 most recent announcement/publish.

        if_modified_since is the if_modified_since header value passed by the web client
        It should be in RFC 1123 format.

        The 'pastweek' listing maps to a single file. The filename depends on whether the
        archiveOrCategory value is an archive or category listing.
        """
        listingType = 'pastweek'
        listingFilePath = ''
        listingFilter = ''

        listingFilePath = self._generate_listing_path(listingType, archiveOrCategory, 0, 0)

        # Check if-modified-since
        if if_modified_since:
            # Return if file has not been updated
            if not self._check_if_modified_since(if_modified_since, listingFilePath):
                # return not modified instead of data
                expires = self._gen_expires()
                return {'not_modified': True, 'expires': expires}

        response = self._get_updates_from_list_file(listingFilePath, listingType, listingFilter)

        # Adjust listing according to skip and show
        response['listings'] = response['listings'][skip:skip + show]

        return response

    def monthly_counts(self,
                       archive: str,
                       year: int) -> ListingCountResponse:
        """Gets monthly listing counts for the year."""
        listingType = 'monthly_counts'
        listingFilePath = ''
        listingFilter = ''

        all_listings = []
        all_pubdates = []
        monthly_count = 0

        monthly_counts = []

        # If current year, limit range to available months
        currentYear = datetime.now().year
        match = re.match(r'\d\d(?P<yy>\d\d)$', str(currentYear))
        currentYear = match.group('yy')
        currentMonth = datetime.now().month

        end_month = 12
        if currentYear == str(year):
            end_month = currentMonth

        # Collect updates for each month
        for month in range(1, end_month + 1):
            yymm = "%02d%02d" % (year, month)
            print(f'Process month listing: {yymm}')

            # Create pubdate for each month. Classic code does not generate
            # pubdates and classic UI does not delimit updates by month.
            pub_date = date(year, month, 1).strftime('%a, %d %b %Y')

            listingFilePath = self._generate_listing_path('month',
                                                          archive, year, month)
            # Make sure listing file exists
            if not os.path.exists(listingFilePath):
                if currentYear == str(year):
                    # This may be possible if new month and no announce has happened
                    # yet. Ignore it until we come up with logic to check whether
                    # announce has happened.
                    print("Skipping current month")
                    logger.debug("Listing file not found for current month. "
                                 "List file path is %s", listingFilePath)
                    continue
                else:
                    raise Exception("Missing monthly listing file {year}{month}")


            # Parse listing file
            response = self._get_updates_from_list_file(listingFilePath, listingType, listingFilter)

            # These are monthly listings
            # {'listings': List[ListingItem],
            # 'pubdates': List[Tuple[date, int]],
            # 'count': int,
            # 'expires': str}

            #{'pubdates': pub_dates_with_count,
            # 'new_count': len(new_items),
            # 'cross_count': len(cross_items),
            # 'expires': self._gen_expires()
            # }
            for item in response['listings']:
                all_listings.append(item)
            if response['pubdates']:
                for pub_date in response['pubdates']:
                    all_pubdates.append(pub_date)
            else:
                # Generate pub_dates for monthly
                all_pubdates.append((pub_date, response['new_count'] + response['cross_count']))
            monthly_counts.append({'year': year, 'month': month, 'new':
                                   response['new_count'], 'cross': response['cross_count']})

        #return {'listings': all_listings,
        #        'pubdates': all_pubdates,
        #        'count': len(all_listings),
        #        'expires': expires  # ???
        #        }
        new_cnt = 0
        cross_cnt = 0
        for i in monthly_counts:
            new_cnt += i['new']
        for i in monthly_counts:
            cross_cnt += i['cross']

        return {'month_counts': monthly_counts,
                'new_count': new_cnt,
                'cross_count': cross_cnt,
                'listings': all_listings,
                }
