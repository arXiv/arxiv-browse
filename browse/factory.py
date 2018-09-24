"""Application factory for browse service components."""
from functools import partial

from arxiv.base.config import BASE_SERVER
from arxiv.base import Base
from flask import Flask, url_for

from browse.domain.identifier import canonical_url
from browse.util.clickthrough import create_ct_url
from browse.routes import ui
from browse.services.database import models
from browse.services.util.email import generate_show_email_hash
from browse.filters import doi_urls, arxiv_urlize, arxiv_id_urls, \
    line_feed_to_br, tex_to_utf


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

    app.jinja_env.globals['canonical_url'] = canonical_url

    app.jinja_env.filters['clickthrough_url_for'] = ct_url_for
    app.jinja_env.filters['show_email_hash'] = \
        partial(generate_show_email_hash,
                secret=app.config.get('SHOW_EMAIL_SECRET'))
    app.jinja_env.filters['doi_urls'] = partial(doi_urls, ct_url_for)
    app.jinja_env.filters['arxiv_id_urls'] = arxiv_id_urls
    app.jinja_env.filters['line_feed_to_br'] = line_feed_to_br
    app.jinja_env.filters['arxiv_urlize'] = arxiv_urlize
    app.jinja_env.filters['tex_to_utf'] = tex_to_utf
    return app
