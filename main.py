from sys import prefix
import time
import os
from email.utils import format_datetime

from flask import Flask, abort, make_response, request

from arxiv.identifier import IdentifierException, Identifier

from google.cloud import storage

from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.cloud_trace_propagator import (
    CloudTraceFormatPropagator,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

############### trace and logging set ###############
# https://cloud.google.com/trace/docs/setup/python-ot#initialize_flask
set_global_textmap(CloudTraceFormatPropagator())

tracer_provider = TracerProvider()
cloud_trace_exporter = CloudTraceSpanExporter()
tracer_provider.add_span_processor(
    BatchSpanProcessor(cloud_trace_exporter)
)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)

import logging
logger = logging.getLogger(__file__)

#################### config ####################
bucket_name = os.environ.get('BUCKET','arxiv-production-data')
"""Name of the GS bucket. Must not have the gs:// prefix"""

path_prefix = os.environ.get('PATH_PREFIX', 'ps_cache')

chunk_size = int(os.environ.get('CHUNK_SIZE', 1024 * 256))
"""chunk size from GS. Bytes. Must be mutiples of 256k"""

#################### App ####################
gs_client = storage.Client()

from flask.logging import default_handler
root = logging.getLogger()
root.addHandler(default_handler)

problems = []
if chunk_size % (1024 *256):
    problems.append('CHUNK_SIZE must be a multiple of 256kb.')

if path_prefix.startswith('/'):
    problems.append(f'PATH_PREFIX should not start with a slash, using keys not gs:// URLs, prefix was {path_prefix}')
    
if not bucket_name:
    problems.append('Must set BUCKET.')
    if bucket_name.startswith('gs://'):
        problems.append('BUCKET must not start with gs://, use just the bucket name.')
    if not gs_client.bucket(bucket_name).exists():        
        problems.append('BUCKET {BUCKET} does not exist or cannot read.')
        problems.append('Using service account {gs_client.get_service_account_email()}.')

if problems:
    [logger.error(prob) for prob in problems]
    exit(1)

bucket = gs_client.bucket(bucket_name)

app = Flask(__name__)

FlaskInstrumentor().instrument_app(app)

def gs_key_for_id(id: Identifier, format: str) -> str:
    archive = id.archive if id.is_old_id else 'arxiv'
    return f"{path_prefix}/{archive}/{format}/{id.yymm}/{id.filename}v{id.version}.pdf"

@app.route("/status")
def status():
    # TODO Check we can read from the bucket
    return {"status": "good"}


@app.route("/pdf/<string:arxiv_id>", methods=['GET', 'HEAD'])
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
        id = Identifier(arxiv_id)
        id.has_version or abort(400, description="version is required")
    except IdentifierException as ex:
        abort(400, description=ex)
        
    key = gs_key_for_id(id, 'pdf')
    logger.debug(f"looking for key {key}")

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


if __name__ == "__main__":    
    app.run(debug=True)

