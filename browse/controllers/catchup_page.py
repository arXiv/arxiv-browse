"""handles requests to the catchup page.
Allows users to access something equivalent to the /new page for up to 90 days back
"""
from typing import Tuple
from datetime import date

from flask import Response, request
from werkzeug.exceptions import BadRequest

def get_catchup_page()-> Response:
    """get the catchup page for a given set of request parameters 
    see process_catchup_params for details on parameters
    """

    subject, start_day, include_abs, page=_process_catchup_params()

    #get data

    #format data

    response={}
    code=200
    headers={}
    return response, code, headers


def _process_catchup_params()->Tuple[str,date, bool, int ]:
    """processes the request parameters to the catchup page
    raises an error or returns usable values
    
    Returns:
    subject: as a string
    start_day: date (date to catchup on)
    abs: bool (include abstracts or not )
    page: int (which page of results, default is 1)
    """

    #check for valid arguments
    ALLOWED_PARAMS={"abs", "subject", "page", "date"}
    unexpected_params = request.args.keys() - ALLOWED_PARAMS
    if unexpected_params:
        raise BadRequest(f"Unexpected parameters: {', '.join(unexpected_params)}")
        
    if "subject" in request.args:
        subject=request.args["subject"]
    else:
        raise BadRequest("Subject required. format: ?subject=subject_here")

    if "date" in request.args:
        date_str=request.args["date"]
    else:
        raise BadRequest("Start date required. format: ?date=YYYY-MM-DD")
    
    if "abs" in request.args:
        abs_str=request.args["abs"]
        if abs_str == "true":
            include_abs=True
        elif abs_str == "false":
            include_abs=False
        else:
            raise BadRequest("Invalid abs value. Use ?abs=true to include abstracts or ?abs=false to not")
    else:
        include_abs=False
    
    if "page" in request.args:
        page_str=request.args["page"]
    else:
        page=1


    return subject, start_day, include_abs, page