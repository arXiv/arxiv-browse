"""Houses controllers for browse.

Each controller corresponds to a distinct browse feature with its own
request handling logic.
"""

from typing import Any, Dict, Optional, Tuple

from http import HTTPStatus as status
from flask import url_for

from browse.domain.identifier import Identifier


Response = Tuple[Dict[str, Any], int, Dict[str, Any]]


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
