"""arxiv browse exceptions."""

from http import HTTPStatus as status
from typing import Optional

from arxiv.base.exceptions import handler
from flask import Response, make_response, render_template
from werkzeug.exceptions import BadRequest, HTTPException


class AbsNotFound(HTTPException):
    """Abs not found HTTPException."""

    code = 404
    description = 'Article does not exist'

    def __init__(self, description: Optional[str] = None,
                 response: Optional[Response] = None,
                 data: Optional[dict] = None) -> None:
        """Override default to support data dict."""
        self.data = data or {}
        super(AbsNotFound, self).__init__(description, response)


@handler(AbsNotFound)
def handle_abs_not_found(error: AbsNotFound) -> Response:
    """Render the base not found error page for abs."""
    rendered = render_template('abs/404.html', **error.data)
    response: Response = make_response(rendered)
    if error.data.get("reason", "unknown") == "deleted":
        response.status_code = status.GONE
    else:
        response.status_code = status.NOT_FOUND
    return response


class TrackbackNotFound(HTTPException):
    """Trackback not found HTTPException."""

    code = 404
    description = 'Article does not exist'

    def __init__(self, description: Optional[str] = None,
                 response: Optional[Response] = None,
                 data: Optional[dict] = None) -> None:
        """Override default to support data dict."""
        self.data = data or {}
        super(TrackbackNotFound, self).__init__(description, response)


@handler(TrackbackNotFound)
def handle_trackback_not_found(error: TrackbackNotFound) -> Response:
    """Render the base 404 error page for tb."""
    rendered = render_template('tb/404.html', **error.data)
    response: Response = make_response(rendered)
    response.status_code = status.NOT_FOUND
    return response


@handler(BadRequest)
def handle_bad_request(error: BadRequest) -> Response:
    """Render the 400 error page for browse."""
    rendered = render_template('400.html', error=error)
    response: Response = make_response(rendered)
    response.status_code = status.BAD_REQUEST
    return response
