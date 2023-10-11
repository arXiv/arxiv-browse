from typing import Optional, Dict, Any, Tuple
from google.cloud import storage
import logging
import tarfile
import io
from browse.services.html_processing import post_process_html
from browse.services.object_store.fileobj import UngzippedFileObj
from browse.services.object_store.object_store_gs import GsObjectStore


logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

DESTINATION_BUCKET_NAME="arxiv-dev-html-papers"

#gets called per html file to process
def post_process_conference (name: str, bucket_name: str) -> Tuple[Dict[str, Optional[Any]], int]: 
    
    #gets the html data from GCP storage
    try:
        gs_client=storage.Client()
        gzipped_file=GsObjectStore(gs_client.bucket(bucket_name)).to_obj(name)
        ungzipped_file=UngzippedFileObj(gzipped_file)
    except Exception as ex:
        logger.error('Error getting file from GCP',exc_info=True)
        return ex, 400

    #get all the interior files
    html_files=[]
    other_files=[]
    if ungzipped_file.name.endswith(".tar"):
        print("panic!")
    else:
        html_files.append(ungzipped_file)

    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
        #process and add each html file
        for file in html_files:
            processed=post_process_conference_file(file)
            html_file_name=file.name
            html_file = io.BytesIO(processed.encode('utf-8'))
            tarinfo = tarfile.TarInfo(html_file_name)
            tarinfo.size = len(processed)
            tar.addfile(tarinfo, html_file)

        #add back other files
        for file in other_files:
            tarinfo = tarfile.TarInfo(file.name)
            tarinfo.size = file.size
            tar.addfile(tarinfo, html_file)


    tar_buffer.seek(0)
    blob_name=name.replace(".html.gz",".tar.gz")
    if blob_name.startswith("ftp/"):
        blob_name=blob_name[4:]

    #upload to GCP
    try:
        destination_bucket=gs_client.bucket(DESTINATION_BUCKET_NAME)
        destination_blob=destination_bucket.blob(blob_name)
        destination_blob.upload_from_file(tar_buffer, content_type='application/gzip')
    except Exception as ex:
        logger.error('Error sending file to GCP',exc_info=True)
        return ex, 400

    response_data: Dict[str, Any] = {}
    response_data['result'] = "success"
    return response_data, 200, 


def post_process_conference_file (file: UngzippedFileObj) -> str: 
#called on each html file in conference proceedings to be processed
    try:
        with file.open() as data: 
            rawdata=data.read()
    except Exception as ex:
        logger.error('Error opening file',exc_info=True)
        return ex, 400

    text_html=rawdata.decode('utf-8')
    processed_html=post_process_html(text_html)

    return processed_html