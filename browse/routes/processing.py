"""Routes for handling the post_processing of conference_proceedings """
import logging
from typing import Dict, Tuple

from flask import Blueprint, render_template, Response, request

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

blueprint = Blueprint('processing', __name__)

# Unwraps payload and only starts processing if it is 
# the desired format and a .html.gz
def _unwrap_payload (payload: Dict[str, str]) -> Tuple[str, str, str]:
    if payload['name'].endswith('.html.gz'):
        id = payload['name'].split('/')[1].replace('.html.gz', '') # TODO: This might fail on old arxiv_ids
        return id, payload['name'], payload['bucket']
    raise ValueError ('Received extraneous file')

@blueprint.route('/post_process_html', methods=['POST'])
def post_process_html () -> Response:
    try:
        id, blob, bucket = _unwrap_payload(request.json)
    except Exception as e:
        return '', 202