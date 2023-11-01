"""Controller for PDF, source and other downloads."""

import logging
from email.utils import format_datetime
from typing import Callable, Optional, Union, List
import tempfile
import mimetypes
from io import BytesIO, StringIO
from typing import Generator

from browse.domain.identifier import Identifier, IdentifierException
from browse.domain.fileformat import FileFormat
from browse.domain.version import VersionEntry
from browse.domain.metadata import DocMetadata
from browse.domain import fileformat

from browse.controllers.files import stream_gen, last_modified, add_time_headers

from browse.services.object_store.fileobj import FileObj, UngzippedFileObj, FileDoesNotExist
from browse.services.object_store.object_store_gs import GsObjectStore

from browse.services.html_processing import post_process_html

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
        if len(arxiv_id_str) > 2048:
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

    #check for existence
    if not isinstance(file, List): #single file
        if not file.exists():
            return not_found(arxiv_id)
    else: #potential list of files
        if not file[0].exists():
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
    return item

def get_html_response(arxiv_id_str: str,
                           archive: Optional[str] = None) -> Response:
    return get_dissemination_resp(fileformat.html, arxiv_id_str, archive, html_response_function)
    
def html_response_function(format: FileFormat,
                file_list: Union[List[FileObj],FileObj],
                arxiv_id: Identifier,
                docmeta: DocMetadata,
                version: VersionEntry)-> Response:
    if docmeta.source_format == 'html':
        return html_source_response_function(file_list,arxiv_id)
    else:
        return _latexml_response(format,file_list,arxiv_id,docmeta,version)

def html_source_response_function(file_list: List[FileObj], arxiv_id: Identifier)-> Response:
    path=arxiv_id.extra
    requested_file=None
    #try and serve specific file path
    if path:
        for file in file_list:
            if file.name.endswith(path):
                requested_file=file
                break
        if requested_file is None: #couldn't find file with that path
            raise NotFound
    else: #just serve the article
        html_files=[]
        file_names=[]
        for file in file_list:
            if file.name.endswith(".html"):
                html_files.append(file)
                file_names.append(_get_html_file_name(file.name))
        if len(html_files)==1: #serve the only html file
            requested_file=html_files[0]
        else: #file selector for multiple html files
            return make_response(render_template("dissemination/multiple_files.html",arxiv_id=arxiv_id, file_names=file_names), 200, {})

    if requested_file.name.endswith(".html"):
        last_mod= last_modified(requested_file)
        output= process_file(requested_file,post_process_html)
        return _source_html_response(output, last_mod)
    else:
        return _guess_response(requested_file, arxiv_id)

def _get_html_file_name(name:str) -> str:
    # file paths should be of form "ps_cache/cs/html/0003/0003064v1/HTTPFS-Paper.html" with a minimum of 5 slashes
    parts = name.split('/')
    if len(parts) > 5:
        result = '/'.join(parts[5:])
    else:
        result= parts[-1]
    return result

def _latexml_response(format: FileFormat,
                    file: FileObj,
                    arxiv_id: Identifier,
                    docmeta: DocMetadata,
                    version: VersionEntry) -> Response:
    
 
    resp=default_resp_fn(format,file,arxiv_id,docmeta,version)
    resp.headers['Content-Type'] = "text/html"
    return resp

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

def _source_html_response(gen: Generator[BytesIO, None, None], last_mod: str) -> Response:
    """make a response for a native html paper"""
    #turn generator into temp file
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        for data in gen:
            temp_file.write(data)
        temp_file.seek(0)
    #make response
        resp: Response = make_response(temp_file.read())
        resp.status_code=200
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