"""RePEc interface for arXiv.

Reimplementation of the legacy ``repec.pl`` CGI script. Serves the
RePEc/ReDIF metadata for the Quantitative Finance (q-fin) and Economics
(econ) sections of arXiv, following the pseudo-HTML/ReDIF "HTTP server"
format documented at http://ideas.repec.org/t/httpserver.html.
"""
import re
import textwrap
from datetime import date
from typing import Dict, List, Optional, Tuple

from arxiv.authors import parse_author_affil
from arxiv.document.exceptions import AbsException
from arxiv.taxonomy.definitions import GROUPS
from arxiv.base import logging

from browse.services.documents import get_doc_service
from browse.services.database import get_repec_paper_ids

logger = logging.getLogger(__name__)

REPEC_PREFIX = "arx"
REPEC_DIR = "papers"
REPEC_ARCHIVE_HANDLE = f"RePEc:{REPEC_PREFIX}"
REPEC_SERIES_HANDLE = f"RePEc:{REPEC_PREFIX}:{REPEC_DIR}"
REPEC_URL = "https://arxiv.org/repec/"
REPEC_ARCHIVE = f"{REPEC_PREFIX}arch.rdf"
REPEC_SERIES = f"{REPEC_PREFIX}seri.rdf"
ADMIN_EMAIL = "help@arxiv.org"

PATH_RE = re.compile(r"^[\w./]*$")


def get_repec(path: str) -> Tuple[str, int, str]:
    """Dispatch a RePEc request by its local path.

    Returns a ``(body, status_code, content_type)`` tuple.
    """
    if not PATH_RE.match(path):
        return _not_found("The resource URI appears to contain illegal characters.\n")

    if path == "":
        return _index([REPEC_ARCHIVE, REPEC_SERIES, f"{REPEC_DIR}/"])
    if path == REPEC_ARCHIVE:
        return _archive()
    if path == REPEC_SERIES:
        return _series()
    if path.startswith(f"{REPEC_DIR}/"):
        remainder = path[len(f"{REPEC_DIR}/"):]
        item_files = _item_files()
        if remainder == "":
            return _index(sorted(item_files.keys()))
        if remainder in item_files:
            return _items(item_files[remainder])
        return _not_found(
            f"No item template {remainder} is available in the {REPEC_DIR} series"
        )

    return _not_found(f"The local URI path was {path}.\n")


def _not_found(msg: str = "") -> Tuple[str, int, str]:
    body = (
        "The arXiv/RePEc resource requested is not available, "
        f"try starting at {REPEC_URL}\n"
    )
    if msg:
        body += msg
    return body, 404, "text/plain"


def _index(paths: List[str]) -> Tuple[str, int, str]:
    """Write a RePEc index in the pseudo-HTML format."""
    lines = ["<HTML>"]
    for path in paths:
        lines.append(f"<BR><A HREF={path}>{path}</A>")
    lines.append("</HTML>\n")
    return "\n".join(lines), 200, "text/html"


def _archive() -> Tuple[str, int, str]:
    body = (
        "Template-type: ReDIF-Archive 1.0\n"
        f"Handle: {REPEC_ARCHIVE_HANDLE}\n"
        "Name: arXiv.org\n"
        f"Maintainer-Email: {ADMIN_EMAIL}\n"
        "Description: The Quantitative Finance and Economics sections of arXiv.org\n"
        f"URL: {REPEC_URL}\n"
    )
    return body, 200, "text/plain"


def _series() -> Tuple[str, int, str]:
    body = (
        "Template-type: ReDIF-Series 1.0\n"
        "Name: Papers\n"
        "Provider-Name: arXiv.org\n"
        "Provider-Homepage: https://arxiv.org/\n"
        "Maintainer-Name: arXiv administrators\n"
        f"Maintainer-Email: {ADMIN_EMAIL}\n"
        "Type: ReDIF-Paper\n"
        f"Handle: {REPEC_SERIES_HANDLE}\n"
    )
    return body, 200, "text/plain"


def _item_files() -> Dict[str, int]:
    """Map of by-year template files to year, from q-fin's start to now.

    q-fin predates econ, so its group start year is an acceptable start.
    """
    start_year = GROUPS["grp_q-fin"].start_year
    end_year = date.today().year
    return {f"{year}.rdf": year for year in range(start_year, end_year + 1)}


def _items(year: int) -> Tuple[str, int, str]:
    parts: List[str] = []
    for paper_id in get_repec_paper_ids(year):
        item = _item(paper_id)
        if item is not None:
            parts.append(f"\n#arXiv:{paper_id}\n")
            parts.append(item)
    return "".join(parts), 200, "text/plain"


def _item(paper_id: str) -> Optional[str]:
    """Render a single ReDIF-Paper record, or None if metadata is unavailable."""
    try:
        metadata = get_doc_service().get_abs(paper_id)
    except AbsException:
        logger.warning("RePEc bad item %s, ignored", paper_id)
        return None

    lines = ["Template-type: ReDIF-Paper 1.0"]

    for author in parse_author_affil(metadata.authors.raw):
        key, first, suffix, *affils = author
        name = key
        if first:
            name = f"{first} {name}"
        if suffix:
            name = f"{name} {suffix}"
        lines.append(f"Author-Name: {name}")
        if first:
            lines.append(f"Author-X-Name-First: {first}")
        lines.append(f"Author-X-Name-Last: {key}")
        for affil in affils:
            lines.append(f"Author-Workplace-Name: {affil}")

    lines.append(f"Title: {metadata.title}")

    # The DB stores the abstract as a single unwrapped line, whereas the legacy
    # .abs files were hard-wrapped at 80 columns. Re-wrap and indent every line
    # by two spaces so continuation lines aren't mistaken for ReDIF tokens.
    abstract = textwrap.fill(
        " ".join(metadata.abstract.split()),
        width=80,
        initial_indent="  ",
        subsequent_indent="  ",
        break_long_words=False,
        break_on_hyphens=False,
    )
    lines.append(f"Abstract: {abstract}")

    versions = sorted(metadata.version_history, key=lambda v: v.version)
    cdate = versions[0].submitted_date
    rdate = versions[-1].submitted_date
    lines.append(f"Creation-Date: {cdate.strftime('%Y-%m')}")
    if cdate != rdate:
        lines.append(f"Revision-Date: {rdate.strftime('%Y-%m')}")

    if metadata.journal_ref:
        lines.append(f"Publication-Status: Published in {metadata.journal_ref}")

    lines.append(f"File-URL: https://arxiv.org/pdf/{paper_id}")
    lines.append("File-Format: application/pdf")
    lines.append("File-Function: Latest version")

    lines.append(f"Handle: {REPEC_SERIES_HANDLE}:{paper_id}\n")

    return "\n".join(lines) + "\n"
