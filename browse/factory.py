"""Application factory for browse service components."""
from functools import partial
from typing import Any
from flask import Flask, url_for
from arxiv.base.urls import canonical_url, clickthrough_url, urlizer
from browse.routes import ui
from browse.services.database import models
from browse.services.util.email import generate_show_email_hash
from browse.filters import line_feed_to_br, tex_to_utf, entity_to_utf, \
    single_doi_url

from arxiv.base.config import BASE_SERVER
from arxiv.base import Base


def create_web_app() -> Flask:
    """Initialize an instance of the browse web application."""
    app = Flask('browse', static_folder='static', template_folder='templates')
    app.config.from_pyfile('config.py')

    # TODO Only needed until this route is added to arxiv-base
    if 'URLS' not in app.config:
        app.config['URLS'] = []
    app.config['URLS'].append(
        ('search_archive', '/search/<archive>', BASE_SERVER))

    models.init_app(app)

    Base(app)
    app.register_blueprint(ui.blueprint)

    if not app.jinja_env.globals:
        app.jinja_env.globals = {}

    app.jinja_env.globals['canonical_url'] = canonical_url

    if not app.jinja_env.filters:
        app.jinja_env.filters = {}

    app.jinja_env.filters['line_feed_to_br'] = line_feed_to_br
    app.jinja_env.filters['tex_to_utf'] = tex_to_utf
    app.jinja_env.filters['entity_to_utf'] = entity_to_utf

    app.jinja_env.filters['clickthrough_url_for'] = clickthrough_url
    app.jinja_env.filters['show_email_hash'] = \
        partial(generate_show_email_hash,
                secret=app.config.get('SHOW_EMAIL_SECRET'))

    app.jinja_env.filters['arxiv_id_urls'] = urlizer(['id'])
    app.jinja_env.filters['arxiv_urlize'] = urlizer(['id', 'doi', 'url'])
    app.jinja_env.filters['arxiv_id_doi_filter'] = urlizer(['id', 'doi'])

    return app
