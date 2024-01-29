"""Controller to download a ancillary file from a .tar.gz"""

import logging
from email.utils import format_datetime
from typing import Literal

import flask_rangerequest
from flask import Response, abort, make_response, render_template
from flask_rangerequest import RangeRequest

from browse.domain.identifier import Identifier, IdentifierException
from browse.services.dissemination import get_article_store
from browse.services.dissemination.article_store import Deleted
from browse.services.documents import get_doc_service
from browse.services.next_published import next_publish
from browse.services.object_store import FileObj
from browse.services.object_store.fileobj import FileFromTar

from . import last_modified, add_time_headers, cc_versioned, stream_gen, add_mimetype

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


def get_extracted_src_file_resp(arxiv_id_str: str,
                                path: str,
                                mode: Literal['html', 'anc']
                                ) -> Response:
    try:
        if len(arxiv_id_str) > 1024:
            abort(400)
        if arxiv_id_str.startswith('arxiv/'):
            abort(400, description="do not prefix non-legacy ids with arxiv/")
        arxiv_id = Identifier(arxiv_id_str)
    except IdentifierException as ex:
        return make_response(render_template("dissemination/bad_id.html",
                                             err_msg=str(ex),
                                             arxiv_id=arxiv_id_str), 404, {})

    if not path:
        abort(400, description="Must pass path part")
    if mode == 'anc' and not path.startswith("anc/"):
        abort(400, description="Invalid path for ancillary file")

    # todo handle exceptions
    doc = get_doc_service().get_abs(arxiv_id)

    if arxiv_id.has_version:
        nf_headers = {'Cache-Control': cc_versioned()}
    else:
        nf_headers = {'Expires': format_datetime(next_publish())}

    ver = doc.get_version()
    if mode == 'anc' and ver is not None \
       and not ver.source_flag.includes_ancillary_files:
        return make_response(
            render_template("src/anc_not_found.html",
                            reason=f"No ancillary files for {arxiv_id.idv}"),
            404, nf_headers)

    dis_res = get_article_store().dissemination('e-print', arxiv_id, doc)

    if dis_res == "ARTICLE_NOT_FOUND" or dis_res == "VERSION_NOT_FOUND" \
       or dis_res == "WITHDRAWN" or dis_res == "NO_SOURCE" \
       or isinstance(dis_res, Deleted):
        # TODO better error handling
        abort(404, description="not found")

    if not isinstance(dis_res, tuple) or not isinstance(dis_res[0], FileObj):
        abort(500, description="Unexpected result for source")

    src_file: FileObj = dis_res[0]
    tarmember = FileFromTar(src_file, path)
    if not tarmember.exists():
        return make_response(
            render_template("src/anc_not_found.html",
                            reason=f"File not in ancillary files for {arxiv_id.idv}"),
            404, nf_headers)

    """RangeRequest does a seek and that seems odd with gzip and tarfile but both of
    those support seek."""
    resp: Response = RangeRequest(
            data=tarmember.open("rb"),  # RangeRequest and flask are expected to call `close()`
            etag=last_modified(src_file),
            last_modified=src_file.updated,
            size=tarmember.size
    ).make_response()

    add_mimetype(resp, tarmember.name)
    add_time_headers(resp, src_file, arxiv_id)
    return resp
