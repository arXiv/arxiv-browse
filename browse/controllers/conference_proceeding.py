from typing import Optional, Dict, Any, Tuple
from google.cloud import storage
import logging
import tarfile
from browse.services.html_processing import post_process_html
from browse.services.object_store.fileobj import UngzippedFileObj
from browse.services.object_store.object_store_gs import GsObjectStore


logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

DESTINATION_BUCKET_NAME="arxiv-dev-html-papers"

def post_process_conference (name: str, bucket_name: str) -> Tuple[Dict[str, Optional[Any]], int]: 
    
    #gets the html data from GCP storage
    try:
        gs_client=storage.Client()
        file=GsObjectStore(gs_client.bucket(bucket_name)).to_obj(name)
        file2=UngzippedFileObj(file)
    except Exception as ex:
        logger.error('Error getting file from GCP',exc_info=True)
        return ex, 400

    with file2.open() as data:
        rawdata=data.read()
    text_html=rawdata.decode('utf-8')
    
    #processes file
    processed_html=post_process_html(text_html)

    new_name=name.replace(".html.gz","").replace(".tar.gz","")
    #put string into html file
    html_file_name=new_name+".html"
    with open(html_file_name, 'w') as html_file:
        html_file.write(processed_html)

    #html file to tar.gz
    output_file_name=new_name+".tar.gz"
    with tarfile.open(output_file_name, 'w:gz') as tar:
        tar.add(html_file_name)

    #upload to GCP
    try:
        destination_bucket=gs_client.bucket(DESTINATION_BUCKET_NAME)
        destination_blob=destination_bucket.blob(output_file_name)
        destination_blob.upload_from_filename(output_file_name)
    except Exception as e:
        logger.error('Error getting file from GCP',exc_info=True)
        return ex, 400


    response_data: Dict[str, Any] = {}
    response_data['result'] = "success"
    return response_data, 200, 

