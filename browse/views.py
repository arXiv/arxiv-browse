"""Views."""
from typing import Any

from browse.controllers import get_institution_from_request
from flask import Blueprint, render_template

blueprint = Blueprint('browse', __name__, url_prefix='')


@blueprint.route('/abs/<arxiv:document_id>', methods=['GET'])
def abstract(document_id: str) -> Any:
    """Abstract (abs) page view."""
    response, code, headers = get_abs_page(arxiv_id)
    if code == status.HTTP_200_OK:
        return render_template('abs/abs.html', **response)
    elif code == status.HTTP_404_NOT_FOUND:
        return render_template('abs/404.html', **response)
    return response
