"""Routes for serving the source of articles.

/src serves the source; the legacy /e-print path permanently redirects to it.
Also serves ancillary files.
"""
import logging
from typing import Optional

from arxiv.identifier import Identifier, IdentifierException
from browse import b_add_surrogate_key

from browse.controllers.files import maxage
from browse.controllers.files.dissemination import get_src_resp
from browse.controllers.files.ancillary_files import get_extracted_src_file_resp
from browse.services.dissemination import get_article_store
from browse.services.documents import get_doc_service
from flask import Blueprint, Response, make_response, redirect, render_template, url_for
from opentelemetry import trace

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

blueprint = Blueprint('src', __name__)

tracer = trace.get_tracer(__name__)


@blueprint.route("/src/<path:arxiv_id>/anc")
def anc_listing(arxiv_id: str):  #type: ignore
    """Serves listing of ancillary files for a paper."""
    data: dict = {}
    docmeta = get_doc_service().get_abs(arxiv_id)
    data['abs_meta'] = docmeta
    data['arxiv_id'] = docmeta.arxiv_identifier
    data['anc_file_list'] = get_article_store().get_ancillary_files(docmeta)

    if data['anc_file_list']:
        resp=make_response(render_template("src/listing.html", **data))
        _src_surrogate_keys(resp, arxiv_id, True)
        return resp
    else:
        resp=make_response(render_template("src/listing_none.html", **data))
        _src_surrogate_keys(resp, arxiv_id, True)
        resp.status_code=404
        return resp


@blueprint.route("/src/<path:arxiv_id>/anc/<path:file_path>")
def anc(arxiv_id: str, file_path:str):  # type: ignore
    """Serves ancillary files or show html page of ancillary files

    Returns just the specified file within the source package. Has
    meaning only for .tar.gz packages and will most frequently be used to access
    ancillary files such as /src/anc/some_file

    ex https://arxiv.org/src/1911.08265v1/anc
    ex https://arxiv.org/src/1911.08265v1/anc/pseudocode.py
    """
    resp=get_extracted_src_file_resp(arxiv_id, f"anc/{file_path}", 'anc')
    _src_surrogate_keys(resp, arxiv_id, True)
    return resp


@blueprint.route("/e-print/<string:arxiv_id_str>")
@blueprint.route("/e-print/<string:archive>/<string:arxiv_id_str>")
def e_print(arxiv_id_str: str, archive: Optional[str]=None):  # type: ignore
    """Permanently redirect legacy /e-print URLs to the canonical /src URL.

    /e-print and /src are the same handler and return byte-identical source
    packages -- before 2024 they differed, but they no longer do. Serving the
    source under two URLs makes crawlers download the (often large) source twice
    and makes the CDN cache it under two keys. Collapsing /e-print onto /src with
    a permanent, edge-cacheable 301 lets Fastly absorb repeat /e-print hits and
    lets crawlers dedupe to a single canonical URL, cutting origin egress.
    Mirrors and other redirect-following clients are unaffected: they follow the
    301 to /src and get the same bytes.

    The redirect itself never depends on the paper's content (it always points at
    /src/<same id>), so it is cached for a long time and carries a single static
    surrogate key for bulk purge should the policy ever be reversed.
    """
    resp=redirect(url_for(".src", arxiv_id_str=arxiv_id_str, archive=archive), 301)
    resp.headers["Surrogate-Control"]=maxage()
    resp.headers=b_add_surrogate_key(resp.headers, ["e-print-redirect"])
    return resp


@blueprint.route("/src/<string:arxiv_id_str>")
@blueprint.route("/src/<string:archive>/<string:arxiv_id_str>")
def src(arxiv_id_str: str, archive: Optional[str]=None):  # type: ignore
    """Serves the source of a requested paper.

    This serves it in the original format submitted and the form that we store it
    in (.tar.gz, .pdf, etc.). Before 2024 it would .tar up single file
    submissions. The legacy /e-print path (used to support the mirrors) now
    permanently redirects here; see `e_print`.
     """
    resp=get_src_resp(arxiv_id_str, archive) #always adds a verion onto the id
    _src_surrogate_keys(resp, arxiv_id_str)
    return resp


def _src_surrogate_keys(resp: Response, arxiv_id_str: str, anc:bool=False) -> None:
    resp.headers=b_add_surrogate_key(resp.headers,["src"])
    if _check_id_for_version(arxiv_id_str):
        resp.headers=b_add_surrogate_key(resp.headers,[f"src-{arxiv_id_str}",
                                                     f"paper-id-{arxiv_id_str}"])
    else:
        resp.headers=b_add_surrogate_key(resp.headers,[f"src-{arxiv_id_str}-current",
                                                     f"paper-id-{arxiv_id_str}-current"])

    if anc:
        resp.headers=b_add_surrogate_key(resp.headers,["anc"])
        if _check_id_for_version(arxiv_id_str):
            resp.headers=b_add_surrogate_key(resp.headers,[f"anc-{arxiv_id_str}"])
        else:
            resp.headers=b_add_surrogate_key(resp.headers,[f"anc-{arxiv_id_str}-current"])


def _check_id_for_version(arxiv_id_str:str) -> bool:
    """returns true if the url was asking for a specific paper version, false otherwise"""
    try:
        arxiv_id= Identifier(arxiv_id_str)
        if arxiv_id.has_version:
            return True
        else:
            return False
    except IdentifierException:
        return False
