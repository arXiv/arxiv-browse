"""Service to get PDF and other disseminations of an item."""
from arxiv.legacy.papers.dissemination.reasons import get_reasons_data
from flask import current_app
import logging

from browse.services.documents import get_doc_service
from browse.services.global_object_store import get_global_object_store, one_time_file

from .article_store import ArticleStore

logger = logging.getLogger(__name__)

_article_store: ArticleStore = None  # type: ignore
# This works because it is thread safe and not bound to the app context.


def get_article_store() -> "ArticleStore":
    """Gets the `ArticleStore` service.

    This returns PDF and other formats of the article."""
    global _article_store
    if _article_store is None:
        config = current_app.config

        dsp_os = get_global_object_store(config["DISSEMINATION_STORAGE_PREFIX"], "_object_store")
        if config["REASONS_FILE_PATH"] == "DEFAULT":
            reason_file = dsp_os.to_obj("reasons.json")
        else:
            logger.info("Loading reasons file from %s", config["REASONS_FILE_PATH"])
            reason_file = one_time_file(config["REASONS_FILE_PATH"])

        if config["SOURCE_STORAGE_PREFIX"] == config["DISSEMINATION_STORAGE_PREFIX"]:
            src_os = dsp_os
        else:
            src_os = get_global_object_store(config["SOURCE_STORAGE_PREFIX"], "_source_store")

        _article_store = ArticleStore(
            get_doc_service(),
            dsp_os,
            src_os,
            get_global_object_store(config["GENPDF_API_STORAGE_PREFIX"], "_genpdf_store"),
            get_global_object_store(config["LATEXML_BUCKET"], "_latexml_store"),
            get_reasons_data(reason_file),
        )

    return _article_store
