"""Service to get PDF and other disseminations of an item."""
from flask import current_app

from browse.services.documents import get_doc_service
from browse.services.global_object_store import get_global_object_store
from arxiv.files.object_store import ObjectStore

from .article_store import ArticleStore

_article_store: ArticleStore = None  # type: ignore
# This works because it is thread safe and not bound to the app context.

_object_store: ObjectStore = None  # type: ignore

_genpdf_store: ObjectStore = None  # type: ignore

_latexml_store: ObjectStore = None # type: ignore


def get_article_store() -> "ArticleStore":
    """Gets the `ArticleStore` service.

    This returns PDF and other formats of the article."""
    global _article_store
    if _article_store is None:
        config = current_app.config
        _article_store = ArticleStore(
            get_doc_service(),
            get_global_object_store(config["DISSEMINATION_STORAGE_PREFIX"], "_object_store"),
            get_global_object_store(config["GENPDF_API_STORAGE_PREFIX"], "_genpdf_store"),
            get_global_object_store(config["LATEXML_BUCKET"], "_latexml_store")
        )

    return _article_store
