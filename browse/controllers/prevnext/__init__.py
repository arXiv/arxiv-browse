"""Handle requests to support sequential navigation between arXiv IDs."""

from flask import url_for
from typing import Tuple, Dict, Any
from werkzeug import MultiDict
from werkzeug.exceptions import InternalServerError, BadRequest

from browse.domain.identifier import Identifier, IdentifierException
from browse.services.database import get_sequential_id
from arxiv import status
from arxiv.taxonomy.definitions import ARCHIVES, CATEGORIES_ACTIVE
from arxiv.base import logging


Response = Tuple[Dict[str, Any], int, Dict[str, Any]]
logger = logging.getLogger(__name__)


def get_prevnext(request_params: MultiDict) -> Response:
    """
    Get the next or previous arXiv ID in the browse context.

    The 'id', 'function', and 'context' request parameters are required. The
    'site' parameter from the classic prevnext is no longer supported.

    Parameters
    ----------
    request_params : dict

    Returns
    -------
    dict
        Search result response data.
    int
        HTTP status code.
    dict
        Headers to add to the response.

    Raises
    ------
    InternalServerError
        Raised when there was an unexpected problem executing the query.
    BadRequest
        Raised when request parameters are missing, invalid, or when an ID
        redirect cannot be returned even when the request parameters are valid.

    """
    if 'id' not in request_params:
        raise BadRequest('Missing article identifier')
    try:
        arxiv_id = Identifier(request_params['id'])
    except IdentifierException:
        raise BadRequest(f"Invalid article identifier {request_params['id']}")

    if not ('function' in request_params
            and request_params['function'] in ['prev', 'next']):
        raise BadRequest('Missing or invalid function request')

    if 'context' not in request_params:
        raise BadRequest('Missing context')
    context = request_params['context']

    if not (context in CATEGORIES_ACTIVE
            or context in ARCHIVES or context == 'all'):
        raise BadRequest('Invalid context')

    is_next = request_params['function'] == 'next'
    try:
        seq_id = get_sequential_id(paper_id=arxiv_id,
                                   is_next=is_next,
                                   context=context)
    except Exception as ex:
        logger.warning(f'Error getting sequential ID: {ex}')
        raise InternalServerError from ex

    if not seq_id:
        raise BadRequest(
            f'No {"next" if is_next else "previous"} article found for '
            f'{arxiv_id.id} in {context}'
        )

    redirect_url = url_for('browse.abstract',
                           arxiv_id=seq_id,
                           context=context)
    return {}, status.HTTP_301_MOVED_PERMANENTLY, {'Location': redirect_url}
