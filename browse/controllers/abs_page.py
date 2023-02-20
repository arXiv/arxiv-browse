"""Handle requests to support the abs feature.

The primary entrypoint to this module is :func:`.get_abs_page`, which
handles GET requests to the abs endpoint.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin
from http import HTTPStatus as status

from arxiv import taxonomy
from arxiv.base import logging
from dateutil import parser
from dateutil.tz import tzutc
from flask import request, url_for
from werkzeug.exceptions import InternalServerError

from browse.controllers import check_supplied_identifier
from browse.domain.category import Category
from browse.domain.identifier import (
    Identifier,
    IdentifierException,
    IdentifierIsArchiveException,
)
from browse.domain.metadata import DocMetadata
from browse.exceptions import AbsNotFound
from browse.services.database import (
    count_trackback_pings,
    get_datacite_doi,
    get_dblp_authors,
    get_dblp_listing_path,
    get_trackback_ping_latest_date,
    has_sciencewise_ping,
)
from browse.services.documents import get_doc_service
from browse.services.prevnext import prevnext_service
from browse.formating.external_refs_cits import (
    DBLP_AUTHOR_SEARCH_PATH,
    DBLP_BASE_URL,
    DBLP_BIBTEX_PATH,
    get_computed_dblp_listing_path,
    get_dblp_bibtex_path,
    include_dblp_section,
    include_inspire_link,
)
from browse.services.documents.base_documents import (
    AbsDeletedException,
    AbsException,
    AbsNotFoundException,
    AbsVersionNotFoundException,
)
from browse.formating.search_authors import (
    queries_for_authors,
    split_long_author_list,
)
from browse.controllers.response_headers import (
    abs_expires_header,
    mime_header_date
)
from browse.formating.metatags import meta_tag_metadata


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

        redirect = check_supplied_identifier(arxiv_identifier, "browse.abstract")
        if redirect:
            return redirect

        abs_meta = get_doc_service().get_abs(arxiv_id)
        not_modified = _check_request_headers(abs_meta, response_data, response_headers)
        if not_modified:
            return {}, status.NOT_MODIFIED, response_headers

        response_data["requested_id"] = (
            arxiv_identifier.idv
            if arxiv_identifier.has_version
            else arxiv_identifier.id
        )
        response_data["abs_meta"] = abs_meta
        response_data["meta_tags"] = meta_tag_metadata(abs_meta)
        response_data["author_links"] = split_long_author_list(
            queries_for_authors(abs_meta.authors.raw), truncate_author_list_size
        )
        response_data["url_for_author_search"] = lambda author_query: url_for(
            "search_archive",
            searchtype="author",
            archive=abs_meta.primary_archive.id,
            query=author_query,
        )

        # Dissemination formats for download links
        download_format_pref = request.cookies.get("xxx-ps-defaults")
        add_sciencewise_ping = _check_sciencewise_ping(abs_meta.arxiv_id_v)
        response_data["formats"] = get_doc_service().get_dissemination_formats(
            abs_meta, download_format_pref, add_sciencewise_ping
        )

        # Following are less critical and template must display without them
        _non_critical_abs_data(abs_meta, arxiv_identifier, response_data)
    except AbsNotFoundException as ex:
        if (arxiv_identifier.is_old_id
            and arxiv_identifier.archive in taxonomy.definitions.ARCHIVES):
            archive_name = taxonomy.definitions.ARCHIVES[arxiv_identifier.archive][
                "name"
            ]
            raise AbsNotFound(
                data={
                    "reason": "old_id_not_found",
                    "arxiv_id": arxiv_id,
                    "archive_id": arxiv_identifier.archive,
                    "archive_name": archive_name,
                }
            ) from ex
        raise AbsNotFound(data={"reason": "not_found", "arxiv_id": arxiv_id}) from ex
    except AbsVersionNotFoundException as ex:
        raise AbsNotFound(
            data={
                "reason": "version_not_found",
                "arxiv_id": arxiv_identifier.idv,
                "arxiv_id_latest": arxiv_identifier.id,
            }
        ) from ex
    except AbsDeletedException as ex:
        raise AbsNotFound(
            data={
                "reason": "deleted",
                "arxiv_id_latest": arxiv_identifier.id,
                "message": ex,
            }
        ) from ex
    except IdentifierIsArchiveException as ex:
        raise AbsNotFound(
            data={"reason": "is_archive", "arxiv_id": arxiv_id, "archive_name": ex}
        ) from ex
    except IdentifierException:
        raise AbsNotFound(data={"arxiv_id": arxiv_id})
    except AbsException as ex:
        raise InternalServerError(
            "There was a problem. If this problem persists, please contact "
            "help@arxiv.org."
        ) from ex

    return response_data, status.OK, response_headers


def _non_critical_abs_data(
    abs_meta: DocMetadata, arxiv_identifier: Identifier, response_data: Dict
) -> None:
    """Get additional non-essential data for the abs page."""
    # The DBLP listing and trackback counts depend on the DB.
    response_data["dblp"] = _check_dblp(abs_meta)
    response_data["trackback_ping_count"] = count_trackback_pings(arxiv_identifier.id)
    if response_data["trackback_ping_count"] > 0:
        response_data["trackback_ping_latest"] = get_trackback_ping_latest_date(
            arxiv_identifier.id
        )

    # Include INSPIRE link in references & citations section
    response_data["include_inspire_link"] = include_inspire_link(abs_meta)

    # Ancillary files
    response_data["ancillary_files"] = get_doc_service().get_ancillary_files(abs_meta)

    # Browse context
    _check_context(arxiv_identifier, abs_meta.primary_category, response_data)

    response_data["is_covid_match"] = _is_covid_match(abs_meta)
    response_data["datacite_doi"] = get_datacite_doi(
        paper_id=abs_meta.arxiv_id
    )


def _check_request_headers(
    docmeta: DocMetadata, response_data: Dict[str, Any], resp_headers: Dict[str, Any]
) -> bool:
    """Check the request headers, update the response headers accordingly."""
    last_mod_dt: datetime = docmeta.modified

    # Latest trackback ping time depends on the database
    if (
        "trackback_ping_latest" in response_data
        and isinstance(response_data["trackback_ping_latest"], datetime)
        and response_data["trackback_ping_latest"] > last_mod_dt
    ):
        # If there is a more recent trackback ping, use that datetime
        last_mod_dt = response_data["trackback_ping_latest"]

    last_mod_mime = mime_header_date(last_mod_dt)
    etag = f'"{last_mod_mime}"'

    resp_headers["Last-Modified"] = last_mod_mime
    resp_headers["ETag"] = etag
    resp_headers["Expires"] = abs_expires_header()[1]

    not_modified = _not_modified(
        last_mod_dt,
        _time_header_parse("If-Modified-Since"),
        _get_req_header("if-none-match"),
        etag,
    )

    return not_modified


def _not_modified(
    last_mod_dt: datetime,
    mod_since_dt: Optional[datetime],
    none_match: Optional[str],
    current_etag: str,
) -> bool:
    if none_match and none_match == current_etag:
        return True
    elif mod_since_dt:
        return mod_since_dt.replace(microsecond=0) >= last_mod_dt.replace(microsecond=0)
    else:
        return False


def _time_header_parse(header: str) -> Optional[datetime]:
    try:
        dt = parser.parse(str(_get_req_header(header)))
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=tzutc())
        return dt
    except (ValueError, TypeError, KeyError):
        pass
    return None


def _get_req_header(header: str) -> Optional[str]:
    """Gets request header.

    Needs to be case insensitive for keys. HTTP header keys are case
    insensitive per RFC 2616.
    """
    return next(
        (
            value
            for key, value in request.headers.items()
            if key.lower() == header.lower()
        ),
        None,
    )


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
    if request.args and "/" not in arxiv_id:
        # To support old references to /abs/<archive>?papernum=\d{7}
        if "papernum" in request.args:
            return f"{arxiv_id}/{request.args['papernum']}"

        for param in request.args:
            # singleton case, where the parameter is the value
            # To support old references to /abs/<archive>?\d{7}
            if not request.args[param] and re.match(r"^\d{7}$", param):
                return f"{arxiv_id}/{param}"
    return arxiv_id


def _check_context(
    arxiv_identifier: Identifier,
    primary_category: Optional[Category],
    response_data: Dict[str, Any],
) -> None:
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
    if "context" in request.args and (
        request.args["context"] == "arxiv"
        or request.args["context"] in taxonomy.definitions.CATEGORIES
        or request.args["context"] in taxonomy.definitions.ARCHIVES
    ):
        context = request.args["context"]
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

    response_data["browse_context"] = context

    prevnext = prevnext_service().prevnext(arxiv_identifier, context)
    next_url = None
    prev_url = None
    if arxiv_identifier.is_old_id or context == "arxiv":
        # Revert to hybrid approach per ARXIVNG-2080
        if prevnext.next_id:
            next_url = url_for(
                "browse.abstract",
                arxiv_id=prevnext.next_id.id,
                context="arxiv" if context == "arxiv" else None,
            )
        if prevnext.previous_id:
            prev_url = url_for(
                "browse.abstract",
                arxiv_id=prevnext.previous_id.id,
                context="arxiv" if context == "arxiv" else None,
            )
    else:  # Use prevnext controller to determine what the previous or next ID is.
        next_url = url_for(
            "browse.previous_next",
            id=arxiv_identifier.id,
            function="next",
            context=context if context else None,
        )
        prev_url = url_for(
            "browse.previous_next",
            id=arxiv_identifier.id,
            function="prev",
            context=context if context else None,
        )
    response_data["browse_context_previous_url"] = prev_url
    response_data["browse_context_next_url"] = next_url


def _is_covid_match(docmeta: DocMetadata) -> bool:
    """Check whether paper is about COVID-19."""
    for field in (docmeta.title, docmeta.abstract):
        if re.search(
            r"(covid[-\s]?19|corona[\s]?virus|sars[-\s]cov[-\s]?2)",
            field,
            flags=re.I | re.M,
        ):
            return True
    return False


def _check_sciencewise_ping(paper_id_v: str) -> bool:
    """Check whether paper has a ScienceWISE ping."""
    try:
        return has_sciencewise_ping(paper_id_v)  # type: ignore
    except IOError:
        return False


def _check_dblp(docmeta: DocMetadata, db_override: bool = False) -> Optional[Dict]:
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
        "base_url": DBLP_BASE_URL,
        "author_search_url": urljoin(DBLP_BASE_URL, DBLP_AUTHOR_SEARCH_PATH),
        "bibtex_base_url": urljoin(DBLP_BASE_URL, DBLP_BIBTEX_PATH),
        "bibtex_path": bibtex_path,
        "listing_url": urljoin(DBLP_BASE_URL, listing_path),
        "author_list": author_list,
    }
