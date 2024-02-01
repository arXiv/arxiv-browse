"""Routes for PDF, source and other downloads."""
from typing import Optional
from flask import Blueprint, redirect, url_for, Response, render_template, request
from werkzeug.exceptions import InternalServerError, BadRequest

from browse.services.documents import get_doc_service
from browse.services.dissemination import get_article_store
from browse.domain.identifier import Identifier, IdentifierException
from browse.domain import fileformat
from browse.controllers.files.dissemination import get_dissemination_resp, get_html_response
from browse.controllers import check_supplied_identifier


blueprint = Blueprint('dissemination', __name__)


@blueprint.route("/pdf/<string:archive>/<string:arxiv_id>.pdf", methods=['GET', 'HEAD'])
@blueprint.route("/pdf/<string:arxiv_id>.pdf", methods=['GET', 'HEAD'])
def redirect_pdf(arxiv_id: str, archive=None):  # type: ignore
    """Redirect urls with .pdf

     There was a period from 2022 to 2024 where PDF were sometimes redirected to {paper_id}.pdf
     so they would download a filename recognized as a PDF. Then Content-Disposition with inline was used instead."""
    arxiv_id = f"{archive}/{arxiv_id}" if archive else arxiv_id
    return redirect(url_for('.pdf', arxiv_id=arxiv_id, _external=True), 301)


@blueprint.route("/pdf/<string:archive>/<string:arxiv_id>", methods=['GET', 'HEAD'])
@blueprint.route("/pdf/<string:arxiv_id>", methods=['GET', 'HEAD'])
def pdf(arxiv_id: str, archive=None):  # type: ignore
    """Want to handle the following patterns:

        /pdf/{archive}/{id}v{v}
        /pdf/{id}v{v}

    The dissemination service does not handle versionless requests. The version should be figured out in some
    other service and redirected.

    Serve these from storage bucket URLs like:

    gs://arxiv-production-data/ps_cache/acc-phys/pdf/9502/9502001v1.pdf

    Does a 400 if the ID is malformed or lacks a version.

    Does a 404 if the key for the ID does not exist on the bucket.
    """
    return get_dissemination_resp(fileformat.pdf, arxiv_id, archive)


@blueprint.route("/format/<string:archive>/<string:arxiv_id>", methods=['GET', 'HEAD'])
@blueprint.route("/format/<string:arxiv_id>", methods=['GET', 'HEAD'])
def format(arxiv_id: str, archive: Optional[str] = None) -> Response:
    """Get formats article."""
    arxiv_id = f"{archive}/{arxiv_id}" if archive else arxiv_id
    try:
        arxiv_identifier = Identifier(arxiv_id=arxiv_id)
    except IdentifierException:
        raise BadRequest("Bad paper identifier")

    redirect = check_supplied_identifier(arxiv_identifier, "dissemination.format")
    if redirect:
        return redirect  # type: ignore

    abs_meta = get_doc_service().get_abs(arxiv_id)
    data = {"arxiv_id": arxiv_identifier.id,
            "arxiv_idv": arxiv_identifier.idv,
            "abs_meta": abs_meta}

    formats = get_article_store().get_all_paper_formats(abs_meta)
    data["formats"] = formats
    for fmt in formats:
        data[fmt] = True

    # The formats from get_dissemination_formats don't do exactly what is needed
    # for the format.html tempalte.
    # TODO what about source?
    # TODO how to disginguish the different ps?
    # TODO DOCX doesn't seem like the url_for in the tempalte will work correctly with the .docx?

    return render_template("format.html", **data), 200, {}  # type: ignore


@blueprint.route("/dvi/<string:archive>/<string:arxiv_id>", methods=['GET', 'HEAD'])
@blueprint.route("/dvi/<string:arxiv_id>", methods=['GET', 'HEAD'])
def dvi(arxiv_id: str) -> Response:
    """Get DVI for article."""
    raise InternalServerError(f"Not yet implemented {arxiv_id}")

@blueprint.route("/html/<string:arxiv_id>", methods=['GET', 'HEAD'])
@blueprint.route("/html/<string:archive>/<path:arxiv_id>", methods=['GET', 'HEAD'])
def html(arxiv_id: str, archive=None):  # type: ignore
    """get html for article"""
    return get_html_response(arxiv_id,archive)


@blueprint.route("/ps/<arxiv_id>")
def ps(arxiv_id: str) -> Response:
    """Get ps for article."""
    raise InternalServerError(f"Not yet implemented {arxiv_id}")
