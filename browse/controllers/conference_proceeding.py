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
        gzipped_file=GsObjectStore(gs_client.bucket(bucket_name)).to_obj(name)
        ungzipped_file=UngzippedFileObj(gzipped_file)
    except Exception as ex:
        logger.error('Error getting file from GCP',exc_info=True)
        return ex, 400
   
    html_files=[]
    other_files=[]

    if ungzipped_file.name.endswith(".tar"): #get all interior files from tar
        with ungzipped_file.open() as data:           
            raw_data=data.read()
            tar_bytes=io.BytesIO(raw_data)

            with tarfile.open(fileobj=tar_bytes, mode='r') as tar: #open tar file from byte string
                for file_info in tar:
                    if file_info.name.endswith(".html"):
                        html_files.append(
                            {"file":tar.extractfile(file_info).read(),
                             "name":file_info.name})
                    else:
                        other_files.append(
                            {"file":tar.extractfile(file_info),
                             "name":file_info.name,
                             "size":file_info.size})

    else: #get single html file
        try:
            with ungzipped_file.open() as data: 
                raw_data=data.read()
                html_files.append({"name":data.name, "file":raw_data} )
        except Exception as ex:
            logger.error('Error opening file',exc_info=True)
            return ex, 400

    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
        #process and add each html file
        for entry in html_files:
            #read and process data
            text_html=entry["file"].decode('utf-8')
            processed=post_process_html(text_html)

            #put back into tar
            html_file_name=entry["name"]      
            html_file = io.BytesIO(processed.encode('utf-8'))
            tarinfo = tarfile.TarInfo(html_file_name)
            tarinfo.size = len(processed)
            tar.addfile(tarinfo, html_file)

        #add back non html files
        for entry in other_files:
            tarinfo = tarfile.TarInfo(entry["name"])
            tarinfo.size = entry["size"]
            tar.addfile(tarinfo, entry["file"])


    tar_buffer.seek(0)
    blob_name=name.replace(".html.gz",".tar.gz")

    #upload to GCP
    try:
        destination_bucket=gs_client.bucket(current_app.config['CLASSIC_HTML_BUCKET'])
        destination_blob=destination_bucket.blob(blob_name)
        destination_blob.upload_from_file(tar_buffer, content_type='application/gzip')
    except Exception as ex:
        logger.error('Error sending file to GCP',exc_info=True)
        return ex, 400

    return {"result":"success"}, 200 