"""Application factory for browse service components."""
from functools import partial
from typing import Any
from flask import Flask, url_for
import jinja2

from browse.util.clickthrough import create_ct_url
from browse.routes import ui
from browse.services.database import models
from browse.services.util.email import generate_show_email_hash

from arxiv.base.config import BASE_SERVER
from arxiv.base import Base
from arxiv.browse.setup_jinja_for_abs import setup_jinja_for_abs
from arxiv.browse.template_loader import browse_template_loader

def create_web_app() -> Flask:
    """Initialize an instance of the browse web application."""
    app = Flask('browse', static_folder='static', template_folder='templates')
    app.config.from_pyfile('config.py')

    # load templates from multiple sources
    # first on list gets perference so browse could override arxiv.browse
    multi_loader = jinja2.ChoiceLoader([
        app.jinja_loader,
        browse_template_loader()
    ])

    app.jinja_loader = multi_loader
    
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

