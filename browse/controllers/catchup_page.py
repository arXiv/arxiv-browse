"""handles requests to the catchup page.
Allows users to access something equivalent to the /new page for up to 90 days back
"""

from flask import Response

def get_catchup_page()-> Response:
    "get the catchup page for a given set of request parameters"
    response={}
    code=200
    headers={}
    return response, code, headers