"""Service to get PDF and other disseminations of an item."""
from browse.config import settings
from google.cloud import storage

from browse.services.documents import get_doc_service
from browse.services.object_store import ObjectStore
from browse.services.object_store.object_store_gs import GsObjectStore
from browse.services.object_store.object_store_local import LocalObjectStore

from .article_store import ArticleStore
from .source_store import SourceStore

_article_store: ArticleStore = None  # type: ignore
# This works because it is thread safe and not bound to the app context.

_object_store: ObjectStore = None  # type: ignore
# This works because it is thread safe and not bound to the app context.

_source_store: SourceStore = None  # type: ignoer


def get_article_store() -> "ArticleStore":
    """Gets the `ArticleStore` service.

    This returns PDF and other formats of the article."""
    global _article_store
    if _article_store is None:
        _article_store = ArticleStore(
            get_doc_service(),
            _get_object_store())

    return _article_store


def get_source_store() -> "SourceStore":
    """Gets the `SourceStore` service.

    This returns the source of an article."""
    global _source_store
    if _source_store is None:
        _source_store = SourceStore(_get_object_store())

    return _source_store


def _get_object_store() -> ObjectStore:
    """Gets the object store."""
    global _object_store
    if _object_store is not None:
        return _object_store

    if not settings.DISSEMINATION_STORAGE_PREFIX.startswith("gs://"):
        _object_store = LocalObjectStore(settings.DISSEMINATION_STORAGE_PREFIX)
    else:
        gs_client = storage.Client()
        bname = settings.DISSEMINATION_STORAGE_PREFIX.replace('gs://','')
        bucket = gs_client.bucket(bname)
        _object_store = GsObjectStore(bucket)

    return _object_store
