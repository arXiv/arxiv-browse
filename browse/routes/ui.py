"""Provides the user interfaces for browse."""
import re
import geoip2.database
import bcrypt

from datetime import datetime
from typing import Callable, Dict, Mapping, Union, Tuple, Any
from flask import (
    Blueprint,
    render_template,
    request,
    Response,
    session,
    current_app,
    url_for,
    redirect,
)

# from flask import request # type: ignore    <--  doesn't work for nose
from werkzeug.exceptions import InternalServerError, BadRequest, NotFound

from arxiv import status
from arxiv.base import logging
from arxiv.base.urls.clickthrough import is_hash_valid
from arxiv import taxonomy
from browse.controllers import (
    abs_page,
    archive_page,
    home_page,
    list_page,
    prevnext,
    tb_page,
    stats_page,
)
from browse.controllers.cookies import get_cookies_page, cookies_to_set
from browse.exceptions import AbsNotFound
from browse.services.database import get_institution
from browse.controllers.year import year_page
from browse.controllers.bibtexcite import bibtex_citation

logger = logging.getLogger(__name__)
geoip_reader = None

blueprint = Blueprint("browse", __name__, url_prefix="/")


@blueprint.before_app_first_request
def load_global_data() -> None:
    """Load global data."""
    global geoip_reader
    try:
        geoip_reader = geoip2.database.Reader("data/GeoLite2-City.mmdb")
    except Exception as ex:
        logger.error("problem loading geoip database: %s", ex)


@blueprint.context_processor
def inject_now() -> Dict:
    """Inject current datetime into request context."""
    return dict(request_datetime=datetime.now())


@blueprint.before_request
def before_request() -> None:
    """ Get geo data and institutional affiliation from ip address. """
    global geoip_reader
    try:
        if geoip_reader:
            # For new db or new session vars, can force a re-check by incrementing 'geoip.version'.
            geoip_version = "1"
            if (
                "geoip.version" not in session
                or session["geoip.version"] != geoip_version
            ):
                session["geoip.version"] = geoip_version
                # https://geoip2.readthedocs.io/en/latest/
                response = geoip_reader.city(request.remote_addr)
                if response:
                    if response.continent:
                        session["continent"] = {
                            "code": response.continent.code,
                            "name": response.continent.names["en"],
                        }
                    if response.country and response.country.iso_code:
                        session["country"] = response.country.iso_code
                    if (
                        response.subdivisions
                        and response.subdivisions.most_specific
                        and response.subdivisions.most_specific.iso_code
                    ):
                        session[
                            "subnational"
                        ] = response.subdivisions.most_specific.iso_code
                    if response.city and response.city.name:
                        session["city"] = response.city.name
    # except AddressNotFoundError as ex:
    #    logger.debug('problem getting match on IP: %s', ex)
    except ValueError as ex:
        logger.debug("problem with IP address format: %s", ex)
    except Exception as ex:
        logger.debug("problem using geoip: %s", ex)

    try:
        if "hashed_user_id" not in session:
            if hasattr(request, "auth") and hasattr(request.auth, "user"):  # type: ignore
                user_id = str(request.auth.user.user_id).encode("utf-8")  # type: ignore
                salt = bcrypt.gensalt()
                tmp = bcrypt.hashpw(user_id, salt)
                hashed_user_id = str(tmp, "utf-8")
                session["hashed_user_id"] = hashed_user_id
    except Exception as ex:
        logger.debug("problem creating hashed_user_id: %s", ex)

    try:
        # Institution: store first institution found in a cookie.
        #   Users who visit multiple institutions keep first until session expires.
        #   Multiple device/browsers have separate pendo sessions
        if "institution" not in session or "institution_id" not in session:
            inst_hash = get_institution(request.remote_addr)
            if inst_hash != None and inst_hash.get("id") != None:
                session["institution_id"] = inst_hash.get("id")
                session["institution"] = inst_hash.get("label")
    except Exception as ex:
        logger.debug("problem looking up institution: %s", ex)


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
    if code == status.HTTP_200_OK:
        return render_template("home/home.html", **response), code, headers  # type: ignore

    raise InternalServerError("Unexpected error")


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

    if code == status.HTTP_200_OK:
        if request.args and "fmt" in request.args and request.args["fmt"] == "txt":
            return Response(response["abs_meta"].raw_safe, mimetype="text/plain")
        return render_template("abs/abs.html", **response), code, headers
    elif code == status.HTTP_301_MOVED_PERMANENTLY:
        return redirect(headers["Location"], code=code)
    elif code == status.HTTP_304_NOT_MODIFIED:
        return "", code, headers

    raise InternalServerError("Unexpected error")


@blueprint.route("category_taxonomy", methods=["GET"])
def category_taxonomy() -> Any:
    """Display the arXiv category taxonomy."""
    response = {
        "groups": taxonomy.definitions.GROUPS,
        "archives": taxonomy.definitions.ARCHIVES_ACTIVE,
        "categories": taxonomy.definitions.CATEGORIES_ACTIVE,
    }
    return (
        render_template("category_taxonomy.html", **response),
        status.HTTP_200_OK,
        None,
    )


@blueprint.route("tb/", defaults={"arxiv_id": ""}, methods=["GET"])
@blueprint.route("tb/<path:arxiv_id>", methods=["GET"])
def tb(arxiv_id: str) -> Response:
    """Get trackbacks associated with an article."""
    response, code, headers = tb_page.get_tb_page(arxiv_id)

    if code == status.HTTP_200_OK:
        return render_template("tb/tb.html", **response), code, headers  # type: ignore
    elif code == status.HTTP_301_MOVED_PERMANENTLY:
        return redirect(headers["Location"], code=code)  # type: ignore
    raise InternalServerError("Unexpected error")


@blueprint.route("tb/recent", methods=["GET", "POST"])
def tb_recent() -> Response:
    """Get the recent trackbacks that have been posted across the site."""
    response, code, headers = tb_page.get_recent_tb_page(request.form)

    if code == status.HTTP_200_OK:
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
    if code == status.HTTP_301_MOVED_PERMANENTLY:
        return redirect(headers["Location"], code=code)  # type: ignore
    raise InternalServerError("Unexpected error")


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
    if "url" in request.args and "v" in request.args:
        if is_hash_valid(
            current_app.config["CLICKTHROUGH_SECRET"],
            request.args.get("url"),
            request.args.get("v"),
        ):
            return redirect(request.args.get("url"))  # type: ignore
        else:
            raise BadRequest("Bad click-through redirect")

    raise NotFound


@blueprint.route(
    "list", defaults={"context": "", "subcontext": ""}, methods=["GET", "POST"]
)
@blueprint.route(
    "list/", defaults={"context": "", "subcontext": ""}, methods=["GET", "POST"]
)
@blueprint.route("list/<context>/<subcontext>", methods=["GET", "POST"])
def list_articles(context: str, subcontext: str) -> Response:
    """
    List articles by context, month etc.

    Context might be a context or an archive; Subcontext should be
    'recent', 'new' or a string of format YYMM.
    """
    response, code, headers = list_page.get_listing(context, subcontext)
    if code == status.HTTP_200_OK:
        # TODO if it is a HEAD request we don't want to render the template
        return render_template(response["template"], **response), code, headers  # type: ignore
    elif code == status.HTTP_301_MOVED_PERMANENTLY:
        return redirect(headers["Location"], code=code)  # type: ignore
    elif code == status.HTTP_304_NOT_MODIFIED:
        return "", code, headers  # type: ignore
    return response, code, headers  # type: ignore


@blueprint.route("stats/main", methods=["GET"])
def main() -> Response:
    """Display the stats main page."""
    response, code, headers = stats_page.get_main_stats_page()
    return render_template("stats/main.html", **response), code, headers  # type: ignore


@blueprint.route("stats/<string:command>", methods=["GET"])
def stats(command: str) -> Response:
    """Display various statistics about the service."""
    params: Dict = {}
    if request.args and "date" in request.args:
        params["requested_date_str"] = str(request.args["date"])

    getters: Mapping[str, Mapping[str, Union[Callable, Union[Dict, Mapping]]]] = {
        "today": {"func": stats_page.get_hourly_stats_page, "params": params},
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
        if code == status.HTTP_200_OK:
            return response["csv"], code, headers  # type: ignore
    elif command in getters:
        getter_params: Mapping = getters[command]["params"]  # type: ignore
        [response, code, headers] = getters[command]["func"](**getter_params)  # type: ignore
        if code == status.HTTP_200_OK:
            return render_template(f"stats/{command}.html", **response), code, headers  # type: ignore
    else:
        raise NotFound
    raise InternalServerError("Unexpected error")


@blueprint.route("format/<arxiv_id>")
def format(arxiv_id: str) -> Response:
    """Get formats article."""
    raise InternalServerError(f"Not yet implemented {arxiv_id}")


@blueprint.route("pdf/<arxiv_id>")
def pdf(arxiv_id: str) -> Response:
    """Get PDF for article."""
    raise InternalServerError(f"Not yet implemented {arxiv_id}")


@blueprint.route("div/<arxiv_id>")
def div(arxiv_id: str) -> Response:
    """Get div for article."""
    raise InternalServerError(f"Not yet implemented {arxiv_id}")


@blueprint.route("e-print/<arxiv_id>")
def eprint(arxiv_id: str) -> Response:
    """Get e-print (source) for article."""
    raise InternalServerError(f"Not yet implemented {arxiv_id}")


@blueprint.route("html/<arxiv_id>")
def html(arxiv_id: str) -> Response:
    """Get html for article."""
    raise InternalServerError(f"Not yet implemented {arxiv_id}")


@blueprint.route("ps/<arxiv_id>")
def ps(arxiv_id: str) -> Response:
    """Get ps for article."""
    raise InternalServerError(f"Not yet implemented {arxiv_id}")


@blueprint.route("src/<arxiv_id>/anc", defaults={"file_name": None})
@blueprint.route("src/<arxiv_id>/anc/<path:file_name>")
def src(arxiv_id: str, file_name: str) -> Response:
    """Get src for article."""
    raise InternalServerError(f"Not Yet Implemented {arxiv_id} {file_name}")


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


@blueprint.route("archive/", defaults={"archive": None})
@blueprint.route("archive/<archive>", strict_slashes=False)
def archive(archive: str):  # type: ignore
    """Landing page for an archive."""
    response, code, headers = archive_page.get_archive(archive)
    if code == status.HTTP_200_OK or code == status.HTTP_404_NOT_FOUND:
        return render_template(response["template"], **response), code, headers
    elif code == status.HTTP_301_MOVED_PERMANENTLY:
        return redirect(headers["Location"], code=code)
    elif code == status.HTTP_304_NOT_MODIFIED:
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


@blueprint.route("year/<archive>", defaults={"year": None})
@blueprint.route("year/<archive>/", defaults={"year": None}, strict_slashes=False)
@blueprint.route("year/<archive>/<int:year>/")
@blueprint.route("year/<archive>/<int:year>")
def year(archive: str, year: int):  # type: ignore
    """Year's stats for an archive."""
    response, code, headers = year_page(archive, year)
    if code == status.HTTP_307_TEMPORARY_REDIRECT:
        return "", code, headers
    return render_template("year.html", **response), code, headers


@blueprint.route("cookies", defaults={"set": ""})
@blueprint.route("cookies/<set>", methods=["POST", "GET"])
def cookies(set):  # type: ignore
    """Cookies landing page and setter."""
    is_debug = request.args.get("debug", None) is not None
    if request.method == "POST":
        debug = {"debug": "1"} if is_debug else {}
        resp = redirect(url_for("browse.cookies", **debug))
        for ctoset in cookies_to_set(request):
            resp.set_cookie(**ctoset)  # type: ignore
        return resp
    response, code, headers = get_cookies_page(is_debug)
    return render_template("cookies.html", **response), code, headers


@blueprint.route('bibtex/<path:arxiv_id>', methods=['GET'])
def bibtex(arxiv_id: str):  # type: ignore
    """Bibtex for a paper."""
    return bibtex_citation(arxiv_id)
