"""Archive landing page."""

import datetime
from typing import Any, Dict, List, Tuple
from http import HTTPStatus as status

from arxiv.taxonomy.definitions import ARCHIVES, ARCHIVES_SUBSUMED, CATEGORIES

from browse.controllers import biz_tz
from browse.controllers.archive_page.by_month_form import ByMonthForm
from browse.controllers.years_operating import stats_by_year, years_operating
from browse.controllers.response_headers import abs_expires_header


def get_archive(archive_id: str) -> Tuple[Dict[str, Any], int, Dict[str, Any]]:
    """Gets archive page."""
    data: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}

    if archive_id == "list":
        return archive_index(archive_id, status_in=status.OK)

    archive = ARCHIVES.get(archive_id, None)
    if not archive:
        cat_id = CATEGORIES.get(archive_id, {}).get("in_archive", None)
        archive = ARCHIVES.get(cat_id, None)
        if not archive:
            return archive_index(archive_id,
                                 status_in=status.NOT_FOUND)
        else:
            archive_id = cat_id

    _write_expires_header(response_headers)

    subsumed_by = ARCHIVES_SUBSUMED.get(archive_id, None)
    if subsumed_by:
        data["subsumed_id"] = archive_id
        data["subsumed_category"] = CATEGORIES.get(archive_id, {})
        data["subsumed_by"] = subsumed_by
        subsuming_category = CATEGORIES.get(subsumed_by, {})
        data["subsuming_category"] = subsuming_category
        archive_id = subsuming_category.get("in_archive", None)
        archive = ARCHIVES.get(archive_id, None)

    years = years_operating(archive)

    data["years"] = years
    data["months"] = MONTHS
    data["days"] = DAYS
    data["archive_id"] = archive_id
    data["archive"] = archive
    data["list_form"] = ByMonthForm(archive_id, archive, years)
    data["stats_by_year"] = stats_by_year(archive_id, archive, years)
    data["category_list"] = category_list(archive_id)

    data["catchup_to"] = datetime.date.today() - datetime.timedelta(days=7)
    data["template"] = "archive/single_archive.html"
    return data, status.OK, response_headers


def archive_index(archive_id: str, status_in: int) -> Tuple[Dict[str, Any], int, Dict[str, Any]]:
    """Landing page for when there is no archive specified."""
    data: Dict[str, Any] = {}
    data["bad_archive"] = archive_id

    archives = [
        (id, ARCHIVES[id]["name"])
        for id in ARCHIVES.keys()
        if id not in ARCHIVES_SUBSUMED and not id.startswith("test")
    ]
    archives.sort(key=lambda tpl: tpl[0]) # type: ignore
    data["archives"] = archives

    defunct = [
        (id, ARCHIVES[id]["name"], ARCHIVES_SUBSUMED.get(id, ""))
        for id in ARCHIVES.keys()
        if "end_date" in ARCHIVES[id]
    ]
    defunct.sort(key=lambda tpl: tpl[0]) # type: ignore
    data["defunct"] = defunct

    data["template"] = "archive/archive_list_all.html"
    return data, status_in, {}


def subsumed_msg(_: Dict[str, str], subsumed_by: str) -> Dict[str, str]:
    """Adds information about subsuming categories and archives."""
    sb = CATEGORIES.get(subsumed_by, {"name": "unknown category"})
    sa = ARCHIVES.get(sb.get("in_archive", None), {"name": "unknown archive"})

    return {"subsumed_by_cat": sb, "subsumed_by_arch": sa}


def category_list(archive_id: str) -> List[Dict[str, str]]:
    """Retunrs categories for archive."""
    cats = []
    for cat_id in CATEGORIES:
        cat = CATEGORIES[cat_id]
        if(cat.get("in_archive", "yuck") == archive_id
           and cat.get("is_active", True)):
            cats.append({"id": cat_id,
                         "name": cat.get("name", ""),
                         "description": cat.get("description", "")})

    cats.sort(key=lambda x: x["name"]) # type: ignore
    return cats


def _write_expires_header(response_headers: Dict[str, Any]) -> None:
    """Writes an expires header for the response."""
    response_headers["Expires"] = abs_expires_header(biz_tz())[1]


DAYS = ["{:0>2d}".format(i) for i in range(1, 32)]

MONTHS = [
    ("01", "01 (Jan)"),
    ("02", "02 (Feb)"),
    ("03", "03 (Mar)"),
    ("04", "04 (Apr)"),
    ("05", "05 (May)"),
    ("06", "06 (Jun)"),
    ("07", "07 (Jul)"),
    ("08", "08 (Aug)"),
    ("09", "09 (Sep)"),
    ("10", "10 (Oct)"),
    ("11", "11 (Nov)"),
    ("12", "12 (Dec)"),
]
