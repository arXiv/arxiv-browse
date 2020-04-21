"""Handle requests to support the abs feature.

The primary entrypoint to this module is :func:`.get_abs_page`, which
handles GET requests to the abs endpoint.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin
from datetime import datetime
from dateutil import parser
from dateutil.tz import tzutc

from flask import url_for
from flask import request
from werkzeug.exceptions import InternalServerError

from arxiv import status, taxonomy
from arxiv.base import logging
from browse.controllers import check_supplied_identifier
from browse.domain.metadata import DocMetadata
from browse.domain.category import Category
from browse.exceptions import AbsNotFound
from browse.services.search.search_authors import queries_for_authors, \
    split_long_author_list
from browse.services.util.metatags import meta_tag_metadata
from browse.services.util.response_headers import abs_expires_header, \
    mime_header_date
from browse.services.document import metadata
from browse.services.document.metadata import AbsException,\
    AbsNotFoundException, AbsVersionNotFoundException, AbsDeletedException
from browse.domain.identifier import Identifier, IdentifierException,\
    IdentifierIsArchiveException
from browse.services.database import count_trackback_pings,\
    get_trackback_ping_latest_date, has_sciencewise_ping, \
    get_dblp_listing_path, get_dblp_authors
from browse.services.util.external_refs_cits import include_inspire_link,\
    include_dblp_section, get_computed_dblp_listing_path, get_dblp_bibtex_path
from browse.services.document.config.external_refs_cits import DBLP_BASE_URL,\
    DBLP_BIBTEX_PATH, DBLP_AUTHOR_SEARCH_PATH

logger = logging.getLogger(__name__)

Response = Tuple[Dict[str, Any], int, Dict[str, Any]]

truncate_author_list_size = 100


def get_abs_page(arxiv_id: str) -> Response:
    """Get abs page data from the document metadata service.

    Parameters
    ----------
    arxiv_id : str
        The arXiv identifier as provided in the request.
    download_format_pref: str
        Download format preference.

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
    response_data: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}
    try:
        arxiv_id = _check_legacy_id_params(arxiv_id)
        arxiv_identifier = Identifier(arxiv_id=arxiv_id)

        redirect = check_supplied_identifier(arxiv_identifier,
                                             'browse.abstract')
        if redirect:
            return redirect

        abs_meta = metadata.get_abs(arxiv_id)
        response_data['requested_id'] = arxiv_identifier.idv \
            if arxiv_identifier.has_version else arxiv_identifier.id
        response_data['abs_meta'] = abs_meta
        response_data['meta_tags'] = meta_tag_metadata(abs_meta)
        response_data['author_links'] = \
            split_long_author_list(queries_for_authors(
                abs_meta.authors.raw), truncate_author_list_size)
        response_data['url_for_author_search'] = \
            lambda author_query: url_for('search_archive',
                                         searchtype='author',
                                         archive=abs_meta.primary_archive.id,
                                         query=author_query)

        # Dissemination formats for download links
        download_format_pref = request.cookies.get('xxx-ps-defaults')
        add_sciencewise_ping = _check_sciencewise_ping(abs_meta.arxiv_id_v)
        response_data['formats'] = metadata.get_dissemination_formats(
            abs_meta,
            download_format_pref,
            add_sciencewise_ping)

        # Following are less critical and template must display without them
        # try:
        _non_critical_abs_data(abs_meta, arxiv_identifier, response_data)
        # except Exception:
        #    logger.warning("Error getting non-critical abs page data",
        #                   exc_info=app.debug)

    except AbsNotFoundException:
        if arxiv_identifier.is_old_id and arxiv_identifier.archive \
           in taxonomy.definitions.ARCHIVES:
            archive_name = taxonomy.definitions.ARCHIVES[arxiv_identifier.archive]['name']
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
    except AbsException as e:
        raise InternalServerError(
            'There was a problem. If this problem persists, please contact '
            'help@arxiv.org.') from e

    response_status = status.HTTP_200_OK

    not_modified = _check_request_headers(
        abs_meta, response_data, response_headers)
    if not_modified:
        return {}, status.HTTP_304_NOT_MODIFIED, response_headers

    return response_data, response_status, response_headers


def _non_critical_abs_data(abs_meta: DocMetadata,
                           arxiv_identifier: Identifier,
                           response_data: Dict)->None:
    """Get additional non-essential data for the abs page."""
    # The DBLP listing and trackback counts depend on the DB.
    response_data['dblp'] = _check_dblp(abs_meta)
    response_data['trackback_ping_count'] = count_trackback_pings(
        arxiv_identifier.id)
    if response_data['trackback_ping_count'] > 0:
        response_data['trackback_ping_latest'] = \
            get_trackback_ping_latest_date(arxiv_identifier.id)

    # Include INSPIRE link in references & citations section
    response_data['include_inspire_link'] = include_inspire_link(
        abs_meta)

    # Ancillary files
    response_data['ancillary_files'] = \
        metadata.get_ancillary_files(abs_meta)

    # Browse context
    _check_context(arxiv_identifier,
                   abs_meta.primary_category,
                   response_data)

    response_data['is_covid_match'] = _is_covid_match(abs_meta)


def _check_request_headers(docmeta: DocMetadata,
                           response_data: Dict[str, Any],
                           headers: Dict[str, Any]) -> bool:
    """Check the request headers, update the response headers accordingly."""
    last_mod_dt: datetime = docmeta.modified

    # Latest trackback ping time depends on the database
    if 'trackback_ping_latest' in response_data \
       and isinstance(response_data['trackback_ping_latest'], datetime) \
       and response_data['trackback_ping_latest'] > last_mod_dt:
        # If there is a more recent trackback ping, use that datetime
        last_mod_dt = response_data['trackback_ping_latest']

    # Check for request headers If-Modified-Since and If-None-Match and compare
    # them to the last modified time to determine whether we will return a
    # "not modified" response
    mod_since_dt = _time_header_parse(headers, 'If-Modified-Since')
    none_match_dt = _time_header_parse(headers, 'If-None-Match')
    not_modified = _not_modified(last_mod_dt, mod_since_dt, none_match_dt)

    last_mod_mime = mime_header_date(last_mod_dt)
    headers['Last-Modified'] = last_mod_mime
    headers['ETag'] = last_mod_mime
    headers['Expires'] = abs_expires_header()[1]

    return not_modified


def _not_modified(last_mod_dt: datetime,
                  mod_since_dt: Optional[datetime],
                  none_match_dt: Optional[datetime])->bool:
    if mod_since_dt and none_match_dt:
        not_modified = (mod_since_dt >= last_mod_dt
                        and none_match_dt >= last_mod_dt)
    elif mod_since_dt and not none_match_dt:
        not_modified = mod_since_dt >= last_mod_dt
    elif none_match_dt and not mod_since_dt:
        not_modified = none_match_dt >= last_mod_dt
    else:
        not_modified = False
    return not_modified


def _time_header_parse(headers: Dict[str, Any], header: str) \
        -> Optional[datetime]:
    if (header in request.headers
            and request.headers[header] is not None):
        try:
            dt = parser.parse(str(request.headers.get(header)))
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=tzutc())
            return dt
        except (ValueError, TypeError):
            print(f'Exception parsing the If-None-Match request header')
            return None
    else:
        return None


def _check_legacy_id_params(arxiv_id: str) -> str:
    """Check for legacy request parameters related to old arXiv identifiers.

    Parameters
    ----------
    arxiv_id : str

    Returns
    -------
    arxiv_id: str
        A possibly modified version of the input arxiv_id string.
    """
    if request.args and '/' not in arxiv_id:
        # To support old references to /abs/<archive>?papernum=\d{7}
        if 'papernum' in request.args:
            return f"{arxiv_id}/{request.args['papernum']}"

        for param in request.args:
            # singleton case, where the parameter is the value
            # To support old references to /abs/<archive>?\d{7}
            if not request.args[param] \
               and re.match(r'^\d{7}$', param):
                return f'{arxiv_id}/{param}'
    return arxiv_id


def _check_context(arxiv_identifier: Identifier,
                   primary_category: Optional[Category],
                   response_data: Dict[str, Any]) -> None:
    """Check context in request parameters and update response accordingly.

    Parameters
    ----------
    arxiv_identifier : :class:`Identifier`
    primary_category : :class: `Category`

    Returns
    -------
    Dict of values to add to response_data
    """
    # Set up the context
    context = None
    if ('context' in request.args and (
            request.args['context'] == 'arxiv'
            or request.args['context'] in taxonomy.definitions.CATEGORIES
            or request.args['context'] in taxonomy.definitions.ARCHIVES)):
        context = request.args['context']
    elif primary_category:
        pc = primary_category.canonical or primary_category
        if not arxiv_identifier.is_old_id:  # new style IDs
            context = pc.id
        else:  # Old style id
            if pc.id in taxonomy.definitions.ARCHIVES:
                context = pc.id
            else:
                context = arxiv_identifier.archive
    else:
        context = None

    response_data['browse_context'] = context

    next_url = None
    prev_url = None
    if arxiv_identifier.is_old_id or context == 'arxiv':
        # Revert to hybrid approach per ARXIVNG-2080
        next_id = metadata.get_next_id(arxiv_identifier)
        if next_id:
            next_url = url_for('browse.abstract',
                               arxiv_id=next_id.id,
                               context='arxiv' if context == 'arxiv' else None)
        previous_id = metadata.get_previous_id(arxiv_identifier)
        if previous_id:
            prev_url = url_for('browse.abstract',
                               arxiv_id=previous_id.id,
                               context='arxiv' if context == 'arxiv' else None)
    else:
        # Use prevnext controller to determine what the previous or next ID is.
        next_url = url_for('browse.previous_next',
                           id=arxiv_identifier.id,
                           function='next',
                           context=context if context else None)
        prev_url = url_for('browse.previous_next',
                           id=arxiv_identifier.id,
                           function='prev',
                           context=context if context else None)

    response_data['browse_context_previous_url'] = prev_url
    response_data['browse_context_next_url'] = next_url


def _is_covid_match(docmeta: DocMetadata) -> bool:
    """Check whether paper is about COVID-19."""
    for field in (docmeta.title, docmeta.abstract):
        if re.search(r'(covid[-\s]?19|coronavirus|sars[-\s]cov[-\s]?2)',
                     field, flags=re.I | re.M):
            return True
    return False


def _check_sciencewise_ping(paper_id_v: str) -> bool:
    """Check whether paper has a ScienceWISE ping."""
    try:
        return has_sciencewise_ping(paper_id_v)  # type: ignore
    except IOError:
        return False


def _check_dblp(docmeta: DocMetadata,
                db_override: bool = False) -> Optional[Dict]:
    """Check whether paper has DBLP Bibliography entry."""
    if not include_dblp_section(docmeta):
        return None
    identifier = docmeta.arxiv_identifier
    listing_path = None
    author_list: List[str] = []
    # fallback check in case DB service is not available
    if db_override:
        listing_path = get_computed_dblp_listing_path(docmeta)
    else:
        try:
            if identifier.id is None:
                return None
            listing_path = get_dblp_listing_path(identifier.id)
            if not listing_path:
                return None
            author_list = get_dblp_authors(identifier.id)
        except IOError:
            # log this
            return None
    if listing_path is not None:
        bibtex_path = get_dblp_bibtex_path(listing_path)
    else:
        return None
    return {
        'base_url': DBLP_BASE_URL,
        'author_search_url':
            urljoin(DBLP_BASE_URL, DBLP_AUTHOR_SEARCH_PATH),
        'bibtex_base_url': urljoin(DBLP_BASE_URL, DBLP_BIBTEX_PATH),
        'bibtex_path': bibtex_path,
        'listing_url': urljoin(DBLP_BASE_URL, listing_path),
        'author_list': author_list
    }
