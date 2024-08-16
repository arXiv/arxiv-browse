"""handles requests to the catchup page.
Allows users to access something equivalent to the /new page for up to 90 days back
"""
from typing import Tuple, Union
from datetime import date, datetime, timedelta

from http import HTTPStatus
from flask import Response, request, redirect, url_for
from werkzeug.exceptions import BadRequest

from arxiv.taxonomy.category import Group, Archive, Category
from arxiv.taxonomy.definitions import CATEGORIES, ARCHIVES, GROUPS


def get_catchup_page()-> Response:
    """get the catchup page for a given set of request parameters 
    see process_catchup_params for details on parameters
    """
    subject, start_day, include_abs, page=_process_catchup_params()
    #check for redirects for noncanon subjects
    if subject.id != subject.canonical_id:
        return redirect(
            url_for('catchup', 
                    subject=subject.canonical_id, 
                    date=start_day, 
                    page=page,
                    abs=include_abs), 
            HTTPStatus.MOVED_PERMANENTLY)

    #get data

    #format data

    response={}
    code=200
    headers={}
    return response, code, headers


def _process_catchup_params()->Tuple[Union[Group, Archive, Category], date, bool, int]:
    """processes the request parameters to the catchup page
    raises an error or returns usable values

    Returns:
    subject: as a Group, Archive, or Category. Still needs to be checked for canonicalness
    start_day: date (date to catchup on)
    abs: bool (include abstracts or not )
    page: int (which page of results, default is 1)
    """

    #check for valid arguments
    ALLOWED_PARAMS={"abs", "subject", "page", "date"}
    unexpected_params = request.args.keys() - ALLOWED_PARAMS
    if unexpected_params:
        raise BadRequest(f"Unexpected parameters. Only accepted parameters are: 'subject', 'date', 'page', and 'abs'")
        
    #subject validation
    subject_str= request.args.get("subject")
    if not subject_str:
        raise BadRequest("Subject required. format: ?subject=subject_here")
    if subject_str == "grp_physics":
        subject=GROUPS["grp_physics"]
    elif subject_str in ARCHIVES:
        subject= ARCHIVES[subject_str]
    elif subject_str in CATEGORIES:
        subject= CATEGORIES[subject_str]
    else:
        raise BadRequest("Invalid subject. Subject must be an archive, category or 'grp_physics'")
    
    #date validation
    date_str=request.args.get("date")
    if not date_str:
        raise BadRequest("Start date required. format: ?date=YYYY-MM-DD")
    try:
        start_day= datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise BadRequest(f"Invalid date format. Use format: ?date=YYYY-MM-DD")
    #only allow dates within the last 90 days (91 just in case time zone differences)
    today=datetime.now().date()
    earliest_allowed=today - timedelta(days=91)
    if start_day < earliest_allowed:
        #TODO link to earliest allowed date
        raise BadRequest(f"Invalid date: {start_day}. Catchup only allowed for past 90 days")
    elif start_day > today:
        raise BadRequest(f"Invalid date: {start_day}. Can't request date later than today")

    #include abstract or not
    abs_str=request.args.get("abs","false")
    if abs_str == "true":
        include_abs=True
    elif abs_str == "false":
        include_abs=False
    else:
        raise BadRequest(f"Invalid abs value. Use ?abs=true to include abstracts or ?abs=false to not")

    #select page number (each page has 2000 items)
    page_str = request.args.get("page", "1") #page defaults to 1
    if page_str.isdigit():
        page=int(page_str)
    else:
        raise BadRequest(f"Invalid page value. Page value should be an integer like ?page=3")

    return subject, start_day, include_abs, page