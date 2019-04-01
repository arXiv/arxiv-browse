"""Web Server Gateway Interface (WSGI) entry-point."""

from browse.factory import create_web_app
import os


_application = create_web_app()


def application(environ, start_response):
    """WSGI application factory."""
    # Apache passes config from SetEnv directives via the request environ.
    for key, value in environ.items():
        if key in _application.config:
            _application.config[key] = value
    return _application(environ, start_response)
