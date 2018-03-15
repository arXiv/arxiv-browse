"""Application factory for browse service components."""

from flask import Flask
from browse.services.database import models
from browse import views


def create_web_app():
    """Initialize an instance of the browse web application."""
    # from browse.views import blueprint

    app = Flask('browse', static_folder='static', template_folder='templates')
    app.config.from_pyfile('config.py')

    models.init_app(app)

    # Base(app)

    from browse.url_converter import ArXivConverter
    app.url_map.converters['arxiv'] = ArXivConverter
    app.register_blueprint(views.blueprint)

    return app
