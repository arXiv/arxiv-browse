"""Year link functions."""


from typing import List, Tuple

from datetime import date

from flask import url_for

from arxiv.taxonomy.definitions import tArchive


def years_operating(archive: tArchive) -> List[int]:
    """Returns list of years operating in desc order. ex [1993,1992,1991]."""
    if (
        not archive
        or "start_date" not in archive
        or not isinstance(archive["start_date"], date)
    ):
        return []
    start = archive["start_date"].year
    end = archive.get("end_date", date.today()).year #end date could be None or a date
    return list(reversed(range(start, end + 1)))


def stats_by_year(
        archive_id: str,
        archive: tArchive,
        years: List[int],
        page_year: int=0) -> List[Tuple[str, str]]:
    """Returns links to year pages."""
    if not archive or not archive_id or not years:
        return [("bogusURL", "NODATA")]
    else:
        return [(_year_stats_link(archive_id, year, page_year), str(year))
                for year in years]


def _year_stats_link(archive_id: str, year: int, page_year: int = 0) -> str:
    if year == page_year:
        return ''
    else:
        return url_for(
            "browse.year",
            year=str(year),  
            archive=archive_id)
