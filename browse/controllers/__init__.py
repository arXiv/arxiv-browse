"""
Houses controllers for browse.

Each controller corresponds to a distinct browse feature with its own request
handling logic.
"""
from flask import request
from typing import Optional
from browse.services.database.models import get_institution


def get_institution_from_request() -> Optional[str]:
    """Get the institution name from the request context."""
    institution_str = None
    try:
        institution_str = get_institution(request.remote_addr)

    except IOError:
        # TODO: log this
        # return {
        #     'explanation': 'Could not access the database.'
        # }, status.HTTP_500_INTERNAL_SERVER_ERROR, {}
        return None

    return institution_str
