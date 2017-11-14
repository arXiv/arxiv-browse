"""Browse controllers."""

from typing import Dict, Optional, Tuple

from flask import request
from flask_api import status
from browse.services.database import get_institution


InstitutionResp = Tuple[Dict[str, str], int]


def get_institution_from_request() -> InstitutionResp:
    """Get the institution name from the request context."""
    institution_str = None
    try:
        institution_opt: Optional[str] = get_institution(request.remote_addr)
        response: InstitutionResp = ({
            'institution': institution_opt
        }, status.HTTP_200_OK) if institution_opt is not None else ({
            'explanation': 'Institution not found.'
        }, status.HTTP_400_BAD_REQUEST)
        return response

    except IOError:
        # TODO: log this
        # return {
        #     'explanation': 'Could not access the database.'
        # }, status.HTTP_500_INTERNAL_SERVER_ERROR, {}
        return None

    return institution_str
