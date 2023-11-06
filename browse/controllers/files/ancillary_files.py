"""Controller to download a ancillary file from a .tar.gz"""

import logging
from email.utils import format_datetime
from typing import Literal

from flask import Response, abort, make_response, render_template

from browse.domain.identifier import Identifier, IdentifierException
from browse.services.dissemination import get_article_store
from browse.services.dissemination.article_store import Deleted
from browse.services.documents import get_doc_service
from browse.services.next_published import next_publish
from browse.services.object_store import FileObj
from browse.services.object_store.fileobj import FileFromTar

from . import last_modified, add_time_headers, cc_versioned, stream_gen
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
        return make_response(render_template("pdf/bad_id.html",
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
       and not ver.source_type.includes_ancillary_files:
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

    if not isinstance(dis_res, tuple):
        abort(500, description="Unexpected result for source")

    src_file = dis_res[0]
    tarmember = FileFromTar(src_file, path)
    if not tarmember.exists():
        return make_response(
            render_template("src/anc_not_found.html",
                            reason=f"File not in ancillary files for {arxiv_id.idv}"),
            404, nf_headers)

    resp = make_response(stream_gen(tarmember), 200)
    # TODO guess Content-Type from file name?
    # resp.headers["Content-Type"] = "application/x-eprint-tar"
    add_time_headers(resp, src_file, arxiv_id)
    resp.headers["ETag"] = last_modified(src_file)
    return resp
