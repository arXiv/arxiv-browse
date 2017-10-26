"""Views."""
from browse.controllers import get_institution_from_request
from flask import Blueprint, render_template

blueprint = Blueprint('browse', __name__, url_prefix='')


@blueprint.route('/abs/<string:document_id>', methods=['GET'])
def abstract(document_id: str):
    """Abstract (abs) page view."""
    institution_data, status = get_institution_from_request()
    return render_template('abs.html', **institution_data)
