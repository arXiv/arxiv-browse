"""Controller for PDF, source and other downloads."""

import logging
from email.utils import format_datetime
from typing import Callable, Optional
from datetime import timezone

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

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


Resp_Fn_Sig = Callable[[FileFormat, FileObj, Identifier, DocMetadata, VersionEntry],
                       Response]


def default_resp_fn(format: FileFormat,
                    file: FileObj,
                    arxiv_id: Identifier,
                    docmeta: DocMetadata,
                    version: VersionEntry) -> Response:
    """Creates a response with approprate headers for the `file`.

    Parameters
    ----------
    format : FileFormat
        `FileFormat` of the `file`
    item : DocMetadata
        article that the response is for.
    file : FileObj
        File object to use in the response.
    """

    # Have to do Range Requests to get GCP CDN to accept larger objects.
    resp: Response = RangeRequest(file.open('rb'),
                                  etag=_last_modified(file),
                                  last_modified=file.updated,
                                  size=file.size).make_response()

    resp.headers['Access-Control-Allow-Origin'] = '*'
    if isinstance(format, FileFormat):
        resp.headers['Content-Type'] = format.content_type

    if resp.status_code == 200:
        # For large files on CloudRun chunked and no content-length needed
        # TODO revisit this, in some cases it doesn't work maybe when
        # combined with gzip encoding?
        #resp.headers['Transfer-Encoding'] = 'chunked'
        resp.headers.pop('Content-Length')

    _add_time_headers(resp, file, arxiv_id)
    return resp


def src_resp_fn(format: FileFormat,
                file: FileObj,
                arxiv_id: Identifier,
                docmeta: DocMetadata,
                version: VersionEntry) -> Response:
    """Prepares a response where the payload will be a tar of the source.

    No matter what the actual format of the source, this will try to return a
    .tar.  If the source is a .pdf then that will be tarred. If the source is a
    gzipped PS file, that will be ungzipped and then tarred.

    This will also uses gzipped transfer encoding. But the client will unencode
    the bytestream and the file will be saved as .tar.
    """
    if file.name.endswith(".tar.gz"):  # Nothing extra to do, already .tar.gz
        outstream = file
    elif file.name.endswith(".gz"):  # need to unzip the single file gz and then tar
        outstream = tar_stream_gen([UngzippedFileObj(file)])  # type: ignore
    else:  # tar single flie like .pdf
        outstream = tar_stream_gen([file])   # type: ignore

    archive = f"{arxiv_id.archive}-" if arxiv_id.is_old_id else ""
    filename = f"arXiv-{archive}{arxiv_id.filename}v{version.version}.tar"

    resp = make_response(outstream, 200)
    resp.headers["Content-Encoding"] = "x-gzip"  # tar_stream_gen() gzips
    resp.headers["Content-Type"] = "application/x-eprint-tar"
    resp.headers["Content-Disposition"] = f"attachment; filename=\"{filename}\""

    _add_time_headers(resp, file, arxiv_id)
    resp.headers["ETag"] = _last_modified(file)

    return resp


def get_src_resp(arxiv_id_str: str,
                 archive: Optional[str] = None) -> Response:
    return get_dissimination_resp("e-print", arxiv_id_str, archive, src_resp_fn)


def get_e_print_resp(arxiv_id_str: str,
                     archive: Optional[str] = None) -> Response:
    return get_dissimination_resp("e-print", arxiv_id_str, archive)


def get_dissimination_resp(format: Acceptable_Format_Requests,
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

    item = get_article_store().dissemination(format, arxiv_id)
    logger. debug(f"dissemination_for_id({arxiv_id.idv}) was {item}")
    if not item or item == "VERSION_NOT_FOUND" or item == "ARTICLE_NOT_FOUND":
        return not_found(arxiv_id)
    elif item == "WITHDRAWN" or item == "NO_SOURCE":
        return withdrawn(arxiv_id)
    elif item == "UNAVAIABLE":
        return unavailable(arxiv_id)
    elif item == "NOT_PDF":
        return not_pdf(arxiv_id)
    elif isinstance(item, Deleted):
        return bad_id(arxiv_id, item.msg)
    elif isinstance(item, CannotBuildPdf):
        return cannot_build_pdf(arxiv_id, item.msg)

    file, item_format, docmeta, version = item
    if not file.exists():
        return not_found(arxiv_id)

    return resp_fn(item_format, file, arxiv_id, docmeta, version)


def _cc_versioned() -> str:
    """Versioned pdfs should not change so let's put a time a bit in the future.

    Non versioned could change during the next publish.

    This could cause a version to stay in a CDN on a delete. That might require
    manual cache invalidation.

    """
    return 'max-age=604800'  # 7 days


def withdrawn(arxiv_id: str) -> Response:
    """Sets expire to one year, max allowed by RFC 2616"""
    headers = {'Cache-Control': 'max-age=31536000'}
    return make_response(render_template("pdf/withdrawn.html",
                                         arxiv_id=arxiv_id),
                         200, headers)


def unavailable(arxiv_id: str) -> Response:
    return make_response(render_template("pdf/unavaiable.html",
                                         arxiv_id=arxiv_id), 500, {})


def not_pdf(arxiv_id: str) -> Response:
    return make_response(render_template("pdf/unavaiable.html",
                                         arxiv_id=arxiv_id), 404, {})


def not_found(arxiv_id: str) -> Response:
    headers = {'Expires': format_datetime(next_publish())}
    return make_response(render_template("pdf/not_found.html",
                                         arxiv_id=arxiv_id), 404, headers)


def bad_id(arxiv_id: str, err_msg: str) -> Response:
    return make_response(render_template("pdf/bad_id.html",
                                         err_msg=err_msg,
                                         arxiv_id=arxiv_id), 404, {})


def cannot_build_pdf(arxiv_id: str, msg: str) -> Response:
    return make_response(render_template("pdf/cannot_build_pdf.html",
                                         err_msg=msg,
                                         arxiv_id=arxiv_id), 404, {})


def _add_time_headers(resp: Response, file: FileObj, arxiv_id: Identifier) -> None:
    resp.headers["Last-Modified"] = _last_modified(file)
    if arxiv_id.has_version:
        resp.headers['Cache-Control'] = _cc_versioned()
    else:
        resp.headers['Expires'] = format_datetime(next_publish())


def _last_modified(fileobj: FileObj) -> str:
    return format_datetime(fileobj.updated.astimezone(timezone.utc),
                           usegmt=True)
