"""Documents Service and implementations."""
from typing import Any, cast

from browse.services.documents.fs_implementation.fs_abs import FsDocMetadataService
from browse.services.documents.db_implementation.db_abs import DbDocMetadataService

from .base_documents import DocMetadataService

def get_doc_service() -> DocMetadataService:
    """Gets the documents service configured for this app context."""
    from browse.config import settings
    from flask import g

    if 'doc_service' not in g:
        g.doc_service = settings.DOCUMENT_ABSTRACT_SERVICE(settings, g)   # pylint disable:E1102

    return cast(DocMetadataService, g.doc_service)


def fs_docs(settings_in: Any, _: Any) -> FsDocMetadataService:
    """Factory function for file system abstract service."""
    return FsDocMetadataService(settings_in.DOCUMENT_LATEST_VERSIONS_PATH,
                                settings_in.DOCUMENT_ORIGNAL_VERSIONS_PATH)


def db_docs(settings_in: Any, _: Any) -> DbDocMetadataService:
    """Factory function for DB backed abstract service."""
    from browse.services.database.models import db
    return DbDocMetadataService(db)
