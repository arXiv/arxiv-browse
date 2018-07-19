"""Application factory for browse service components."""
from functools import partial
from inspect import getmembers, isfunction

from arxiv.base import Base
from flask import Flask, url_for

from browse.routes import ui
from browse.services.database import models
from browse.services.util.email import generate_show_email_hash
from browse.filters import abstract_breaks, filter_urls


def create_web_app() -> Flask:
    """Initialize an instance of the browse web application."""
    app = Flask('browse', static_folder='static', template_folder='templates')
    app.config.from_pyfile('config.py')

    models.init_app(app)

    Base(app)
    app.register_blueprint(ui.blueprint)

    app.jinja_env.filters['show_email_hash'] = \
        partial(generate_show_email_hash,
                secret=app.config.get('SHOW_EMAIL_SECRET'))

    app.jinja_env.filters['abstract_breaks'] = abstract_breaks
    app.jinja_env.filters['filter_urls'] = filter_urls

    return app
