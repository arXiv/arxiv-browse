"""
Handle requests to support the abs feature.

The primary entrypoint to this module is :func:`.get_abs_page`, which handles
GET requests to the abs endpoint.
"""

from typing import Tuple, Dict, Any, Optional
from flask import url_for
from werkzeug.exceptions import InternalServerError, NotFound
from werkzeug.datastructures import MultiDict

from arxiv import status, taxonomy
from browse.exceptions import AbsNotFound
from browse.services.util.metatags import meta_tag_metadata
from browse.services.document import metadata
from browse.services.document.metadata import AbsException,\
     AbsNotFoundException, AbsVersionNotFoundException, AbsDeletedException
from browse.domain.identifier import Identifier, IdentifierException,\
    IdentifierIsArchiveException


Response = Tuple[Dict[str, Any], int, Dict[str, Any]]


def get_abs_page(arxiv_id: str, request_params: MultiDict) -> Response:
    """
    Get abs page data from the document metadata service.

    Parameters
    ----------
    arxiv_id : str
        The arXiv identifier as provided in the request.
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
        redirect_url = _check_supplied_identifier(arxiv_identifier)
        if redirect_url:
            return {},\
                   status.HTTP_301_MOVED_PERMANENTLY,\
                   {'Location': redirect_url}

        abs_meta = metadata.get_abs(arxiv_id)
        response_data['abs_meta'] = abs_meta
        response_data['meta_tags'] = meta_tag_metadata(abs_meta)

        _check_context(arxiv_identifier,
                       request_params,
                       response_data)

    except AbsNotFoundException:
        if arxiv_identifier.is_old_id and arxiv_identifier.archive \
           in taxonomy.ARCHIVES:
            archive_name = taxonomy.ARCHIVES[arxiv_identifier.archive]['name']
            raise AbsNotFound(data={'reason': 'old_id_not_found',
                                    'arxiv_id': arxiv_id,
                                    'archive_id': arxiv_identifier.archive,
                                    'archive_name': archive_name})
        raise AbsNotFound(data={'reason': 'not_found', 'arxiv_id': arxiv_id})
    except AbsVersionNotFoundException:
        raise AbsNotFound(data={'reason': 'version_not_found',
                                'arxiv_id': arxiv_identifier.idv,
                                'arxiv_id_latest': arxiv_identifier.id})
    except AbsDeletedException as e:
        raise AbsNotFound(data={'reason': 'deleted',
                                'arxiv_id_latest': arxiv_identifier.id,
                                'message': e})
    except IdentifierIsArchiveException as e:
        raise AbsNotFound(data={'reason': 'is_archive',
                                'arxiv_id': arxiv_id,
                                'archive_name': e})
    except IdentifierException:
        raise AbsNotFound(data={'arxiv_id': arxiv_id})
    except (AbsException, Exception) as e:
        raise InternalServerError(
            'There was a problem. If this problem persists, please contact '
            'help@arxiv.org.') from e
    metadata.get_next_id(identifier=arxiv_identifier)
    return response_data, status.HTTP_200_OK, {}


def _check_supplied_identifier(arxiv_identifier: Identifier) -> Optional[str]:
    """
    Provide redirect URL if supplied ID does not match parsed ID.

    Parameters
    ----------
    arxiv_identier : :class:`Identifier`

    Returns
    -------
    redirect_url: str
        A `browse.abstract` redirect URL that uses the canonical
        arXiv identifier.

    """
    if arxiv_identifier and arxiv_identifier.ids != arxiv_identifier.id and \
            arxiv_identifier.ids != arxiv_identifier.idv:
        redirect_url = url_for('browse.abstract',
                               arxiv_id=arxiv_identifier.idv
                               if arxiv_identifier.has_version
                               else arxiv_identifier.id)
        return redirect_url
    return None


def _check_context(arxiv_identifier: Identifier,
                   request_params: MultiDict,
                   response_data) -> None:
    """
    Check context in request parameters and update response accordingly.

    Parameters
    ----------
    arxiv_identifier : :class:`Identifier`

    request_params: MultiDict

    response_data: dict

    Returns
    -------
    None

    """
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
    elif arxiv_identifier.is_old_id:
        response_data['browse_context_next_id'] = \
            metadata.get_next_id(arxiv_identifier)
        response_data['browse_context_previous_id'] = \
            metadata.get_previous_id(arxiv_identifier)
