"""Application factory for browse service components."""

from flask import Flask
import logging

def create_web_app(config_filename):
    """Initialize an instance of the web application."""
    from browse.routes import blueprint

    app = Flask('browse', static_folder='static', template_folder='templates')
    app.config.from_pyfile(config_filename)
    app.register_blueprint(blueprint)
    return app
