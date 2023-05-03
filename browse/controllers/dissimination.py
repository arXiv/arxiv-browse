"""Controller for PDF, source and other downloads."""
import logging
from email.utils import format_datetime
from typing import Callable, Optional

from arxiv.identifier import Identifier, IdentifierException
from browse.domain.fileformat import FileFormat
from browse.services.dissemination import get_article_store
from browse.services.dissemination.article_store import (
    Acceptable_Format_Requests, CannotBuildPdf, Deleted)
from browse.services.dissemination.fileobj import FileObj
from browse.services.dissemination.next_published import next_publish
from browse.stream.tarstream import tar_stream_gen
from flask import Blueprint, Response, abort, make_response, render_template
from flask_rangerequest import RangeRequest

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

blueprint = Blueprint('dissemination', __name__)


def default_resp_fn(format: FileFormat, file: FileObj, arxiv_id: Identifier) -> Response:
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
                                  etag=file.etag,
                                  last_modified=file.updated,
                                  size=file.size).make_response()

    resp.headers['Access-Control-Allow-Origin'] = '*'
    if isinstance(format, FileFormat):
        resp.headers['Content-Type'] = format.content_type

    if resp.status_code == 200:
        # To do Large PDFs on Cloud Run both chunked and no content-length are needed
        resp.headers['Transfer-Encoding'] = 'chunked'
        resp.headers.pop('Content-Length')

    if arxiv_id.has_version:
        resp.headers['Cache-Control'] = _cc_versioned()
    else:
        resp.headers['Expires'] = format_datetime(next_publish())
    return resp


def src_resp_fn(format: FileFormat, file: FileObj, arxiv_id: Identifier) -> Response:
    """Prepares a response where the payload will be a tar.gz of the source."""
    if file.name.endswith(".tar.gz"):  # Nothing extra to do, already .tar.gz
        return default_resp_fn(format, file, arxiv_id)

    if file.name.endswith(".gz"):
        def tgen():  # type: ignore
            raise Exception("Not yet implemented")
    else:
        filename = "fakefilename.txt"
        def tgen():  # type: ignore
            tsg = tar_stream_gen([])

    return make_response(tgen(), {
        "Content-Encoding": "x-gzip",
        "Content-Type": "application/x-eprint-tar",
        "Content-Disposition": "attachment; filename=\"{filename}\"",
    })



    #     #     with gzip.open(file) as stream_in:

    # out_stream = io.BytesIO()
    # with tarfile.open(fileobj=out_stream, mode='w|gz') as out_stream:
    #     # if file.name.endswith(".gz"):
    #     #     with gzip.open(file) as stream_in:

    #     else:
    #         with open(file, 'rb'):


Resp_Fn_Sig = Callable[[FileFormat, FileObj, Identifier], Response]

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
            abort(400, description="do not prefix with arxiv/ for non-legacy ids")
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

    file, item_format = item
    if not file.exists():
        return not_found(arxiv_id)
    return resp_fn(item_format, file, arxiv_id)


def _cc_versioned() -> str:
    """Versioned pdfs should not change so let's put a time a bit in the future.
    Non versioned could change during the next publish."""
    return 'max-age=604800'  # 7 days


def withdrawn(arxiv_id: str) -> Response:
    # one year, max allowed by RFC 2616
    headers = {'Cache-Cache': 'max-age=31536000'}
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
