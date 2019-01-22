"""Handle requests to display the trackbacks for a particular article ID."""

from typing import Any, Dict, Tuple
from werkzeug.exceptions import InternalServerError, NotFound, BadRequest

from arxiv import status
from arxiv.base import logging
from arxiv.base.globals import get_application_config
from browse.exceptions import TrackbackNotFound
from browse.services.database import get_trackback_pings, \
                                     get_recent_trackback_pings
from browse.domain.identifier import Identifier, IdentifierException
from browse.services.document import metadata
from browse.services.document.metadata import AbsException
from browse.services.search.search_authors import queries_for_authors, \
    split_long_author_list

app_config = get_application_config()
logger = logging.getLogger(__name__)

Response = Tuple[Dict[str, Any], int, Dict[str, Any]]
truncate_author_list_size = 10


def get_tb_page(arxiv_id: str) -> Response:
    """Get the data needed to display the trackback display page."""
    response_data: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}

    try:
        arxiv_identifier = Identifier(arxiv_id=arxiv_id)
        response_data['arxiv_identifier'] = arxiv_identifier
        trackback_pings = get_trackback_pings(arxiv_identifier.id)
        response_data['trackback_pings'] = trackback_pings
        if trackback_pings:
            abs_meta = metadata.get_abs(arxiv_identifier.id)
            response_data['abs_meta'] = abs_meta
            response_data['author_links'] = \
                split_long_author_list(queries_for_authors(
                    abs_meta.authors.raw), truncate_author_list_size)
        response_status = status.HTTP_200_OK

    except (AbsException, IdentifierException):
        raise TrackbackNotFound(data={'arxiv_id': arxiv_id})
    except Exception:
        raise InternalServerError

    return response_data, response_status, response_headers


def get_recent_tb_page() -> Response:
    """Get the data needed to display the recent trackbacks page."""
    response_data: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}

    try:
        recent_trackback_pings = get_recent_trackback_pings()
        response_data['recent_trackback_pings'] = recent_trackback_pings
        print(f'RECENT:\n{recent_trackback_pings}')
        response_status = status.HTTP_200_OK

    except Exception:
        raise InternalServerError

    return response_data, response_status, response_headers

# def _transform_recent(recent_tuple: Tuple):
#     """Transform the tuple returned by `get_recent_trackback_pings()`."""
#
