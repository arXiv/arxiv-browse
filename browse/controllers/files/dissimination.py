"""Controller for PDF, source and other downloads."""

import logging
from email.utils import format_datetime
from typing import Callable, Optional

from arxiv.identifier import Identifier, IdentifierException
from browse.domain.fileformat import FileFormat
from browse.domain.version import VersionEntry
from browse.domain.metadata import DocMetadata

from browse.services.object_store.fileobj import FileObj, UngzippedFileObj

from browse.services.dissemination import get_article_store
from browse.services.dissemination.article_store import (
    Acceptable_Format_Requests, CannotBuildPdf, Deleted)
from browse.services.next_published import next_publish

from browse.stream.tarstream import tar_stream_gen
from flask import Response, abort, make_response, render_template
from flask_rangerequest import RangeRequest

from . import last_modified, add_time_headers

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


Resp_Fn_Sig = Callable[[FileFormat, FileObj, Identifier, DocMetadata,
                        VersionEntry], Response]


def default_resp_fn(file_format: FileFormat,
                    file: FileObj,
                    arxiv_id: Identifier,
                    docmeta: DocMetadata,
                    version: VersionEntry,
                    extra: Optional[str] = None) -> Response:
    """Creates a response with appropriate headers for the `file`.

    Parameters
    ----------
    file_format : FileFormat
        `FileFormat` of the `file`
    item : DocMetadata
        article that the response is for.
    file : FileObj
        File object to use in the response.
    """

    # Have to do Range Requests to get GCP CDN to accept larger objects.
    resp: Response = RangeRequest(file.open('rb'),
                                  etag=last_modified(file),
                                  last_modified=file.updated,
                                  size=file.size).make_response()

    resp.headers['Access-Control-Allow-Origin'] = '*'
    if isinstance(file_format, FileFormat):
        resp.headers['Content-Type'] = file_format.content_type

    if resp.status_code == 200:
        # For large files on CloudRun chunked and no content-length needed
        # TODO revisit this, in some cases it doesn't work maybe when
        # combined with gzip encoding?
        # resp.headers['Transfer-Encoding'] = 'chunked'
        resp.headers.pop('Content-Length')

    add_time_headers(resp, file, arxiv_id)
    return resp


def src_resp_fn(format: FileFormat,
                file: FileObj,
                arxiv_id: Identifier,
                docmeta: DocMetadata,
                version: VersionEntry,
                extra: Optional[str] = None) -> Response:
    """Prepares a response where the payload will be a tar of the source.

    No matter what the actual format of the source, this will try to return a
    .tar.  If the source is a .pdf then that will be tarred. If the source is a
    gzipped PS file, that will be ungzipped and then tarred.

    This will also uses gzipped transfer encoding. But the client will unencode
    the bytestream and the file will be saved as .tar.
    """
    if file.name.endswith(".tar.gz"):  # Nothing extra to do, already .tar.gz
        resp = RangeRequest(file.open('rb'), etag=last_modified(file),
                            last_modified=file.updated,
                            size=file.size).make_response()
    elif file.name.endswith(".gz"):  # unzip single file gz and then tar
        outstream = tar_stream_gen([UngzippedFileObj(file)])
        resp = make_response(outstream, 200)
    else:  # tar single flie like .pdf
        outstream = tar_stream_gen([file])
        resp = make_response(outstream, 200)

    archive = f"{arxiv_id.archive}-" if arxiv_id.is_old_id else ""
    filename = f"arXiv-{archive}{arxiv_id.filename}v{version.version}.tar"

    resp.headers["Content-Encoding"] = "x-gzip"  # tar_stream_gen() gzips
    resp.headers["Content-Type"] = "application/x-eprint-tar"
    resp.headers["Content-Disposition"] = \
        f"attachment; filename=\"{filename}\""
    add_time_headers(resp, file, arxiv_id)
    resp.headers["ETag"] = last_modified(file)
    return resp  # type: ignore


def get_src_resp(arxiv_id_str: str,
                 archive: Optional[str] = None) -> Response:
    return get_dissimination_resp("e-print", arxiv_id_str, archive,
                                  src_resp_fn)


def get_e_print_resp(arxiv_id_str: str,
                     archive: Optional[str] = None) -> Response:
    return get_dissimination_resp("e-print", arxiv_id_str, archive)


def get_dissimination_resp(file_format: Acceptable_Format_Requests,
                           arxiv_id_str: str,
                           archive: Optional[str] = None,
                           resp_fn: Resp_Fn_Sig = default_resp_fn) -> Response:
    """
    Returns a `Flask` response ojbject for a given `arxiv_id` and `FileFormat`.

    The response will include headers and may do a range response.
    """
    arxiv_id_str = f"{archive}/{arxiv_id_str}" if archive else arxiv_id_str
    try:
        if len(arxiv_id_str) > 40:
            abort(400)
        if arxiv_id_str.startswith('arxiv/'):
            abort(400, description="do not prefix non-legacy ids with arxiv/")
        arxiv_id = Identifier(arxiv_id_str)
    except IdentifierException as ex:
        return bad_id(arxiv_id_str, str(ex))

    item = get_article_store().dissemination(file_format, arxiv_id)
    logger. debug(f"dissemination_for_id({arxiv_id.idv}) was {item}")
    if not item or item == "VERSION_NOT_FOUND" or item == "ARTICLE_NOT_FOUND":
        return not_found(arxiv_id)
    elif item == "WITHDRAWN":
        return withdrawn(arxiv_id)
    elif item == "NO_SOURCE":
        return no_source(arxiv_id)
    elif item == "UNAVAILABLE":
        return unavailable(arxiv_id)
    elif item == "NOT_PDF":
        return not_pdf(arxiv_id)
    elif isinstance(item, Deleted):
        return bad_id(arxiv_id.ids, item.msg)
    elif isinstance(item, CannotBuildPdf):
        return cannot_build_pdf(arxiv_id, item.msg)

    file, item_format, docmeta, version = item
    if not file.exists():
        return not_found(arxiv_id)

    return resp_fn(item_format, file, arxiv_id, docmeta, version)


def no_source(arxiv_id: Identifier) -> Response:
    """Response sent when the source is missing.

    This could be either due to an administrative removal of source, which
    isn't an error and should be a 404

    or

    It could be due to a technical problem where the source isn't synced yet.

    This returns a 500 so the technical problem with sync can more easily be
    detected. Later this could be set to a less severe.
    """
    headers = {'Cache-Control': 'max-age=3000'}
    return make_response(render_template("pdf/withdrawn.html",
                                         arxiv_id=arxiv_id),
                         500, headers)


def withdrawn(arxiv_id: Identifier) -> Response:
    """Response sent when the paper version is withdrawn.

    Sets expire to one year since this isn't going to change
    in the future, max allowed by RFC 2616"""
    headers = {'Cache-Control': 'max-age=31536000'}
    return make_response(render_template("pdf/withdrawn.html",
                                         arxiv_id=arxiv_id),
                         200, headers)


def unavailable(arxiv_id: Identifier) -> Response:
    """Response sent when the article and version exists but files cannot be found.

    This is an error since the expected files don't exist. """
    return make_response(render_template("pdf/unavaiable.html",
                                         arxiv_id=arxiv_id), 500, {})


def not_pdf(arxiv_id: Identifier) -> Response:
    """Response when there is no PDF for this paper.

    The client requested a PDF for a paper which has a different format."""
    return make_response(render_template("pdf/unavaiable.html",
                                         arxiv_id=arxiv_id), 404, {})


def not_found(arxiv_id: Identifier) -> Response:
    """Response when the paper or version does not exist."""
    headers = {'Expires': format_datetime(next_publish())}
    return make_response(render_template("pdf/not_found.html",
                                         arxiv_id=arxiv_id), 404, headers)


def not_found_anc(arxiv_id: Identifier) -> Response:
    """Response when an ancillary file does not exist."""
    headers = {'Expires': format_datetime(next_publish())}
    return make_response(render_template("src/anc_not_found.html",
                                         arxiv_id=arxiv_id), 404, headers)


def bad_id(arxiv_id: str, err_msg: str) -> Response:
    """Response when the client requests a bad ID."""
    return make_response(render_template("pdf/bad_id.html",
                                         err_msg=err_msg,
                                         arxiv_id=arxiv_id), 404, {})


def cannot_build_pdf(arxiv_id: Identifier, msg: str) -> Response:
    """Response when the PDF cannot be built.

    These are listed in the REASONS."""
    return make_response(render_template("pdf/cannot_build_pdf.html",
                                         err_msg=msg,
                                         arxiv_id=arxiv_id), 404, {})
