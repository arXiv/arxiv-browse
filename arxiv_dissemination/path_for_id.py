"""Path to the PDF for a given ID"""

import re
from typing import Union, Literal, Optional
from pathlib import Path

from cloudpathlib.anypath import to_anypath
from cloudpathlib import CloudPath

from arxiv.identifier import Identifier

import logging
logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)

APath = Union[CloudPath, Path]

FORMATS = Union[Literal["pdf"], Literal["ps"]]

def path_for_id(storage_prefix: str, format:FORMATS, arxiv_id:Identifier) -> Optional[APath]:
    """Path to the PDF for a given ID"""
    if format != "pdf":
        raise Exception("Only PDF is currently supported")

    if not arxiv_id.has_version:
        current_pdf = current_pdf_path(storage_prefix, arxiv_id)
        if current_pdf.exists():
            return current_pdf

        pdf = cached_current_pdf(storage_prefix, format, arxiv_id)
        if pdf.exists():
            return pdf
        else:
            logger.debug("no file found for %s, tried %s", arxiv_id.idv, [str(current_pdf)])
            return None
    else:
        # Try the ps_cache first since that covers most papers    
        ps_cache_pdf = ps_cache_pdf_path(storage_prefix, format, arxiv_id)
        if ps_cache_pdf.exists():
            return ps_cache_pdf

        non_current_pdf=previous_pdf_path(storage_prefix, arxiv_id)
        if non_current_pdf.exists():
            return non_current_pdf

        current_pdf = current_pdf_path(storage_prefix, arxiv_id)
        if current_pdf.exists():
            return current_pdf
        else:
            logger.debug("no file found for %s, tried %s", arxiv_id.idv,
                         [str(ps_cache_pdf), str(non_current_pdf), str(current_pdf)])
            return None

def _ps_cache_part(storage_prefix:str, format: FORMATS, arxiv_id: Identifier) -> str:
    archive = arxiv_id.archive if arxiv_id.is_old_id else 'arxiv'
    return f"{storage_prefix}/ps_cache/{archive}/{format}/{arxiv_id.yymm}"
    
def ps_cache_pdf_path(storage_prefix: str, format:FORMATS, arxiv_id: Identifier)  -> APath:
    """Returns the path for a PDF from the ps_cache for a version.

    For PDFs in ps_cache, all of the versions are in the same directory so
    there is no current/non-current distinction when using the ps_cache.

    All the PDFs in ps_cache should have been built from tex.
    
    This will return the proper path if it exists or not."""
    dir = _ps_cache_part(storage_prefix, format, arxiv_id)
    return to_anypath(f"{dir}/{arxiv_id.filename}v{arxiv_id.version}.pdf")


def current_pdf_path(storage_prefix, arxiv_id: Identifier) -> APath:
    """Returns the path for a PDF only submission for a current version.

    This will return the proper path if it exists or not."""

    # TODO Need to add check such that a v23 doesn't return
    # current version on a paper with only 3 versions.
    archive = arxiv_id.archive if arxiv_id.is_old_id else 'arxiv'
    return to_anypath(f"{storage_prefix}/ftp/{archive}/papers/{arxiv_id.yymm}/{arxiv_id.filename}.pdf")


def previous_pdf_path(storage_prefix, arxiv_id: Identifier) -> APath:
    """Returns the path for a PDF only submission for a non current version.

    This will return the proper path if it exists or not."""
    archive = arxiv_id.archive if arxiv_id.is_old_id else 'arxiv'
    return to_anypath(f"{storage_prefix}/orig/{archive}/papers/{arxiv_id.yymm}/{arxiv_id.filename}v{arxiv_id.version}.pdf")


v_regex = re.compile(r'.*v(\d+)')

def _path_to_version(path):
    mtch = v_regex.search(path.name)
    if mtch:
        return mtch.group(1)
    else:
        return 0
    
def cached_current_pdf(storage_prefix: str, format: FORMATS, arxiv_id:Identifier) -> APath:
    """Current pdf from ps_cache.

    If the current pdf is not in `ftp/` then we are dealing with a TeX submission and
    have to find the highest numbered pdf in ps_cache.
    """
    dir = _ps_cache_part(storage_prefix, format, arxiv_id)
    pdf_versions = to_anypath(f"{dir}").glob(f"{arxiv_id.filename}*")
    return max(pdf_versions, key=_path_to_version)    
