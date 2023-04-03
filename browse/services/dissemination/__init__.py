"""Service to get PDF and other disseminations of an item."""
from typing import Literal

from browse.config import settings
from google.cloud import storage

from .article_store import ArticleStore
from .object_store import ObjectStore
from .object_store_gs import GsObjectStore
from .object_store_local import LocalObjectStore

_article_store:ArticleStore = None
#This works because it is thread safe and not bound to the app context.

_object_store: ObjectStore = None
#This works because it is thread safe and not bound to the app context.

def get_article_store() -> "ArticleStore":
    """Gets the `ArticleStore` service used by dissemination."""
    global _article_store
    if _article_store == None:
        _article_store = ArticleStore(_get_object_store())

    return _article_store

def _get_object_store() -> ObjectStore:
    """Gets the object store."""
    global _object_store
    if _object_store is not None:
        return _object_store

    if not settings.DISSEMINATION_STORAGE_PREFIX.startswith("gs://"):
        _object_store = LocalObjectStore(settings.DISSEMINATION_STORAGE_PREFIX)
    else:
        gs_client = storage.Client()
        bname= settings.DISSEMINATION_STORAGE_PREFIX.replace('gs://','')
        bucket = gs_client.bucket(bname)
        _object_store = GsObjectStore(bucket)

    return _object_store
