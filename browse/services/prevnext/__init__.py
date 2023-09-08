"Previous and next document ID service."
from typing import cast

from flask import current_app, g

from .prevnext_base import PrevNextService


def prevnext_service() -> PrevNextService:
    """Gets the prev next service configured for this app context."""
    if 'prevnext_service' not in g:
        fn = current_app.config["PREV_NEXT_SERVICE"]
        g.prevnext_service = fn(current_app.config)

    return cast(PrevNextService, g.prevnext_service)


def fsprevnext(config: dict) -> PrevNextService:
    """Integration function for prev next service that uses the FS."""
    from .FSPrevNext import FSPrevNext
    return FSPrevNext(config["DOCUMENT_LATEST_VERSIONS_PATH"],
                      config["DOCUMENT_ORIGNAL_VERSIONS_PATH"])
