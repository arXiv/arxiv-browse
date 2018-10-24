"""Handle requests to support the home page."""

from typing import Any, Dict, List, Optional, Tuple
from flask import url_for
from flask import request
from werkzeug.exceptions import InternalServerError

from arxiv import status, taxonomy
from arxiv.base import logging

logger = logging.getLogger(__name__)

Response = Tuple[Dict[str, Any], int, Dict[str, Any]]


def get_home_page() -> Response:
    """Get the data needed to generated the home page."""
    response_data: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}

    response_data['groups'] = taxonomy.GROUPS
    response_data['archives'] = taxonomy.ARCHIVES_ACTIVE
    response_data['categories'] = taxonomy.CATEGORIES_ACTIVE

    response_status = status.HTTP_200_OK

    return response_data, response_status, response_headers
