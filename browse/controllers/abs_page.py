"""Handle requests to support the abs feature.

The primary entrypoint to this module is :func:`.get_abs_page`, which
handles GET requests to the abs endpoint.
"""
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from http import HTTPStatus as status
from dateutil import parser
from dateutil.tz import tzutc
from flask import request, url_for
from werkzeug.exceptions import InternalServerError

from arxiv.base import logging
from arxiv.taxonomy.definitions import ARCHIVES, CATEGORIES
from arxiv.taxonomy.category import Category
from arxiv.identifier import (
    Identifier,
    IdentifierException,
    IdentifierIsArchiveException,
)
from arxiv.document.metadata import DocMetadata
from arxiv.document.exceptions import (
    AbsDeletedException,
    AbsException,
    AbsNotFoundException,
    AbsVersionNotFoundException,
)
from arxiv.integration.fastly.headers import add_surrogate_key

from browse.exceptions import AbsNotFound
from browse.services.database import (
    count_trackback_pings,
    get_datacite_doi,
    get_dblp_authors,
    get_dblp_listing_path,
    get_trackback_ping_latest_date,
    get_latexml_publish_dt,
)
from browse.services.documents import get_doc_service
from browse.services.dissemination import get_article_store
from browse.controllers import check_supplied_identifier
from browse.formatting.external_refs_cits import (
    DBLP_BASE_URL,
    DBLP_BIBTEX_PATH,
    DBLP_AUTHOR_SEARCH_PATH,
    include_inspire_link,
    include_dblp_section,
    get_computed_dblp_listing_path,
    get_dblp_bibtex_path,
)
from browse.formatting.latexml import get_latexml_url
from browse.formatting.search_authors import queries_for_authors, split_long_author_list
from browse.controllers.response_headers import mime_header_date
from browse.formatting.metatags import meta_tag_metadata

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
        if not Identifier.is_mostly_safe(arxiv_id):
            raise AbsNotFound(data={"reason": "poorly formatted paper id"})

        arxiv_id = _check_legacy_id_params(arxiv_id)
        arxiv_identifier = Identifier(arxiv_id=arxiv_id)
        response_headers=add_surrogate_key(response_headers,[f"abs-{arxiv_identifier.id}", f"paper-id-{arxiv_identifier.id}"])
        redirect = check_supplied_identifier(arxiv_identifier, "browse.abstract")
        if redirect:
            return redirect

        abs_meta = get_doc_service().get_abs(arxiv_identifier)
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
        response_data['latexml_url'] = get_latexml_url(abs_meta)

        # Dissemination formats for download links
        response_data["formats"] = abs_meta.get_requested_version().formats()

        if response_data['latexml_url'] is not None:
            response_data['formats'].insert(1, 'latexml')

        response_data["withdrawn_versions"] = []
        response_data["higher_version_withdrawn"] = False
        response_data["withdrawn"] = False
        for ver in abs_meta.version_history:
            if ver.withdrawn_or_ignore:
                response_data["withdrawn_versions"].append(ver)
                if abs_meta.version == ver.version:
                    response_data["withdrawn"] = True
                if not response_data["higher_version_withdrawn"] and ver.version > abs_meta.version:
                    response_data["higher_version_withdrawn"] = True
                    response_data["higher_version_withdrawn_submitter"] = _get_submitter(abs_meta.arxiv_identifier,
                                                                                         ver.version)

        response_data["encrypted"] = abs_meta.get_requested_version().source_flag.source_encrypted


        _non_critical_abs_data(abs_meta, arxiv_identifier, response_data)

    except AbsNotFoundException as ex:
        if (arxiv_identifier.is_old_id
            and arxiv_identifier.archive in ARCHIVES):
            archive_name = ARCHIVES[arxiv_identifier.archive].full_name
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
    response_data["ancillary_files"] = get_article_store().get_ancillary_files(abs_meta)

    _prevnext_links(arxiv_identifier, abs_meta.primary_category, response_data)

    response_data["is_covid_match"] = _is_covid_match(abs_meta)
    response_data["datacite_doi"] = get_datacite_doi(
        paper_id=abs_meta.arxiv_id
    )


def _check_request_headers(
    docmeta: DocMetadata, response_data: Dict[str, Any], resp_headers: Dict[str, Any]
) -> bool:
    """Check the request headers, update the response headers accordingly."""
    version = docmeta.get_version()
    if version:
        html_updated = get_latexml_publish_dt(docmeta.arxiv_id, version.version) or datetime.min.replace(tzinfo=timezone.utc)
    else:
        html_updated = datetime.min.replace(tzinfo=timezone.utc)
    last_mod_dt: datetime = max(html_updated, docmeta.modified)

    # Latest trackback ping time depends on the database
    if 'trackback_ping_latest' in response_data \
       and isinstance(response_data['trackback_ping_latest'], datetime) \
       and response_data['trackback_ping_latest'] > last_mod_dt:
        # If there is a more recent trackback ping, use that datetime
        last_mod_dt = response_data["trackback_ping_latest"]

    resp_headers["Last-Modified"] = mime_header_date(last_mod_dt)

    #resp_headers["Expires"] = abs_expires_header(biz_tz())
    # Above we had a Expires: based on publish time but admins wanted shorter when
    # handling service tickets.
    resp_headers["Surrogate-Control"] = "max-age=3600"  # caching services may strip this
    resp_headers["Cache-Control"] = "max-age=3600"

    mod_since_dt = _time_header_parse("If-Modified-Since")
    return bool(mod_since_dt and mod_since_dt.replace(microsecond=0) >= last_mod_dt.replace(microsecond=0))


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
    """Gets request header, needs to be case insensative for keys.

    HTTP header keys are case insensitive. RFC 2616
    """
    return next((value for key, value in request.headers.items()
                 if key.lower() == header.lower()), None)


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


def _prevnext_links(
    arxiv_identifier: Identifier,
    primary_category: Optional[Category],
    response_data: Dict[str, Any],
) -> None:
    """Adds previous and next URLs and context to response."""
    context = None
    if "context" in request.args and (
        request.args["context"] == "arxiv"
        or request.args["context"] in CATEGORIES
        or request.args["context"] in ARCHIVES
    ):
        context = request.args["context"]
    elif primary_category:
        context = primary_category.canonical_id
    elif arxiv_identifier.is_old_id: 
        if arxiv_identifier.archive in ARCHIVES: #context from old style id
                    context=ARCHIVES[arxiv_identifier.archive].canonical_id

    response_data["browse_context"] = context
    response_data["browse_context_previous_url"] = url_for(
            "browse.previous_next",
            id=arxiv_identifier.id,
            function="prev",
            context=context if context else None,
        )
    response_data["browse_context_next_url"] = url_for(
            "browse.previous_next",
            id=arxiv_identifier.id,
            function="next",
            context=context if context else None,
        )


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


def _get_submitter(arxiv_id: Identifier, ver:Optional[int]=None) -> Optional[str]:
    """Gets the submitter of the version."""
    try:
        abs_meta = get_doc_service().get_abs(f"{arxiv_id.id}v{ver}")
        return abs_meta.submitter.name or None
    except:
        return None
