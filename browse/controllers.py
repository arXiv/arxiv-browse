"""Browse controllers."""
import re
from flask import request
from arxiv import status, taxonomy
from typing import Tuple, Dict, Any, Optional
from browse.services.document import metadata
from browse.services.document.metadata import AbsNotFoundException,\
    AbsVersionNotFoundException, AbsDeletedException
from browse.domain.identifier import Identifier, IdentifierException,\
    IdentifierIsArchiveException
from browse.services.database.models import get_institution
from werkzeug.exceptions import InternalServerError

Response = Tuple[Dict[str, Any], int, Dict[str, Any]]


def get_abs_page(arxiv_id: str) -> Response:
    """Get the data that constitutes an /abs page."""
    response_data = {}  # type: Dict[str, Any]
    arxiv_id_latest = re.sub(r'(v[\d]+)$', '', arxiv_id)
    try:
        arxiv_identifier = Identifier(arxiv_id=arxiv_id)
        abs_meta = metadata.get_abs(arxiv_id)
        response_data['abs_meta'] = abs_meta
    except AbsNotFoundException as e:
        if arxiv_identifier.is_old_id and arxiv_identifier.archive in taxonomy.ARCHIVES:
            archive_name = taxonomy.ARCHIVES[arxiv_identifier.archive]['name']
            return {'reason': 'old_id_not_found',
                    'arxiv_id': arxiv_id,
                    'archive_id': arxiv_identifier.archive,
                    'archive_name': archive_name},\
                status.HTTP_404_NOT_FOUND, {}
        else:
            return {'reason': 'not_found', 'arxiv_id': arxiv_id}, \
                status.HTTP_404_NOT_FOUND, {}
    except AbsVersionNotFoundException as e:
        return {'reason': 'version_not_found',
                'arxiv_id': arxiv_id,
                'arxiv_id_latest': arxiv_id_latest},\
            status.HTTP_404_NOT_FOUND, {}
    except AbsDeletedException as e:
        return {'reason': 'deleted', 'arxiv_id_latest': arxiv_id_latest,
                'message': e},\
            status.HTTP_404_NOT_FOUND, {}
    except IdentifierIsArchiveException as e:
        return {'reason': 'is_archive',
                'arxiv_id': arxiv_id,
                'archive_name': e},\
            status.HTTP_404_NOT_FOUND, {}
    except IdentifierException as e:
        return {'arxiv_id': arxiv_id}, status.HTTP_404_NOT_FOUND, {}
    except IOError as e:
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
