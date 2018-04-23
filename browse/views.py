"""Provides the user intefaces for browse."""
from typing import Dict, Callable, Union, Any, Optional

from browse.controllers import get_abs_page, get_institution_from_request
from flask import Blueprint, render_template, Response, session

blueprint = Blueprint('browse', __name__, url_prefix='')


@blueprint.before_request
def before_request():
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


@blueprint.route('/abs/<arxiv:document_id>', methods=['GET'])
def abstract(document_id: str) -> Union[str, Response]:
    """Abstract (abs) page view."""
    # print(session)
    # institution_data, status = get_institution_from_request()
    response, code, headers = get_abs_page(document_id)
    return render_template('abs.html', **response)
