"""Dissemination flask application"""
import os

from pathlib import Path

from flask import Flask

from .routes import blueprint
from .trace import setup_trace

import logging
logging.basicConfig(level=logging.INFO)

from google.cloud import storage

from arxiv.base import Base
from arxiv.legacy.papers.dissemination.reasons import reasons
from arxiv.legacy.papers.deleted import is_deleted

from arxiv_dissemination.services.object_store_gs import GsObjectStore
from arxiv_dissemination.services.object_store_local import LocalObjectStore
from arxiv_dissemination.services.article_store import ArticleStore

import arxiv_dissemination

def factory():
    #################### config ####################
    storage_prefix = os.environ.get('STORAGE_PREFIX','gs://arxiv-production-data')
    """Storage prefix to use. Ex gs://arxiv-production-data

    If it is a GS bucket it must be just gs://{BUCKET_NAME} and not have
    any key parts.

    Use something like `/cache/` for a file system. Use something like
    `./testing/data/` for testing data. Must end with a /
    """

    trace = bool(os.environ.get('TRACE', '1') == '1')
    """To activate Google logging and trace.

    On by default, set to 0 to deactivate.
    """

    #################### App ####################
    app = Flask(__name__)
    app.config.update(storage_prefix=storage_prefix)
    Base(app)
    app.register_blueprint(blueprint)

    ############### trace and logging setup ###############
    if trace:
        setup_trace(__name__,app)

    app.logger.info(f"trace is {trace}")
    app.logger.info(f"storage_prefix is {storage_prefix}")

    problems = []
    if not storage_prefix.startswith("gs://"):
        app.logger.warning(f"Using local files as object store at {storage_prefix}, Use this in testing only.")
        if not Path(storage_prefix).exists():
            problems.append(f"Directory {storage_prefix} does not exist.")
        if not storage_prefix.endswith('/'):
            problems.append(f'If using a local FS, STORAGE_PREFIX must end with a slash, was {storage_prefix}')
        setattr(app, 'object_store', LocalObjectStore(storage_prefix))
    else:
        gs_client = storage.Client()
        bname= storage_prefix.replace('gs://','')
        if '/' in bname:
            problems.append(f"GS bucket should not have a key part, was {bname}")
        bucket = gs_client.bucket(bname)
        if not bucket.exists():
            problems.append(f"GS bucket {bucket} does not exist.")
        setattr(app, 'object_store', GsObjectStore(bucket))


    setattr(app, 'article_store', ArticleStore(app.object_store, reasons, is_deleted))
    stat, msg = app.article_store.status()
    if stat != 'GOOD':
        problems.append(f"article_store status {stat} due to {msg}")

    if problems:
        [app.logger.error(prob) for prob in problems]
        exit(1)

    return app
