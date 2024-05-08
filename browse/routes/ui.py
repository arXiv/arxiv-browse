"""Provides the user interfaces for browse."""
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Tuple, Union, Optional
from http import HTTPStatus as status

from arxiv.taxonomy.definitions import GROUPS
from arxiv.base import logging
from arxiv.base.urls.clickthrough import is_hash_valid
from flask import (
    Blueprint,
    Response,
    current_app,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound

from browse.controllers import (
    abs_page,
    archive_page,
    home_page,
    list_page,
    prevnext,
    stats_page,
    tb_page,
    add_surrogate_key
)
from browse.controllers.openurl_cookie import make_openurl_cookie, get_openurl_page
from browse.controllers.cookies import get_cookies_page, cookies_to_set
from browse.exceptions import AbsNotFound # TODO: BASE
from browse.services.database import get_institution
from browse.controllers.year import year_page
from browse.controllers.bibtexcite import bibtex_citation
from browse.controllers.list_page import author

logger = logging.getLogger(__name__)
geoip_reader = None

blueprint = Blueprint("browse", __name__, url_prefix="/")


@blueprint.app_context_processor
def inject_now() -> Dict:
    """Inject current datetime into request context."""
    return dict(request_datetime=datetime.now())


@blueprint.after_request
def apply_response_headers(response: Response) -> Response:
    """Apply response headers to all responses."""
    """Prevent UI redress attacks."""
    response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    return response


@blueprint.route("index", methods=["GET"])
@blueprint.route("/", methods=["GET"])
def home() -> Response:
    """Home page view."""
    response, code, headers = home_page.get_home_page()
    if code == status.OK:
        return render_template("home/home.html", **response), code, headers  # type: ignore

    raise InternalServerError("Unexpected error")

@blueprint.route("/favicon.ico")
@blueprint.route("/apple-touch-icon-120x120-precomposed.png")
@blueprint.route("/apple-touch-icon-120x120.png")
@blueprint.route("/apple-touch-icon-precomposed.png")
def favicon() -> Response:
    """Send favicon."""
    return send_file(Path(current_app.root_path, "static/images/icons/favicon.ico"))

@blueprint.route("abs", methods=["GET"])
def bare_abs() -> Any:
    """Check several legacy request parameters."""
    if request.args:
        if "id" in request.args:
            return abstract(request.args["id"])
        elif "archive" in request.args and "papernum" in request.args:
            return abstract(f"{request.args['archive']}/{request.args['papernum']}")
        else:
            for param in request.args:
                # singleton case, where the parameter is the value
                # e.g. /abs?<archive>/\d{7}
                if not request.args[param] and re.match(
                    r"^[a-z\-]+(\.[A-Z]{2})?\/\d{7}$", param
                ):
                    return abstract(param)

    """Return abs-specific 404."""
    raise AbsNotFound


@blueprint.route("abs/", methods=["GET"], defaults={"arxiv_id": ""})
@blueprint.route("abs/<path:arxiv_id>", methods=["GET"])
def abstract(arxiv_id: str) -> Any:
    """Abstract (abs) page view."""
    response, code, headers = abs_page.get_abs_page(arxiv_id)

    if code == status.OK:
        if request.args and "fmt" in request.args and request.args["fmt"] == "txt":
            return Response(response["abs_meta"].raw(), mimetype="text/plain")
        return render_template("abs/abs.html", **response), code, headers
    elif code == status.MOVED_PERMANENTLY:
        return redirect(headers["Location"], code=code)
    elif code == status.NOT_MODIFIED:
        return "", code, headers

    raise InternalServerError("Unexpected error")


@blueprint.route("category_taxonomy", methods=["GET"])
def category_taxonomy() -> Any:
    """Display the arXiv category taxonomy."""
    response = {"groups": GROUPS}
    return (
        render_template("category_taxonomy.html", **response),
        status.OK,
        None,
    )

@blueprint.route("institutional_banner", methods=["GET"])
def institutional_banner() -> Any:
    try:
        result = get_institution(request.remote_addr)
        if result:
            return (result, status.OK)
        else:
            return ("{}", status.OK)
    except Exception as ex:
        return ("", status.INTERNAL_SERVER_ERROR)


@blueprint.route("tb/recent", methods=["GET", "POST"])
def tb_recent() -> Response:
    """Get the recent trackbacks that have been posted across the site."""
    response, code, headers = tb_page.get_recent_tb_page(request.form)

    if code == status.OK:
        return render_template("tb/recent.html", **response), code, headers  # type: ignore
    raise InternalServerError("Unexpected error")


@blueprint.route(
    "tb/redirect/",
    methods=["GET"],
    defaults={"trackback_id": "", "hashed_document_id": ""},
)
@blueprint.route(
    "tb/redirect/<string:trackback_id>/<string:hashed_document_id>", methods=["GET"]
)
def tb_redirect(trackback_id: str, hashed_document_id: str) -> Response:
    """Get the trackback redirect link."""
    response, code, headers = tb_page.get_tb_redirect(trackback_id, hashed_document_id)
    if code == status.MOVED_PERMANENTLY:
        return redirect(headers["Location"], code=code)  # type: ignore
    raise InternalServerError("Unexpected error")


@blueprint.route("tb/<path:arxiv_id>", methods=["GET"])
def tb(arxiv_id: str) -> Response:
    """Get trackbacks associated with an article."""
    response, code, headers = tb_page.get_tb_page(arxiv_id)
    if code == status.OK:
        return render_template("tb/tb.html", **response), code, headers  # type: ignore
    elif code == status.MOVED_PERMANENTLY:
        return redirect(headers["Location"], code=code)  # type: ignore
    raise InternalServerError("Unexpected error")


@blueprint.route("tb", strict_slashes=False)
def tb_nothing() -> Response:
    """Handle a no data trackback."""
    raise BadRequest()


@blueprint.route("prevnext", methods=["GET", "POST"])
def previous_next() -> Tuple[Dict[str, Any], int, Dict[str, Any]]:
    """Previous/Next navigation used on /abs page."""
    return prevnext.get_prevnext(
        request.args.get("id", default=""),
        request.args.get("function", default=""),
        request.args.get("context", default=""),
    )


@blueprint.route("trackback/", methods=["GET"], defaults={"arxiv_id": ""})
@blueprint.route("trackback/<path:arxiv_id>", methods=["GET", "POST"])
def trackback(arxiv_id: str) -> Union[str, Response]:
    """Route to define new trackbacks for papers."""
    raise InternalServerError(f"Not Yet Implemented {arxiv_id}")


@blueprint.route("ct")
def clickthrough() -> Response:
    """Generate redirect for clickthrough links."""
    # Phasing out clickthrough and just supporting until all the links are gone.
    if datetime.now().year > 2024:
        raise NotFound

    if 'url' in request.args and 'v' in request.args:
        sec = current_app.config["CLICKTHROUGH_SECRET"].get_secret_value()
        url = request.args.get('url')
        v = request.args.get('v')
        if url and v and is_hash_valid(sec, url, v):
            return redirect(url)  # type: ignore
        else:
            raise BadRequest("Bad click-through redirect")

    raise NotFound


@blueprint.route(
    "list", defaults={"context": "", "subcontext": ""}, methods=["GET", "POST"],
    strict_slashes=False
)
@blueprint.route("list/<context>/<subcontext>", methods=["GET", "POST"])
def list_articles(context: str, subcontext: str) -> Response:
    """
    List articles by context, month etc.

    Context might be a context or an archive; Subcontext should be
    'recent', 'new' or a string of format YYMM.
    """
    response, code, headers = list_page.get_listing(context, subcontext)
    headers.update(add_surrogate_key(headers,["list"]))
    if code == status.OK:
        #if subcontext not in ["new", "recent", "pastweek"]:
            #response=_add_year_url_alert(response)

        # TODO if it is a HEAD request we don't want to render the template
        return render_template(response["template"], **response), code, headers  # type: ignore
    elif code == status.MOVED_PERMANENTLY:
        return redirect(headers["Location"], code=code)  # type: ignore
    elif code == status.NOT_MODIFIED:
        return "", code, headers  # type: ignore
    return response, code, headers  # type: ignore


@blueprint.route("stats/main", methods=["GET"])
def main() -> Response:
    """Display the stats main page."""
    response, code, headers = stats_page.get_main_stats_page()
    return render_template("stats/main.html", **response), code, headers  # type: ignore



@blueprint.route("stats/today", methods=["GET"])
def stats_today() -> Response:
    """Display statistics about today or a day."""
    if request.args and "date" in request.args:
        date = str(request.args["date"])
    else:
        date = None
    [response, code, headers] = stats_page.get_hourly_stats_page(current_app.config["ARXIV_BUSINESS_TZ"], date)
    return render_template("stats/today.html", **response), code, headers  # type: ignore


@blueprint.route("stats/<string:command>", methods=["GET"])
def stats(command: str) -> Response:
    """Display various statistics about the service."""
    params: Dict = {}
    if request.args and "date" in request.args:
        params["requested_date_str"] = str(request.args["date"])

    getters: Mapping[str, Mapping[str, Union[Callable, Union[Dict, Mapping]]]] = {
        "monthly_submissions": {
            "func": stats_page.get_monthly_submissions_page,
            "params": {},
        },
        "monthly_downloads": {
            "func": stats_page.get_monthly_downloads_page,
            "params": {},
        },
    }
    csv_getters: Mapping[str, Mapping[str, Union[Callable, Union[Dict, Mapping]]]] = {
        "get_hourly": {"func": stats_page.get_hourly_stats_csv, "params": params},
        "get_monthly_downloads": {
            "func": stats_page.get_download_stats_csv,
            "params": {},
        },
        "get_monthly_submissions": {
            "func": stats_page.get_submission_stats_csv,
            "params": {},
        },
    }
    if not command:
        raise NotFound
    if command in csv_getters:
        csv_getter_params: Mapping = csv_getters[command]["params"]  # type: ignore
        [response, code, headers] = csv_getters[command]["func"](  # type: ignore
            **csv_getter_params
        )
        if code == status.OK:
            return response["csv"], code, headers  # type: ignore
    elif command in getters:
        getter_params: Mapping = getters[command]["params"]  # type: ignore
        [response, code, headers] = getters[command]["func"](**getter_params)  # type: ignore
        if code == status.OK:
            return render_template(f"stats/{command}.html", **response), code, headers  # type: ignore
    else:
        raise NotFound
    raise InternalServerError("Unexpected error")


@blueprint.route("show-email/<path:show_email_hash>/<path:arxiv_id>")
def show_email(show_email_hash: str, arxiv_id: str) -> Response:
    """Show the email for the submitter for an article."""
    raise InternalServerError(f"Not Yet Implemented{show_email_hash} {arxiv_id}")


# Maybe auth protected URL in arxiv-browse?
# ('will the auth service allow paths not defined in it's
#  repo to be protected?')
@blueprint.route("auth/show-endorsers/<path:arxiv_id>")
def show_endorsers(arxiv_id: str) -> Response:
    """Show endorsers for an article."""
    raise InternalServerError(f"Not yet implemented {arxiv_id}")


@blueprint.route("refs/<path:arxiv_id>")
def refs(arxiv_id: str) -> Response:
    """Show the references for an article."""
    raise InternalServerError(f"Not yet implemented {arxiv_id}")


@blueprint.route("cits/<path:arxiv_id>")
def cits(arxiv_id: str) -> Response:
    """Show the citations for an artcile."""
    raise InternalServerError(f"Not yet implemented {arxiv_id}")


@blueprint.route("form")
def form(arxiv_id: str) -> Response:
    """Old form interface to lists of articles."""
    raise InternalServerError(f"Not yet implemented {arxiv_id}")


@blueprint.route("archive")
@blueprint.route("archive/")
@blueprint.route("archive/<archive>", strict_slashes=False)
def archive(archive: Optional[str] = None):  # type: ignore
    """Landing page for an archive."""
    if archive is None:
        return archive_page.archive_index("list", status_in=200)

    response, code, headers = archive_page.get_archive(archive)
    if code == status.OK or code == status.NOT_FOUND:
        return render_template(response["template"], **response), code, headers
    elif code == status.MOVED_PERMANENTLY:
        return redirect(headers["Location"], code=code)
    elif code == status.NOT_MODIFIED:
        return "", code, headers
    return response, code, headers


@blueprint.route("archive/<archive>/<junk>", strict_slashes=False)
def archive_with_extra(archive: str, junk: str):  # type: ignore
    """
    Archive page with extra, 301 redirect to just the archive.

    This handles some odd URLs that have ended up in search engines.
    See also ARXIVOPS-2119.
    """
    return redirect(url_for("browse.archive", archive=archive), code=301)


@blueprint.route("year/<archive>")
@blueprint.route("year/<archive>/")
def year_default(archive: str):  # type: ignore
    """Year's stats for an archive."""
    response, code, headers = year_page(archive, None)
    if code == status.TEMPORARY_REDIRECT:
        return "", code, headers
    elif code == status.MOVED_PERMANENTLY:
        return redirect(headers["Location"], code=code) 
    response=_add_year_url_alert(response)
    return render_template("year.html", **response), code, headers


@blueprint.route("year/<archive>/<int:year>/")
@blueprint.route("year/<archive>/<int:year>")
def year(archive: str, year: int):  # type: ignore
    """Year's stats for an archive."""
    response, code, headers = year_page(archive, year)
    if code == status.TEMPORARY_REDIRECT:
        return "", code, headers
    elif code == status.MOVED_PERMANENTLY:
        return redirect(headers["Location"], code=code) 
    response=_add_year_url_alert(response)
    return render_template("year.html", **response), code, headers


@blueprint.route("cookies", defaults={"set": ""})
@blueprint.route("cookies/<set>", methods=["POST", "GET"])
def cookies(set):  # type: ignore
    """Cookies landing page and setter."""
    is_debug = request.args.get("debug", None) is not None
    if request.method == "POST":
        debug = {"debug": "1"} if is_debug else {}
        resp = redirect(url_for("browse.cookies", **debug)) # type: ignore
        for ctoset in cookies_to_set(request):
            resp.set_cookie(**ctoset) # type: ignore
        return resp
    response, code, headers = get_cookies_page(is_debug)
    return render_template("cookies.html", **response), code, headers


@blueprint.route('bibtex/<path:arxiv_id>', methods=['GET'])
def bibtex(arxiv_id: str):  # type: ignore
    """BibTeX for a paper."""
    return bibtex_citation(arxiv_id)


@blueprint.route("robots.txt")
def robots_txt() -> Response:
    """Robots.txt endpoint."""
    # This is intended for browse.arxiv.org before this code is at arxiv.org
    return make_response("User-agent: * \nDisallow: /", 200)


@blueprint.route('openurl-cookie', methods=['GET', 'POST'])
def openurl_cookie (): # type: ignore
    if request.method == 'POST':
        resp = redirect(url_for('browse.openurl_cookie'))
        resp.set_cookie(**make_openurl_cookie())  # type: ignore
        return resp
    response, code, headers = get_openurl_page()
    return render_template('openurl_cookies.html', **response), code, headers


@blueprint.route('a/<id>.<any("html", "json", "atom", "atom2"):ext>', methods=['GET'])
@blueprint.route('a/<id>', defaults={'ext': None}, methods=['GET'])
def a (id: str, ext: str):  # type: ignore
    if ext is None and '.' in id:
        raise BadRequest
    if ext == 'atom':
        return Response(author.get_atom(id), content_type='application/atom+xml')
    if ext == 'atom2':
        return Response(author.get_atom2(id), mimetype='application/atom+xml')
    if ext == 'json':
        ajson = author.get_json(id)
        if ajson is not None:
            return ajson
        else:
            return make_response("", 404, {})

    response, code, headers = author.get_html_page(id)
    return render_template('list/author.html', **response), code, headers

def _add_year_url_alert(data: Dict[str, Any]) -> Dict[str, Any]:
    alert_title = "Change to 4 digit year in URLs"
    alert_content = "ArXiv is updating URLs for the /list and /year paths to use 4 digit years: /YYYY for years and /YYYY-MM for months. Old paths will be redirected to the new correct forms where possible. Caution: /2002 no longer represents Feb 2020; it now represents the year 2002."

    data['alert_title'] = alert_title
    data['alert_content'] = alert_content
    return data
