"""Application factory for browse service components."""

from flask import Flask
from browse.services.database.models import dbx as db


def create_web_app(config_filename: str) -> Flask:
    """Initialize an instance of the browse web application."""
    from browse.views import blueprint

    app: Flask = Flask('browse', static_folder='static',
                       template_folder='templates')
    app.config.from_pyfile(config_filename)

    from browse.url_converter import ArXivConverter
    app.url_map.converters['arxiv'] = ArXivConverter

    db.init_app(app)

    app.register_blueprint(blueprint)

    return app
