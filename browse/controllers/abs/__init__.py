"""
Handle requests to support the abs feature.

The primary entrypoint to this module is :func:`.get_abs_page`, which handles
GET requests to the abs endpoint.
"""

from typing import Tuple, Dict, Any
from arxiv import status, taxonomy
from browse.services.document import metadata
from browse.services.document.metadata import AbsException,\
     AbsNotFoundException, AbsVersionNotFoundException, AbsDeletedException
from browse.domain.identifier import Identifier, IdentifierException,\
    IdentifierIsArchiveException
from werkzeug.exceptions import InternalServerError
from werkzeug.datastructures import MultiDict

Response = Tuple[Dict[str, Any], int, Dict[str, Any]]


def get_abs_page(arxiv_id: str, request_params: MultiDict) -> Response:
    """
    Get abs page data from the document metadata service.

    Parameters
    ----------
    arxiv_id : str
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
    :class:`.InternalServerError`
        Raised when there was an unexpected problem executing the query.

    """
    response_data = {}  # type: Dict[str, Any]

    try:
        arxiv_identifier = Identifier(arxiv_id=arxiv_id)
        abs_meta = metadata.get_abs(arxiv_id)
        response_data['abs_meta'] = abs_meta
        if 'context' in request_params\
           and (request_params['context'] in taxonomy.CATEGORIES
                or request_params['context'] in taxonomy.ARCHIVES
                or request_params['context'] == 'arxiv'):
            if request_params['context'] == 'arxiv':
                response_data['browse_context_next_id'] = \
                    metadata.get_next_id(arxiv_identifier)
                response_data['browse_context_previous_id'] = \
                    metadata.get_previous_id(arxiv_identifier)
            response_data['browse_context'] = request_params['context']
    except AbsNotFoundException as e:
        if arxiv_identifier.is_old_id and arxiv_identifier.archive \
           in taxonomy.ARCHIVES:
            archive_name = taxonomy.ARCHIVES[arxiv_identifier.archive]['name']
            return {'reason': 'old_id_not_found',
                    'arxiv_id': arxiv_id,
                    'archive_id': arxiv_identifier.archive,
                    'archive_name': archive_name},\
                status.HTTP_404_NOT_FOUND, {}
        return {'reason': 'not_found', 'arxiv_id': arxiv_id}, \
            status.HTTP_404_NOT_FOUND, {}
    except AbsVersionNotFoundException as e:
        return {'reason': 'version_not_found',
                'arxiv_id': arxiv_identifier.idv,
                'arxiv_id_latest': arxiv_identifier.id},\
            status.HTTP_404_NOT_FOUND, {}
    except AbsDeletedException as e:
        return {'reason': 'deleted', 'arxiv_id_latest': arxiv_identifier.id,
                'message': e},\
            status.HTTP_404_NOT_FOUND, {}
    except IdentifierIsArchiveException as e:
        return {'reason': 'is_archive',
                'arxiv_id': arxiv_id,
                'archive_name': e},\
            status.HTTP_404_NOT_FOUND, {}
    except IdentifierException as e:
        return {'arxiv_id': arxiv_id}, status.HTTP_404_NOT_FOUND, {}
    except (AbsException, Exception) as e:
        raise InternalServerError(
            'There was a problem. If this problem persists, please contact '
            'help@arxiv.org.') from e
    metadata.get_next_id(identifier=arxiv_identifier)
    return response_data, status.HTTP_200_OK, {}
