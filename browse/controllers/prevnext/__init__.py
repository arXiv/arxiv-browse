"""Handle requests to support sequential navigation between arXiv IDs."""

from flask import request, url_for
from typing import Tuple, Dict, Any
from werkzeug import MultiDict
from werkzeug.exceptions import InternalServerError

from browse.domain import Identifier
from browse.services.database import get_sequential_id
from arxiv import status

Response = Tuple[Dict[str, Any], int, Dict[str, Any]]


def get_prevnext(request_params: MultiDict) -> Response:
    """Get the next or previous arXiv ID in the browse context."""
    response_data: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}

    print(f'next for 0906.4150 {get_sequential_id("0906.4150")}')

    try:
        nav_id = get_sequential_id('1234')
    except Exception as ex:
        raise InternalServerError

    response_status = status.HTTP_301_MOVED_PERMANENTLY

    redirect_url: str = url_for('browse.abstract',
                                arxiv_id=nav_id)
    return {},\
        status.HTTP_301_MOVED_PERMANENTLY,\
        {'Location': redirect_url}
    # return response_data, response_status, response_headers
