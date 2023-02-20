"Previous and next document ID service."
from typing import Any, cast
from browse.config import Settings

from .prevnext_base import PrevNextService

def prevnext_service() -> PrevNextService:
    """Gets the prev next service configured for this app context."""
    from flask import g
    from browse.config import settings
    if 'prevnext_service' not in g:
        g.prevnext_service = settings.PREV_NEXT_SERVICE(settings, g)   # pylint disable:E1102

    return cast(PrevNextService, g.prevnext_service)


def fsprevnext(settings_in: Settings, _: Any) -> PrevNextService:
    """Integration function for prev next service that uses the FS."""
    from .FSPrevNext import FSPrevNext
    return FSPrevNext(settings_in.DOCUMENT_LATEST_VERSIONS_PATH,
                      settings_in.DOCUMENT_ORIGNAL_VERSIONS_PATH)
