"""Archive landing page."""

from datetime import datetime, date
from typing import Dict, Any, Tuple, List

from flask import Response, request, url_for

from arxiv import status
from arxiv.taxonomy.definitions import ARCHIVES, CATEGORIES, ARCHIVES_SUBSUMED

from browse.controllers.archive_page.by_month_form import ByMonthForm
from browse.controllers.archive_page.catchup_form import CatchupForm

def get_archive( archive_id: str) -> Response:
    data:Dict[str,Any] ={}

    archive = ARCHIVES.get( archive_id, None)    
    subsumed_by = ARCHIVES_SUBSUMED.get( archive_id, None)

    data.update(subsumed_msg(archive, subsumed_by))
    
    if not archive:
        return archive_index( archive_id , status=404)

    data['archive_id'] = archive_id
    data['archive'] = archive
    data['list_form'] = ByMonthForm(archive_id, archive)
    data['catchup_form'] = CatchupForm(archive_id, archive)
    data['stats_by_year'] = stats_by_year(archive_id, archive)
    
    # TODO categories within archive

    data['template'] = 'archive/single_archive.html'
    return data, status.HTTP_200_OK, {}


def archive_index( archive_id: str, status: int) -> Response:
    raise RuntimeError('/archive with no archive set is not yet implemented. See archive_index()')


def subsumed_msg( archive:Dict[str,str], subsumed_by:str) ->Dict[str,str]:
    """Adds information about subsuming categories and archives."""
    sb = CATEGORIES.get(subsumed_by,
                        {'name':'unknown category'})
    sa = ARCHIVES.get(sb.get('in_archive',None),
                      {'name':'unknown archive'})
    
    return {
        'subsumed_by_cat' : sb,
        'subsumed_by_arch' : sa
    }

def stats_by_year( archive_id: str, archive: Dict[str,Any]) -> List[Tuple[Any,str]]:
    if ( not archive
         or not archive_id
         or not 'start_date' in archive
         or not isinstance(archive['start_date'], date) ):
        return []

    start = archive['start_date'].year
    end = date.today().year
    
    values =  [(_year_stats_link(archive_id, i), str(i)) for i in range(start,end+1)]
    values.reverse()
    return values


def _year_stats_link(archive_id:str, num:int)->Any:
    return url_for('browse.year' ,
                   year=str(num)[-2:], #danger: 2 digit year, NG can accept 4 digit
                   archive=archive_id)
