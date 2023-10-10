from typing import Optional, Dict, Any, Tuple
from google.cloud import storage
import logging
from browse.services.html_processing import post_process_html
from browse.services.object_store.fileobj import UngzippedFileObj
from browse.services.object_store.object_store_gs import GsObjectStore


logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

def post_process_conference (name: str, bucket_name: str) -> Tuple[Dict[str, Optional[Any]], int, Dict[str, str]]: # Either pass blob info and get blob + process, or get blob before hand and pass str of html here
    
    #gets the html data from GCP storage
    gs_client=storage.Client()
    file=GsObjectStore(gs_client.bucket(bucket_name)).to_obj(name)
    file2=UngzippedFileObj(file)

    with file2.open() as data:
        rawdata=data.read()
    text_html=rawdata.decode('utf-8')
    
    #processes file
   # title, extradata, lis=(parse_conference_html(text_html))
    processed_html=post_process_html(text_html)
    

    response_data: Dict[str, Any] = {}

    response_data['title'] = "empty"
    return response_data, 200, dict()

