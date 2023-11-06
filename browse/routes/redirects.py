"""Redirects for help and other paths."""
import re

from flask import Blueprint, current_app, redirect, request
from werkzeug.exceptions import BadRequest

blueprint = Blueprint("redirects", __name__)


@blueprint.route("/terms/arXiv/", defaults={"path": ""})
@blueprint.route("/terms/arXiv/<path:path>")
@blueprint.route("/terms/MSC2000/", defaults={"path": ""})
@blueprint.route("/terms/MSC2000/<path:path>")
@blueprint.route("/terms/ACM1998/", defaults={"path": ""})
@blueprint.route("/terms/ACM1998/<path:path>")
def redirect_to_api_user_manual(path: str):  # type: ignore
    """Redirects to export user manual."""
    return redirect("http://export.arxiv.org/api_help/docs/user-manual.html",
                    code=301)


@blueprint.route("/corr/subjectclasses/", defaults={"path": ""})
@blueprint.route("/corr/subjectclasses/<path:path>")
def redirect_corr_sub(path: str):  # type: ignore
    """redirect to https://arxiv.org/archive/cs."""
    return redirect("https://arxiv.org/archive/cs", code=301)


SAFE_HELP = re.compile(r"[a-zA-Z0-9.-/]*")


@blueprint.route("/help/")
@blueprint.route("/help/<path:path>")
@blueprint.route("/brand/")
@blueprint.route("/brand/<path:path>")
@blueprint.route("/hypertex/")
@blueprint.route("/hypertex/<path:path>")
@blueprint.route("/about/")
@blueprint.route("/about/<path:path>")
@blueprint.route("/new/")
@blueprint.route("/new/<path:path>")
def help_redirect(help_path: str = ""):  # type: ignore
    """Redirect to help pages."""
    help_domain = current_app.config["HELP_SERVER"]
    if SAFE_HELP.fullmatch(request.path):
        return redirect(f"https://{help_domain}/{request.path}",
                        code=301)

    raise BadRequest()


@blueprint.route("/corr/", defaults={"path": ""})
@blueprint.route("/corr/<path:path>")
def redirect_to_cs_help(path: str):   # type: ignore
    """redirect to https://info.arxiv.org/help/cs/index.html."""
    help_domain = current_app.config["HELP_SERVER"]
    return redirect(f"https://{help_domain}/help/cs/index.html",
                    code=301)
