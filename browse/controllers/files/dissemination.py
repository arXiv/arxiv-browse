"""Controller for PDF, source and other downloads."""

import logging
from pathlib import Path
from typing import Callable, Optional, Union, List
import tempfile
import mimetypes
from io import BytesIO
from typing import Generator

from browse.domain.identifier import Identifier, IdentifierException
from browse.domain.fileformat import FileFormat
from browse.domain.version import VersionEntry
from browse.domain.metadata import DocMetadata
from browse.domain import fileformat

from browse.controllers.files import last_modified, add_time_headers, add_mimetype, \
    download_file_base, maxage

from browse.services.object_store.fileobj import FileObj

from browse.services.html_processing import post_process_html

from browse.services.dissemination import get_article_store
from browse.services.dissemination.article_store import (
    Acceptable_Format_Requests, CannotBuildPdf, Deleted)

from browse.stream.file_processing import process_file
from flask import Response, abort, make_response, render_template
from flask_rangerequest import RangeRequest
from werkzeug.exceptions import  NotFound


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
    """Creates a response with appropriate headers for the `file`.

    Parameters
    ----------
    format : FileFormat
        `FileFormat` of the `file`
    docmeta : DocMetadata
        article that the response is for.
    file : FileObj
        File object to use in the response.
    version: VersionEntry
        Version of the paper to consider.
    extra: Optional[str], optional
        Any extra after the normal URL path part. For use in anc files or html files.
    """
    # Have to do Range Requests to get GCP and fastly CDNs to accept larger objects.
    resp: Response = RangeRequest(file.open('rb'),
                                  etag=file.etag,
                                  last_modified=file.updated,
                                  size=file.size).make_response()

    resp.headers['Access-Control-Allow-Origin'] = '*'
    if isinstance(format, FileFormat):
        resp.headers['Content-Type'] = format.content_type

    add_time_headers(resp, file, arxiv_id)
    return resp


def src_resp_fn(format: FileFormat,
                file: FileObj,
                arxiv_id: Identifier,
                docmeta: DocMetadata,
                version: VersionEntry,
                extra: Optional[str] = None) -> Response:
    """Download source"""
    resp = RangeRequest(file.open('rb'),
                        etag=file.etag,
                        last_modified=file.updated,
                        size=file.size).make_response()

    suffixes = Path(file.name).suffixes
    if not arxiv_id.is_old_id:
        suffixes.pop(0)  # get rid of .12345
    filename = download_file_base(arxiv_id, version) + "".join(suffixes)
    resp.headers["Content-Disposition"] = f"attachment; filename=\"{filename}\""

    add_mimetype(resp, file.name)
    add_time_headers(resp, file, arxiv_id)
    return resp  # type: ignore

def pdf_resp_fn(format: FileFormat,
                 file: FileObj,
                    arxiv_id: Identifier,
                    docmeta: DocMetadata,
                    version: VersionEntry,
                    extra: Optional[str] = None) -> Response:
    """funciton to make a `Response` for a PDF."""
    resp = default_resp_fn(format, file, arxiv_id, docmeta, version, extra)
    filename = f"{arxiv_id.filename}v{version.version} .pdf"
    resp.headers["Content-Disposition"] = f"inline; filename=\"{filename}\""
    return resp

def get_pdf_resp(arxiv_id_str: str, archive: Optional[str] = None) -> Response:
    """Gets a `Response` for a PDF reqeust."""
    return get_dissemination_resp(fileformat.pdf, arxiv_id_str, archive, pdf_resp_fn)

def get_src_resp(arxiv_id_str: str,
                 archive: Optional[str] = None) -> Response:
    return get_dissemination_resp("e-print", arxiv_id_str, archive, src_resp_fn)


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
    logger. debug(f"dissemination_for_id(%s) was %s", arxiv_id.idv, item)
    if not item or item == "VERSION_NOT_FOUND" or item == "ARTICLE_NOT_FOUND":
        return not_found(arxiv_id)
    elif item == "WITHDRAWN" or item == "NO_SOURCE":
        return withdrawn(arxiv_id, arxiv_id.has_version)
    elif item == "UNAVAILABLE":
        return unavailable(arxiv_id)
    elif item == "NOT_PDF":
        return not_pdf(arxiv_id)
    elif item == "NO_HTML":
        return no_html(arxiv_id)
    elif isinstance(item, Deleted):
        return bad_id(arxiv_id, item.msg)
    elif isinstance(item, CannotBuildPdf):
        return cannot_build_pdf(arxiv_id, item.msg)

    file, item_format, docmeta, version = item

    # check for existence
    if not isinstance(file, List): # single file
        if not file.exists():
            return not_found(arxiv_id)
    else: # potential list of files
        if not file[0].exists():
            return not_found(arxiv_id)

    return resp_fn(item_format, file, arxiv_id, docmeta, version) #type: ignore

def get_html_response(arxiv_id_str: str,
                           archive: Optional[str] = None) -> Response:
    return get_dissemination_resp(fileformat.html, arxiv_id_str, archive, html_response_function)
    
def html_response_function(format: FileFormat,
                file_list: Union[List[FileObj],FileObj],
                arxiv_id: Identifier,
                docmeta: DocMetadata,
                version: VersionEntry)-> Response:
    if docmeta.source_format == 'html':
        if not isinstance(file_list,list):
            return unavailable(arxiv_id)
        return html_source_response_function(file_list,arxiv_id)
    else:
        if not isinstance(file_list,FileObj):
            return unavailable(arxiv_id)
        return _latexml_response(format,file_list,arxiv_id,docmeta,version)

def html_source_response_function(file_list: List[FileObj], arxiv_id: Identifier)-> Response:
    path=arxiv_id.extra
    requested_file=None
    #try and serve specific file path
    if path:
        for file in file_list:
            if path[1:]== _get_html_file_name(file.name): #first character of path is /
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
        if len(html_files)<1:
            return unavailable(arxiv_id)
        if len(html_files)==1: #serve the only html file
            requested_file=html_files[0]
        else: #file selector for multiple html files
            return multiple_html_files(arxiv_id,file_names)

    if requested_file.name.endswith(".html"):
        last_mod= last_modified(requested_file)
        output= process_file(requested_file, post_process_html)
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

    return _guess_response(file,arxiv_id)

def _guess_response(file: FileObj, arxiv_id:Identifier) -> Response:
    """make a response for an unknown file type"""
    resp: Response = RangeRequest(file.open('rb'),
                                  etag=file.etag,
                                  last_modified=file.updated,
                                  size=file.size).make_response()

    resp.headers['Access-Control-Allow-Origin'] = '*'
    add_time_headers(resp, file, arxiv_id)
    content_type, _ = mimetypes.guess_type(file.name)
    if content_type:
        resp.headers["Content-Type"] = content_type
    return resp

def _source_html_response(gen: Generator[BytesIO, None, None], last_mod: str) -> Response:
    """make a response for a native html paper"""
    #turn generator into temp file
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        for data in gen:
            temp_file.write(data) #type: ignore
        temp_file.seek(0)
    #make response
        resp: Response = make_response(temp_file.read())
        resp.status_code=200
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers["Last-Modified"] = last_mod
        resp.headers['Cache-Control'] = maxage(False)
        resp.headers["Content-Type"] = "text/html"
        resp.headers["ETag"] = last_mod
    return resp 

def withdrawn(arxiv_id: Identifier, had_specific_version: bool=False) -> Response:
    """Sets expire to one year, max allowed by RFC 2616"""
    if had_specific_version:
        headers = {'Cache-Control': 'max-age=31536000'}
    else:
        headers = {'Cache-Control': maxage(False)}
    return make_response(render_template("dissemination/withdrawn.html",
                                         arxiv_id=arxiv_id),
                         404, headers)


def unavailable(arxiv_id: Identifier) -> Response:
    return make_response(render_template("dissemination/unavailable.html",
                                         arxiv_id=arxiv_id), 500, {})


def not_pdf(arxiv_id: Identifier) -> Response:
    return make_response(render_template("dissemination/unavailable.html",
                                         arxiv_id=arxiv_id), 404, {})

def no_html(arxiv_id: Identifier) -> Response:
    return make_response(render_template("dissemination/no_html.html",
                                         arxiv_id=arxiv_id), 404, {})

def not_found(arxiv_id: Identifier) -> Response:
    headers = {'Cache-Control': maxage(arxiv_id.has_version)}
    return make_response(render_template("dissemination/not_found.html",
                                         arxiv_id=arxiv_id), 404, headers)


def not_found_anc(arxiv_id: Identifier) -> Response:
    headers = {'Cache-Control':  maxage(arxiv_id.has_version)}
    return make_response(render_template("src/anc_not_found.html",
                                         arxiv_id=arxiv_id), 404, headers)


def bad_id(arxiv_id: Union[Identifier,str], err_msg: str) -> Response:
    return make_response(render_template("dissemination/bad_id.html",
                                         err_msg=err_msg,
                                         arxiv_id=arxiv_id), 404, {})


def cannot_build_pdf(arxiv_id: Identifier, msg: str) -> Response:
    return make_response(render_template("dissemination/cannot_build_pdf.html",
                                         err_msg=msg,
                                         arxiv_id=arxiv_id), 404, {})

def multiple_html_files(arxiv_id: Identifier, file_names: List[str]) -> Response:
    resp=make_response(render_template("dissemination/multiple_files.html",
                                         arxiv_id=arxiv_id, file_names=file_names), 200, {})
    resp.headers["Content-Type"] = "text/html"
    resp.headers['Cache-Control'] = maxage(arxiv_id.has_version)
    return resp
