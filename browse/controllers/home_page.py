"""Handle requests to support the home page."""

import os
import re
from typing import Any, Dict, Optional, Tuple

from http import HTTPStatus as status

from flask import current_app

from arxiv.taxonomy.definitions import GROUPS, CATEGORIES
from arxiv.base import logging
from arxiv.base.globals import get_application_config

from browse.services.database import get_document_count

app_config = get_application_config()
logger = logging.getLogger(__name__)

Response = Tuple[Dict[str, Any], int, Dict[str, Any]]

RE_TOTAL_PAPERS = re.compile(r'^total_papers\s+(?P<count>[0-9]+)',
                             re.MULTILINE)


def get_home_page() -> Response:
    """Get the data needed to generate the home page."""
    response_data: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}

    # We're removing the document count for now until we can
    # do this without a DB query on each page
    # try:
    #     response_data['document_count'] = _get_document_count()
    # except Exception as ex:
    #     raise InternalServerError from ex

    response_data['groups'] = GROUPS
    response_data['categories'] = CATEGORIES
    response_headers['Surrogate-Control'] = "max-age: 3600"
    return response_data, status.OK, response_headers


def _get_document_count() -> Optional[int]:

    try: # check DB for document count first
        return get_document_count()  # type: ignore
    except Exception as ex:
        logger.warning('Error getting document count from DB: %s', ex)

    try: # if DB is unavailable, fall back to legacy static file method
        daily_stats_path = current_app.config['BROWSE_DAILY_STATS_PATH']
        if daily_stats_path and os.path.isfile(daily_stats_path):
            with open(daily_stats_path, mode='r') as statsf:
                stats = statsf.read()
                stats_match = RE_TOTAL_PAPERS.match(stats)
                if stats_match:
                    return int(stats_match.group('count'))
        else:
            raise FileNotFoundError
    except (KeyError, FileNotFoundError):
        logger.warning('Daily stats file not found')

    return None
