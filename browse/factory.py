"""Application factory for browse service components."""
import os
from functools import partial

import logging

from flask.logging import default_handler

from arxiv.base import Base
from arxiv.base.urls import canonical_url, clickthrough_url, urlizer
from arxiv.base.filters import tidy_filesize
from flask import Flask
from flask_s3 import FlaskS3

# This gives the error on import
# RuntimeError: __class__ not set defining 'User' as <class 'arxiv.users.domain.User'>. Was __classcell__ propagated to type.__new__?
# from arxiv.users.auth import Auth

from browse.config import Settings
from browse.routes import ui, dissemination, src
from browse.services.database import models
from browse.services.check import service_statuses
from browse.formatting.email import generate_show_email_hash
from browse.filters import entity_to_utf

s3 = FlaskS3()


def create_web_app(**kwargs) -> Flask: # type: ignore
    """Initialize an instance of the browse web application."""
    root = logging.getLogger()
    root.addHandler(default_handler)

    settings = Settings(**kwargs)
    settings.check()

    app = Flask('browse',
                static_url_path=f'/static/browse/{settings.APP_VERSION}')
    app.config.from_object(settings)  # facilitates sqlalchemy flask plugins
    setattr(app, 'settings', settings)  # facilitates typed access to settings

    models.init_app(app)  # type: ignore

    Base(app)
    #Auth(app)
    app.register_blueprint(ui.blueprint)
    app.register_blueprint(dissemination.blueprint)
    app.register_blueprint(src.blueprint)
    s3.init_app(app)

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    if not app.jinja_env.globals:
        app.jinja_env.globals = {}

    app.jinja_env.globals['canonical_url'] = canonical_url

    if not app.jinja_env.filters:
        app.jinja_env.filters = {}

    app.jinja_env.filters['entity_to_utf'] = entity_to_utf

    app.jinja_env.filters['clickthrough_url_for'] = clickthrough_url
    app.jinja_env.filters['show_email_hash'] = \
        partial(generate_show_email_hash,
                secret=settings.SHOW_EMAIL_SECRET.get_secret_value())  # pylint: disable=E1101

    app.jinja_env.filters['arxiv_id_urls'] = urlizer(['arxiv_id'])
    app.jinja_env.filters['arxiv_urlize'] = urlizer(['arxiv_id', 'doi', 'url'])
    app.jinja_env.filters['arxiv_id_doi_filter'] = urlizer(['arxiv_id', 'doi'])
    app.jinja_env.filters['tidy_filesize'] = tidy_filesize

    @app.before_first_request
    def check_services()->None:
        problems = service_statuses()
        if problems:
            app.logger.error("Problems with services!!!!!")
            [app.logger.error(prob) for prob in problems]

    return app


def setup_trace(name: str, app: Flask):  # type: ignore
    """Setup GCP trace and logging."""
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
    tracer = trace.get_tracer(name)
    FlaskInstrumentor().instrument_app(app)
    return tracer
