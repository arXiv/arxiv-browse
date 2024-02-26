"""Service to get PDF and other disseminations of an item."""
from flask import current_app
from urllib.parse import urlparse
from google.cloud import storage

from browse.services.documents import get_doc_service
from browse.services.object_store import ObjectStore
from browse.services.object_store.object_store_gs import GsObjectStore
from browse.services.object_store.object_store_local import LocalObjectStore

from .article_store import ArticleStore

_article_store: ArticleStore = None  # type: ignore
# This works because it is thread safe and not bound to the app context.

_object_store: ObjectStore = None  # type: ignore
# This works because it is thread safe and not bound to the app context.
_genpdf_store: ObjectStore = None  # type: ignore


def get_global_object_store(path: str, global_name: str) -> ObjectStore:
    """Creates an object store from given path."""
    store = globals().get(global_name)
    if store is None:
        uri = urlparse(path)
        if uri.scheme == "gs":
            gs_client = storage.Client()
            store = GsObjectStore(gs_client.bucket(uri.netloc))
        else:
            store = LocalObjectStore(path)
        globals()[global_name] = store
    return store


def get_article_store() -> "ArticleStore":
    """Gets the `ArticleStore` service.

    This returns PDF and other formats of the article."""
    global _article_store
    if _article_store is None:
        config = current_app.config
        _article_store = ArticleStore(
            get_doc_service(),
            get_global_object_store(config["DISSEMINATION_STORAGE_PREFIX"], "_object_store"),
            get_global_object_store(config["GENPDF_API_STORAGE_PREFIX"], "_genpdf_store")
        )

    return _article_store
