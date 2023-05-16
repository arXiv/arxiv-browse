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
import re
from datetime import date, datetime
from typing import List, Literal, Tuple, Union

from browse.domain.category import Category
from browse.domain.metadata import DocMetadata, AuthorList
from browse.domain.version import VersionEntry, SourceType
from browse.services import APath
from browse.services.listing import (Listing, ListingItem,
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
REPLACED_FORM = re.compile(r'^(replaced with revised version)|^((figures|part) added)',
                           re.IGNORECASE)
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

ParsingMode = Literal['month', 'monthly_counts', 'year']


def get_updates_from_list_file(year:int, month: int, listingFilePath: APath,
                               parsingMode: ParsingMode, listingFilter: str='')\
                               -> Union[Listing, NotModifiedResponse, MonthCount]:
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
    new_items:List[ListingItem] = []
    cross_items:List[ListingItem] = []
    rep_items:List[ListingItem] = []

    # TODO I think pubdates are only used by pastweek, check if this is true,
    # and alter the API so month listings don't return them.
    # pastweek
    pub_dates:List[date] = []
    pub_counts:List[int] = []

    with listingFilePath.open('rb') as fh:
        data = fh.read()

    lines = codecs.decode(data, encoding='utf-8',errors='ignore').split("\n")


    # Skip forward to first \\,
    #   which brings us to first publish date for pastweek
    # \\
    # /*Tue, 20 Jul 2021 */
    #\\
    #   or first update entry for monthly listing
    line = lines.pop(0)
    while (len(lines) and not re.match(r'^\\', line)):
        line = lines.pop(0)
        line = line.replace('\n', '')

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

        # Read up to the next \\
        while (len(lines) and re.match(r'^\\', line)):
            if len(lines):
                line = lines.pop(0)

        # Now process all fields up to the next \\
        item_lines=[]
        while (len(lines) and not re.match(r'^\\', line)):
            item_lines.append(line)
            if len(lines):
                line = lines.pop(0)
                line = line.replace('\n', '')
            else:
                break

        article, neworcross = _parse_item(item_lines)

        # If we have id, register the update
        #   apply filtering (if we are dealing with monthly listing)
        if article:
            primary = article.primary_category.id if article.primary_category else ''
            if not listingFilter or (re.match(f'^{listingFilter}', primary)
                                     and neworcross == 'new' ):
                # push update
                item = ListingItem(id=article.arxiv_id, listingType=neworcross,
                                   primary=primary, article=article)
                if neworcross == 'new':
                    new_items.append(item)
                elif neworcross == 'cross':
                    cross_items.append(item)
                elif neworcross =='rep':
                    rep_items.append(item)

            elif listingFilter:
                secondaries = ' '.join(article.categories.split()[1:])  # type: ignore
                if re.search(listingFilter, secondaries):
                    item = ListingItem(id=article.arxiv_id, listingType=neworcross,
                                       primary=primary, article=article)
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

    count = len(new_items)

    pub_dates_with_count:List[Tuple[date,int]] = []
    index = 0
    for pdate in pub_dates:
        pub_dates_with_count.append((pdate, pub_counts[index]))
        index = index + 1

    for pd in pub_dates_with_count:
        (date, count) = pd

    if parsingMode == 'monthly_counts':
        # We need the new and cross counts for the monthly count summary
        return MonthCount(
            year=year, month=month, new=len(new_items), cross=len(cross_items),
            expires=gen_expires(), listings=new_items + cross_items + rep_items)
    else:
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



RE_FROM_FIELD = re.compile(
    r'(?P<from>From:\s*)(?P<name>[^<]+)?\s+(<(?P<email>.*)>)?')
RE_DATE_COMPONENTS = re.compile(
    r'^Date\s*(?::|\(revised\s*(?P<version>.*?)\):)\s*(?P<date>.*?)'
    r'(?:\s+\((?P<size_kilobytes>\d+)kb,?(?P<source_type>.*)\))?$')

RE_REP_COMPONENTS = re.compile(
    r'^replaced with revised version\s*(?P<date>.*?)'
    r'(?:\s+\((?P<size_kilobytes>\d+)kb,?(?P<source_type>.*)\))?$')

RE_ARXIV_ID_FROM_PREHISTORY = re.compile(
    r'(Paper:\s+|Paper \(\*cross-listing\*\):|arXiv:)(?P<arxiv_id>\S+)')

RE_FIELDS=re.compile(r"^(?P<field_name>\S*):\s+(?P<value>.*?)(?=\n\S)", re.S|re.M)
RE_CROSS = re.compile(r"\(\*cross-listing\*\)")

def _parse_item(item_lines: List[str]) -> Tuple[DocMetadata, str]:
    """EX
    arXiv:2301.01082
    From: Sumanta Kumar Sahoo  <example@example.com>
    Date: Tue, 3 Jan 2023 13:17:28 GMT   (6183kb,AD)

Title: A search for variable subdwarf B stars in TESS Full Frame Images III. An
    update on variable targets in both ecliptic hemispheres -- contamination
    analysis and new sdB pulsators
    Authors: S. K. Sahoo (1 and 2), A. S. Baran (2, 3 and 4), H.L. Worters (5), P.
    N\'emeth (2, 6 and 7) and D. Kilkenny (8) ((1) Nicolaus Copernicus
    Astronomical Centre of the Polish Academy of Sciences Poland, (2) ARDASTELLA
    Research Group Poland, (3) Astronomical Observatory of University of Warsaw
    Poland, (4) Missouri State University USA, (5) South African Astronomical
    Observatory South Africa, (6) Astronomical Institute of the Czech Academy of
    Sciences Czech Republic, (7) Astroserver.org Hungary, (8) University of the
    Western Cape South Africa)
    Categories: astro-ph.SR
    Journal-ref: Monthly Notices of the Royal Astronomical Society, Volume 519,
    Issue 2, February 2023, Pages 2486-2499
    DOI: 10.1093/mnras/stac3676
    License: http://creativecommons.org/licenses/by/4.0/
    """
    neworcross='new'    
    raw = "\n".join(item_lines)
    prehistory, misc_fields = re.split(r'\n\n', raw)
    
    idm = re.search(RE_ARXIV_ID_FROM_PREHISTORY, prehistory)
    if idm:
        id = idm.group('arxiv_id')
    else:
        id = 'unknown-id'

    crossm = re.search(RE_CROSS, prehistory)
    if crossm:
        neworcross='cross'

    datem = re.search(RE_DATE_COMPONENTS, raw)
    if datem:
        ver = datem.group('version')
        kb = datem.group('size_kilobytes')
        source_type = datem.group('source_type')
    else:
        ver,kb,source_type=1,0,''

    
    fieldms = re.finditer(RE_FIELDS, misc_fields)
    if fieldms:
        fields = {fieldm.group('field_name'): fieldm.group('value').replace('\n  ', ' ')
                  for fieldm in fieldms}
    else:
        fields = {}

    if fields.get('Categories',None):
        raw_cats =fields.get('Categories','')
        cats = raw_cats.split()
        primary_category = cats[0]
        secondary_categories = cats[1:]
    else:
        raw_cats=''
        primary_category = ''
        secondary_categories = []

    lai = DocMetadata(
        arxiv_id=id,
        arxiv_id_v=f"{id}v{ver}",
        title=fields.get('Title',''),
        authors=AuthorList(fields.get('Authors','')),
        abstract='',
        categories=raw_cats,
        primary_category= Category(primary_category),
        secondary_categories=[Category(sc) for sc in secondary_categories],
        comments=fields.get('Comments',''),
        journal_ref=fields.get('Journal-ref',''),
        version = ver,
        version_history = [VersionEntry(version=ver, raw='', submitted_date=None,
                                        size_kilobytes=kb,
                                        source_type=SourceType(source_type))],
        raw_safe = '',
        submitter=None,
        arxiv_identifier=None,
        primary_archive = None,
        primary_group = None,
        modified = None,        
    )

    
    return lai, neworcross
