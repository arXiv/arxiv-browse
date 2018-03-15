""" WSGI entry point """

from browse.factory import create_web_app
import os

def application(environ, start_response):
    for key, value in environ.items():
        os.environ[key] = str(value)
    app = create_web_app()
    return app(environ, start_response)
