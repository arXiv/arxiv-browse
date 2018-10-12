"""Application factory for browse service components."""
from functools import partial
from typing import Any

from arxiv.base.config import BASE_SERVER
from arxiv.base import Base
from flask import Flask, url_for

from jinja2 import Markup
from browse.domain.identifier import canonical_url
from browse.util.clickthrough import create_ct_url
from browse.util.id_patterns import do_dois_id_urls_to_tags, do_id_to_tags
from browse.routes import ui
from browse.services.database import models
from browse.services.util.email import generate_show_email_hash
from browse.filters import line_feed_to_br, tex_to_utf, entity_to_utf, \
    single_doi_url


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

    ct_url_for = partial(create_ct_url, app.config.get(
        'CLICKTHROUGH_SECRET'), url_for)

    if not app.jinja_env.globals:
        app.jinja_env.globals = {}

    app.jinja_env.globals['canonical_url'] = canonical_url

    if not app.jinja_env.filters:
        app.jinja_env.filters = {}

    app.jinja_env.filters['line_feed_to_br'] = line_feed_to_br
    app.jinja_env.filters['tex_to_utf'] = tex_to_utf
    app.jinja_env.filters['entity_to_utf'] = entity_to_utf

    app.jinja_env.filters['clickthrough_url_for'] = ct_url_for
    app.jinja_env.filters['show_email_hash'] = \
        partial(generate_show_email_hash,
                secret=app.config.get('SHOW_EMAIL_SECRET'))

    def ct_single_doi_filter(doi: str)->str:
        return single_doi_url(ct_url_for, doi)

    app.jinja_env.filters['single_doi_url'] = ct_single_doi_filter

    def _id_to_url(id: str)->Any:
        return url_for('browse.abstract', arxiv_id=id)

    def contextualized_id_filter(text: str)->str:
        return do_id_to_tags(_id_to_url, text)

    app.jinja_env.filters['arxiv_id_urls'] = contextualized_id_filter

    def contextualized_doi_id_url_filter(text: str)->str:
        return do_dois_id_urls_to_tags(_id_to_url, ct_url_for, text)

    app.jinja_env.filters['arxiv_urlize'] = contextualized_doi_id_url_filter

    return app
