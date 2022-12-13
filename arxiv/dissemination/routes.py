from datetime import datetime, timezone

from email.utils import format_datetime
import logging

from flask import abort, make_response, request, Blueprint, current_app

from arxiv.identifier import IdentifierException, Identifier

from cloudpathlib.anypath import to_anypath

logger = logging.getLogger(__file__)

blueprint = Blueprint('routes',__name__)

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
        id.has_version or abort(400, description="version is required")
    except IdentifierException as ex:
        abort(400, description=ex)

    format = 'pdf'
    archive = id.archive if id.is_old_id else 'arxiv'
    item = to_anypath(f"{current_app.config['storage_prefix']}/{archive}/{format}/{id.yymm}/{id.filename}v{id.version}.pdf")
    logger.debug(f"looking for key {item}")
    if not item.exists() : abort(404)

    if request.method == 'GET':
        def stream():
            with item.open('rb') as fh:
                done = False
                while (not done and fh.readable() and not fh.closed):
                    bytes = fh.read(chunk_size)
                    if bytes:
                        yield bytes
                    else:
                        done = True

        resp = make_response(stream())
    else:
        resp = make_response('')

    resp.headers.set('Access-Control-Allow-Origin', '*')
    resp.headers.set('Content-Type', 'application/pdf')
    stat = item.stat()
    resp.headers.set('Last-Modified', format_datetime(datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)))
    resp.headers.set('Content-Length', stat.st_size)
    if hasattr(item, 'etag'): # TODO arxiv.org etag is very different do we need to fix or is using the gs value fine?
        resp.headers.set('ETag', item.etag)

    return resp
