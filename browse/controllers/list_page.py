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
import math

from flask import current_app
from flask import url_for

from werkzeug.exceptions import ServiceUnavailable, BadRequest
from arxiv import status, taxonomy

from browse.services.search.search_authors import queries_for_authors, \
    split_long_author_list, AuthorList
from browse.services.document.listings import ListingService
from browse.services.document import metadata
from browse.domain.metadata import DocMetadata
from browse.controllers.abs_page import truncate_author_list_size

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

    listing_service = _get_listing_service(current_app)
    if not listing_service:
        raise ServiceUnavailable

    response_data: Dict[str, Any] = {}

    if time_period == 'new':
        response_data['list_time'] = 'new'
        (l_ids, count) = listing_service.list_new_articles(
            subject_or_category, skipn, shown)
    elif time_period in ['pastweek', 'recent']:
        response_data['list_time'] = time_period
        (l_ids, count) = listing_service.list_pastweek_articles(
            subject_or_category, skipn, shown)
    elif time_period == 'current':
        response_data['list_time'] = 'current'
        (l_ids, count) = listing_service.list_articles_by_month(
            subject_or_category, 1999, 12, skipn, shown)
    else:
        yandm = _year_month(time_period)
        if yandm is None:
            raise BadRequest
        list_year, list_month = yandm
        response_data['list_time'] = time_period
        response_data['list_year'] = str(list_year)
        if list_month:
            response_data['list_month'] = str(list_month)
            response_data['list_month_name'] = calendar.month_abbr[list_month]
            (l_ids, count) = listing_service.list_articles_by_month(
                subject_or_category, list_year, list_month, skipn, shown)
        else:
            (l_ids, count) = listing_service.list_articles_by_year(
                subject_or_category, list_year, skipn, shown)

    articles = [metadata.get_abs(id) for id in l_ids]
    author_links = {ar.arxiv_id_v: _author_links(ar) for ar in articles}

    # TODO if it is a HEAD, and nothing has changed, then the service could not send back data for not_modified

    # TODO write cache expires headers

    # TODO make sure handle HEAD

    # TODO generate breadcrumbs data

    response_data.update({
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
        'author_links': author_links,
        'paging': _paging(count, skipn, shown,
                          subject_or_category, time_period)
    })

    def author_query(article, query):
        return url_for('search_archive',
                       searchtype='author',
                       archive=article.primary_archive.id,
                       query=query)
    response_data['url_for_author_search'] = author_query

    response_data.update(_more_fewer(shown, count))

    return response_data, status.HTTP_200_OK, {}


def _get_listing_service(app) -> ListingService:
    return app.config['listing_service']


def _year_month(tp: str)->Optional[Tuple[int, Optional[int]]]:
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


def _author_links(abs_meta: DocMetadata) -> Tuple[AuthorList, AuthorList, int]:
    #  Handle the author list in a very similar way to abs page.
    return split_long_author_list(queries_for_authors(abs_meta.authors.raw),
                                  truncate_author_list_size)


def _more_fewer( show: int, count: int) -> Dict[str, Any]:
    # we want first show_values[n] where show_values[n] < show and show_values[n+1] > show
    nplus1s = _show_values[1:]
    n_n1_tups = map(lambda n, n1: (n, n1), _show_values, nplus1s)
    tup_f = filter(lambda nt: nt[0] < show and nt[1] >= show, n_n1_tups)
    rd = {'mf_fewer': next(tup_f, (None, None))[0]}

    if count < _show_values[-1] and show < _show_values[-1]:
        rd['mf_all'] = count

    # python lacks a find(labmda x:...) ?
    rd['mf_more'] = next(
        filter(lambda x: x > show and x < count, _show_values), None)
    return rd


def _paging(count, skipn, shown, context, subcontext) -> List[Any]:
    B = 3  # num of buffer pages on each side of current
    P = skipn / shown  # short cut page to current page
    L = math.floor(count-1 / (skipn+1))+1  # total number of pages
    S = 2 * B + 2 * 2 + 1  # number of total links in the pages sections:
    #  2*buffer + 2*(first number + dots) + current

    def _page_dict(n, nolink=False)->Dict[Any, Any]:

        # What the @#%$, this isn't working:str(math.(n+shown, count))
        # I get error: AttributeError: module 'math' has no attribute 'min'
        if n+shown > count:
            txt = str(n+1)+'-'+str(count)
        else:
            txt = str(n+1)+'-'+str(n+shown)

        if nolink:
            return {'nolink': txt}
        else:
            return {'skip': n,
                    'txt': txt,
                    'url': url_for('.list_articles',
                                   context=context,
                                   subcontext=subcontext,
                                   skip=n,
                                   show=shown)
                    }

    R = range(0, count, shown)

    if L < S:  # just show all numbers number of pages is less than slots
        return [_page_dict(n) for n in R if n < skipn] + \
            [{'nolink': skipn}] + [_page_dict(n) for n in R if n > skipn]

    page_links = []
    if skipn >= shown:  # Not on first page?
        page_links = [_page_dict(0)]

    prebuffer = [n for n in R if n >= (
        skipn - shown * B) and n < skipn and n > 0]

    # No dots between first and prebuffer
    if prebuffer:
        if prebuffer[0] <= shown * B:
            page_links = page_links + \
                [_page_dict(n) for n in prebuffer]
        else:
            page_links.append({'nolink': '...'})
            page_links = page_links + \
                [_page_dict(n) for n in prebuffer]

    page_links.append(_page_dict(skipn, True))  # current page

    postbuffer = [n for n in R if n > skipn and n <= (skipn + shown * B)]
    if postbuffer:
        page_links = page_links + \
            [_page_dict(n) for n in postbuffer]
        if postbuffer[-1] < R[-1]:  # Need dots between postbuffer and last
            page_links.append({'nolink': '...'})

    if postbuffer and postbuffer[-1] < R[-1]:
        page_links.append(_page_dict(R[-1]))  # last
    return page_links
