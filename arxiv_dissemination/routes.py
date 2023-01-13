from datetime import datetime, timezone, timedelta

from email.utils import format_datetime
import logging

from opentelemetry import trace
from flask import abort, Blueprint, current_app, render_template, redirect, url_for

from flask_rangerequest import RangeRequest

from arxiv.identifier import IdentifierException, Identifier

from arxiv_dissemination.services.next_published import next_publish

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

blueprint = Blueprint('routes',__name__)

tracer = trace.get_tracer(__name__)

@blueprint.route("/pdf/status")
def status():
    #TODO check that can read from storage
    return {"status": "good"}


@blueprint.route("/pdf/<string:category>/<string:arxiv_id>", methods=['GET', 'HEAD'])
def redirect_legacy_id_pdf(category: str, arxiv_id: str):
    """Redirect urls that don't end with .pdf so they download to a filename recognized as a PDF."""
    return redirect(url_for('routes.serve_legacy_id_pdf', category=category, arxiv_id=arxiv_id), 301)


@blueprint.route("/pdf/<string:arxiv_id>", methods=['GET', 'HEAD'])
def redirect_pdf(arxiv_id: str):
    """Redirect urls that don't end with .pdf so they download to a filename recognized as a PDF."""
    return redirect(url_for('routes.serve_pdf', arxiv_id=arxiv_id), 301)


@blueprint.route("/pdf/<string:category>/<string:arxiv_id>.pdf", methods=['GET', 'HEAD'])
def serve_legacy_id_pdf(category: str, arxiv_id: str):
    """Serve PDFs for legacy IDs"""
    return serve_pdf( f"{category}/{arxiv_id}")



@blueprint.route("/pdf/<string:arxiv_id>", methods=['GET', 'HEAD'])
@blueprint.route("/pdf/<string:arxiv_id>.pdf", methods=['GET', 'HEAD'])
def serve_pdf(arxiv_id: str):
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
    try:
        if len(arxiv_id) > 40:
            abort(400)
        if arxiv_id.startswith('arxiv/'):
            abort(400, description="do not prefix with arxiv/ for non-legacy ids")
        id = Identifier(arxiv_id)
    except IdentifierException as ex:
        return bad_id(arxiv_id, str(ex))

    item = current_app.article_store.dissemination_for_id('pdf', id)
    logger. debug(f"dissemination_for_id({id.idv}) was {item}")
    if not item or item=="VERSION_NOT_FOUND" or item == "ARTICLE_NOT_FOUND":
        return not_found(arxiv_id)
    elif item in ["WITHDRAWN", "NO_SOURCE"] :
        return withdrawn(arxiv_id)
    elif item == "UNAVAIABLE": # TODO Render a html page similar to what legacy does
        return unavaiable(arxiv_id)
    elif not item or not item.exists():
        return not_found(arxiv_id)

    resp = RangeRequest(item.open('rb'),
                        etag=item.etag,
                        last_modified = item.updated,
                        size=item.size).make_response()

    resp.headers['Access-Control-Allow-Origin']='*'
    resp.headers['Content-Type'] = 'application/pdf'

    if resp.status_code == 200:
        # To do Large PDFs on Cloud Run both chunked and no content-length are needed
        resp.headers['Transfer-Encoding'] = 'chunked'
        resp.headers.pop('Content-Length')

    if id.has_version:
        resp.headers['Cache-Control'] = _cc_versioned()
    else:
        resp.headers['Expires'] = format_datetime(next_publish())
    return resp


def _cc_versioned():
    """Versioned pdfs should not change so let's put a time a bit in the future.
    Non versioned could change during the next publish."""
    return 'max-age=604800' # 7 days

def withdrawn(arxiv_id: str):
    headers = {'Cache-Cache': 'max-age=31536000'} # one year, max allowed by RFC 2616
    return render_template("pdf/withdrawn.html", arxiv_id=arxiv_id), 200, headers

def unavaiable(arxiv_id: str):
    return render_template("pdf/unavaiable.html", arxiv_id=arxiv_id), 500, {}

def not_found(arxiv_id: str):
    headers = {'Expires': format_datetime(next_publish())}
    return render_template("pdf/not_found.html", arxiv_id=arxiv_id), 404, headers

def bad_id( arxiv_id: str, err_msg: str):
    return render_template("pdf/bad_id.html", err_msg=err_msg, arxiv_id=arxiv_id), 404, {}
