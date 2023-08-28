"Previous and next document ID service."
from typing import Any, cast

from flask import current_app, g

from browse.config import Settings
from .prevnext_base import PrevNextService

def prevnext_service() -> PrevNextService:
    """Gets the prev next service configured for this app context."""
    if 'prevnext_service' not in g:
        fn = current_app.settings.PREV_NEXT_SERVICE # type: ignore
        g.prevnext_service = fn(current_app.settings)  # type: ignore

    return cast(PrevNextService, g.prevnext_service)


def fsprevnext(settings_in: Settings) -> PrevNextService:
    """Integration function for prev next service that uses the FS."""
    from .FSPrevNext import FSPrevNext
    return FSPrevNext(settings_in.DOCUMENT_LATEST_VERSIONS_PATH,
                      settings_in.DOCUMENT_ORIGNAL_VERSIONS_PATH)
