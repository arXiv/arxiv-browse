"""Documents Service and implementations."""
from typing import Any, cast

from browse.config import Settings
from .base_documents import DocMetadataService
from browse.services.documents.fs_implementation.fs_abs import FsDocMetadataService


def get_doc_service() -> DocMetadataService:
    """Gets the documents service configured for this app context."""
    from browse.config import settings
    from flask import g

    if 'doc_service' not in g:
        g.doc_service = settings.DOCUMENT_ABSTRACT_SERVICE(settings, g)   # pylint disable:E1102

    return cast(DocMetadataService, g.doc_service)


def fs_docs(settings_in: Settings, _: Any) -> FsDocMetadataService:
    """Integration function for file system abstract service."""
    return FsDocMetadataService(settings_in.DOCUMENT_LATEST_VERSIONS_PATH,
                                settings_in.DOCUMENT_ORIGNAL_VERSIONS_PATH)
