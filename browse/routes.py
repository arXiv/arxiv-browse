from flask import Blueprint, render_template
blueprint = Blueprint('browse', __name__, url_prefix='')

@blueprint.route('/abs')
def abs():
    return render_template('abs.html')
