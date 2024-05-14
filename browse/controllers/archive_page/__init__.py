"""Archive landing page."""

import datetime
from typing import Any, Dict, List, Tuple, Optional
from http import HTTPStatus as status

from arxiv.taxonomy.definitions import (
    ARCHIVES,
    ARCHIVES_ACTIVE, 
    ARCHIVES_SUBSUMED, 
    CATEGORIES
)
from arxiv.taxonomy.category import Category, Archive

from browse.controllers import biz_tz, add_surrogate_key
from browse.controllers.archive_page.by_month_form import ByMonthForm
from browse.controllers.years_operating import stats_by_year, years_operating
from browse.controllers.response_headers import abs_expires_header


def get_archive(archive_id: Optional[str]) -> Tuple[Dict[str, Any], int, Dict[str, Any]]:
    """Gets archive page."""
    data: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}
    response_headers.update(add_surrogate_key(response_headers,["archive"]))

    if not archive_id or archive_id == "list":
        return archive_index("list", status_in=status.OK)

    archive = ARCHIVES.get(archive_id, None)
    if not archive: #check if maybe its a category
        category = CATEGORIES.get(archive_id, None)
        if category:
            archive=category.get_archive()
    if not archive:
        return archive_index(archive_id,
                                 status_in=status.NOT_FOUND)

    _write_expires_header(response_headers)

    if archive.is_active==False: #subsumed archives
        subsuming_category=archive.get_canonical()
        if not isinstance(subsuming_category, Category):
            return archive_index(archive_id,
                                 status_in=status.NOT_FOUND)
        data["subsumed_id"] = archive.id
        data["subsuming_category"] = subsuming_category
        archive = subsuming_category.get_archive()

    years = years_operating(archive)
    data["years"] = years
    data["months"] = MONTHS
    data["days"] = DAYS
    data["archive"] = archive
    data["list_form"] = ByMonthForm(archive, years)
    data["stats_by_year"] = stats_by_year(archive, years)
    data["category_list"] = category_list(archive)

    data["catchup_to"] = datetime.date.today() - datetime.timedelta(days=7)
    data["template"] = "archive/single_archive.html"
    return data, status.OK, response_headers


def archive_index(bad_archive_id: str, status_in: int) -> Tuple[Dict[str, Any], int, Dict[str, Any]]:
    """Landing page for when there is no archive specified."""
    data: Dict[str, Any] = {}
    data["bad_archive"] = bad_archive_id

    archives = [
        value 
        for key,value in ARCHIVES_ACTIVE.items()
        if not key.startswith("test")
    ]
    archives.sort(key=lambda x: x.id)
    data["archives"] = archives

    defunct = [
        ARCHIVES[id] 
        for id in ARCHIVES_SUBSUMED.keys()
    ]
    defunct.sort(key=lambda x: x.id)
    data["defunct"] = defunct

    data["template"] = "archive/archive_list_all.html"
    headers: Dict[str,str]={}
    headers.update(add_surrogate_key(headers,["archive"]))
    return data, status_in, headers


def category_list(archive: Archive) -> List[Category]:
    """Returns active categories for archive."""
    cats = [cat for cat in archive.get_categories()]
    cats.sort(key=lambda x: x.id)
    return cats


def _write_expires_header(response_headers: Dict[str, Any]) -> None:
    """Writes an expires header for the response."""
    response_headers["Expires"] = abs_expires_header(biz_tz())


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
