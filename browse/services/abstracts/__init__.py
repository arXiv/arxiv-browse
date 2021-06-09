from typing import Any, cast

from browse.config import Settings
from .base import AbstractService


def get_abs_service() -> AbstractService:
    """Gets the abstracts service configured for this app context"""
    from browse.config import settings
    from flask import g
    if 'abs_service' not in g:
        g.abs_service = settings.DOCUMENT_ABSTRACT_SERVICE(settings, g)

    return cast(AbstractService, g.abs_service)


def fs_abs(settings_in: Settings, _: Any) -> AbstractService:
    from browse.services.abstracts.fs_abs import AbsMetaSession
    return AbsMetaSession(settings_in.DOCUMENT_LATEST_VERSIONS_PATH,
                          settings_in.DOCUMENT_ORIGNAL_VERSIONS_PATH)

