"""Routes for PDF, source and other downloads."""
from typing import Optional
from flask import Blueprint, redirect, url_for, Response, render_template, request, current_app, make_response
from werkzeug.exceptions import InternalServerError, BadRequest

from browse.services.documents import get_doc_service
from browse.services.dissemination import get_article_store

# Temporary imports before moving over to controller
from browse.services.object_store.object_store_gs import GsObjectStore
from browse.services.object_store.fileobj import UngzippedFileObj, FileFromTar
from browse.controllers.files import stream_gen

from browse.domain.identifier import Identifier, IdentifierException
from browse.domain import fileformat
from browse.controllers.files.dissimination import get_dissimination_resp
from browse.controllers import check_supplied_identifier


blueprint = Blueprint('dissemination', __name__)


@blueprint.route("/pdf/<string:archive>/<string:arxiv_id>", methods=['GET', 'HEAD'])
@blueprint.route("/pdf/<string:arxiv_id>", methods=['GET', 'HEAD'])
def redirect_pdf(arxiv_id: str, archive=None):  # type: ignore
    """Redirect urls without .pdf so they download a filename recognized as a PDF."""
    arxiv_id = f"{archive}/{arxiv_id}" if archive else arxiv_id
    return redirect(url_for('.pdf', arxiv_id=arxiv_id, _external=True), 301)


@blueprint.route("/pdf/<string:archive>/<string:arxiv_id>.pdf", methods=['GET', 'HEAD'])
@blueprint.route("/pdf/<string:arxiv_id>.pdf", methods=['GET', 'HEAD'])
def pdf(arxiv_id: str, archive=None):  # type: ignore
    """Want to handle the following patterns:

        /pdf/{archive}/{id}v{v}
        /pdf/{archive}/{id}v{v}.pdf
        /pdf/{id}v{v}
        /pdf/{id}v{v}.pdf

    The dissemination service does not handle versionless
    requests. The version should be figured out in some other service
    and redirected to the CDN.

    Serve these from storage bucket URLs like:

    gs://arxiv-production-data/ps_cache/acc-phys/pdf/9502/9502001v1.pdf

    Does a 400 if the ID is malformed or lacks a version.

    Does a 404 if the key for the ID does not exist on the bucket.
    """
    return get_dissimination_resp(fileformat.pdf, arxiv_id, archive)


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

    download_format_pref = request.cookies.get("xxx-ps-defaults")
    add_sciencewise_ping = False
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


@blueprint.route("/html/<arxiv_id>")
@blueprint.route("/html/<arxiv_id>/<path:path>")
def html(arxiv_id: str, path: Optional[str] = None) -> Response:
    """Get html for article."""
    if arxiv_id.endswith('.html'):
        return redirect(f'/html/{arxiv_id.split(".html")[0]}')
    
    try:
        arxiv_identifier = Identifier(arxiv_id=arxiv_id)
        metadata = get_doc_service().get_abs(arxiv_identifier)
    except IdentifierException:
        raise BadRequest("Bad paper identifier")

        
    if metadata.get_version().source_type == 'html':
        # Put post_processing code here
        ...

        ###############################
    else:
        obj_store = GsObjectStore(current_app.config['CONVERTED_BUCKET_ARXIV_ID'])
        
    tar = UngzippedFileObj(obj_store.to_obj(f'{arxiv_identifier.idv}.tar.gz'))
    if path:
        tarmember = FileFromTar(tar, path)
    else:
        tarmember = FileFromTar(tar, f'{arxiv_identifier.idv}.html')
    if tarmember.exists():
        return make_response(stream_gen(tarmember), 200)
    return BadRequest("No such file exists in conversion")


@blueprint.route("/ps/<arxiv_id>")
def ps(arxiv_id: str) -> Response:
    """Get ps for article."""
    raise InternalServerError(f"Not yet implemented {arxiv_id}")
