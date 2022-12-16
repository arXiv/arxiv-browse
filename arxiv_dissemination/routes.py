from datetime import datetime, timezone

from email.utils import format_datetime
import logging

from opentelemetry import trace
from flask import abort, make_response, request, Blueprint, current_app, Response, stream_with_context

from arxiv.identifier import IdentifierException, Identifier

from .path_for_id import path_for_id

logger = logging.getLogger(__file__)

blueprint = Blueprint('routes',__name__)

tracer = trace.get_tracer(__name__)

@blueprint.route("/status")
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
    chunk_size = current_app.config['chunk_size']

    try:
        if len(arxiv_id) > 40:
            abort(400)
        if arxiv_id.startswith('arxiv/'):
            abort(400, description="do not prefix with arxiv/ for non-legacy ids")
        id = Identifier(arxiv_id)
        item = path_for_id(current_app.config['storage_prefix'], 'pdf', id)
        logging.debug(f"looking for key {item}")
    except IdentifierException as ex:
        abort(400, description=ex)

    if not item: abort(404)

    headers = {}
    headers['Access-Control-Allow-Origin']='*'
    headers['Content-Type'] = 'application/pdf'
    stat = item.stat()
    headers['Last-Modified'] = format_datetime(datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc))
    headers['Transfer-Encoding'] = 'chunked'

    if hasattr(item, 'etag'): # TODO arxiv.org etag is very different do we need to fix or is using the gs value fine?
        headers['ETag'] = item.etag


    if request.method == 'GET':
        def stream():
            with tracer.start_as_current_span("stream") as g_trace:
                try:
                    with item.open('rb') as fh:
                        done = False
                        while (not done and fh.readable() and not fh.closed):
                            bytes = fh.read(chunk_size)
                            if bytes:
                                yield bytes
                            else:
                                done = True
                except Exception as ex:
                    g_trace.record_exception(ex)
                    logger.exception(ex)

        return Response(stream_with_context(stream()), 200, headers)
    else: # HEAD request method
        return '', headers
