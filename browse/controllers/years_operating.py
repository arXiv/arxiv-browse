"""Year link functions."""

from typing import Dict, Any, Tuple, List, no_type_check
from datetime import date

from flask import url_for


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
        archive_id: str,
        archive: Dict[str, Any],
        years: List[int],
        page_year: int=0) -> List[Tuple[str, str]]:
    """Returns links to year pages."""
    if not archive or not archive_id or not years:
        return [("bogusURL", "NODATA")]
    else:
        return [(_year_stats_link(archive_id, year, page_year), str(year))
                for year in years]


def _year_stats_link(archive_id: str, year: int, page_year:int =0) -> str:
    if year == page_year:
        return ''
    else:
        return url_for(  #type: ignore
            "browse.year",
            year=str(year),  # 4 digit year
            archive=archive_id)
