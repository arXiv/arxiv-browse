"""Documents Service and implementations."""
from typing import Any, cast

from flask import g, current_app

from .base_documents import DocMetadataService

def get_doc_service() -> DocMetadataService:
    """Gets the documents service configured for this app context."""
    if 'doc_service' not in g:
        g.doc_service = current_app.settings.DOCUMENT_ABSTRACT_SERVICE(current_app.settings, g) # type: ignore

    return cast(DocMetadataService, g.doc_service)


def fs_docs(settings_in: Any, _: Any) -> DocMetadataService:
    """Factory function for file system abstract service."""
    from browse.services.documents.fs_implementation.fs_abs import FsDocMetadataService
    return FsDocMetadataService(settings_in.DOCUMENT_LATEST_VERSIONS_PATH,
                                settings_in.DOCUMENT_ORIGNAL_VERSIONS_PATH)


def db_docs(settings_in: Any, _: Any) -> DocMetadataService:
    """Factory function for DB backed abstract service."""
    from browse.services.documents.db_implementation.db_abs import DbDocMetadataService
    from browse.services.database.models import db
    return DbDocMetadataService(db,
                                settings_in.ARXIV_BUSINESS_TZ)
