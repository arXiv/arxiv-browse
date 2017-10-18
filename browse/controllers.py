from flask import current_app, request
from browse import status
from browse.services.db import MemberInstitutionService

def get_institution_from_request():

   try:
       institution_service = MemberInstitutionService()
       institution_str = institution_service.get_institution(request.remote_addr)
       return {
            'institution': institution_str
        }, status.HTTP_200_OK

   except IOError as e:
        return {
            'explanation': 'Could not access the database.'
        }, status.HTTP_500_INTERNAL_SERVER_ERROR
