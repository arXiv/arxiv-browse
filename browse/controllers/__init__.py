"""Houses controllers for browse.

Each controller corresponds to a distinct browse feature with its own
request handling logic.
"""
from typing import Any, Dict, Optional, Tuple
from zoneinfo import ZoneInfo

from http import HTTPStatus as status
from flask import url_for, current_app

from arxiv.identifier import Identifier
from werkzeug.datastructures import Headers


# The body is usually a template-context dict, but a controller may also return
# a ready-made body string (e.g. the list_page 503 served on a listing
# inconsistency, which must not go through normal template rendering).
Response = Tuple[Dict[str, Any]|str, int|status, Dict[str, Any]|Headers]


def check_supplied_identifier(id: Identifier, route: str) -> Optional[Response]:
    """Provide redirect URL if supplied ID does not match parsed ID.

    Parameters
    ----------
    arxiv_identifier : :class:`Identifier`
    route : str
        The route to use in creating the redirect response with arxiv_id

    Returns
    -------
    redirect_url: str
        A redirect URL that uses a canonical arXiv identifier.
    """
    if not id or id.ids == id.id or id.ids == id.idv:
        return None

    arxiv_id = id.idv if id.has_version else id.id
    redirect_url: str = url_for(route, arxiv_id=arxiv_id)
    return {},\
        status.MOVED_PERMANENTLY,\
        {'Location': redirect_url}



_arxiv_biz_tz = None
def biz_tz() -> ZoneInfo:
    global _arxiv_biz_tz
    if _arxiv_biz_tz is None:
        _arxiv_biz_tz = ZoneInfo(current_app.config["ARXIV_BUSINESS_TZ"])
        if _arxiv_biz_tz is None:
            raise ValueError("Must set ARXIV_BUSINESS_TZ to a valid timezone")
        return _arxiv_biz_tz
    else:
        return _arxiv_biz_tz
