"""Routes for PDF, source and other downloads."""
from typing import Optional, Dict
from flask import Blueprint, redirect, url_for, Response, render_template, request
from werkzeug.exceptions import InternalServerError, BadRequest

from browse.services.documents import get_doc_service
from arxiv.identifier import Identifier, IdentifierException
from arxiv.files import fileformat
from arxiv.integration.fastly.headers import add_surrogate_key

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
        raise BadRequest(f"Bad paper identifier: {arxiv_id}")

    redirect = check_supplied_identifier(arxiv_identifier, "dissemination.format")
    if redirect:
        return redirect  # type: ignore

    abs_meta = get_doc_service().get_abs(arxiv_id)
    data = {"arxiv_id": arxiv_identifier.id,
            "arxiv_idv": arxiv_identifier.idv,
            "abs_meta": abs_meta}
    data["encrypted"] = abs_meta.version_history[abs_meta.version - 1].source_flag.source_encrypted

    formats = data["formats"] = abs_meta.get_requested_version().formats()
    for fmt in formats:
        data[fmt] = True
    # TODO DOCX doesn't seem like the url_for in the template will work correctly with the .docx?
    headers: Dict[str,str]={}
    headers=add_surrogate_key(headers,["format", f"paper-id-{arxiv_identifier.id}"])
    if arxiv_identifier.has_version: 
        headers=add_surrogate_key(headers,["format-versioned"])
    else:
        headers=add_surrogate_key(headers,["format-unversioned"])
    return render_template("format.html", **data), 200, headers # type: ignore


@blueprint.route("/dvi/<string:archive>/<string:arxiv_id>", methods=['GET', 'HEAD'])
@blueprint.route("/dvi/<string:arxiv_id>", methods=['GET', 'HEAD'])
def dvi(arxiv_id: str) -> Response:
    """Get DVI for article."""
    raise InternalServerError(f"Not yet implemented {arxiv_id}")

@blueprint.route("/html/<string:arxiv_id>", methods=['GET', 'HEAD'])
@blueprint.route("/html/<string:archive>/<path:arxiv_id>", methods=['GET', 'HEAD'])
@blueprint.route("/html/<string:arxiv_id>/", methods=['GET', 'HEAD'])
def html(arxiv_id: str, archive=None):  # type: ignore
    """get html for article"""
    return get_html_response(arxiv_id,archive)


@blueprint.route("/ps/<arxiv_id>")
def ps(arxiv_id: str) -> Response:
    """Get ps for article."""
    raise InternalServerError(f"Not yet implemented {arxiv_id}")
