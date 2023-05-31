"""Parse listing files of type new.

Due to use of CloudPathLib these can be either local files or cloud object
stores.

The New format basically has abs files as listing items. They lack the "From:" line
that is found in abs files.
"""

# TODO Fix these
# mypy: disable-error-code="assignment,attr-defined"

import codecs
import re
from datetime import date, datetime
from typing import List, Literal, Optional, Tuple, Union

from browse.services.object_store import FileObj
from browse.services.documents.fs_implementation.parse_abs import (
    parse_abs, parse_abs_top)
from browse.services.listing import (ListingItem, ListingNew,
                                     gen_expires)

DATE     = re.compile(r'^Date:\s+')
SUBJECT  = re.compile(r'^Subject:\s+')
RECEIVED = re.compile(r'^\s*received from\s+(?P<date_range>.*)', re.MULTILINE)

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


def parse_new_listing_file(listingFilePath: FileObj, listingFilter: str='')\
                           -> Union[ListingNew]:
    """Parses a new or new.{CATEGORY} listing file.

    An archive with sub categories will have a combined new listing for the time
    period in addition to a new listing file each category. new, new.CL, new.DF,
    etc.

    Listing file markup is used to identify new and cross submissions.
    """
    extras = {}

    new_items:List[ListingItem] = []
    cross_items:List[ListingItem] = []
    rep_items:List[ListingItem] = []

    # new
    announce_date: Optional[date] = None
    submit_start_date: Optional[date] = None
    submit_end_date: Optional[date] = None

    with listingFilePath.open('rb') as fh:
        rawdata = fh.read()
    data =codecs.decode(rawdata, encoding='utf-8',errors='ignore')
    lines = data.split("\n")

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

    # Pull received date out of data, not from line
    # received from  Fri 16 Jul 21 18:00:00 GMT  to  Mon 19 Jul 21 18:00:00 GMT
    received = RECEIVED.search(data)
    if received:
        date_from_to = str(received.group('date_range'))
        date_short_from_to = re.sub(r'\s+\d\d:\d\d:\d\d\s+\w\w\w', '', date_from_to)
        extras['date_from_to'] = date_from_to
        extras['date_short_from_to'] = date_short_from_to
        res = re.match(r'(.*)\s+to\s+(.*)$', date_short_from_to)
        if res:
            submit_start_date = datetime.strptime(res.group(1), '%a %d %b %y ')
            submit_end_date = datetime.strptime(res.group(2), '%a %d %b %y')


    # advance to "------" rule just before first listing
    while( not (lines[0].startswith('-------') and lines[1] == r'\\')):
        lines.pop(0)

    lines.pop(0) # pop off the '-----' rule

    # Lines how has the new listings, then a rule, the cross listings, then a
    # rule, the rep listings then a rule and then some unused tail matter.  line
    # should be at // that is part of the first listing item Now cycle through
    # and process update entries in file.

    new_lines, cross_lines, rep, end = _split_sections(("\n").join(lines))
    new_items = [_to_item(data, 'new') for data in _split_items(new_lines)]
    cross_items = [_to_item(data, 'cross') for data in _split_items(cross_lines)]
    rep_items = [_to_item(data, 'rep') for data in _split_items(rep)]

    return ListingNew(listings= new_items + cross_items + rep_items,
                      announced= announce_date,  # type: ignore
                      submitted= (submit_start_date, submit_end_date),  # type: ignore
                      new_count= len(new_items),
                      cross_count= len(cross_items),
                      rep_count= len(rep_items),
                      expires= gen_expires())



NORMAL="------------------------------------------------------------------------------\n"
CROSS="%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-%-\n"
REP="%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%--%%\n"
END = "%%%---%%%---%%%---%%%---%%%---%%%---%%%---%%%---%%%---%%%---%%%---%%%---%%%---\n"

    
def _split_sections(data:str) -> Tuple[str,str,str,str]:
    new_lines, other_linesA = data.split(CROSS)
    cross_lines, other_linesB = other_linesA.split(REP)
    rep_lines, end = other_linesB.split(END)
    return new_lines, cross_lines, rep_lines, end


def _split_items(data: str) -> List[str]:
    if data.startswith(NORMAL):
        data = data[len(NORMAL):] # srtip NORMAL off if found

    if not data:
        return []
    return data.split(NORMAL)

def _to_item(data: str, ltype: Literal['new', 'cross', 'rep']) -> ListingItem:
    if ltype == 'rep':
        parts = data.split(r"\\") # similar to component split of parse_abs
        data = parts[1].strip()
        doc = parse_abs_top(data,
                            #TODO bogus time but don't think it is used in listing page.
                            datetime.now(),
                            '')
        return ListingItem(doc.arxiv_id, ltype, doc.primary_category, doc)  # type: ignore
    else:
        data = _strip_extra(data)
        doc = parse_abs(data,
                        #TODO bogus time but don't think it is used in listing page.
                        datetime.now())
        return ListingItem(doc.arxiv_id, ltype, doc.primary_category, doc) # type: ignore


_stripex_re = re.compile(r"\\\\ \( https.*kb.*\)")

def _strip_extra(data: str) -> str:
    """Srips the extra "(https://arxiv.org/abs/1234.12345,  234332kb)" """
    return _stripex_re.sub('', data)
