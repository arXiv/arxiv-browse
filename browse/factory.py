"""Application factory for browse service components."""

from flask import Flask
from browse.services.database import models
from browse.routes import ui


def create_web_app() -> Flask:
    """Initialize an instance of the browse web application."""
    app = Flask('browse', static_folder='static', template_folder='templates')
    app.config.from_pyfile('config.py')

    models.init_app(app)

    # from browse.url_converter import ArXivConverter
    # app.url_map.converters['arxiv'] = ArXivConverter
    app.register_blueprint(ui.blueprint)

    return app
