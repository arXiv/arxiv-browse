"""Application factory for browse service components."""
from functools import partial
from flask import Flask
from flask_s3 import FlaskS3

from arxiv.base.urls import canonical_url, clickthrough_url, urlizer
from browse.config import settings
from browse.routes import ui
from browse.services.database import models
from browse.services.util.email import generate_show_email_hash
from browse.filters import entity_to_utf

from arxiv.base.config import BASE_SERVER
from arxiv.base import Base
#from arxiv.users.auth import Auth

s3 = FlaskS3()


def create_web_app() -> Flask:
    """Initialize an instance of the browse web application."""
    settings.check()
    app = Flask('browse', static_url_path=f'/static/browse/{settings.APP_VERSION}')
    app.config.from_object(settings)  # facilitates sqlalchemy and other flask plugins
    app.settings = settings  # facilitates typed access to settings
    
    # TODO Only needed until this route is added to arxiv-base
    # TODO Remove this, this is in arxiv.base.config.URLS
    if 'URLS' not in app.config:
        app.config['URLS'] = []
    app.config['URLS'].append(
        ('search_archive', '/search/<archive>', BASE_SERVER))

    models.init_app(app)  # type: ignore
    Base(app)
    # TODO nothing from auth is imported and no auth decorators are used, is it in use?
    # Auth(app)
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
                secret=app.settings.SHOW_EMAIL_SECRET.get_secret_value())

    app.jinja_env.filters['arxiv_id_urls'] = urlizer(['arxiv_id'])
    app.jinja_env.filters['arxiv_urlize'] = urlizer(['arxiv_id', 'doi', 'url'])
    app.jinja_env.filters['arxiv_id_doi_filter'] = urlizer(['arxiv_id', 'doi'])

    return app
