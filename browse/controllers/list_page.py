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
from typing import Any, Dict, List, Optional, Tuple

from flask import current_app
from flask import url_for

from arxiv import status, taxonomy

from browse.services.search.search_authors import queries_for_authors, \
    split_long_author_list, AuthorList
from browse.services.document.listings import ListingService
from browse.services.document import metadata
from browse.domain.metadata import DocMetadata

_show_values = [5, 10, 25, 50, 100, 250, 500, 1000, 2000]
"""" Values of $show for more/fewer/all."""

_min_show = _show_values[0]
_max_show = _show_values[-1]
_default_show = _show_values[2]

Response = Tuple[Dict[str, Any], int, Dict[str, Any]]


def get_listing(  # md_service: Any,
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
        shown = _default_show
    else:
        shown = int(show)
        if shown > _show_values[-1]:
            shown = _show_values[-1]

    if (not subject_or_category or
        not (time_period and
             (time_period.isdigit() or
              time_period in ['new', 'current', 'pastweek', 'recent']))):
        return {}, status.HTTP_400_BAD_REQUEST, {}

    if subject_or_category in taxonomy.CATEGORIES:
        list_type = 'category'
        list_ctx_name = taxonomy.CATEGORIES[subject_or_category]['name']
        list_ctx_id = subject_or_category
        list_ctx_in_archive = taxonomy.CATEGORIES[subject_or_category]['in_archive']
    elif subject_or_category in taxonomy.ARCHIVES:
        list_type = 'archive'
        list_ctx_id = subject_or_category
        list_ctx_name = taxonomy.ARCHIVES[subject_or_category]['name']
    else:
        return {}, status.HTTP_400_BAD_REQUEST, {}

    listing_service = _get_listing_service(current_app)
    if not listing_service:
        return {}, status.HTTP_503_SERVICE_UNAVAILABLE, {}

    if time_period == 'new':
        list_time = 'new'
        (l_ids, count) = listing_service.list_new_articles(
            subject_or_category, skipn, shown)
    elif time_period in ['pastweek', 'recent']:
        list_time = time_period
        (l_ids, count) = listing_service.list_pastweek_articles(
            subject_or_category, skipn, shown)
    elif time_period == 'current':
        list_time = 'current'
        (l_ids, count) = listing_service.list_articles_by_month(
            subject_or_category, 1999, 12, skipn, shown)
    else:
        list_time = time_period
        list_year = _year(time_period)
        list_month = _month(time_period)
        (l_ids, count) = listing_service.list_articles_by_month(
            subject_or_category, list_year, list_month, skipn, shown)

    articles = [metadata.get_abs(id) for id in l_ids]
    author_links = {ar.arxiv_id_v: _author_links(ar) for ar in articles}

    # TODO if it is a HEAD, and nothing has changed, then the service could not send back data for not_modified

    # TODO write cache expires headers

    # TODO make sure handle HEAD

    # TODO generate breadcrumbs data

    # TODO generate data for inter page navigation

    response_data = {
        'context': subject_or_category,
        'ids': l_ids,
        'articles': articles,
        'count': count,
        'subcontext': time_period,
        'shown': shown,
        'skipn': skipn,
        'list_type': list_type,
        'list_ctx_name': list_ctx_name,
        'list_ctx_id': list_ctx_id,
        'list_ctx_in_archive': list_ctx_in_archive,
        'list_time': list_time,
        'list_year': list_year,
        'list_month': list_month,
        'list_month_name': calendar.month_abbr[list_month],
        'author_links': author_links,
    }
    
    def author_query(article, query):
        return url_for('search_archive',
                       searchtype='author',
                       archive=article.primary_archive.id,
                       query=query)
    response_data['url_for_author_search'] = author_query

    return response_data, status.HTTP_200_OK, {}


def _get_listing_service(app) -> ListingService:
    return app.config['listing_service']


def _is_yyoryymm(time_period: str)->bool:
    try:
        a = int(time_period)
        if len(time_period) == 2:
            return True  # any 2 digit year is fine
        if len(time_period) == 4:
            mm = int(time_period[2:])
            return mm > 0 and mm < 13  # must be a month
        else:
            return False
    except ValueError:
        return False


def _year(tp: str)->int:
    if len(tp) == 4+2:  # wow, 4 digit year!
        return int(tp[0:4])

    yy_part = int(tp[:2])
    if yy_part >= 91 and yy_part <= 99:
        return 1900 + yy_part
    else:
        return 2000 + yy_part


def _month(tp: str)->int:
    return int(tp[-2:])


# TODO: The list page must trunate the author list, what size does it use?
_truncate_author_list_size = 10


def _author_links(abs_meta: DocMetadata) -> Tuple[AuthorList, AuthorList, int]:
    return split_long_author_list(queries_for_authors(abs_meta.authors.raw),
                                  _truncate_author_list_size)
