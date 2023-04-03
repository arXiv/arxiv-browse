"""Routes for /src /e-prints and ancillary."""
import logging
from typing import Optional

from arxiv.identifier import Identifier, IdentifierException
from browse.services.documents import get_doc_service
from browse.services.documents.base_documents import (
    AbsNotFoundException, AbsVersionNotFoundException)
from flask import Blueprint, abort, render_template
from opentelemetry import trace

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

blueprint = Blueprint('src', __name__)

tracer = trace.get_tracer(__name__)


def _id_check(arxiv_id: Optional[str], archive:Optional[str]) -> Optional[Identifier]:
    """Checks that the id is valid and that it exists in the metadata as an paper."""
    arxiv_id = f"{archive}/{arxiv_id}" if archive else arxiv_id
    try:
        if arxiv_id is None or len(arxiv_id) > 40:
            abort(400)
        if archive and len(archive) > 20:
            abort(400)
        if arxiv_id.startswith('arxiv/'):
            abort(400, description="do not prefix with arxiv/ for non-legacy ids")
        aid = Identifier(f"{archive}/{arxiv_id}" if archive else arxiv_id)
    except IdentifierException as ex:
        abort(400)

    try:
        # TODO Don't double parse the ID
        metadata = get_doc_service().get_abs(aid.id)
        return metadata
    except (AbsNotFoundException, AbsVersionNotFoundException):
        abort(404)
    abort(500) # not sure, should not get here



@blueprint.route("/src/<string:arxiv_id>")
@blueprint.route("/src/<string:archive>/<int:arxiv_id>")
def src(arxiv_id:str, archive:Optional[str]=None):
    """Serves the source of a requested paper as a tar.gz.

     /src/id - tar.gz of whole source package

    /src/id/file - Returns just the specified file within the source package. Has
    meaning only for .tar.gz packages and will most frequently be used to access
    ancillary files such as /src/anc/some_file
    """
    mdata = _id_check(arxiv_id, archive)

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


    return render_template("debug.html", data= aid), 200, {}

    # result = get_doc_se
    # result = get_article_store().get_source(aid)
    #if result == "


@blueprint.route("/src/<string:arxiv_id>/anc", strict_slashes=False)
@blueprint.route("/src/<string:archive>/<int:old_id>/anc", strict_slashes=False)
def anc_listing(arxiv_id: Optional[str]=None, old_id:Optional[str]=None, archive:str='arxiv'):
    """Show html page of ancillary files for arxiv_id."""
    pass     # TODO


@blueprint.route("/src/<string:arxiv_id>/<string:file>")
@blueprint.route("/src/<string:archive>/<int:old_id>/<string:file>")
def anc(file: str, arxiv_id: Optional[str]=None, old_id:Optional[str]=None, archive:str='arxiv'):
    """Serves ancillary files.

    Returns just the specified file within the source package. Has
    meaning only for .tar.gz packages and will most frequently be used to access
    ancillary files such as /src/anc/some_file
    """
    pass     # TODO

@blueprint.route("/e-print/<string:arxiv_id>")
@blueprint.route("/e-print/<string:archive>/<int:old_id>")
def e_prints(arxiv_id: Identifier):
    """Serves source package in form that we store it (.tar.gz, .pdf, etc.)"""
    pass     # TODO
