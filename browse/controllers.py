"""Browse controllers."""
import re
from typing import Tuple, Dict, Any, Optional

from arxiv import status
from flask import request
from werkzeug.exceptions import InternalServerError

from browse.domain.identifier import IdentifierException
from browse.domain.metatags import meta_tag_metadata
from browse.domain.routes import search_author
from browse.services.database.models import get_institution
from browse.services.document import metadata
from browse.services.document.metadata import AbsNotFoundException, \
    AbsVersionNotFoundException
from browse.services.search.search_authors import queries_for_authors

Response = Tuple[Dict[str, Any], int, Dict[str, Any]]


def get_abs_page(arxiv_id: str) -> Response:
    """Get the data that constitutes an /abs page."""
    response_data = {}  # type: Dict[str, Any]

    try:
        abs_meta = metadata.get_abs(arxiv_id)
        response_data['abs_meta'] = abs_meta
        response_data['meta_tags'] = meta_tag_metadata(abs_meta)
        response_data['author_links'] = queries_for_authors(abs_meta.authors)
        response_data['author_search_url_fn'] = search_author
    except AbsNotFoundException:
        return {'not_found': True, 'arxiv_id': arxiv_id}, \
                 status.HTTP_404_NOT_FOUND, {}
    except AbsVersionNotFoundException:
        arxiv_id_latest = re.sub(r'(v[\d]+)$', '', arxiv_id)
        return {'version_not_found': True,
                'arxiv_id': arxiv_id,
                'arxiv_id_latest': arxiv_id_latest}, \
            status.HTTP_404_NOT_FOUND, {}
    except IdentifierException:
        return {'arxiv_id': arxiv_id}, status.HTTP_404_NOT_FOUND, {}
    except IOError:
        # TODO: handle differently?
        raise InternalServerError(
            "There was a problem. If this problem "
            "persists, please contact help@arxiv.org."
        )

    return response_data, status.HTTP_200_OK, {}


def get_institution_from_request() -> Optional[str]:
    """Get the institution name from the request context."""
    institution_str = None
    try:
        institution_str = get_institution(request.remote_addr)

    except IOError:
        # TODO: log this
        # return {
        #     'explanation': 'Could not access the database.'
        # }, status.HTTP_500_INTERNAL_SERVER_ERROR, {}
        return None

    return institution_str
