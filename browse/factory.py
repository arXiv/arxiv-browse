"""Application factory for browse service components."""
from functools import partial
from typing import Any, Optional, Callable, Dict
from flask import Flask, url_for
from arxiv.browse.domain.identifier import canonical_url
from browse.util.clickthrough import create_ct_url
from arxiv.browse.util.id_patterns import do_dois_id_urls_to_tags, do_id_to_tags, \
    do_dois_arxiv_ids_to_tags
from browse.routes import ui
from browse.services.database import models
from browse.services.util.email import generate_show_email_hash
from arxiv.browse.filters import line_feed_to_br, tex_to_utf, entity_to_utf, \
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

    ct_url_for = partial(create_ct_url, app.config.get(
        'CLICKTHROUGH_SECRET'), url_for)

    def id_to_url(id: str)->Any:
        return url_for('browse.abstract', arxiv_id=id)

    email_hash =partial(generate_show_email_hash,
                        secret=app.config.get('SHOW_EMAIL_SECRET'))

    setup_jinja_for_abs( app.jinja_env, ct_url_for, id_to_url, email_hash)
    
    return app


def setup_jinja_for_abs(jinja_env: Any,
                        ct_url_for: Callable[[str],str],
                        id_to_url: Callable[[str],Any],
                        email_hash: Callable[[str],Optional[str]])->None:
    """Add filters and functions to jinja_env to suppor the abs page macros"""
    
    if not jinja_env.globals:
        jinja_env.globals = {}

    jinja_env.globals['canonical_url'] = canonical_url

    def ct_single_doi_filter(doi: str)->str:
        return single_doi_url(ct_url_for, doi)

    def contextualized_id_filter(text: str)->str:
        return do_id_to_tags(id_to_url, text)

    def contextualized_doi_id_url_filter(text: str)->str:
        return do_dois_id_urls_to_tags(id_to_url, ct_url_for, text)

    def ct_doi_filter(text: str)->str:
        return do_dois_arxiv_ids_to_tags(id_to_url,
                                         ct_url_for,
                                         text)

    if not jinja_env.filters:
        jinja_env.filters = {}

    jinja_env.filters['line_feed_to_br'] = line_feed_to_br
    jinja_env.filters['tex_to_utf'] = tex_to_utf
    jinja_env.filters['entity_to_utf'] = entity_to_utf

    jinja_env.filters['clickthrough_url_for'] = ct_url_for
    jinja_env.filters['show_email_hash'] = email_hash
    
    jinja_env.filters['single_doi_url'] = ct_single_doi_filter
    jinja_env.filters['arxiv_id_urls'] = contextualized_id_filter
    jinja_env.filters['arxiv_urlize'] = contextualized_doi_id_url_filter
    jinja_env.filters['arxiv_id_doi_filter'] = ct_doi_filter
