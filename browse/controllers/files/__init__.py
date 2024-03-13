from typing import Iterator, Union
from email.utils import format_datetime
from flask import Response, make_response, render_template
from datetime import timezone
import mimetypes

from arxiv.identifier import Identifier
from arxiv.document.version import VersionEntry
from arxiv.files import FileObj


BUFFER_SIZE = 1024 * 4

def maxage(versioned: bool=False) -> str:
    """Returns a "max-age=N" `str` for use with "Cache-Control".

    This could cause a version to stay in a CDN on delete. That might require
    manual cache invalidation.

    versioned: if the request was for a versioned paper or the current version.
    """
    return f'max-age={60 * 30}' if versioned else f'max-age={60 * 15}'  # sec


def add_time_headers(resp: Response, file: FileObj, arxiv_id: Identifier) -> None:
    """Adds time headers to `resp` given the `file` and `arxiv_id`."""
    resp.headers["Last-Modified"] = last_modified(file)
    resp.headers['Cache-Control'] = maxage(arxiv_id.has_version)


def last_modified(fileobj: FileObj) -> str:
    """Returns a value for use with HTTP last-Modified."""
    return format_datetime(fileobj.updated.astimezone(timezone.utc),
                           usegmt=True)


def stream_gen(file: FileObj) -> Iterator[bytes]:
    """Returns a generator that returns the bytes from `file` to be used with a
    Flask response."""
    with file.open("rb") as fh:
        while True:
            chunk = fh.read(BUFFER_SIZE)
            if not chunk:
                break
            yield chunk


def add_mimetype(resp: Response, filename: Union[str|FileObj]) -> None:
    content_type, _ = mimetypes.guess_type(filename.name if isinstance(filename, FileObj) else filename)
    if content_type:
        resp.headers["Content-Type"] = content_type


def download_file_base(arxiv_id: Identifier, version: Union[VersionEntry|int|str]) -> str:
    """Returns a `str` to use for a downloaded filename.

    It will always have a version so that if the user has a download directory full of
    arxiv files new ones will not overwrite old ones.

    Ex. arXiv-cs02021234v3 or arXiv-1802.12345v9"""
    v_num = version.version if isinstance(version, VersionEntry) else int(version)
    return f"arXiv-{arxiv_id.squashed}v{v_num}"


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
