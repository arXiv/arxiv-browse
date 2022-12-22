from datetime import datetime, timezone, timedelta

from email.utils import format_datetime
import logging

from opentelemetry import trace
from flask import abort, Blueprint, current_app

from flask_rangerequest import RangeRequest

from arxiv.identifier import IdentifierException, Identifier

from .path_for_id import path_for_id

logger = logging.getLogger(__file__)

blueprint = Blueprint('routes',__name__)

tracer = trace.get_tracer(__name__)

@blueprint.route("/pdf/status")
def status():
    if current_app.config['storage'].exists():
        return {"status": "good"}
    else:
        abort(500, "could not read from storage")


@blueprint.route("/pdf/<string:category>/<string:arxiv_id>", methods=['GET', 'HEAD'])
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
        item = path_for_id('pdf', id)
        logging.debug(f"looking for key {item}")
    except IdentifierException as ex:
        abort(400, description=ex)

    if not item or not item.exists():
            abort(404)
            return

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
        resp.headers['Expires'] = format_datetime(_next_publish())
    return resp


def _cc_versioned():
    """Versioned pdfs should not change so let's put a time a bit in the future."""
    return 'max-age=604800' # 7 days


def _next_publish(now=None):
    """This guesses the next publish but knows nothing about holidays.

    This is a conservative approch. If this is used for Expires
    headers should never cache when the contents were updated due to publish. It will
    cache less then optimal when there is a holiday and nothing could
    have been updated.
    """
    if now == None:
        now = datetime.now()

    if now.weekday() in [0,1,2,3,6]:
        if now.hour > 20 and now.hour < 21:
            #It's around publish time, PDF might change, really short
            return now.replace(minute=now.minute + 5)
        elif now.hour > 21:
            return _next_publish((now + timedelta(days=1)).replace(hour=12))
        else:
            return now.replace(hour=20)

    if now.weekday() == 4:
        return (now + timedelta(days=2)).replace(hour=20)
    if now.weekday() == 5:
        return (now + timedelta(days=2)).replace(hour=20)
