"""Dissemination flask application"""

import os

from flask import Flask

from google.cloud import storage

from .routes import blueprint

import logging
logger = logging.getLogger(__file__)

#################### config ####################
bucket_name = os.environ.get('BUCKET','arxiv-production-data')
"""Name of the GS bucket. Must not have the gs:// prefix"""

path_prefix = os.environ.get('PATH_PREFIX', 'ps_cache')

chunk_size = int(os.environ.get('CHUNK_SIZE', 1024 * 256))
"""chunk size from GS. Bytes. Must be mutiples of 256k"""

trace = bool(os.environ.get('TRACE', '1') == '1')

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

app.config.update(
    path_prefix = path_prefix,
    chunk_size=chunk_size,
    gs_client=gs_client,
    bucket=bucket,
    )

app.register_blueprint(blueprint)


############### trace and logging setup ###############
if trace:
    logger.warn(f"Setting google cloud trace and logging")
    from opentelemetry import trace
    from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.propagators.cloud_trace_propagator import (
        CloudTraceFormatPropagator,
    )
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # https://cloud.google.com/trace/docs/setup/python-ot#initialize_flask
    set_global_textmap(CloudTraceFormatPropagator())

    tracer_provider = TracerProvider()
    cloud_trace_exporter = CloudTraceSpanExporter()
    tracer_provider.add_span_processor(
        BatchSpanProcessor(cloud_trace_exporter)
    )
    trace.set_tracer_provider(tracer_provider)
    tracer = trace.get_tracer(__name__)

    FlaskInstrumentor().instrument_app(app)
else:
    logger.warn("No setup of google cloud trace and logging")
