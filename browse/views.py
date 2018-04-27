"""Provides the user intefaces for browse."""
from typing import Union

from browse.controllers import get_abs_page, get_institution_from_request
from flask import Blueprint, render_template, redirect, Response, session
from arxiv import status
from arxiv.base import exceptions

blueprint = Blueprint('browse', __name__, url_prefix='')


@blueprint.before_request
def before_request() -> None:
    if 'institution' not in session:
        institution = get_institution_from_request()
        session['institution'] = institution


@blueprint.after_request
def apply_response_headers(response: Response) -> Response:
    """Hook for applying response headers to all responses."""
    """Prevent UI redress attacks"""
    response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response


# @blueprint.route('/abs/<arxiv:document_id>', methods=['GET'])
@blueprint.route('/abs/', methods=['GET'], defaults={'arxiv_id': ''})
@blueprint.route('/abs/<path:arxiv_id>', methods=['GET'])
def abstract(arxiv_id: str) -> Union[str, Response]:
    """Abstract (abs) page view."""
    response, code, headers = get_abs_page(arxiv_id)
    if code == status.HTTP_200_OK:
        return render_template('abs/abs.html', **response)
    elif code == status.HTTP_404_NOT_FOUND:
        return render_template('abs/404.html', **response)
    return response
