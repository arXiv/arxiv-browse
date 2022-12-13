from email.utils import format_datetime
import logging

from flask import abort, make_response, request, Blueprint, current_app

from arxiv.identifier import IdentifierException, Identifier

logger = logging.getLogger(__file__)

blueprint = Blueprint('routes',__name__)

@blueprint.route("/status")
def status():
    # TODO Check we can read from the bucket
    return {"status": "good"}


@blueprint.route("/pdf/<string:category>/<string:arxiv_id>", methods=['GET', 'HEAD'])
@blueprint.route("/pdf/<string:category>/<string:arxiv_id>.pdf", methods=['GET', 'HEAD'])
def serve_legacy_id_pdf(category: str, arxiv_id: str):
    """Serve PDFs for legacy IDs"""
    return serve_pdf( f"{category}/{arxiv_id}")



def gs_key_for_id(id: Identifier, format: str) -> str:
    archive = id.archive if id.is_old_id else 'arxiv'
    return f"{current_app.config['path_prefix']}/{archive}/{format}/{id.yymm}/{id.filename}v{id.version}.pdf"


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

    key = gs_key_for_id(id, 'pdf')
    logger.debug(f"looking for key {key}")

    bucket = current_app.config['bucket']
    blob = bucket.get_blob(key, chunk_size=chunk_size)
    if not blob: abort(404)

    if request.method == 'GET':
        def stream():
            with blob.open('rb') as gsf:
                done = False
                while (not done and gsf.readable() and not gsf.closed):
                    bytes = gsf.read(chunk_size)
                    if bytes:
                        yield bytes
                    else:
                        done = True

        resp = make_response(stream())
    else:
        resp = make_response('')

    # TODO arxiv.org etag is very different do we need to fix or is using the gs value fine?
    resp.headers.set('ETag', blob.etag)

    resp.headers.set('Content-Type', 'application/pdf')
    resp.headers.set('Last-Modified', format_datetime(blob.updated))
    resp.headers.set('Content-Length', blob.size)
    resp.headers.set('Access-Control-Allow-Origin', '*')

    if blob.content_encoding:
        resp.headers.set('Content-Encoding', blob.content_encoding)
    if blob.content_disposition:
        resp.headers.set('Content-Disposition', blob.content_disposition)
    if blob.cache_control:
        resp.headers.set('Cache-Control', blob.cache_control)
    if blob.content_language:
        resp.headers.set('Content-Language', blob.content_language)

    return resp
