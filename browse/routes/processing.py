"""Routes for handling the post_processing of conference_proceedings """
import logging
from typing import Dict, Tuple

from browse.controllers.conference_proceeding import post_process_conference
from flask import Blueprint, render_template, Response, request

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

blueprint = Blueprint('processing', __name__)

# Unwraps payload and only starts processing if it is 
#urls can take form of ftp/arxiv/papers/RANDNUMBER/ID.html.gz or ftp/CATNAME/papers/RANDNUMBER/ID.gz
# the desired format and a .html.gz
def _unwrap_payload (payload: Dict[str, str]) -> Tuple[str, str, str]:
    if payload['name'].endswith('.html.gz'):
        return payload['name'], payload['bucket']
    raise ValueError ('Received extraneous file')

#this should only be called on html format conference proceeedings
@blueprint.route('/post_process_html', methods=['POST'])
def post_process_html () -> Response:
    try:
        blob, bucket = _unwrap_payload(request.json)
    except KeyError as e:
        return e, 400
    except Exception as e:
        return e, 400
  
    response, code = post_process_conference(blob, bucket)
    return response, code