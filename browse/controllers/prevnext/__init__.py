"""Handle requests to support sequential navigation between arXiv IDs."""

from flask import request, url_for
from typing import Tuple, Dict, Any
from werkzeug import MultiDict
from werkzeug.exceptions import InternalServerError, BadRequest, NotFound

from browse.domain.identifier import Identifier, IdentifierException
from browse.services.database import get_sequential_id
from arxiv import status
from arxiv.taxonomy import ARCHIVES, CATEGORIES_ACTIVE
from arxiv.base import logging


Response = Tuple[Dict[str, Any], int, Dict[str, Any]]
logger = logging.getLogger(__name__)
REQUIRED_PARAMS = ('function', 'id')


def get_prevnext(request_params: MultiDict) -> Response:
    """Get the next or previous arXiv ID in the browse context."""
    response_data: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}

    site = 'arxiv.org'
    try:
        if 'id' in request_params:
            arxiv_id = Identifier(request_params['id'])
        else:
            raise BadRequest('Missing article identifier')
        if not ('function' in request_params
                and request_params['function'] in ['prev', 'next']):
            raise BadRequest('Missing or invalid function request')
        if 'context' in request_params:
            context = request_params['context']
            if not (context in CATEGORIES_ACTIVE
                    or context in ARCHIVES or context == 'all'):
                raise BadRequest('Invalid context')
        else:
            raise BadRequest('Missing context')

    except IdentifierException:
        raise BadRequest(f"Invalid article identifier {request_params['id']}")

    try:
        is_next = request_params['function'] == 'next'
        seq_id = get_sequential_id(paper_id=arxiv_id,
                                   is_next=is_next,
                                   context=context)
        if seq_id:
            # TODO: add context to URL
            redirect_url = url_for('browse.abstract', arxiv_id=seq_id)
            return {},\
                status.HTTP_301_MOVED_PERMANENTLY, {'Location': redirect_url}
        else:
            raise BadRequest(
                f'No {"next" if is_next else "previous"} article found for '
                f'{arxiv_id.id} in {context}'
            )
    except BadRequest:
        raise
    except Exception as ex:
        logger.warning(f'Error getting sequential ID: {ex}')
        raise InternalServerError
