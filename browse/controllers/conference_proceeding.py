from typing import Optional, Dict, Any, Tuple
from google.cloud import storage
import logging
import tarfile
import io

from flask import current_app

from browse.services.html_processing import post_process_html
from browse.services.object_store.fileobj import UngzippedFileObj
from browse.services.object_store.object_store_gs import GsObjectStore


logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

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

    blob_name=name[4:].replace(".html.gz","").replace(".tar.gz","") #remove ftp/ and file types
    file_name=blob_name.split("/")[-1]
    #put string into html file
    html_file_name=file_name+".html"

    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
        # Create a file-like object from the HTML content
        html_file = io.BytesIO(processed_html.encode('utf-8'))
        
        # Add the HTML file-like object to the tar archive
        tarinfo = tarfile.TarInfo(html_file_name)
        tarinfo.size = len(processed_html)
        tar.addfile(tarinfo, html_file)
        
    tar_buffer.seek(0)

    #upload to GCP
    try:
        destination_bucket=gs_client.bucket(current_app.config['CLASSIC_HTML_BUCKET'])
        destination_blob=destination_bucket.blob(blob_name+".tar.gz")
        destination_blob.upload_from_file(tar_buffer, content_type='application/gzip')
    except Exception as ex:
        logger.error('Error sending file to GCP',exc_info=True)
        return ex, 400

    response_data: Dict[str, Any] = {}
    response_data['result'] = "success"
    return response_data, 200, 

