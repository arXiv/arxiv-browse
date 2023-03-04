"""arXiv listing backed by files.

Due to use of CloudPathLib these can be either local files or cloud object
stores.

"""

# TODO come back and fix up these type errors
# mypy: disable-error-code="return,arg-type,assignment,attr-defined"

import codecs
import logging
import re
from datetime import date, datetime
from typing import List, Literal, Optional, Tuple, Union

from browse.services import APath
from browse.services.listing import (Listing, ListingItem, ListingNew,
                                     MonthCount, NotModifiedResponse,
                                     gen_expires)

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG


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


def _is_rule(line: str, type: str) -> Tuple[int, Literal['','cross','rep','end']]:
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

def get_updates_from_list_file(year:int, month: int, listingFilePath: APath,
                               listingType: str, listingFilter: str='') -> Union[Listing, ListingNew, NotModifiedResponse, MonthCount]:
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
            dl_date = re.sub(r'^Date:\s+', '', dateline)
            short_date = re.sub(r'\s+\d\d:\d\d:\d\d\s+\w\w\w', '', dl_date)
            extras['Date'] = dl_date
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
        (is_rule, type_change) = _is_rule(line, type)
        while (is_rule):
            if is_rule and type_change:
                type = type_change
            if len(lines):
                line = lines.pop(0)
            else:
                break
            (is_rule, type_change) = _is_rule(line, type)
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
        (rule, new_type) = _is_rule(line, type)
        if new_type:
            type = new_type
        while len(lines) and not rule:
            line = lines.pop(0)
            line = line.replace('\n', '')
            (rule, new_type) = _is_rule(line, type)
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
    for pdate in pub_dates:
        pub_dates_with_count.append((pdate, pub_counts[index]))
        index = index + 1

    for pd in pub_dates_with_count:
        (date, count) = pd

    if format == 'monthly_counts':
        # We need the new and cross counts for the monthly count summary
        return MonthCount(
            year=year, month=month, new=len(new_items), cross=len(cross_items),
            expires=gen_expires(), listings=new_items + cross_items + rep_items)
    elif listingType == 'new':
        return ListingNew(listings= new_items + cross_items + rep_items,
                          announced= announce_date,
                          submitted= (submit_start_date, submit_end_date),
                          new_count= len(new_items),
                          cross_count= len(cross_items),
                          rep_count= len(rep_items),
                          expires= gen_expires())
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
                       expires=gen_expires())
