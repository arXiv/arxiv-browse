"""Handle requests for info about one year of archive activity."""

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Tuple
from http import HTTPStatus as status

from arxiv.taxonomy.definitions import ARCHIVES
from flask import url_for
from werkzeug.exceptions import BadRequest, NotFound

from arxiv.integration.fastly.headers import add_surrogate_key

from browse.controllers.list_page import get_listing_service
from browse.controllers.years_operating import stats_by_year, years_operating
from browse.services.listing import MonthCount

YEAR_CACHE_TIME= 60*60*24*10 #10 days

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

    headers={}
    #redirect 2 digit years
    if year < 100:
        if year >= 91:
            year = 1900 + year
        else:
            year = 2000 + year
        
        new_address=url_for("browse.year", archive=archive_id, year=year)
        headers["Surrogate-Control"]="max-age=31536000" # a year
        headers["Location"]=new_address
        return {}, status.MOVED_PERMANENTLY, headers
        
    #early years make no sense
    if year<1990:
        raise BadRequest(f"Invalid Year: {year}")

    if year > thisYear:
        raise NotFound(f"Invalid Year: {year}") #not BadRequest, might be valid in future

    if archive_id not in ARCHIVES:
        raise BadRequest("Unknown archive.")
    else:
        archive = ARCHIVES[archive_id]

    #check if archive was active
    start= archive.start_date.year
    if year< start:
        raise BadRequest(f"Invalid year: {year}. {archive.full_name} starts in {start}")
    
    if archive.end_date: 
        end=archive.end_date.year
        if year>end:
            raise BadRequest(f"Invalid year: {year}. {archive.full_name} ended in {end}")

    listing_service = get_listing_service()
    count_listing = listing_service.monthly_counts(archive.id, year)
    month_data = [
        MonthData(
            month_count= month_count,
            art=ascii_art_month(archive.id, month_count), 
            yymm= f"{month_count.month:02}",
            my = date(year=int(month_count.year),month=int(month_count.month), day=1).strftime("%b %Y"),
            url= url_for('browse.list_articles', context=archive.id,
                         subcontext=f"{month_count.year:04}-{month_count.month:02}")) 
        for month_count in count_listing.by_month]

    response_data: Dict[str, Any] = {
        'archive': archive, 
        'month_data': month_data,
        'listing': count_listing,
        'year': str(year),
        'stats_by_year': stats_by_year( archive, years_operating(archive), year) 
    }
    headers["Surrogate-Control"]=f"max-age={YEAR_CACHE_TIME}"
    headers=add_surrogate_key(headers,["year", f"year-{archive.id}", f"year-{archive.id}-{year:04d}"])
    if date.today().year==year: 
        headers=add_surrogate_key(headers,["announce"])

    response_status = status.OK

    return response_data, response_status, headers


ASCII_ART_STEP = 20
ASCII_ART_CHR = '|'
ASCII_ART_URL_STEP = 100


def ascii_art_month(archive_id: str, month: MonthCount) -> List[Tuple[str, Optional[str]]]:
    """Make ascii art for a MonthTotal."""
    tot = month.new + month.cross
    yyyymm = f"{month.year:04}-{month.month:02}" 

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


