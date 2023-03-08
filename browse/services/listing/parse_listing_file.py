"""Listing service for arXiv backed by legacy listing files.

Due to use of CloudPathLib these can be either local files or cloud object
stores.

There are three formats:
new: with more fields and abstracts, crosses and replacements.
month: with a From: field and no abstract, crosses at the bottom, no replacements
pastweek: with a month like format

The main difference between month and pastweek is the header is a little
different. But it looks like skipping to the first 'dash line followed by \\' would
work for both.
"""

# TODO come back and fix up these type errors
# mypy: disable-error-code="return,arg-type,assignment,attr-defined"

import codecs
import logging
import re
from datetime import date, datetime
from typing import List, Literal, Optional, Tuple, Union

from browse.domain.metadata import DocMetadata
from browse.services import APath
from browse.services.documents.fs_implementation.parse_abs import parse_abs_top
from browse.services.listing import (Listing, ListingItem, ListingNew,
                                     MonthCount, NotModifiedResponse,
                                     gen_expires)

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

ParsingMode = Literal['new', 'month', 'monthly_counts', 'year', 'pastweek']

def get_updates_from_list_file(year:int, month: int, listingFilePath: APath,
                               parsingMode: ParsingMode, listingFilter: str='')\
                               -> Union[Listing, ListingNew, NotModifiedResponse,
                                        MonthCount]:
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
    """
    format = ''
    if parsingMode == 'monthly_counts':
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
    if parsingMode == 'pastweek' or parsingMode == 'month':
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

    # 'line' has the '\\' before the first item
    # Now cycle through and process update entries in file
    type = 'new'

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

        # consume any \\
        while (len(lines) and re.match(r'^\\', line)):
            if len(lines):
                line = lines.pop(0)

        # Now process all fields up to the next \\
        listing_lines: List[str] = [line]
        # Since the non-new listings don't have abstracts we don't have the
        # problem of // being in the abstract so we can just use the // delimiters.
        while (len(lines) and not re.match(r'^\\', line)):
            line = lines.pop(0)
            listing_lines.append(line)

        doc = _parse_doc(listing_lines)
        primary_category = doc.primary_category.id
        secondary_categories = ' '.join([sc.id for sc in doc.secondary_categories])

        # If we have id, register the update
        #   apply filtering (if we are dealing with monthly listing)
        if doc:
            filter = f'^{listingFilter}'
            if not listingFilter or (re.match(filter, primary_category)
                                     and type == 'new' ):
                # push update
                item = ListingItem(id=doc.arxiv_id, listingType=type,
                                   primary=primary_category, article=doc)
                if type == 'new':
                    new_items.append(item)
                elif type == 'cross':
                    cross_items.append(item)
                elif type =='rep':
                    rep_items.append(item)

            elif listingFilter and re.search(listingFilter, secondary_categories):
                item = ListingItem(id=id, listingType=type, primary=primary_category,
                                   article=doc)
                cross_items.append(item)

        #  Now complete the reading of this entry by reading everything up to the
        #  next rule.
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
    if parsingMode == 'pastweek':
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
    elif parsingMode == 'new':
        return ListingNew(listings= new_items + cross_items + rep_items,
                          announced= announce_date,
                          submitted= (submit_start_date, submit_end_date),
                          new_count= len(new_items),
                          cross_count= len(cross_items),
                          rep_count= len(rep_items),
                          expires= gen_expires())
    elif parsingMode == 'pastweek' or parsingMode == 'month' \
            or parsingMode == 'year':
        #{'listings': List[ListingItem],
        # 'pubdates': List[Tuple[date, int]],
        # 'count': int,
        # 'expires': str}

        # There are no pubdates for month, so we will create one and add count
        # to be consistent with API
        if parsingMode == 'month':
            date = re.search(r'(?P<date>\d{4})$', str(listingFilePath))
            if date:
                yymm_string = date.group('date')
                pub_date = datetime.strptime(yymm_string, '%y%m')
                pub_dates_with_count.append((pub_date, len(new_items + cross_items)))

        return Listing(listings=new_items + cross_items,
                       pubdates=pub_dates_with_count,
                       count=len(new_items + cross_items),
                       expires=gen_expires())



def _parse_doc(listing_lines: List[str]) -> DocMetadata:
    """Parses the lines from a listing file to a DocMetadata"""
    return parse_abs_top("\n".join(listing_lines),
                         #TODO bogus time but don't think it is used in listing page.
                         datetime.now(),
                         '')
