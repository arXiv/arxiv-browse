"""Parses pastweek listing files.

Due to use of CloudPathLib these can be either local files or cloud object
stores.

pastweek is with a month like format with

    ------------------------------------------------------------------------------
    \\
    /* Fri, 3 Mar 2023 */
    \\
    ------------------------------------------------------------------------------

that indicate the date.
"""

# TODO come back and fix up these type errors
# mypy: disable-error-code="return,arg-type,assignment,attr-defined"

import codecs
import re
from datetime import datetime
from typing import List, Literal, Tuple, Union
from dataclasses import dataclass

from browse.domain.metadata import DocMetadata
from browse.services import APath
from browse.services.documents.fs_implementation.parse_abs import parse_abs_top
from browse.services.listing import (ListingItem, Listing, gen_expires)



@dataclass
class PastweekDay:
    """A list of items from a single day"""
    datestr: str
    items: List[ListingItem]


def parse_listing_pastweek(listingFilePath: APath)\
        -> Listing:
    """Read the paperids that have been updated from a listings file.

    pastweek contains updates for the last five publish days.

    The new, pastweek, and current month listings are dynamic and
    are updated after each publish. The monthly listing file is the only
    permanent record of older announcements.

    An archive with sub categories will have a combined pastweek listing for the
    time period in addition to a new/pastweek listing file each category. pastweek,
    pastweek.CL, pastweek.DF, etc.

    Listing file markup is used to identify new and cross submissions.
    """
    days: List[PastweekDay] = []
    day = PastweekDay('warning-unset',[])
    section = 'new'

    with listingFilePath.open('rb') as fh:
        data = fh.read()

    lines = codecs.decode(data, encoding='utf-8',errors='ignore').split("\n")
    line = lines.pop(0).replace('\n','')
    while(line):
        (is_rule, section_change) = _is_rule(line, section)
        while (is_rule):
            if is_rule and section_change:
                section = section_change
            if len(lines):
                line = lines.pop(0).replace('\n','')
            else:
                break
            (is_rule, section_change) = _is_rule(line, section)
            if section == 'end':
                break

        # consume any \\
        while (len(lines) and re.match(r'^\\', line)):
            line = lines.pop(0).replace('\n','')

        # Now accumulate all lines up to the next \\
        listing_lines: List[str] = []
        # Since the non-new listings don't have abstracts we don't have the
        # problem of // being in the abstract so we can just use the // delimiters.
        while (len(lines) and not re.match(r'^\\', line)):
            listing_lines.append(line)
            line = lines.pop(0).replace('\n','')


        start_new_date = re.search(r"/\* (.*) \*/", " ".join(listing_lines))
        if start_new_date:
            day = PastweekDay(start_new_date.group(1), [])
            days.append(day)
        else:
            doc, type = _parse_doc(listing_lines)
            if doc:
                item = ListingItem(id=doc.arxiv_id, listingType=type,
                                   primary=doc.primary_category.id, # type: ignore
                                   article=doc)
                day.items.append(item)

        #  Now complete the reading of this entry by reading everything up to the
        #  next rule.
        (rule, new_section) = _is_rule(line, section)
        if new_section:
            section = new_section
        while len(lines) and not rule:
            line = lines.pop(0).replace('\n','')
            (rule, new_section) = _is_rule(line, section)
            if new_section:
                section = new_section

        # Read the next line for while loop
        if len(lines):
            line = lines.pop(0).replace('\n','')
        else:
            break

    listings = [item for day in days for item in day.items]
    return Listing(listings=listings,
                   count=len(listings),
                   pubdates=_recent_skip_for_days(days),
                   expires=gen_expires())



def _parse_doc(listing_lines: List[str]) -> Tuple[DocMetadata, str]:
    """Parses the lines from a listing file to a DocMetadata"""
    data = "\n".join(listing_lines)
    abs = parse_abs_top(data,
                        #TODO bogus time but don't think it is used in listing page.
                        datetime.now(),
                        '')
    cross = "(*corss-listing*)" in "\n".join(listing_lines[:3])
    return abs, 'cross' if cross else 'new' # no replacements in pastweek



RULES_NORMAL     = re.compile(r'^------------')
RULES_CROSSES    = re.compile(r'^%-%-%-%-%-%-')
RULES_REPLACESES = re.compile(r'^%%--%%--%%--')
RULES_END        = re.compile(r'^%%%---%%%---')


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

def _recent_skip_for_days(days:List[PastweekDay]) -> List[Tuple[datetime,int]]:
    """For each day make the number of items to skip to get to that day."""
    counts = [len(day.items) for day in days[:-1]]
    counts.insert(0,0) # skip zero for first entry
    return [(datetime.strptime(day.datestr, '%a, %d %b %Y'), count) for day, count in  zip(days, counts)]
