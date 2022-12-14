"""Dissemination flask application"""
import os

from flask import Flask

from .routes import blueprint

from cloudpathlib.anypath import to_anypath

import logging
logger = logging.getLogger(__file__)

"""Type for Path that is either a cloud or local path."""

#################### config ####################
storage_prefix = os.environ.get('STORAGE_PREFIX','gs://arxiv-production-data')
"""Storage prefix to use. Ex gs://arxiv-production-data/ps_cache

Use something like /cache/ps_cache for a file system.

Use something like ./testing/ps_cahe for testing data.

Should not end with a /.
"""

chunk_size = int(os.environ.get('CHUNK_SIZE', 1024 * 256))
"""chunk size from GS. Bytes. Must be mutiples of 256k"""

trace = bool(os.environ.get('TRACE', '1') == '1')
"""To activate Google logging and trace.

On by default,anything other than 1 deactivates.
"""
#################### App ####################

from flask.logging import default_handler
root = logging.getLogger()
root.addHandler(default_handler)

problems = []
if chunk_size % (1024 *256):
    problems.append('CHUNK_SIZE must be a multiple of 256kb.')
if storage_prefix.endswith('/'):
    problems.append(f'STORAGE_PREFIX should not end with a slash, prefix was {path_prefix}')
if not to_anypath(storage_prefix).exists():
        problems.append('BUCKET {STORAGE_PREFIX} does not exist or cannot read.')
if problems:
    [logger.error(prob) for prob in problems]
    exit(1)

app = Flask(__name__)
app.config.update(
    storage_prefix=storage_prefix,
    chunk_size=chunk_size,
    )
app.register_blueprint(blueprint)

############### trace and logging setup ###############
if trace:
    logger.warning(f"Setting google cloud trace and logging")
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
    logger.warning("No setup of google cloud trace and logging")
