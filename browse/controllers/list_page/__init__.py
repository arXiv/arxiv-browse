"""Handle requests for the /list pages.

/list requests will show a list of articles for a category for a given
time period.

The primary entrypoint to this module is :func:`.get_list_page`, which
handles GET and POST requests to the list endpoint.

This should handle requests like:
/list/$category/YYMM
/list/$category/new|recent|current|pastweek
/list/$archive/new|recent|current|pastweek
/list/$archive/YY
/list/$category/YY

And all of the above with ?skip=n&show=n
Examples of odd requests to throw out:
/list/?400
/list/cs/14?skip=%25CRAZYSTUFF
/list/1801.00023

1. Figure out what category and time_period is being requested. It's
either a POST or GET with params about what to get OR it's all in the
path.

Things to figure out:
A: what subject category is being requested
B: time period aka listing_type: 'pastweek' 'new' 'current' 'pastyear'
C: show_abstracts only if listing_type='new'

2. Query the listing service for that category and time_period

3. Check for not modified.

4. Display the page

Differences from legacy arxiv:
Doesn't handle the /view path.
"""
import calendar
import logging
import math
from datetime import date, datetime
from http import HTTPStatus as status
from typing import Any, Dict, List, Optional, Tuple, Union
import re

from arxiv import taxonomy
from arxiv.taxonomy.definitions import CATEGORIES

from browse.controllers.abs_page import truncate_author_list_size
from browse.controllers.list_page.paging import paging
from browse.domain.metadata import DocMetadata
from browse.formatting.search_authors import (AuthorList, queries_for_authors,
                                              split_long_author_list)
from browse.services.documents import get_doc_service
from browse.services.documents.format_codes import formats_from_source_type
from browse.services.listing import (Listing, ListingNew, NotModifiedResponse,
                                     get_listing_service)

from browse.formatting.latexml import get_latexml_url

from flask import request, url_for
from werkzeug.exceptions import BadRequest

logger = logging.getLogger(__name__)

show_values = [5, 10, 25, 50, 100, 250, 500, 1000, 2000]
"""" Values of $show for more/fewer/all."""

max_show = show_values[-1]
"""Max value for show that controller respects."""

default_show = show_values[2]
"""Default value for show."""

Response = Tuple[Dict[str, Any], int, Dict[str, Any]]

type_to_template = {
    'new': 'list/new.html',
    'recent': 'list/recent.html',
    'current': 'list/month.html',
    'month': 'list/month.html',
    'year': 'list/year.html'
}

def get_listing(subject_or_category: str,
                time_period: str,
                skip: str = '',
                show: str = '') -> Response:
    """
    Handle requests to list articles.

    Parameters
    ----------
    subject_or_category
       Subject or categtory to get listing for.
    time_period
       YY or YYMM or 'recent' or 'pastweek' or 'new' or 'current'.
       recent and pastweek mean the last 5 listings,
       new means the most recent listing,
       current means the listings for the current month.
    skip
       Number of articles to skip for this subject and time_period.
    show
       Number of articles to show
    """
    skip = skip or request.args.get('skip', '0')
    show = show or request.args.get('show', '')
    if request.args.get('archive', None) is not None:
        subject_or_category = request.args.get('archive')  # type: ignore
    if request.args.get('year', None):
        time_period = request.args.get('year')  # type: ignore
        month = request.args.get('month', None)
        if month and month != 'all':
            time_period = time_period + request.args.get('month')  # type: ignore

    if (not subject_or_category or
        not (time_period and
             (time_period.isdigit() or
              time_period in ['new', 'current', 'pastweek', 'recent']))):
        raise BadRequest

    if subject_or_category in taxonomy.CATEGORIES:
        list_type = 'category'
        list_ctx_name = taxonomy.CATEGORIES[subject_or_category]['name']
        list_ctx_id = subject_or_category
        list_ctx_in_archive = taxonomy.CATEGORIES[subject_or_category]['in_archive']
    elif subject_or_category in taxonomy.ARCHIVES:
        list_type = 'archive'
        list_ctx_id = subject_or_category
        list_ctx_name = taxonomy.ARCHIVES[subject_or_category]['name']
        list_ctx_in_archive = list_ctx_name
    else:
        raise BadRequest

    listing_service = get_listing_service()

    if not skip or not skip.isdigit():
        skipn = 0
    else:
        skipn = int(skip)

    if not show or not show.isdigit():
        if time_period == 'new':
            shown = max_show
        else:
            shown = default_show
    else:
        shown = min(int(show), max_show)

    if_mod_since = request.headers.get('If-Modified-Since', None)

    response_data: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}

    if time_period == 'new':
        list_type = 'new'
        new_resp: Union[ListingNew, NotModifiedResponse] =\
            listing_service.list_new_articles(subject_or_category, skipn,
                                              shown, if_mod_since)
        response_headers.update(_expires_headers(new_resp))
        if isinstance(new_resp, NotModifiedResponse):
            return {}, status.NOT_MODIFIED, response_headers
        listings = new_resp.listings
        count = new_resp.new_count + \
            new_resp.rep_count + new_resp.cross_count
        response_data['announced'] = new_resp.announced
        response_data['submitted'] = new_resp.submitted
        response_data.update(
            index_for_types(new_resp, subject_or_category, time_period, skipn, shown))
        response_data.update(sub_sections_for_types(new_resp, skipn, shown))

    elif time_period in ['pastweek', 'recent']:
        # A bit different due to returning days not listings
        list_type = 'recent'
        rec_resp = listing_service.list_pastweek_articles(
            subject_or_category, skipn, shown, if_mod_since)
        response_headers.update(_expires_headers(rec_resp))
        if isinstance(rec_resp, NotModifiedResponse):
            return {}, status.NOT_MODIFIED, response_headers
        listings = rec_resp.listings
        count = rec_resp.count
        response_data['pubdates'] = rec_resp.pubdates

    else:  # current or YYMM or YYYYMM
        yandm = year_month(time_period)
        if yandm is None:
            raise BadRequest
        list_year, list_month = yandm
        response_data['list_time'] = time_period
        response_data['list_year'] = str(list_year)
        if list_month or list_month == 0:
            if list_month < 1 or list_month > 12:
                raise BadRequest
            list_type = 'month'
            response_data['list_month'] = str(list_month)
            response_data['list_month_name'] = calendar.month_abbr[list_month]
            resp = listing_service.list_articles_by_month(
                subject_or_category, list_year, list_month, skipn, shown, if_mod_since)
        else:
            list_type = 'year'
            resp = listing_service.list_articles_by_year(
                subject_or_category, list_year, skipn, shown, if_mod_since)

        response_headers.update(_expires_headers(resp))
        if isinstance(resp, NotModifiedResponse):
            return {}, status.NOT_MODIFIED, response_headers
        listings = resp.listings
        count = resp.count
        if resp.pubdates and resp.pubdates[0]:
            response_data['pubmonth'] = resp.pubdates[0][0]
        else:
            response_data['pubmonth'] = datetime.now() # just to make the template happy

    # TODO if it is a HEAD, and nothing has changed, send not modified

    idx = 0

    for item in listings:
        idx = idx + 1
        setattr(item, 'list_index', idx + skipn)
        if not hasattr(item, 'article') or item.article is None:
            setattr(item, 'article', get_doc_service().get_abs(item.id))

    response_data['listings'] = listings
    response_data['author_links'] = authors_for_articles(listings)
    response_data['downloads'] = dl_for_articles(listings)
    response_data['latexml'] = latexml_links_for_articles(listings)

    response_data.update({
        'context': subject_or_category,
        'count': count,
        'subcontext': time_period,
        'shown': shown,
        'skipn': skipn,
        'list_type': list_type,
        'list_ctx_name': list_ctx_name,
        'list_ctx_id': list_ctx_id,
        'list_ctx_in_archive': list_ctx_in_archive,
        'paging': paging(count, skipn, shown,
                         subject_or_category, time_period),
        'viewing_all': shown >= count,
        'template': type_to_template[list_type]
    })

    response_data.update(more_fewer(shown, count, shown >= count))

    def author_query(article: DocMetadata, query: str)->str:
        try:
            if article.primary_archive:
                archive = article.primary_archive.id
            else:
                archive = CATEGORIES[article.primary_category.id]['in_archive'] # type: ignore
            return str(url_for('search_archive',
                           searchtype='author',
                           archive=archive,
                           query=query))
        except (AttributeError, KeyError):
            return str(url_for('search_archive',
                               searchtype='author',
                               archive=list_ctx_in_archive,
                               query=query))

    response_data['url_for_author_search'] = author_query

    return response_data, status.OK, response_headers




def year_month(tp: str)->Optional[Tuple[int, Optional[int]]]:
    """Gets the year and month from the time_period parameter."""
    if tp == "current":
        day = date.today()
        return day.year, day.month

    if not tp or len(tp) > 6 or len(tp) < 2:
        return None

    if len(tp) == 2:  # 2dig year
        return int(tp), None

    if len(tp) == 4:  # 2 dig year, 2 dig month
        mm_part = int(tp[2:4])

        yy_part = int(tp[:2])
        if yy_part >= 91 and yy_part <= 99:
            return (1900 + yy_part, mm_part)
        else:
            return (2000 + yy_part, mm_part)

    if len(tp) == 4+2:  # wow, 4 digit year!
        return int(tp[0:4]), int(tp[4:])
    else:
        return None


def more_fewer(show: int, count: int, viewing_all: bool) -> Dict[str, Any]:
    """Links for the more/fewer sections.

    We want first show_values[n] where show_values[n] < show and
    show_values[n+1] > show
    """
    nplus1s = show_values[1:]
    n_n1_tups = map(lambda n, n1: (n, n1), show_values, nplus1s)
    tup_f = filter(lambda nt: nt[0] < show and nt[1] >= show, n_n1_tups)
    rd = {'mf_fewer': next(tup_f, (None, None))[0]}

    if not viewing_all and count < max_show and show < max_show:
        rd['mf_all'] = count

    # python lacks a find(labmda x:...) ?
    rd['mf_more'] = next(
        filter(lambda x: x > show and x < count, show_values), None)  # type: ignore

    return rd

def _src_code(article: DocMetadata)->str:
    vhs = [vh for vh in article.version_history if vh.version == article.version]
    if vhs:
        return vhs[0].source_type.code
    else:
        return ''

def dl_for_article(article: DocMetadata)-> Dict[str, Any]:
    """Gets the download links for an article."""
    dl_pref = request.cookies.get('xxx-ps-defaults')
    return {article.arxiv_id_v: formats_from_source_type(_src_code(article), dl_pref)}

def dl_for_articles(items: List[Any])->Dict[str, Any]:
    """Gets the download links for an article."""
    dl_pref = request.cookies.get('xxx-ps-defaults')
    return {item.article.arxiv_id_v: formats_from_source_type(_src_code(item.article), dl_pref)
            for item in items}

def latexml_links_for_article (article: DocMetadata)->Dict[str, Any]:
    """Returns a Dict of article id to latexml links"""
    return {article.arxiv_id_v: get_latexml_url(article, True)}

def latexml_links_for_articles (listings: List[Any])->Dict[str, Any]:
    """Returns a Dict of article id to latexml links"""
    return {item.article.arxiv_id_v: get_latexml_url(item.article, True)
                for item in listings}

def authors_for_article(article: DocMetadata)->Dict[str, Any]:
    """Returns a Dict of article id to author links."""
    return {article.arxiv_id_v: author_links(article)}

def authors_for_articles(listings: List[Any])->Dict[str, Any]:
    """Returns a Dict of article id to author links."""
    return {item.article.arxiv_id_v: author_links(item.article)
            for item in listings}


def author_links(abs_meta: DocMetadata) -> Tuple[AuthorList, AuthorList, int]:
    """Creates author list links in a very similar way to abs page."""
    raw = abs_meta.authors.raw
    return split_long_author_list(queries_for_authors(raw),
                                  truncate_author_list_size)


def index_for_types(resp: ListingNew,
                    context: str, subcontext: str,
                    skipn: int, shown: int) ->Dict[str, Any]:
    """Creates index for types of new papers in a ListingNew."""
    ift = []
    new_count = resp.new_count
    cross_count = resp.cross_count
    rep_count = resp.rep_count

    if new_count > 0:
        if skipn != 0:
            ift.append(('New submissions',
                        url_for('.list_articles',
                                context=context, subcontext=subcontext,
                                skip=0, show=shown),
                        0))
        else:
            ift.append(('New submissions', '', 0))

    if cross_count > 0:
        cross_index = new_count + 1
        c_skip = math.floor(new_count / shown) * shown

        if new_count > shown:
            ift.append(('Cross-lists',
                        url_for('.list_articles',
                                context=context, subcontext=subcontext,
                                skip=c_skip, show=shown),
                        cross_index))
        else:
            ift.append(('Cross-lists', '', cross_index))

    if rep_count > 0:
        rep_index = new_count+cross_count + 1
        rep_skip = math.floor((new_count + cross_count)/shown) * shown
        if new_count + cross_count > shown:
            ift.append(('Replacements',
                        url_for('.list_articles',
                                context=context, subcontext=subcontext,
                                skip=rep_skip, show=shown),
                        rep_index))
        else:
            ift.append(('Replacements', '', rep_index))

    return {'index_for_types': ift}


def sub_sections_for_types(
        resp: ListingNew,
        skipn: int, shown: int) -> Dict[str, Any]:
    """Creates data used in section headings on /list/ARCHIVE/new."""
    secs = []
    new_count = resp.new_count
    cross_count = resp.cross_count
    rep_count = resp.rep_count

    news = [item for item in resp.listings if item.listingType == 'new']
    crosses = [item for item in resp.listings
               if item.listingType == 'cross']
    reps = [item for item in resp.listings if item.listingType == 'rep']

    cross_start = new_count+1
    rep_start = new_count + cross_count + 1
    last_shown = skipn + shown

    if news:
        secs.append({
            'type': 'new',
            'items': news,
            'total': new_count,
            'continued': skipn > 0,
            'last': skipn >= new_count - shown
        })
    # else already skipped past new section

    if crosses:
        secs.append({
            'type': 'cross',
            'items': crosses,
            'total': cross_count,
            'continued': skipn + 1 > cross_start,
            'last': skipn >= rep_start - shown
        })
    # else skipped past cross section

    if reps:
        secs.append({
            'type': 'rep',
            'items': reps,
            'total': rep_count,
            'continued': skipn + 1 > rep_start,
            'last': last_shown >= new_count + cross_count + rep_count
        })

    for sec in secs:
        typ = {'new': 'New',
               'cross': 'Cross',
               'rep': 'Replacement'}[sec['type']] # type: ignore
        date = resp.announced.strftime('%A, %-d %B %Y')

        showing = 'showing '
        if sec['continued']:
            showing = 'continued, ' + showing
            if sec['last']:
                showing = showing + 'last '
        if not sec['last'] and not sec['continued']:
            showing = showing + 'first '

        n = len(sec['items'])  # type: ignore
        tot = sec['total']
        sec['heading'] = f'{typ} submissions for {date} '\
            f'({showing}{n} of {tot} entries )'

    return {'sub_sections_for_types': secs}


def _not_modified(response: Union[Listing, ListingNew, NotModifiedResponse]) -> bool:
    return bool(response and isinstance(response, NotModifiedResponse))


def _expires_headers(listing_resp:
                     Union[Listing, ListingNew, NotModifiedResponse]) \
                     -> Dict[str, str]:
    if listing_resp and listing_resp.expires:
        return {'Expires': str(listing_resp.expires)}
    else:
        return {}
