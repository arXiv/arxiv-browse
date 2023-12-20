"""Handle requests for info about one year of archive activity."""

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Tuple
from http import HTTPStatus as status

from arxiv import taxonomy
from flask import url_for
from werkzeug.exceptions import BadRequest

from browse.controllers.list_page import get_listing_service
from browse.controllers.years_operating import stats_by_year, years_operating
from browse.services.listing import MonthTotal, YearCount, MonthCount


@dataclass
class MonthData:
    """Class to pass data to template"""
    month_count: MonthCount
    art: List[Tuple[str, Optional[str]]]
    yymm:str
    my:str
    url:str


def year_page(archive_id: str, year: Optional[int]) -> Any:
    """
    Get year page for archive.

    Parameters
    ----------
    archive : str
    Must be an arXiv archive identifier.

    year: Optional[int]
    Must be a two or four digit year.

    Returns
    -------
    dict
        Search result response data.
    int
        HTTP status code.
    dict
        Headers to add to the response.

    """
    thisYear = date.today().year

    if year is None:
        year = thisYear

    if year > thisYear:
        # 307 because year might be valid in the future
        return {}, status.TEMPORARY_REDIRECT, {'Location': '/'}

    if year < 100:
        if year >= 91:
            year = 1900 + year
        else:
            year = 2000 + year

    if archive_id not in taxonomy.ARCHIVES:
        raise BadRequest("Unknown archive.")
    else:
        archive = taxonomy.ARCHIVES[archive_id]

    listing_service = get_listing_service()
    count_listing = listing_service.monthly_counts(archive_id, year)
    month_data = [
        MonthData(
            month_count= month_count,
            art=ascii_art_month(archive_id, month_count),
            yymm= f"{str(month_count.year)[2:]}{month_count.month:02}",
            my = date(year=int(month_count.year),month=int(month_count.month), day=1).strftime("%b %Y"),
            url= url_for('browse.list_articles', context=archive_id,
                         subcontext=f"{month_count.year%100}{month_count.month:02}")) #TODO return to 4 digit year when all of listings is running on browse
        for month_count in count_listing.by_month]

    response_data: Dict[str, Any] = {
        'archive_id': archive_id,
        'archive': archive,
        'month_data': month_data,
        'listing': count_listing,
        'year': str(year),
        'stats_by_year': stats_by_year(archive_id, archive, years_operating(archive), year)
    }
    response_headers: Dict[str, Any] = {}

    response_status = status.OK

    return response_data, response_status, response_headers


ASCII_ART_STEP = 20
ASCII_ART_CHR = '|'
ASCII_ART_URL_STEP = 100


def ascii_art_month(archive_id: str, month: MonthCount) -> List[Tuple[str, Optional[str]]]:
    """Make ascii art for a MonthTotal."""
    tot = month.new + month.cross
    yyyymm = f"{month.year%100}{month.month:02}" #TODO return to 4 digit year when all of listings is running on browse

    def _makestep(idx: int) -> Tuple[str, Optional[str]]:
        if idx % ASCII_ART_URL_STEP == 0:
            return (ASCII_ART_CHR,
                    url_for('browse.list_articles',
                            context=archive_id,
                            subcontext=yyyymm,
                            skip=idx))
        else:
            return (ASCII_ART_CHR, None)

    art = [_makestep(idx) for idx in range(0, tot, ASCII_ART_STEP)]

    if tot % ASCII_ART_STEP >= ASCII_ART_STEP/2:
        art.append(('!', None))

    return art


