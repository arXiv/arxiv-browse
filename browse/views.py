from flask import Flask, Blueprint, render_template, request
from flask import current_app as app
blueprint = Blueprint('browse', __name__, url_prefix='')

from browse.controllers import get_institution_from_request

@blueprint.route('/abs/<string:document_id>', methods = ['GET'])
def abstract(document_id: str):

    institution_data, status = get_institution_from_request()
    return render_template('abs.html', **institution_data)
