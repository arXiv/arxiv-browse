"""Documents Service and implementations."""
from typing import Any, cast

from flask import g, current_app

from arxiv.files.object_store import ObjectStore

from browse.services.documents.base_documents import DocMetadataService
from browse.services.global_object_store import get_global_object_store

_doc_latest_versions_store: ObjectStore = None # type: ignore
_doc_original_versions_store: ObjectStore = None # type: ignore

def get_doc_service() -> DocMetadataService:
    """Gets the documents service configured for this app context."""
    if 'doc_service' not in g:
        g.doc_service = current_app.config["DOCUMENT_ABSTRACT_SERVICE"](current_app.config, g)

    return cast(DocMetadataService, g.doc_service)


def fs_docs(config: dict, _: Any) -> DocMetadataService:
    """Factory function for file system abstract service."""
    from browse.services.documents.fs_implementation.fs_abs import FsDocMetadataService
    return FsDocMetadataService(
        get_global_object_store(config["ABS_PATH_ROOT"], '_doc_latest_versions_store'),
    )


def db_docs(config: dict, _: Any) -> DocMetadataService:
    """Factory function for DB backed abstract service."""
    from browse.services.documents.db_implementation.db_abs import DbDocMetadataService
    return DbDocMetadataService()
