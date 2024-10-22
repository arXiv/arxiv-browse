from typing import Iterator, Union, Dict, List
from email.utils import format_datetime
from flask import Response, make_response, render_template
from datetime import timezone
import mimetypes

from arxiv.identifier import Identifier
from arxiv.document.version import VersionEntry
from arxiv.files import FileObj
from arxiv.integration.fastly.headers import add_surrogate_key

BUFFER_SIZE = 1024 * 4

CACHE_AGE_SEC_VERSIONED = 60 * 60 * 24 * 7
"""cache-control max-age for versioned requests.

An example of a versioned request: /pdf/0202.12345v1

This is set long since changes to old versions are infrequent. When old papers
change, right after the announce process there is a call to purge the paper's
related URLs from the fastly cache.

"""

CACHE_AGE_SEC_UNVERSIONED = 60 * 60 * 24
"""cache-control max-age for unversioned requests.

An example of an unversioned request: /pdf/0202.12345

These can change during the next publish. Right after the announce process,
replacements have all their related URLs invalidated.

"""

def maxage(versioned: bool=False) -> str:
    """Returns a "max-age=N" `str` for use with "Surrogate-Control".

    This could cause a version to stay in a CDN on delete. That might require
    manual cache invalidation.

    versioned: if the request was for a versioned paper or the current version.
    """
    return f'max-age={CACHE_AGE_SEC_VERSIONED}' if versioned else f'max-age={CACHE_AGE_SEC_UNVERSIONED}'  # sec


def add_time_headers(resp: Response, file: FileObj, arxiv_id: Identifier) -> None:
    """Adds time headers to `resp` given the `file` and `arxiv_id`."""
    resp.headers["Last-Modified"] = last_modified(file)
    resp.headers['Surrogate-Control'] = maxage(arxiv_id.has_version)


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
    """adds the appropriate content type header to the response based on file name"""
    name = filename.name if isinstance(filename, FileObj) else filename

    if name.endswith(".gz"):
        content_type: str|None="application/gzip"
    else:
        content_type, _ = mimetypes.guess_type(name)    

    if content_type:
        resp.headers["Content-Type"] = content_type
        if content_type=="text/html":
            resp.headers['Content-Type'] = "text/html; charset=utf-8" #all our html should be in utf-8


def download_file_base(arxiv_id: Identifier, version: Union[VersionEntry|int|str]) -> str:
    """Returns a `str` to use for a downloaded filename.

    It will always have a version so that if the user has a download directory full of
    arxiv files new ones will not overwrite old ones.

    Ex. arXiv-cs02021234v3 or arXiv-1802.12345v9"""
    v_num = version.version if isinstance(version, VersionEntry) else int(version)
    return f"arXiv-{arxiv_id.squashed}v{v_num}"

def no_source(arxiv_id: Identifier, had_specific_version: bool=False) -> Response:
    """Sets expire to one year, max allowed by RFC 2616"""
    headers= _unavailable_headers(arxiv_id, ["no-source"])
    if had_specific_version:
        headers['Surrogate-Control']= 'max-age=31536000'
    else:
        headers['Surrogate-Control']= maxage(False)
    return make_response(render_template("dissemination/no_source.html",
                                         arxiv_id=arxiv_id),
                         404, headers)

def withdrawn(arxiv_id: Identifier, had_specific_version: bool=False) -> Response:
    """Sets expire to one year, max allowed by RFC 2616"""
    headers= _unavailable_headers(arxiv_id, ["withdrawn"])
    if had_specific_version:
        headers['Surrogate-Control']= 'max-age=31536000'
    else:
        headers['Surrogate-Control']= maxage(False)
    return make_response(render_template("dissemination/withdrawn.html",
                                         arxiv_id=arxiv_id),
                         404, headers)

def not_public(arxiv_id: Identifier, had_specific_version: bool=False) -> Response:
    """ Returned for pages whose source is encrypted/ made not public by the author.
    Sets expire to one year, max allowed by RFC 2616"""
    headers= _unavailable_headers(arxiv_id, ["not-public"])
    if had_specific_version:
        headers['Surrogate-Control']= 'max-age=31536000'
    else:
        headers['Surrogate-Control']= maxage(False)
    return make_response(
        render_template("dissemination/not_public.html",arxiv_id=arxiv_id), 403, headers
    )


def unavailable(arxiv_id: Identifier) -> Response:
    headers= _unavailable_headers(arxiv_id, [])
    return make_response(render_template("dissemination/unavailable.html",
                                         arxiv_id=arxiv_id), 500, headers)


def not_pdf(arxiv_id: Identifier) -> Response:
    headers= _unavailable_headers(arxiv_id, ["pdf"])
    return make_response(render_template("dissemination/unavailable.html",
                                         arxiv_id=arxiv_id), 404, headers)


def no_html(arxiv_id: Identifier) -> Response:
    headers= _unavailable_headers(arxiv_id, ["html"])
    return make_response(render_template("dissemination/no_html.html",
                                         arxiv_id=arxiv_id), 404, headers)


def not_found(arxiv_id: Identifier) -> Response:
    headers= _unavailable_headers(arxiv_id, ["not-found"])
    return make_response(render_template("dissemination/not_found.html",
                                         arxiv_id=arxiv_id), 404, headers)


def not_found_anc(arxiv_id: Identifier) -> Response:
    headers= _unavailable_headers(arxiv_id, ["anc"])
    return make_response(render_template("src/anc_not_found.html",
                                         arxiv_id=arxiv_id), 404, headers)


def bad_id(arxiv_id: Union[Identifier,str], err_msg: str) -> Response:
    headers: Dict[str,str]
    if isinstance(arxiv_id,str):
        headers={'Surrogate-Control': 'max-age=31536000'}
        headers=add_surrogate_key(headers, ["paper-unavailable", "bad-id"])
    else:
        headers= _unavailable_headers(arxiv_id, [])
        headers['Surrogate-Control']= 'max-age=31536000'
    return make_response(render_template("dissemination/bad_id.html",
                                         err_msg=err_msg,
                                         arxiv_id=arxiv_id), 404, headers)


def cannot_build_pdf(arxiv_id: Identifier, msg: str, fmt: str) -> Response:
    headers= _unavailable_headers(arxiv_id, ["pdf"])
    return make_response(render_template("dissemination/cannot_build_pdf.html",
                                         msg=msg,
                                         fmt=fmt,
                                         arxiv_id=arxiv_id), 404, headers)

def _unavailable_headers(arxiv_id: Identifier, other_tags: List[str]) -> Dict[str,str]:
    keys=["paper-unavailable", f"paper-id-{arxiv_id.id}"] + other_tags

    if arxiv_id.has_version: 
        keys.append(f"paper-id-{arxiv_id.idv}")
        keys.append(f"unavailable-{arxiv_id.idv}")
        for tag in other_tags:
            keys.append(f"{tag}-{arxiv_id.idv}")
    else:
        keys.append(f"paper-id-{arxiv_id.id}-current")
        keys.append(f"unavailable-{arxiv_id.id}-current")
        for tag in other_tags:
            keys.append(f"{tag}-{arxiv_id.id}-current")

    headers: Dict[str,str]={}
    headers['Surrogate-Control'] = maxage(arxiv_id.has_version)
    headers=add_surrogate_key(headers, keys)
    return headers