"""Routes for PDF, source and other downloads."""
from typing import Optional
from flask import Blueprint, redirect, url_for, Response, render_template, request
from werkzeug.exceptions import InternalServerError, BadRequest

from browse.services.documents import get_doc_service
from browse.services.dissemination import get_article_store
from browse.domain.identifier import Identifier, IdentifierException
from browse.domain import fileformat
from browse.controllers.files.dissemination import get_dissemination_resp, get_html_response, get_pdf_resp
from browse.controllers import check_supplied_identifier


blueprint = Blueprint('dissemination', __name__)


@blueprint.route("/pdf/<string:archive>/<string:arxiv_id>.pdf", methods=['GET', 'HEAD'])
@blueprint.route("/pdf/<string:arxiv_id>.pdf", methods=['GET', 'HEAD'])
def redirect_pdf(arxiv_id: str, archive=None):  # type: ignore
    """Redirect URLs with .pdf to a URL without.

    In past a redirect from /pdf/paperid to /pdf/paperid.pdf was used to cause
    the browser to download the file with the .pdf extension. This is to support
    any user who has bookmarked or saved a PDF URL with the .pdf extension in
    the past so they will get a redirect to the "normal" PDF URL. I think we
    started using the redirect because of an ignorance of the "inline" mode of
    the content-disposition header.

    Now a content-disposition is used. It is a standard mechanism that is part
    of HTTP to provide a way for the server to specify what the file name should
    be on download.

    The content-disposition preservers the "if I download this to my computer,
    save it in a file named {paper_id}.pdf" behavior, and it does that in a
    direct and standard way. It also eliminates the redirect, which is wasteful
    and only indirectly communicates the download file name.

    """
    arxiv_id = f"{archive}/{arxiv_id}" if archive else arxiv_id
    return redirect(url_for('.pdf', arxiv_id=arxiv_id, _external=True), 301)


@blueprint.route("/pdf/<string:archive>/<string:arxiv_id>", methods=['GET', 'HEAD'])
@blueprint.route("/pdf/<string:arxiv_id>", methods=['GET', 'HEAD'])
def pdf(arxiv_id: str, archive=None):  # type: ignore
    """Want to handle the following patterns:

        /pdf/{archive}/{id}v{v}
        /pdf/{id}v{v}

    The dissemination service does not handle versionless
    requests. The version should be figured out in some other service
    and redirected to the CDN.

    Does a 400 if the ID is malformed or lacks a version.

    Does a 404 if the key for the ID does not exist on the bucket.
    """
    return get_pdf_resp(arxiv_id, archive)

@blueprint.route("/pdf_test/<string:archive>/<string:arxiv_id>.pdf", methods=['GET', 'HEAD'])
@blueprint.route("/pdf_test/<string:arxiv_id>.pdf", methods=['GET', 'HEAD'])
def pdf_test(arxiv_id: str, archive=None):  # type: ignore
    """Path to test pdf via fastly.

    Can be removed when no longer needed."""
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
