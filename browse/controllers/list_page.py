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

from typing import Any, Dict, List, Optional, Tuple

from flask import current_app
from arxiv import status
from browse.services.document.listings import ListingService
from browse.services.document import metadata

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

    if not (time_period and
            (time_period.isdigit() or
             time_period in ['new', 'current', 'pastweek', 'recent'])):
        return {}, status.HTTP_400_BAD_REQUEST, {}

    if not (subject_or_category and
            len(subject_or_category) < 20):
        return {}, status.HTTP_400_BAD_REQUEST, {}

    listing_service = _get_listing_service(current_app)
    if not listing_service:
        return {}, status.HTTP_503_SERVICE_UNAVAILABLE, {}

    # TODO need to use actual info from request
    (l_ids, count) = listing_service.list_articles_by_month('xx', 1999, 12, skipn, shown)

    articles = [metadata.get_abs(id) for id in l_ids]

    # TODO if it is a HEAD, and nothing has changed, then the service could not send back data for not_modified

    # TODO get metadata for ids

    # TODO write cache expires headers

    # TODO make sure handle HEAD

    # TODO generate breadcrumbs data

    # TODO generate data for inter page navigation

    response_data = {
        'test': 'something',
        'ids': l_ids,
        'articles': articles,
        'count': count
    }
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
