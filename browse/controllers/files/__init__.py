from typing import Iterator, Union
from email.utils import format_datetime
from flask import Response
from datetime import timezone
import mimetypes

from browse.domain.identifier import Identifier
from browse.domain.version import VersionEntry
from browse.services.next_published import next_publish
from browse.services.object_store import FileObj


BUFFER_SIZE = 1024 * 4

def cc_versioned() -> str:
    """Versioned PDFs should not change so let's put a time a bit in the future.

    Non versioned could change during the next publish.

    This could cause a version to stay in a CDN on a delete. That might require
    manual cache invalidation.

    """
    return 'max-age=604800'  # 7 days


def add_time_headers(resp: Response, file: FileObj, arxiv_id: Identifier) -> None:
    """Adds time headers to `resp` given the `file` and `arxiv_id`."""
    resp.headers["Last-Modified"] = last_modified(file)
    if arxiv_id.has_version:
        resp.headers['Cache-Control'] = cc_versioned()
    else:
        resp.headers['Expires'] = format_datetime(next_publish())


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
