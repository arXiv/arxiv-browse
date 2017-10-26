"""Browse controllers."""
from flask import request
from flask_api import status
from browse.services.database.util import get_institution


def get_institution_from_request():
    """Get the institution name from the request context."""
    try:
        institution_str = get_institution(request.remote_addr)
        return {
            'institution': institution_str
        }, status.HTTP_200_OK

    except IOError:
        return {
            'explanation': 'Could not access the database.'
        }, status.HTTP_500_INTERNAL_SERVER_ERROR
