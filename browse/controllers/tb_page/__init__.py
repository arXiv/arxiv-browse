"""Handle requests to display the trackbacks for a particular article ID."""

import re
from typing import Any, Dict, List, Tuple
from werkzeug.exceptions import InternalServerError, NotFound, BadRequest
from werkzeug.datastructures import MultiDict

from arxiv import status
from arxiv.base import logging
from arxiv.base.globals import get_application_config
from browse.exceptions import TrackbackNotFound
from browse.services.database import get_paper_trackback_pings, \
                                     get_recent_trackback_pings, \
                                     get_trackback_ping
from browse.controllers import check_supplied_identifier
from browse.domain.identifier import Identifier, IdentifierException
from browse.services.document import metadata
from browse.services.document.metadata import AbsException
from browse.services.search.search_authors import queries_for_authors, \
    split_long_author_list

app_config = get_application_config()
logger = logging.getLogger(__name__)

Response = Tuple[Dict[str, Any], int, Dict[str, Any]]
truncate_author_list_size = 10
trackback_count_options = [25, 50, 100, 200]


def get_tb_page(arxiv_id: str) -> Response:
    """Get the data needed to display the trackback display page."""
    response_data: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}
    if not arxiv_id:
        raise TrackbackNotFound(data={'missing_id': True})
    try:
        arxiv_identifier = Identifier(arxiv_id=arxiv_id)
        redirect = check_supplied_identifier(arxiv_identifier,
                                             'browse.tb')
        if redirect:
            return redirect
        response_data['arxiv_identifier'] = arxiv_identifier
        trackback_pings = get_paper_trackback_pings(arxiv_identifier.id)
        response_data['trackback_pings'] = trackback_pings
        if len(trackback_pings) > 0:
            # Don't need to get article metadata if there are no trackbacks
            abs_meta = metadata.get_abs(arxiv_identifier.id)
            response_data['abs_meta'] = abs_meta
            response_data['author_links'] = \
                split_long_author_list(queries_for_authors(
                    abs_meta.authors.raw), truncate_author_list_size)
        response_status = status.HTTP_200_OK

    except (AbsException, IdentifierException):
        raise TrackbackNotFound(data={'arxiv_id': arxiv_id})
    except Exception as ex:
        logger.warning(f'Error getting trackbacks: {ex}')
        raise InternalServerError

    return response_data, response_status, response_headers


def get_recent_tb_page(request_params: MultiDict) -> Response:
    """Get the data needed to display the recent trackbacks page."""
    response_data: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}
    max_num_trackbacks = trackback_count_options[0]

    views = ''
    if request_params:
        if 'views' in request_params:
            views = request_params['views']
            print(f'views: {views}')
        else:
            raise BadRequest

    try:
        if views:
            max_num_trackbacks = int(views)
        recent_trackback_pings = get_recent_trackback_pings(max_num_trackbacks)
        response_data['max_num_trackbacks'] = max_num_trackbacks
        response_data['recent_trackback_pings'] = recent_trackback_pings
        response_data['article_map'] = _get_article_map(recent_trackback_pings)
        response_data['trackback_count_options'] = trackback_count_options
        response_status = status.HTTP_200_OK
    except ValueError:
        raise BadRequest
    except Exception as ex:
        logger.warning(f'Error getting trackbacks: {ex}')
        raise InternalServerError

    return response_data, response_status, response_headers


def get_tb_redirect(trackback_id: str, hashed_document_id: str) -> Response:
    """Get the redirect location for a trackback ID and hashed_document_id."""

    try:
        tb_id = int(trackback_id)
        m = re.match(r'[\da-f]+', hashed_document_id)
        if not m:
            raise ValueError
        trackback = get_trackback_ping(trackback_id=tb_id)
        if trackback.hashed_document_id == hashed_document_id:
            response_status = status.HTTP_301_MOVED_PERMANENTLY
            return {}, response_status, {'Location': trackback.url}
    except ValueError:
        raise TrackbackNotFound()
    except Exception:
        raise InternalServerError

    raise TrackbackNotFound()


def _get_article_map(recent_trackbacks: List[Tuple]) -> Dict[str, List[tuple]]:
    """Get a mapping of trackback URLs to articles to simplify display."""
    article_map: Dict[str, List[tuple]] = {}
    for rtb in recent_trackbacks:
        url = rtb[0].url
        article = (rtb[1], rtb[2])
        if url not in article_map:
            article_map[url] = []
        if article not in article_map[url]:
            article_map[url].append(article)
    return article_map
