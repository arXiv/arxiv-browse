"""Routes for /src /e-prints and ancillary."""
import logging
from typing import Optional
from email.utils import format_datetime

from flask import Blueprint, abort, render_template
from flask_rangerequest import RangeRequest

from opentelemetry import trace

from arxiv.identifier import Identifier, IdentifierException
from browse.services.documents import get_doc_service
from browse.services.documents.base_documents import (
    AbsNotFoundException, AbsVersionNotFoundException)
from browse.services.dissemination import get_source_store
from browse.services.next_published import next_publish

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

blueprint = Blueprint('src', __name__)

tracer = trace.get_tracer(__name__)


def _id_check(arxiv_id: Optional[str], archive: Optional[str]) -> Optional[Identifier]:
    """Checks that the id is valid and that it exists in the metadata as an
    paper."""
    arxiv_id = f"{archive}/{arxiv_id}" if archive else arxiv_id
    try:
        if arxiv_id is None or len(arxiv_id) > 40:
            abort(400)
        if archive and len(archive) > 20:
            abort(400)
        if arxiv_id.startswith('arxiv/'):
            abort(400, description="do not prefix with arxiv/ for non-legacy ids")
        aid = Identifier(f"{archive}/{arxiv_id}" if archive else arxiv_id)
    except IdentifierException:
        abort(400)

    try:
        metadata = get_doc_service().get_abs(aid.id)
        return metadata
    except (AbsNotFoundException, AbsVersionNotFoundException):
        abort(404)


@blueprint.route("/src/<string:arxiv_id>")
@blueprint.route("/src/<string:archive>/<int:arxiv_id>")
def src(arxiv_id: str, archive: Optional[str]=None):  # type: ignore
    """Serves the source of a requested paper as a tar.gz.

    /src/id - tar.gz of whole source package

    /src/id/file - Returns just the specified file within the source package. Has
    meaning only for .tar.gz packages and will most frequently be used to access
    ancillary files such as /src/anc/some_file
    """
    doc = _id_check(arxiv_id, archive)
    if not doc:
        abort(404)

    # TODO need test data for src_format pdf
    # 2101.04792 v1-4

    # TODO need test data for src_format ps

    # TODO need test data for src_format html
    # TODO need test data for src_format tex
    # TODO need test data for src_format pdftex
    # TODO need test data for src_format docx
    # TODO need test data for src_format odf
    # TODO need test data for is_single_file (1)
    # TODO need test data for src_format is_encrypted (S)
    # TODO need test data for src_format has_ancillary_files (A)
    # TODO need test data for src_format has_pilot_data (B)

    # TODO need to do /src/id/file

    file = get_source_store().get_src(doc.arxiv_identifier, doc)
    if not file:
        abort(404)
    format = get_source_store().get_src_format(doc, file)

    resp = RangeRequest(file.open('rb'),
                        etag=file.etag,
                        last_modified=file.updated,
                        size=file.size).make_response()

    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Content-Type'] = format.content_type

    if resp.status_code == 200:
        # To do Large PDFs on Cloud Run both chunked and no content-length are needed
        resp.headers['Transfer-Encoding'] = 'chunked'
        resp.headers.pop('Content-Length')

    if doc.arxiv_identifier.has_version:
        resp.headers['Cache-Control'] = _cc_versioned()
    else:
        resp.headers['Expires'] = format_datetime(next_publish())
    return resp


@blueprint.route("/src/<string:arxiv_id>/anc", strict_slashes=False)
@blueprint.route("/src/<string:archive>/<int:old_id>/anc", strict_slashes=False)
def anc_listing(arxiv_id: Optional[str]=None, old_id:Optional[str]=None, archive:str='arxiv'):  # type: ignore
    """Show html page of ancillary files for arxiv_id."""
    pass     # TODO


@blueprint.route("/src/<string:arxiv_id>/<string:file>")
@blueprint.route("/src/<string:archive>/<int:old_id>/<string:file>")
def anc(file: str, arxiv_id: Optional[str]=None, old_id:Optional[str]=None, archive:str='arxiv'):  # type: ignore
    """Serves ancillary files.

    Returns just the specified file within the source package. Has
    meaning only for .tar.gz packages and will most frequently be used to access
    ancillary files such as /src/anc/some_file
    """
    pass     # TODO

@blueprint.route("/e-print/<string:arxiv_id>")
@blueprint.route("/e-print/<string:archive>/<int:old_id>")
def e_prints(arxiv_id: Identifier):  # type: ignore
    """Serves source package in form that we store it (.tar.gz, .pdf, etc.)"""
    pass     # TODO


def _cc_versioned():  # type: ignore
    """Versioned pdfs should not change so let's put a time a bit in the future.
    Non versioned could change during the next publish."""
    return 'max-age=604800' # 7 days
