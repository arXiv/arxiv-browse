"""Handle requests for the /list pages.

/list requests will show a list of articles for a category for a given
time period.

The primary entrypoint to this module is :func:`.get_list_page`, which
handles GET and POST requests to the list endpoint.

Mainly this should handle requests like:
/list/$category/YYMM
/list/$category/YYMM
/list/category/recent
/list/category/YYMM?skip=n&show=n
/list/archive/new|recent|pastweek
/list/archive/YY
/list/$category/YY

Odd:
?400
cs/14?skip=%25CRAZYSTUFF

1. Figure out what category and yymm is being requested
It's either a POST or GET with params about what to get.
OR it's all in the path.

Things to figure out:
A: what subject category is being requested
B: time period aka listing_type: 'pastweek' 'new' 'current' 'pastyear'
C: show_abstracts only if listing_type='new'

2. Find the listing for that category and yymm

3. Check for not modified.

4. Disply the page
Title,
RSS header,
breadcrumbs
figure out which updates to show.
display them,
show pagination


Differences from legacy arxiv:
Doesn't server the /view path.

"""
import calendar
from typing import Any, Dict, List, Optional, Tuple, cast
import math

from flask import current_app, request, url_for

from werkzeug.exceptions import ServiceUnavailable, BadRequest
from arxiv import status, taxonomy

from browse.services.search.search_authors import queries_for_authors, \
    split_long_author_list, AuthorList
from browse.services.listing import ListingService
from browse.services.document import metadata
from browse.domain.metadata import DocMetadata
from browse.controllers.abs_page import truncate_author_list_size
from browse.controllers.list_page.paging import paging

from flask import current_app as app

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

def get_listing(
        subject_or_category: str,
        time_period: str,
        skip: str,
        show: str) -> Response:
    """Handle requests to list articles.

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
       Number of articles to show.
"""

    # TODO make sure to handle POST too

    if not skip or not skip.isdigit():
        skipn = 0
    else:
        skipn = int(skip)

    if not show or not show.isdigit():
        shown = default_show
    else:
        shown = min(int(show), max_show)

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

    listing_service = get_listing_service(current_app)
    if not listing_service:
        raise ServiceUnavailable

    response_data: Dict[str, Any] = {}

    if time_period == 'new':
        list_type = 'new'
        new_resp = listing_service.list_new_articles(
            subject_or_category, skipn, shown)
        listings = new_resp['listings']
        count = new_resp['count']
        lst_resp = new_resp

    elif time_period in ['pastweek', 'recent']:
        list_type = 'recent'
        rec_resp = listing_service.list_pastweek_articles(
            subject_or_category, skipn, shown)
        listings = rec_resp['listings']
        count = rec_resp['count']
        lst_resp = rec_resp

        # TODO make day table of contents anchors

    elif time_period == 'current':
        list_type = 'current'
        cur_resp = listing_service.list_articles_by_month(
            subject_or_category, 1999, 12, skipn, shown)
        listings = cur_resp['listings']
        count = cur_resp['count']
        lst_resp = cur_resp

    else:  # YYMM or YYYYMM?
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
            month_reps = listing_service.list_articles_by_month(
                subject_or_category, list_year, list_month, skipn, shown)
            listings = month_reps['listings']
            count = month_reps['count']
            lst_resp = month_reps
        else:
            list_type = 'year'
            year_resp = listing_service.list_articles_by_year(
                subject_or_category, list_year, skipn, shown)
            listings = year_resp['listings']
            count = year_resp['count']
            lst_resp = year_resp

    # TODO if it is a HEAD, and nothing has changed, send not modified
    # TODO write cache expires headers

    # Fix up listings if too big, this doesn't work great but will prevent
    # a huge page from being generated if the listing service screws up.
    # if len(listings) > shown:
    #     listings = listings[:shown]

    # Types of pages:
    # new and current and YYMM -> all listings in one list
    # recent -> all in one list, but anchors to specific days

    for item in listings:
        if not type(item) is dict:
            app.logger.error('problem during /list for ' + time_period
                             + ' type of item is not dict, it is ' + str(type(item)))
        else:
            item['article'] = metadata.get_abs(item['id'])

#    articles = [metadata.get_abs(item['id']) for item in listings]

    response_data['listings'] = listings
    response_data['author_links'] = authors_for_articles(listings)
    response_data['downloads'] = dl_for_articles(listings)

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
        'template' : type_to_template[list_type]
    })

    def author_query(article: DocMetadata, query: str)->str:
        return str(url_for('search_archive',
                           searchtype='author',
                           archive=article.primary_archive.id,
                           query=query))
    response_data['url_for_author_search'] = author_query

    response_data.update(more_fewer(shown, count, shown >= count))

    if list_type == 'new':
        response_data['announced'] = lst_resp['pubdates'][0][0]
        response_data.update(index_for_types(listings))
    if list_type == 'month' or list_type == 'current':
        response_data['pubmonth'] = lst_resp['pubdates'][0][0]
    if list_type == 'year':
        response_data['pubmonth'] = lst_resp['pubdates'][0][0]
    if list_type == 'recent':
        response_data['pubdates'] = lst_resp['pubdates']
        
    return response_data, status.HTTP_200_OK, {}


def get_listing_service(app: Any) -> ListingService:
    """Get the listing service from the Flask app.

    There is probably a better way to do this."""
    return cast(ListingService, app.config['listing_service'])


def year_month(tp: str)->Optional[Tuple[int, Optional[int]]]:
    """Gets the year and month from the time_period parameter."""

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

    We want first show_values[n] where show_values[n] < show and show_values[n+1] > show
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


def dl_for_articles(items: List[Any])->Dict[str, Any]:
    """Gets the download links for an article """
    dl_pref = request.cookies.get('xxx-ps-defaults')
    return {item['article'].arxiv_id_v: metadata.get_dissemination_formats(item['article'], dl_pref)
            for item in items}


def authors_for_articles(listings: List[Any])->Dict[str, Any]:
    return {item['article'].arxiv_id_v: author_links(item['article']) for item in listings}


def author_links(abs_meta: DocMetadata) -> Tuple[AuthorList, AuthorList, int]:
    """Creates author list links in a very similar way to abs page."""
    return split_long_author_list(queries_for_authors(abs_meta.authors.raw),
                                  truncate_author_list_size)


def index_for_types(items: List[Any]) ->Dict[str, Any]:
    ift = []
    if items and len(items):
        ift.append(('New submissions', 0))

    first_cross = next((ix for (ix, item) in enumerate(
        items) if item['listingType'] == 'cross'), None)
    if first_cross:
        ift.append(('Cross-lists', first_cross))

    first_rep = next((ix for (ix, item) in enumerate(
        items) if item['listingType'] == 'rep'), None)
    if first_rep:
        ift.append(('Replacements', first_rep))

    return {'index_for_types': ift}
