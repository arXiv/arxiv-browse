"""Controller for PDF, source and other downloads."""

import logging
from pathlib import Path
from typing import Callable, Optional, Union, List
import mimetypes

from arxiv.identifier import Identifier, IdentifierException
from arxiv.files.fileformat import FileFormat
from arxiv.document.version import VersionEntry
from arxiv.document.metadata import DocMetadata
from arxiv.files import fileformat

from browse.controllers.files import last_modified, add_time_headers, \
    download_file_base, maxage, withdrawn, unavailable, not_pdf, no_html,\
    not_found, bad_id, cannot_build_pdf
from browse import config

from arxiv.files import FileObj, FileTransform

from browse.services.html_processing import post_process_html

from browse.services.dissemination import get_article_store
from browse.services.dissemination.article_store import (
    Acceptable_Format_Requests, CannotBuildPdf, Deleted)

from flask import Response, abort, make_response, render_template, request, current_app, stream_with_context
from flask_rangerequest import RangeRequest


logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


Resp_Fn_Sig = Callable[[FileFormat, FileObj, Identifier, DocMetadata,
                        VersionEntry], Response]


def default_resp_fn(format: Optional[FileFormat],
                    file: FileObj,
                    arxiv_id: Identifier,
                    docmeta: Optional[DocMetadata] = None,
                    version: Optional[VersionEntry] = None,
                    guess_content_type: Optional[bool] = False) -> Response:
    """Creates a response with appropriate headers for the `file`.

    Parameters
    ----------
    format : FileFormat
        `FileFormat` of the `file`
    docmeta : DocMetadata
        article that the response is for.
    file : FileObj
        File object to use in the response.
    version: VersionEntry
        Version of the paper to consider.
    extra: Optional[str], optional
        Any extra after the normal URL path part. For use in anc files or html files.
    """
    resp: Response = Response()
    if request.method == 'GET' and 'range' in [hk.lower() for hk in request.headers.keys()]:
        # Fastly requires Range response to cache large objects (>20MB),
        # Cloud run requires response larger than 20MB to be chunked but Range response will be smaller.
        resp = RangeRequest(file.open('rb'),
                            etag=file.etag,
                            last_modified=file.updated,
                            size=file.size).make_response()
    else:
        # Cloud run needs chunked for large responses
        if request.method == "GET":
            # Flask/werkzeug automatically do Transfer-Encoding: chunked for a file
            resp = make_response(stream_with_context(iter(file.open("rb"))))
            # but the unit test client doesn't do that so we force it for those
            # see https://github.com/pallets/flask/issues/5424
            resp.headers["Transfer-Encoding"] = "chunked"
            # Don't set Content-Length, it will disable Transfer-Encoding: chunked
        else:
            resp.headers["Content-Length"] = str(file.size)

        resp.set_etag(file.etag)
        resp.headers["Last-Modified"] = last_modified(file)
        resp.headers["Accept-Ranges"] = "bytes"


    resp.headers['Access-Control-Allow-Origin'] = '*'

    if guess_content_type:
        content_type, _ = mimetypes.guess_type(file.name)
        if content_type:
            resp.headers["Content-Type"] = content_type
    else:
        if format and isinstance(format, FileFormat):
            resp.headers['Content-Type'] = format.content_type

    add_time_headers(resp, file, arxiv_id)
    return resp


def _src_response(format: FileFormat,
                  file: FileObj,
                  arxiv_id: Identifier,
                  docmeta: DocMetadata,
                  version: VersionEntry,
                  extra: Optional[str] = None) -> Response:
    """Download source"""
    resp = default_resp_fn(format, file, arxiv_id, docmeta, version)
    suffixes = Path(file.name).suffixes
    if not arxiv_id.is_old_id:
        suffixes.pop(0)  # get rid of .12345
    filename = download_file_base(arxiv_id, version) + "".join(suffixes)
    resp.headers["Content-Disposition"] = f"attachment; filename=\"{filename}\""
    return resp


def pdf_resp_fn(format: FileFormat,
                file: FileObj,
                arxiv_id: Identifier,
                docmeta: DocMetadata,
                version: VersionEntry,
                extra: Optional[str] = None) -> Response:
    """function to make a `Response` for a PDF."""
    resp = default_resp_fn(format, file, arxiv_id, docmeta, version)
    filename = f"{arxiv_id.filename}v{version.version}.pdf"
    resp.headers["Content-Disposition"] = f"inline; filename=\"{filename}\""
    return resp


def get_pdf_resp(arxiv_id_str: str, archive: Optional[str] = None) -> Response:
    """Gets a `Response` for a PDF reqeust."""
    return get_dissemination_resp(fileformat.pdf, arxiv_id_str, archive, pdf_resp_fn)


def get_src_resp(arxiv_id_str: str,
                 archive: Optional[str] = None) -> Response:
    return get_dissemination_resp("e-print", arxiv_id_str, archive, _src_response)


def get_dissemination_resp(format: Acceptable_Format_Requests,
                           arxiv_id_str: str,
                           archive: Optional[str] = None,
                           resp_fn: Resp_Fn_Sig = default_resp_fn) -> Response:
    """
    Returns a `Flask` response ojbject for a given `arxiv_id` and `FileFormat`.

    The response will include headers and may do a range response.
    """
    arxiv_id_str = f"{archive}/{arxiv_id_str}" if archive else arxiv_id_str
    try:
        if len(arxiv_id_str) > 2048:
            abort(400)
        if arxiv_id_str.startswith('arxiv/'):
            abort(400, description="do not prefix non-legacy ids with arxiv/")
        arxiv_id = Identifier(arxiv_id_str)
    except IdentifierException as ex:
        return bad_id(arxiv_id_str, str(ex))
    item = get_article_store().dissemination(format, arxiv_id)
    logger. debug(f"dissemination_for_id(%s) was %s", arxiv_id.idv, item)
    if not item or item == "VERSION_NOT_FOUND" or item == "ARTICLE_NOT_FOUND":
        return not_found(arxiv_id)
    elif item == "WITHDRAWN" or item == "NO_SOURCE":
        return withdrawn(arxiv_id, arxiv_id.has_version)
    elif item == "UNAVAILABLE":
        return unavailable(arxiv_id)
    elif item == "NOT_PDF":
        return not_pdf(arxiv_id)
    elif item == "NO_HTML":
        return no_html(arxiv_id)
    elif isinstance(item, Deleted):
        return bad_id(arxiv_id, item.msg)
    elif isinstance(item, CannotBuildPdf):
        return cannot_build_pdf(arxiv_id, item.msg)

    file, item_format, docmeta, version = item

    # check for existence
    if not isinstance(file, List): # single file
        if not file.exists():
            return not_found(arxiv_id)
    else: # potential list of files
        if not file[0].exists():
            return not_found(arxiv_id)

    return resp_fn(item_format, file, arxiv_id, docmeta, version) #type: ignore


def get_html_response(arxiv_id_str: str,
                      archive: Optional[str] = None) -> Response:
    return get_dissemination_resp(fileformat.html, arxiv_id_str, archive, _html_response)


def _html_response(format: FileFormat,
                   file_list: Union[List[FileObj],FileObj],
                   arxiv_id: Identifier,
                   docmeta: DocMetadata,
                   version: VersionEntry) -> Response:
    if docmeta.source_format == 'html' or version.source_flag.html:
        return _html_source_listing_response(file_list, arxiv_id)
    elif isinstance(file_list, FileObj):
        return default_resp_fn(format, file_list, arxiv_id, docmeta, version, guess_content_type=True)
    else:
        # Not a data error since a non-html-source paper might legitimately not have a latexml HTML
        return unavailable(arxiv_id)


def _html_source_single_response(file: FileObj, arxiv_id: Identifier) -> Response:
    """Produces a `Response`for a single file for a paper with HTML source."""
    if _is_html_name(file):  # do post_processing
        return default_resp_fn(fileformat.html, FileTransform(file, post_process_html), arxiv_id)
    else:
        return default_resp_fn(None, file, arxiv_id, guess_content_type=True)


def _html_source_listing_response(file_list: Union[List[FileObj],FileObj], arxiv_id: Identifier) -> Response:
    """Produces a listing `Response` for a paper with HTML source."""
    if isinstance(file_list, FileObj):
        return _html_source_single_response(file_list, arxiv_id)

    html_files = []
    file_names = []
    for file in file_list:
        if _is_html_name(file):
            html_files.append(file)
            file_names.append(_get_html_file_name(file.name))
    if len(html_files) < 1:
        if current_app.config["ARXIV_LOG_DATA_INCONSTANCY_ERRORS"]:
            logger.error(f"No source HTML files found for arxiv_id: {arxiv_id}")
        return unavailable(arxiv_id)
    if len(html_files) == 1:  # serve the only html file
        return _html_source_single_response(html_files[0], arxiv_id)
    else:  # file selector for multiple html files
        return make_response(render_template("dissemination/multiple_files.html",
                                             arxiv_id=arxiv_id, file_names=file_names), 200,
                             {"Cache-Control": maxage(arxiv_id.has_version)})


def _get_html_file_name(name:str) -> str:
    # file paths should be of form "ps_cache/cs/html/0003/0003064v1/HTTPFS-Paper.html" with a minimum of 5 slashes
    parts = name.split('/')
    if len(parts) > 5:
        result = '/'.join(parts[5:])
    else:
        result= parts[-1]
    return result


def _is_html_name(name: Union[str, FileObj]) -> bool:
    f_name = name.name if isinstance(name, FileObj) else name
    return f_name.lower().endswith(".html") or f_name.lower().endswith(".htm")


