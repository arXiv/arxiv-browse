"""Archive landing page."""

from datetime import date
from typing import Dict, Any, Tuple, List, no_type_check

from flask import Response, url_for

from arxiv import status
from arxiv.taxonomy.definitions import ARCHIVES, CATEGORIES, ARCHIVES_SUBSUMED

from browse.controllers.archive_page.by_month_form import ByMonthForm
from browse.controllers.archive_page.catchup_form import CatchupForm
from browse.services.util.response_headers import abs_expires_header


def get_archive(archive_id: str) -> Response:
    """Gets archive page."""
    data: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}

    if archive_id == "list":
        return archive_index(archive_id, status=status.HTTP_200_OK)

    archive = ARCHIVES.get(archive_id, None)
    if not archive:
        cat_id = CATEGORIES.get(archive_id, {}).get("in_archive", None)
        archive = ARCHIVES.get(cat_id, None)
        if not archive:
            return archive_index(archive_id,
                                 status=status.HTTP_404_NOT_FOUND)
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

    data["archive_id"] = archive_id
    data["archive"] = archive
    data["list_form"] = ByMonthForm(archive_id, archive, years)
    data["catchup_form"] = CatchupForm(archive_id, archive, years)
    data["stats_by_year"] = stats_by_year(archive_id, archive, years)
    data["category_list"] = category_list(archive_id)

    data["template"] = "archive/single_archive.html"
    return data, status.HTTP_200_OK, response_headers  # type: ignore


def archive_index(archive_id: str, status: int) -> Response:
    """Landing page for when there is no archive specified."""
    data: Dict[str, Any] = {}
    data["bad_archive"] = archive_id

    archives = [
        (id, ARCHIVES[id]["name"])
        for id in ARCHIVES.keys()
        if id not in ARCHIVES_SUBSUMED and not id.startswith("test")
    ]
    archives.sort(key=lambda tpl: tpl[0])
    data["archives"] = archives

    defunct = [
        (id, ARCHIVES[id]["name"], ARCHIVES_SUBSUMED.get(id, ""))
        for id in ARCHIVES.keys()
        if "end_date" in ARCHIVES[id]
    ]
    defunct.sort(key=lambda tpl: tpl[0])
    data["defunct"] = defunct
    
    data["template"] = "archive/archive_list_all.html"
    return data, status, {}  # type: ignore


def subsumed_msg(archive: Dict[str, str], subsumed_by: str) -> Dict[str, str]:
    """Adds information about subsuming categories and archives."""
    sb = CATEGORIES.get(subsumed_by, {"name": "unknown category"})
    sa = ARCHIVES.get(sb.get("in_archive", None), {"name": "unknown archive"})

    return {"subsumed_by_cat": sb, "subsumed_by_arch": sa}


def years_operating(archive: Dict[str, Any]) -> List[int]:
    """Returns list of years operating in desc order. ex [1993,1992,1991]."""
    if (
        not archive
        or "start_date" not in archive
        or not isinstance(archive["start_date"], date)
    ):
        return []
    start = archive["start_date"].year
    end = archive.get("end_date", None) or date.today().year
    return list(reversed(range(start, end + 1)))


def stats_by_year(
    archive_id: str, archive: Dict[str, Any], years: List[int]
) -> List[Tuple[str, str]]:
    """Returns links to year pages."""
    if not archive or not archive_id or not years:
        return [("bogusURL", "NODATA")]
    else:
        return [(_year_stats_link(archive_id, i), str(i)) for i in years]


@no_type_check  # url_for should return str but is not typed in Flask
def _year_stats_link(archive_id: str, num: int) -> str:
    return url_for(
        "browse.year",
        year=str(num)[-2:],  # danger: 2 digit year, NG can accept 4 digit
        archive=archive_id,
    )


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

    cats.sort(key=lambda x: x["name"])
    return cats


def _write_expires_header(response_headers: Dict[str, Any]) -> None:
    """Writes an expires header for the response."""
    response_headers["Expires"] = abs_expires_header()[1]
