from flask import current_app, request
from browse import status
from browse.services.database import get_institution

def get_institution_from_request():

   try:
       institution_str = get_institution(request.remote_addr)
       return {
            'institution': institution_str
        }, status.HTTP_200_OK

   except IOError as e:
        return {
            'explanation': 'Could not access the database.'
        }, status.HTTP_500_INTERNAL_SERVER_ERROR
