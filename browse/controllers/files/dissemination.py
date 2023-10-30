"""Controller for PDF, source and other downloads."""

import logging
from email.utils import format_datetime
from typing import Callable, Optional, Union
import tarfile
import mimetypes
from io import BytesIO
from typing import Generator

from browse.domain.identifier import Identifier, IdentifierException
from browse.domain.fileformat import FileFormat
from browse.domain.version import VersionEntry
from browse.domain.metadata import DocMetadata
from browse.domain import fileformat

from browse.controllers.files import stream_gen, last_modified, add_time_headers

from browse.services.object_store.fileobj import FileObj, UngzippedFileObj, FileFromTar, FileDoesNotExist
from browse.services.object_store.object_store_gs import GsObjectStore
from browse.services.object_store.object_store_local import LocalObjectStore

from browse.services.documents import get_doc_service
from browse.services.html_processing import post_process_html2

from browse.services.dissemination import get_article_store
from browse.services.dissemination.article_store import (
    Acceptable_Format_Requests, CannotBuildPdf, Deleted)
from browse.services.next_published import next_publish

from browse.stream.file_processing import process_file
from browse.stream.tarstream import tar_stream_gen
from flask import Response, abort, make_response, render_template, current_app
from flask_rangerequest import RangeRequest
from werkzeug.exceptions import BadRequest, NotFound
from google.cloud import storage


logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


Resp_Fn_Sig = Callable[[FileFormat, FileObj, Identifier, DocMetadata,
                        VersionEntry], Response]


def default_resp_fn(format: FileFormat,
                    file: FileObj,
                    arxiv_id: Identifier,
                    docmeta: DocMetadata,
                    version: VersionEntry,
                    extra: Optional[str] = None) -> Response:
    """Creates a response with approprate headers for the `file`.

    Parameters
    ----------
    format : FileFormat
        `FileFormat` of the `file`
    item : DocMetadata
        article that the response is for.
    file : FileObj
        File object to use in the response.
    """

    # Have to do Range Requests to get GCP CDN to accept larger objects.
    resp: Response = RangeRequest(file.open('rb'),
                                  etag=last_modified(file),
                                  last_modified=file.updated,
                                  size=file.size).make_response()

    resp.headers['Access-Control-Allow-Origin'] = '*'
    if isinstance(format, FileFormat):
        resp.headers['Content-Type'] = format.content_type

    if resp.status_code == 200:
        # For large files on CloudRun chunked and no content-length needed
        # TODO revisit this, in some cases it doesn't work maybe when
        # combined with gzip encoding?
        # resp.headers['Transfer-Encoding'] = 'chunked'
        resp.headers.pop('Content-Length')

    add_time_headers(resp, file, arxiv_id)
    return resp


def src_resp_fn(format: FileFormat,
                file: FileObj,
                arxiv_id: Identifier,
                docmeta: DocMetadata,
                version: VersionEntry,
                extra: Optional[str] = None) -> Response:
    """Prepares a response where the payload will be a tar of the source.

    No matter what the actual format of the source, this will try to return a
    .tar.  If the source is a .pdf then that will be tarred. If the source is a
    gzipped PS file, that will be ungzipped and then tarred.

    This will also uses gzipped transfer encoding. But the client will unencode
    the bytestream and the file will be saved as .tar.
    """
    if file.name.endswith(".tar.gz"):  # Nothing extra to do, already .tar.gz
        resp = RangeRequest(file.open('rb'), etag=last_modified(file),
                            last_modified=file.updated,
                            size=file.size).make_response()
    elif file.name.endswith(".gz"):  # unzip single file gz and then tar
        outstream = tar_stream_gen([UngzippedFileObj(file)])
        resp = make_response(outstream, 200)
    else:  # tar single flie like .pdf
        outstream = tar_stream_gen([file])
        resp = make_response(outstream, 200)

    archive = f"{arxiv_id.archive}-" if arxiv_id.is_old_id else ""
    filename = f"arXiv-{archive}{arxiv_id.filename}v{version.version}.tar"

    resp.headers["Content-Encoding"] = "x-gzip"  # tar_stream_gen() gzips
    resp.headers["Content-Type"] = "application/x-eprint-tar"
    resp.headers["Content-Disposition"] = \
        f"attachment; filename=\"{filename}\""
    add_time_headers(resp, file, arxiv_id)
    resp.headers["ETag"] = last_modified(file)
    return resp  # type: ignore


def get_src_resp(arxiv_id_str: str,
                 archive: Optional[str] = None) -> Response:
    return get_dissemination_resp("e-print", arxiv_id_str, archive,
                                  src_resp_fn)


def get_e_print_resp(arxiv_id_str: str,
                     archive: Optional[str] = None) -> Response:
    return get_dissemination_resp("e-print", arxiv_id_str, archive)


def get_dissemination_resp(format: Acceptable_Format_Requests,
                           arxiv_id_str: str,
                           archive: Optional[str] = None,
                           resp_fn: Resp_Fn_Sig = default_resp_fn) -> Response:
    """
    Returns a `Flask` response ojbject for a given `arxiv_id` and `FileFormat`.

    The response will include headers and may do a range response.
    """
    arxiv_id_str = f"{archive}/{arxiv_id_str}" if archive else arxiv_id_str
    try:
        if len(arxiv_id_str) > 40:
            abort(400)
        if arxiv_id_str.startswith('arxiv/'):
            abort(400, description="do not prefix non-legacy ids with arxiv/")
        arxiv_id = Identifier(arxiv_id_str)
    except IdentifierException as ex:
        return bad_id(arxiv_id_str, str(ex))

    item = get_article_store().dissemination(format, arxiv_id)
    logger. debug(f"dissemination_for_id({arxiv_id.idv}) was {item}")
    if not item or item == "VERSION_NOT_FOUND" or item == "ARTICLE_NOT_FOUND":
        return not_found(arxiv_id)
    elif item == "WITHDRAWN" or item == "NO_SOURCE":
        return withdrawn(arxiv_id)
    elif item == "UNAVAILABLE":
        return unavailable(arxiv_id)
    elif format==fileformat.pdf and item == "NOT_PDF":
        return not_pdf(arxiv_id)
    elif isinstance(item, Deleted):
        return bad_id(arxiv_id, item.msg)
    elif format==fileformat.pdf and isinstance(item, CannotBuildPdf):
        return cannot_build_pdf(arxiv_id, item.msg)

    file, item_format, docmeta, version = item
    if not file.exists():
        return not_found(arxiv_id)

    return resp_fn(item_format, file, arxiv_id, docmeta, version)

def _get_latexml_conversion_file (arxiv_id: Identifier) -> Union[str, FileObj]: # str here should be the conditions
    """this is unused and leftover in case we want to reference peices from it, delete when done"""
    obj_store = GsObjectStore(storage.Client().bucket(current_app.config['LATEXML_BUCKET']))
    if arxiv_id.extra:
        item = obj_store.to_obj(f'{arxiv_id.idv}/{arxiv_id.extra}')
        if isinstance(item, FileDoesNotExist):
            return "NO_SOURCE" # TODO: This could be more specific
    else:
        item = obj_store.to_obj(f'{arxiv_id.idv}/{arxiv_id.idv}.html')
        if isinstance(item, FileDoesNotExist):
            return "ARTICLE_NOT_FOUND"


def get_html_response_old(arxiv_id_str: str,
                           archive: Optional[str] = None,
                           resp_fn: Resp_Fn_Sig = default_resp_fn) -> Response:
    """this is unused and leftover in case we want to reference peices from it, delete when done"""
    # if arxiv_id_str.endswith('.html'):
    #     return redirect(f'/html/{arxiv_id.split(".html")[0]}') 
    #TODO possibly add handling for .html at end of path, doesnt currently work on legacy either, currently causes Identifier Exception

    arxiv_id_str = f"{archive}/{arxiv_id_str}" if archive else arxiv_id_str
    try:
        if len(arxiv_id_str) > 40:
            abort(400)
        if arxiv_id_str.startswith('arxiv/'):
            abort(400, description="do not prefix non-legacy ids with arxiv/")
        arxiv_id = Identifier(arxiv_id_str)
    except IdentifierException as ex:
        return bad_id(arxiv_id_str, str(ex))

    metadata = get_doc_service().get_abs(arxiv_id)

    if metadata.source_format == 'html': #TODO find a way to distinguish that works. perhaps all the latex files have a latex source?
        native_html = True
        #TODO doesnt brian C have some sort of abstraction so we dont have to do this
        if not current_app.config["DISSEMINATION_STORAGE_PREFIX"].startswith("gs://"):
            obj_store = LocalObjectStore(current_app.config["DISSEMINATION_STORAGE_PREFIX"])
            #TODO would these files also come gzipped or some other format
        else:
            obj_store = GsObjectStore(storage.Client().bucket(
                current_app.config["DISSEMINATION_STORAGE_PREFIX"].replace('gs://', '')))
            
        item = get_article_store().dissemination(fileformat.html, arxiv_id)

       
    else:
        native_html = False
        #TODO assign some of the other variables like item format
        #you probably want to wire this one to go through dissemination too
        requested_file = _get_latexml_conversion_file(arxiv_id)
        if not arxiv_id.extra:
            return requested_file # Serve static asset
        docmeta = metadata
        version = docmeta.version
        item_format = fileformat.html

    if not item or item == "VERSION_NOT_FOUND" or item == "ARTICLE_NOT_FOUND":
            return not_found(arxiv_id)
    elif item == "WITHDRAWN" or item == "NO_SOURCE":
        return withdrawn(arxiv_id)
    elif item == "UNAVAILABLE":
        return unavailable(arxiv_id)
    elif isinstance(item, Deleted):
        return bad_id(arxiv_id, item.msg)

    if native_html:
        gzipped_file, item_format, docmeta, version = item
        if not gzipped_file.exists():
            return not_found(arxiv_id)
        #TODO some sort of error handlingfor not beign able to retrieve file, draft in conference proceeding.py
        unzipped_file=UngzippedFileObj(gzipped_file)

        if unzipped_file.name.endswith(".html"): #handle single html files here
            requested_file=unzipped_file
        else:
            tar_file=unzipped_file
            if arxiv_id.extra: #get specific file from tar file
                tarmember=FileFromTar(tar_file,arxiv_id.extra)
                if not tarmember.exists():
                    pass #TODO return appropriate error
                else:
                    requested_file=tarmember
            else: #check if one html file which we can serve or many to be selected from
                html_files=[]
                with tar_file.open(mode="rb") as fh:
                    with tarfile.open(fileobj=fh, mode="r") as tar:
                        for file_info in tar:
                            if file_info.name.endswith(".html"):
                                html_files.append(file_info.path)
                if len(html_files) ==1:
                    tarmember=FileFromTar(tar_file,html_files[0])
                    if not tarmember.exists():
                        pass #TODO return appropriate error
                    else:
                        requested_file=tarmember
                else:
                    pass #TODO do something about multiple file options
        #TODO process file here
        with requested_file.open('rb') as f:
            output= process_file(f,post_process_html2) #TODO put this into a file object

    response=default_resp_fn(item_format,requested_file,arxiv_id,docmeta,version)
    if native_html: 
        """special cases for the fact that documents within conference proceedings can change 
        which will appear differently in the conference proceeding even if the conference proceeding paper stays the same"""
        response.headers['Expires'] = format_datetime(next_publish())
        #TODO handle file modification times here

    return response

def get_html_response(arxiv_id_str: str,
                           archive: Optional[str] = None) -> Response:
    return get_dissemination_resp(fileformat.html, arxiv_id_str, archive, html_response_function)
    
def html_response_function(format: FileFormat,
                file: FileObj,
                arxiv_id: Identifier,
                docmeta: DocMetadata,
                version: VersionEntry)-> Response:
    if docmeta.source_format == 'html':
        return html_source_response_function(file,arxiv_id)
    else:
        return default_resp_fn(format,file,arxiv_id,docmeta,version)

def html_source_response_function(file: FileObj, arxiv_id: Identifier)-> Response:
    path=arxiv_id.extra

    if file.name.endswith(".html.gz") and path:
        raise NotFound

    unzipped_file = UngzippedFileObj(file)

    if unzipped_file.name.endswith(".html"):  # handle single html files here
        requested_file = unzipped_file
    else: #tar files here
        tar_file=unzipped_file
        if path: #get specific file from tar file
                tarmember=FileFromTar(tar_file, path)
                if not tarmember.exists():
                    raise NotFound
                else:
                    requested_file=tarmember
        else: #check if one html file which we can serve or many to be selected from
            html_files=[]
            with tar_file.open(mode="rb") as fh:
                with tarfile.open(fileobj=fh, mode="r") as tar:
                    for file_info in tar:
                        if file_info.name.endswith(".html"):
                            html_files.append(file_info.path)
            if len(html_files) ==1:
                tarmember=FileFromTar(tar_file,html_files[0])
                if not tarmember.exists():
                    raise NotFound
                else:
                    requested_file=tarmember
            else: #file selector for multiple html files
                return make_response(render_template("dissemination/multiple_files.html",arxiv_id=arxiv_id, files=html_files), 200, {})

    if requested_file.name.endswith(".html"):
        last_mod= last_modified(requested_file)
        with requested_file.open('rb') as f:
            output= process_file(f,post_process_html2)
        return _source_html_response(output, last_mod)
    else:
        return _guess_response(requested_file, arxiv_id)

def _latexml_response(file: FileObj, arxiv_id:Identifier) -> Response:
    #TODO actually Erin can do this part, Mark just needs to call it
    pass

def _guess_response(file: FileObj, arxiv_id:Identifier) -> Response:
    """make a response for an unknown file type"""
    resp: Response = RangeRequest(file.open('rb'),
                                  etag=last_modified(file),
                                  last_modified=file.updated,
                                  size=file.size).make_response()

    resp.headers['Access-Control-Allow-Origin'] = '*'
    add_time_headers(resp, file, arxiv_id)
    content_type, _ =mimetypes.guess_type(file.name)
    if content_type:
        resp.headers["Content-Type"] =content_type
    return resp

def _source_html_response(file: Generator[BytesIO, None, None], last_mod: str) -> Response:
    """make a response for a native html paper"""
    resp: Response = RangeRequest(file.open('rb'),
                                  etag=last_mod,
                                  last_modified=last_mod,
                                  size=file.size).make_response()

    resp.headers.pop('Content-Length')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers["Last-Modified"] = last_mod
    resp.headers['Expires'] = format_datetime(next_publish()) #conference proceedigns can change if the papers they reference get updated
    resp.headers["Content-Type"] = "text/html"
    resp.headers["ETag"] = last_mod
    return resp 

def withdrawn(arxiv_id: str) -> Response:
    """Sets expire to one year, max allowed by RFC 2616"""
    headers = {'Cache-Control': 'max-age=31536000'}
    return make_response(render_template("dissemination/withdrawn.html",
                                         arxiv_id=arxiv_id),
                         200, headers)


def unavailable(arxiv_id: str) -> Response:
    return make_response(render_template("dissemination/unavailable.html",
                                         arxiv_id=arxiv_id), 500, {})


def not_pdf(arxiv_id: str) -> Response:
    return make_response(render_template("dissemination/unavailable.html",
                                         arxiv_id=arxiv_id), 404, {})


def not_found(arxiv_id: str) -> Response:
    headers = {'Expires': format_datetime(next_publish())}
    return make_response(render_template("dissemination/not_found.html",
                                         arxiv_id=arxiv_id), 404, headers)


def not_found_anc(arxiv_id: str) -> Response:
    headers = {'Expires': format_datetime(next_publish())}
    return make_response(render_template("src/anc_not_found.html",
                                         arxiv_id=arxiv_id), 404, headers)


def bad_id(arxiv_id: str, err_msg: str) -> Response:
    return make_response(render_template("dissemination/bad_id.html",
                                         err_msg=err_msg,
                                         arxiv_id=arxiv_id), 404, {})


def cannot_build_pdf(arxiv_id: str, msg: str) -> Response:
    return make_response(render_template("dissemination/cannot_build_pdf.html",
                                         err_msg=msg,
                                         arxiv_id=arxiv_id), 404, {})