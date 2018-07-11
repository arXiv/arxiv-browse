"""Application factory for browse service components."""
from functools import partial

from arxiv.base import Base
from flask import Flask, url_for

from browse.util.clickthrough import create_ct_url
from browse.routes import ui
from browse.services.database import models


def create_web_app() -> Flask:
    """Initialize an instance of the browse web application."""
    app = Flask('browse', static_folder='static', template_folder='templates')
    app.config.from_pyfile('config.py')

    models.init_app(app)

    Base(app)
    app.register_blueprint(ui.blueprint)

    app.jinja_env.filters['clickthrough_url_for'] = partial(
        create_ct_url, app.config.get('SECRET_KEY'), url_for)
    return app
