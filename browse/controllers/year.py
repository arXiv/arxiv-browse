"""Handle requests for info about one year of archive activity."""

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from arxiv import status, taxonomy
from flask import url_for
from werkzeug.exceptions import BadRequest

from browse.controllers.list_page import get_listing_service
from browse.controllers.years_operating import stats_by_year, years_operating
from browse.domain.listing import MonthCount


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
        return {}, status.HTTP_307_TEMPORARY_REDIRECT, {'Location': '/'}

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
    month_listing = listing_service.monthly_counts(archive_id, year)

    for month in month_listing['month_counts']:
        month['art'] = ascii_art_month(archive_id, month)  # type: ignore
        month['yymm'] = f"{month['year']}-{month['month']:02}"  # type: ignore
        month['url'] = url_for('browse.list_articles',  # type: ignore
                               context=archive_id,
                               subcontext=f"{month['year']}{month['month']:02}")

    response_data: Dict[str, Any] = {
        'archive_id': archive_id,
        'archive': archive,
        'months': month_listing['month_counts'],
        'listing': month_listing,
        'year': str(year),
        'stats_by_year': stats_by_year(archive_id, archive, years_operating(archive), year)
    }
    response_headers: Dict[str, Any] = {}

    response_status = status.HTTP_200_OK

    return response_data, response_status, response_headers


ASCII_ART_STEP = 20
ASCII_ART_CHR = '|'
ASCII_ART_URL_STEP = 100


def ascii_art_month(archive_id: str, month: MonthCount) -> List[Tuple[str, Optional[str]]]:
    """Make ascii art for a MonthCount."""
    tot = month['new'] + month['cross']
    yyyymm = f"{month['year']}{month['month']:02}"

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
