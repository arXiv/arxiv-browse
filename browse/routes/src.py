"""Routes for serving the source of articles. /src /e-prints and ancillary."""
import logging
from typing import Optional

from browse.controllers.files.dissemination import (get_dissemination_resp,
                                              get_src_resp)
from browse.controllers.files.ancillary_files import get_extracted_src_file_resp
from browse.services.dissemination import get_article_store
from browse.services.documents import get_doc_service
from flask import Blueprint, render_template
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
        return render_template("src/listing.html", **data), 200, {}
    else:
        return render_template("src/listing_none.html", **data), 404, {}


@blueprint.route("/src/<path:arxiv_id>/anc/<path:file_path>")
def anc(arxiv_id: str, file_path:str):  # type: ignore
    """Serves ancillary files or show html page of ancillary files

    Returns just the specified file within the source package. Has
    meaning only for .tar.gz packages and will most frequently be used to access
    ancillary files such as /src/anc/some_file

    ex https://arxiv.org/src/1911.08265v1/anc
    ex https://arxiv.org/src/1911.08265v1/anc/pseudocode.py
    """
    return get_extracted_src_file_resp(arxiv_id, f"anc/{file_path}", 'anc')


@blueprint.route("/e-print/<string:arxiv_id_str>")
@blueprint.route("/e-print/<string:archive>/<string:arxiv_id_str>")
@blueprint.route("/src/<string:arxiv_id_str>")
@blueprint.route("/src/<string:archive>/<string:arxiv_id_str>")
def src(arxiv_id_str: str, archive: Optional[str]=None):  # type: ignore
    """Serves the source of a requested paper.

    This serves it in the original format submitted. Before 2024 it would .tar up
    single file submissions.

    The e-print path serves the source of a requested paper as original format submitted and
    form that we store it (.tar.gz, .pdf, etc.). It is used to support the mirrors.
    Before 2024 /src behavior was different than /e-print.
     """
    return get_src_resp(arxiv_id_str, archive)


# TODO need test data for src_format ps
# tests/data/abs_files/orig/cond-mat/papers/9805/9805021v1.ps.gz


# TODO need test data for src_format html
# TODO need test data for src_format tex
# TODO need test data for src_format pdftex
# TODO need test data for src_format docx
# TODO need test data for src_format odf
# TODO need test data for is_single_file (1)
# TODO need test data for src_format is_encrypted (S)
# TODO need test data for src_format has_ancillary_files (A)
# ex. https://arxiv.org/src/1911.08265v1/anc/pseudocode.py
# TODO need test data for src_format has_pilot_data (B)

# TODO need to do /src/id/file
