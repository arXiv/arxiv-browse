"""Application factory for browse service components."""
from functools import partial

import logging
from flask.logging import default_handler

from arxiv.base import Base
from arxiv.base.config import BASE_SERVER
from arxiv.base.urls import canonical_url, clickthrough_url, urlizer
from arxiv_auth.auth import Auth
from flask import Flask
from flask_s3 import FlaskS3

from browse.config import APP_VERSION
from browse.filters import entity_to_utf
from browse.routes import ui
from browse.services.database import models
from browse.services.util.email import generate_show_email_hash


from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.cloud_trace_propagator import (
    CloudTraceFormatPropagator,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

s3 = FlaskS3()


def create_web_app() -> Flask:
    """Initialize an instance of the browse web application."""

    set_global_textmap(CloudTraceFormatPropagator())

    root = logging.getLogger()
    root.addHandler(default_handler)

    app = Flask('browse', static_url_path=f'/static/browse/{APP_VERSION}')
    app.config.from_pyfile('config.py')

    models.init_app(app)  # type: ignore
    Base(app)
    Auth(app)
    app.register_blueprint(ui.blueprint)
    s3.init_app(app)

    if not app.jinja_env.globals:
        app.jinja_env.globals = {}

    app.jinja_env.globals['canonical_url'] = canonical_url

    if not app.jinja_env.filters:
        app.jinja_env.filters = {}

    app.jinja_env.filters['entity_to_utf'] = entity_to_utf

    app.jinja_env.filters['clickthrough_url_for'] = clickthrough_url
    app.jinja_env.filters['show_email_hash'] = \
        partial(generate_show_email_hash,
                secret=app.config.get('SHOW_EMAIL_SECRET'))

    app.jinja_env.filters['arxiv_id_urls'] = urlizer(['arxiv_id'])
    app.jinja_env.filters['arxiv_urlize'] = urlizer(['arxiv_id', 'doi', 'url'])
    app.jinja_env.filters['arxiv_id_doi_filter'] = urlizer(['arxiv_id', 'doi'])

    # see https://cloud.google.com/trace/docs/setup/python-ot#import_and_configuration
    # and https://github.com/GoogleCloudPlatform/opentelemetry-operations-python/tree/main/docs/exporter/flask_e2e
    FlaskInstrumentor().instrument_app(app)

    # Would also like to try
    # https://cloud.google.com/blog/products/devops-sre/google-cloud-logging-python-client-library-v3-0-0-release
    # but the use of logging in the NG flask apps odd
    # due to a querky setup from arxiv.base.logging

    return app
