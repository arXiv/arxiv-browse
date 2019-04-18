"""Provides the user intefaces for browse."""
import re
from datetime import datetime
from typing import Callable, Dict, Mapping, Union
from flask import Blueprint, render_template, request, Response, session, \
    current_app, url_for, redirect
from werkzeug.exceptions import InternalServerError, BadRequest, NotFound

from arxiv import status
from arxiv.base import logging
from arxiv.base.urls.clickthrough import is_hash_valid
from browse.controllers import abs_page, archive_page, home_page, list_page, \
    prevnext, tb_page, stats_page
from browse.controllers.cookies import get_cookies_page, cookies_to_set
from browse.exceptions import AbsNotFound
from browse.services.database import get_institution
from browse.controllers.year import year_page

logger = logging.getLogger(__name__)

blueprint = Blueprint('browse', __name__, url_prefix='/')


@blueprint.context_processor
def inject_now() -> None:
    return dict(request_datetime=datetime.now())


@blueprint.before_request
def before_request() -> None:
    """Get instituional affiliation from session."""
    if 'institution' not in session:
        logger.debug('Adding institution to session')
        session['institution'] = get_institution(request.remote_addr)


@blueprint.after_request
def apply_response_headers(response: Response) -> Response:
    """Apply response headers to all responses."""
    """Prevent UI redress attacks."""
    response.headers['Content-Security-Policy'] = "frame-ancestors 'none'"
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'

    return response


@blueprint.route('index', methods=['GET'])
@blueprint.route('/', methods=['GET'])
def home() -> Response:
    """Home page view."""
    response, code, headers = home_page.get_home_page()
    if code == status.HTTP_200_OK:
        return render_template('home/home.html', **response), code, headers  # type: ignore

    raise InternalServerError('Unexpected error')


@blueprint.route('abs', methods=['GET'])
def bare_abs() -> Response:
    """Check several legacy request parameters."""
    if request.args:
        if 'id' in request.args:
            return abstract(request.args['id'])  # type: ignore
        elif 'archive' in request.args and 'papernum' in request.args:
            return abstract(  # type: ignore
                f"{request.args['archive']}/{request.args['papernum']}")
        else:
            for param in request.args:
                # singleton case, where the parameter is the value
                # e.g. /abs?<archive>/\d{7}
                if not request.args[param] \
                   and re.match(r'^[a-z\-]+(\.[A-Z]{2})?\/\d{7}$', param):
                    return abstract(param)  # type: ignore

    """Return abs-specific 404."""
    raise AbsNotFound


@blueprint.route('abs/', methods=['GET'], defaults={'arxiv_id': ''})
@blueprint.route('abs/<path:arxiv_id>', methods=['GET'])
def abstract(arxiv_id: str) -> Response:
    """Abstract (abs) page view."""
    response, code, headers = abs_page.get_abs_page(arxiv_id)

    if code == status.HTTP_200_OK:
        if request.args \
                and 'fmt' in request.args \
                and request.args['fmt'] == 'txt':
            return Response(
                response['abs_meta'].raw_safe,
                mimetype='text/plain')
        return render_template('abs/abs.html', **response), code, headers  # type: ignore
    elif code == status.HTTP_301_MOVED_PERMANENTLY:
        return redirect(headers['Location'], code=code)  # type: ignore
    elif code == status.HTTP_304_NOT_MODIFIED:
        return '', code, headers  # type: ignore

    raise InternalServerError('Unexpected error')


@blueprint.route('tb/', defaults={'arxiv_id': ''}, methods=['GET'])
@blueprint.route('tb/<path:arxiv_id>', methods=['GET'])
def tb(arxiv_id: str) -> Response:
    """Get trackbacks associated with an article."""
    response, code, headers = tb_page.get_tb_page(arxiv_id)

    if code == status.HTTP_200_OK:
        return render_template('tb/tb.html', **response), code, headers  # type: ignore
    elif code == status.HTTP_301_MOVED_PERMANENTLY:
        return redirect(headers['Location'], code=code)  # type: ignore
    raise InternalServerError('Unexpected error')


@blueprint.route('tb/recent', methods=['GET', 'POST'])
def tb_recent() -> Response:
    """Get the recent trackbacks that have been posted across the site."""
    response, code, headers = tb_page.get_recent_tb_page(request.form)

    if code == status.HTTP_200_OK:
        return render_template('tb/recent.html', **response), code, headers  # type: ignore
    raise InternalServerError('Unexpected error')


@blueprint.route('tb/redirect/',
                 methods=['GET'],
                 defaults={'trackback_id': '', 'hashed_document_id': ''})
@blueprint.route('tb/redirect/<string:trackback_id>/<string:hashed_document_id>',
                 methods=['GET'])
def tb_redirect(trackback_id: str, hashed_document_id: str) -> Response:
    """Get the trackback redirect link."""
    response, code, headers = tb_page.get_tb_redirect(trackback_id,
                                                      hashed_document_id)
    if code == status.HTTP_301_MOVED_PERMANENTLY:
        return redirect(headers['Location'], code=code)  # type: ignore
    raise InternalServerError('Unexpected error')


@blueprint.route('prevnext', methods=['GET', 'POST'])
def previous_next() -> Union[str, Response]:
    """Previous/Next navigation used on /abs page."""
    if not request.args:
        raise BadRequest
    response, code, headers = prevnext.get_prevnext(request.args)
    if code == status.HTTP_301_MOVED_PERMANENTLY:
        return redirect(headers['Location'], code=code)  # type: ignore
    raise InternalServerError('Unexpected error')


@blueprint.route('trackback/', methods=['GET'], defaults={'arxiv_id': ''})
@blueprint.route('trackback/<path:arxiv_id>', methods=['GET', 'POST'])
def trackback(arxiv_id: str) -> Union[str, Response]:
    """Route to define new trackbacks for papers."""
    raise InternalServerError(f'Not Yet Implemented {arxiv_id}')


@blueprint.route('ct')
def clickthrough() -> Response:
    """Generate redirect for clickthrough links."""
    if 'url' in request.args and 'v' in request.args:
        if is_hash_valid(current_app.config['CLICKTHROUGH_SECRET'],
                         request.args.get('url'),
                         request.args.get('v')):
            return redirect(request.args.get('url'))  # type: ignore
        else:
            raise BadRequest('Bad click-through redirect')

    raise NotFound


@blueprint.route('list', defaults={'context': '', 'subcontext': ''},
                 methods=['GET', 'POST'])
@blueprint.route('list/', defaults={'context': '', 'subcontext': ''},
                 methods=['GET', 'POST'])
@blueprint.route('list/<context>/<subcontext>', methods=['GET', 'POST'])
def list_articles(context: str, subcontext: str) -> Response:
    """
    List articles by context, month etc.

    Context might be a context or an archive; Subcontext should be
    'recent', 'new' or a string of format YYMM.
    """
    response, code, headers = \
        list_page.get_listing(context, subcontext)  # type: ignore
    if code == status.HTTP_200_OK:
        # TODO if it is a HEAD request we don't want to render the template
        return render_template(response['template'], **response), code, headers  # type: ignore
    elif code == status.HTTP_301_MOVED_PERMANENTLY:
        return redirect(headers['Location'], code=code)  # type: ignore
    elif code == status.HTTP_304_NOT_MODIFIED:
        return '', code, headers  # type: ignore
    return response, code, headers  # type: ignore


@blueprint.route('stats/<string:command>',
                 methods=['GET'])
def stats(command: str) -> Response:
    """Display various statistics about the service."""
    params: Dict = {}
    if request.args and 'date' in request.args:
        params['requested_date_str'] = str(request.args['date'])

    getters: Mapping[str, Mapping[str, Union[Callable, Union[Dict, Mapping]]]] = {
        'today':  {'func': stats_page.get_hourly_stats_page, 'params': params},
        'monthly_submissions':
            {'func': stats_page.get_monthly_submissions_page, 'params': {}},
        'monthly_downloads':
            {'func': stats_page.get_monthly_downloads_page, 'params': {}}
    }
    csv_getters: Mapping[str, Mapping[str, Union[Callable, Union[Dict, Mapping]]]] = {
        'get_hourly':
            {'func': stats_page.get_hourly_stats_csv, 'params': params},
        'get_monthly_downloads':
            {'func': stats_page.get_download_stats_csv, 'params': {}},
        'get_monthly_submissions':
            {'func': stats_page.get_submission_stats_csv, 'params': {}}
    }
    if not command:
        raise NotFound
    if command in csv_getters:
        csv_getter_params: Mapping = csv_getters[command]['params']  # type: ignore
        [response, code, headers] = csv_getters[command]['func'](  # type: ignore
            **csv_getter_params)
        if code == status.HTTP_200_OK:
            return response['csv'], code, headers  # type: ignore
    elif command in getters:
        getter_params: Mapping = getters[command]['params']  # type: ignore
        [response, code, headers] = getters[command]['func'](**getter_params)  # type: ignore
        if code == status.HTTP_200_OK:
            return render_template(f'stats/{command}.html', **response), code, headers  # type: ignore
    else:
        raise NotFound
    raise InternalServerError('Unexpected error')


@blueprint.route('format/<arxiv_id>')
def format(arxiv_id: str) -> Response:
    """Get formats article."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('pdf/<arxiv_id>')
def pdf(arxiv_id: str) -> Response:
    """Get PDF for article."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('div/<arxiv_id>')
def div(arxiv_id: str) -> Response:
    """Get div for article."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('e-print/<arxiv_id>')
def eprint(arxiv_id: str) -> Response:
    """Get e-print (source) for article."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('html/<arxiv_id>')
def html(arxiv_id: str) -> Response:
    """Get html for article."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('ps/<arxiv_id>')
def ps(arxiv_id: str) -> Response:
    """Get ps for article."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('src/<arxiv_id>/anc', defaults={'file_name': None})
@blueprint.route('src/<arxiv_id>/anc/<path:file_name>')
def src(arxiv_id: str, file_name: str) -> Response:
    """Get src for article."""
    raise InternalServerError(f'Not Yet Implemented {arxiv_id} {file_name}')


@blueprint.route('show-email/<path:show_email_hash>/<path:arxiv_id>')
def show_email(show_email_hash: str, arxiv_id: str) -> Response:
    """Show the email for the submitter for an article."""
    raise InternalServerError(
        f'Not Yet Implemented{show_email_hash} {arxiv_id}')


# Maybe auth protected URL in arxiv-browse?
# ('will the auth service allow paths not defined in it's
#  repo to be protected?')
@blueprint.route('auth/show-endorsers/<path:arxiv_id>')
def show_endorsers(arxiv_id: str) -> Response:
    """Show endorsers for an article."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('refs/<path:arxiv_id>')
def refs(arxiv_id: str) -> Response:
    """Show the references for an article."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('cits/<path:arxiv_id>')
def cits(arxiv_id: str) -> Response:
    """Show the citations for an artcile."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('form')
def form(arxiv_id: str) -> Response:
    """Old form interface to lists of articles."""
    raise InternalServerError(f'Not yet implemented {arxiv_id}')


@blueprint.route('archive/', defaults={'archive': None})
@blueprint.route('archive/<archive>')
def archive(archive: str):  # type: ignore
    """Landing page for an archive."""
    response, code, headers = archive_page.get_archive(archive)  # type: ignore
    if code == status.HTTP_200_OK or code == status.HTTP_404_NOT_FOUND:
        return render_template(response['template'], **response), code, headers
    elif code == status.HTTP_301_MOVED_PERMANENTLY:
        return redirect(headers['Location'], code=code)
    elif code == status.HTTP_304_NOT_MODIFIED:
        return '', code, headers
    return response, code, headers


@blueprint.route('year/<archive>', defaults={'year': None})
@blueprint.route('year/<archive>/', defaults={'year': None}, strict_slashes=False)
@blueprint.route('year/<archive>/<int:year>/')
@blueprint.route('year/<archive>/<int:year>')
def year(archive: str, year: int):  # type: ignore
    """Year's stats for an archive."""
    response, code, headers = year_page(archive, year)
    if code == status.HTTP_307_TEMPORARY_REDIRECT:
        return '', code, headers
    return render_template('year.html', **response), code, headers


@blueprint.route('cookies', defaults={'set': ''})
@blueprint.route('cookies/<set>', methods=['POST', 'GET'])
def cookies(set):  # type: ignore
    """Cookies landing page and setter."""
    is_debug = request.args.get('debug', None) is not None
    if request.method == 'POST':
        debug = {'debug': '1'} if is_debug else {}
        resp = redirect(url_for('browse.cookies', **debug))
        for ctoset in cookies_to_set(request):
            resp.set_cookie(**ctoset)  # type: ignore
        return resp
    response, code, headers = get_cookies_page(is_debug)
    return render_template('cookies.html', **response), code, headers
