"""Documents Service and implementations."""
from typing import Any, cast

from flask import g, current_app

from .base_documents import DocMetadataService

def get_doc_service() -> DocMetadataService:
    """Gets the documents service configured for this app context."""
    if 'doc_service' not in g:
        g.doc_service = current_app.config["DOCUMENT_ABSTRACT_SERVICE"](current_app.config, g)

    return cast(DocMetadataService, g.doc_service)


def fs_docs(config: dict, _: Any) -> DocMetadataService:
    """Factory function for file system abstract service."""
    from browse.services.documents.fs_implementation.fs_abs import FsDocMetadataService
    return FsDocMetadataService(config["DOCUMENT_LATEST_VERSIONS_PATH"],
                                config["DOCUMENT_ORIGNAL_VERSIONS_PATH"])


def db_docs(config: dict, _: Any) -> DocMetadataService:
    """Factory function for DB backed abstract service."""
    from browse.services.documents.db_implementation.db_abs import DbDocMetadataService
    from arxiv.db import engine
    return DbDocMetadataService(engine,
                                config["ARXIV_BUSINESS_TZ"])
