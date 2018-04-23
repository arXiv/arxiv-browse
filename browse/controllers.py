"""Browse controllers."""
from flask import request, session
from arxiv import status
from typing import Tuple, Dict, Any
from browse.services.document import metadata
from browse.services.database.models import get_institution
from werkzeug.exceptions import InternalServerError, NotFound

Response = Tuple[Dict[str, Any], int, Dict[str, Any]]


def get_abs_page(arxiv_id: str) -> Response:
    """Get the data that constitutes an /abs page."""
    response_data = {}  # type: Dict[str, Any]
    try:
        abs_meta = metadata.get_abs(arxiv_id)
        response_data['abs_meta'] = abs_meta
        response_data['monster'] = 'lobster'
    except IOError as e:
        # TODO: handle differently?
        raise InternalServerError(
            "There was a problem. If this problem "
            "persists, please contact help@arxiv.org."
        )

    return response_data, status.HTTP_200_OK, {}


def get_institution_from_request() -> str:
    """Get the institution name from the request context."""
    print('get_institution_from_request')
    institution_str = None
    try:
        institution_str = get_institution(request.remote_addr)

    except IOError:
        #TODO: log this
        # return {
        #     'explanation': 'Could not access the database.'
        # }, status.HTTP_500_INTERNAL_SERVER_ERROR, {}
        return None

    return institution_str
