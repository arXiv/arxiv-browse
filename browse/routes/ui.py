"""Provides the user intefaces for browse."""
import re
from typing import Union
from flask import Blueprint, render_template, request, Response, session, \
    redirect, current_app
from werkzeug.exceptions import InternalServerError, NotFound

from arxiv import status
from browse.controllers import abs_page
from browse.exceptions import AbsNotFound
from browse.util.clickthrough import is_hash_valid
from browse.services.database import get_institution

blueprint = Blueprint('browse', __name__, url_prefix='')


@blueprint.before_request
def before_request() -> None:
    """Get instituional affiliation from session."""
    if 'institution' not in session:
        session['institution'] = get_institution(request.remote_addr)


@blueprint.after_request
def apply_response_headers(response: Response) -> Response:
    """Apply response headers to all responses."""
    """Prevent UI redress attacks."""
    response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    if request.endpoint == 'browse.abstract':
        # TODO: set Expires, Last-Modified, ETag response headers
    return response


@blueprint.route('/abs', methods=['GET'])
def bare_abs() -> Response:
    """Check several legacy request parameters."""
    if request.args:
        if 'id' in request.args:
            return abstract(request.args['id'])
        elif 'archive' in request.args and 'papernum' in request.args:
            return abstract(
                f"{request.args['archive']}/{request.args['papernum']}")
        else:
            for param in request.args:
                # singleton case, where the parameter is the value
                # e.g. /abs?<archive>/\d{7}
                if not request.args[param] \
                   and re.match(r'^[a-z\-]+(\.[A-Z]{2})?\/\d{7}$', param):
                    return abstract(param)

    """Return abs-specific 404."""
    raise AbsNotFound


@blueprint.route('/abs/', methods=['GET'], defaults={'arxiv_id': ''})
@blueprint.route('/abs/<path:arxiv_id>', methods=['GET'])
def abstract(arxiv_id: str) -> Response:
    """Abstract (abs) page view."""
    download_format_pref = request.cookies.get('xxx-ps-defaults')

    response, code, headers = abs_page.get_abs_page(arxiv_id,
                                                    request.args,
                                                    download_format_pref)

    if code == status.HTTP_200_OK:
        if request.args \
          and 'fmt' in request.args \
          and request.args['fmt'] == 'txt':
            return Response(
                    response['abs_meta'].raw_safe,
                    mimetype='text/plain')
        return render_template('abs/abs.html', **response), code, headers
    if code == status.HTTP_301_MOVED_PERMANENTLY:
        return redirect(headers['Location'], code=code)

    raise InternalServerError('Unexpected error')


@blueprint.route('/trackback/', methods=['GET'], defaults={'arxiv_id': ''})
@blueprint.route('/trackback/<path:arxiv_id>', methods=['GET', 'POST'])
def trackback(arxiv_id: str) -> Union[str, Response]:
    """Route to define new trackbacks for papers."""
    raise InternalServerError(f'Not Yet Implemented {arxiv_id}')


@blueprint.route('/ct')
def clickthrough() -> Response:
    """Controller to log clickthrough to bookmarking sites."""
    if 'url' in request.args and 'v' in request.args \
            and is_hash_valid(current_app.config['SECRET_KEY'],
                              request.args.get('url'),
                              request.args.get('v')):
        return redirect(request.args.get('url'))

    raise NotFound()

# Satic resources (not sure how to do these in NG):
# @blueprint.route(//static.arxiv.org/css/arXiv.css?v=20170424)
# @blueprint.route(/favicon.ico)
# @blueprint.route(http://arxiv.org/)

# Not sure how to do these cross repo links,
# Will talk to Erick or look into arxiv-base to see.
# @blueprint.route(/IgnoreMe)
# @blueprint.route(/find)
# @blueprint.route(/form)
# @blueprint.route(/help)
# @blueprint.route(/help/arxiv_identifier)
# @blueprint.route(/help/arxiv_identifier)
# @blueprint.route(/help/mathjax/)
# @blueprint.route(/help/trackback/)
# @blueprint.route(/help/contact)
# @blueprint.route(/help/social_bookmarking)
# @blueprint.route(/search)
# @blueprint.route(/user/login)


@blueprint.route('/list/<context>/<subcontext>')
def list_articles(current_context: str, yymm: str) -> Response:
    """
    List articles by context, month etc.

    Context might be a context or an archive
    Subcontext should be 'recent' 'new' or a string of format yymm
    """
    raise InternalServerError(f'Not yet implemented {current_context} {yymm}')


@blueprint.route('/format/<arxiv_id>')
def format(arxiv_id: str) -> Response:
    """Get formats article."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('/pdf/<arxiv_id>')
def pdf(arxiv_id: str) -> Response:
    """Get PDF for article."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('/div/<arxiv_id>')
def div(arxiv_id: str) -> Response:
    """Get div for article."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('/html/<arxiv_id>')
def html(arxiv_id: str) -> Response:
    """Get html for article."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('/ps/<arxiv_id>')
def ps(arxiv_id: str) -> Response:
    """Get ps for article."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('/src/<arxiv_id>/anc', defaults={'file_name': None})
@blueprint.route('/src/<arxiv_id>/anc/<path:file_name>')
def src(arxiv_id: str, file_name: str) -> Response:
    """Get src for article."""
    raise InternalServerError(f'Not Yet Implemented {arxiv_id} {file_name}')


@blueprint.route('/tb/<path:arxiv_id>')
def tb(arxiv_id: str) -> Response:
    """Get tb for article."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('/show-email/<path:show_email_hash>/<path:arxiv_id>')
def show_email(show_email_hash: str, arxiv_id: str) -> Response:
    """show the email for the submitter for an article."""
    raise InternalServerError(
        f'Not Yet Implemented{show_email_hash} {arxiv_id}')


# Maybe auth protected URL in arxiv-browse?
# ('will the auth service allow paths not defined in it's
#  repo to be protected?')
@blueprint.route('/auth/show-endorsers/<path:arxiv_id>')
def show_endorsers(arxiv_id: str) -> Response:
    """show endorsers for an article."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('/refs/<path:arxiv_id>')
def refs(arxiv_id: str) -> Response:
    """Show the references for an article. (Links/proxy to inspire?)"""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('/cits/<path:arxiv_id>')
def cits(arxiv_id: str) -> Response:
    """Show the citations for an artcile. (links/proxy inspire?)"""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('/form')
def form(arxiv_id: str) -> Response:
    """Old form interface to lists of articles.(Mabye get rid of this?)"""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')
