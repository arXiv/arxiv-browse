"""Handle requests to display the trackbacks for a particular article ID."""

from typing import Any, Dict, Tuple
from werkzeug.exceptions import InternalServerError

from arxiv import status
from arxiv.base import logging
from arxiv.base.globals import get_application_config
from browse.services.database import get_trackback_pings
from browse.domain.identifier import Identifier, IdentifierException,\
    IdentifierIsArchiveException

app_config = get_application_config()
logger = logging.getLogger(__name__)

Response = Tuple[Dict[str, Any], int, Dict[str, Any]]


def get_tb_page(arxiv_id: str) -> Response:
    """Get the data needed to display the trackback display page."""
    response_data: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}

    try:
        arxiv_identifier = Identifier(arxiv_id=arxiv_id)
        trackback_pings = get_trackback_pings(arxiv_identifier.id)
    except IdentifierException:
        raise AbsNotFound(data={'arxiv_id': arxiv_id})

    response_status = status.HTTP_200_OK

    return response_data, response_status, response_headers
