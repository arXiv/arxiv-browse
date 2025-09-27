"""Service to get source for an article."""

import logging
import re
from typing import Optional, List

from arxiv.identifier import Identifier
from arxiv.document.metadata import DocMetadata
from arxiv.document.version import VersionEntry
from arxiv.files.key_patterns import abs_path_current_parent, abs_path_orig_parent, current_pdf_path, previous_pdf_path, \
    previous_ps_path, current_ps_path
from arxiv.files.object_store import ObjectStore
from arxiv.files import FileObj
from arxiv.formats import list_ancillary_files

logger = logging.getLogger(__file__)

src_regex = re.compile(r'.*(\.tar\.gz|\.pdf|\.ps\.gz|\.gz|\.div\.gz|\.html\.gz)')

MAX_ITEMS_IN_PATTERN_MATCH = 1000
"""This uses pattern matching on all the keys in an itmes directory. If
the number if items is very large the was probably a problem"""

# TODO move this src_path_prefix() to arxiv-base+
def src_path_prefix(arxiv_id: Identifier, is_current:bool) -> str:
    """Returns a path prefix that can be used to find the source of a version of a paper.

    Source files do not have a single file key pattern due to the multiple types of source formats.
    Ex. 2001.00001v1.pdf vs 2001.00001v1.tar.gz.

    An object key prefix where the file then need to be listed is used. List operations in GS are more expensive
    some other operations. In the future the DB should have a table of metadata_id -> source_file with a checksum.
    """
    if is_current:
        return f"{abs_path_current_parent(arxiv_id)}/{arxiv_id.filename}"
    else:
        return f"{abs_path_orig_parent(arxiv_id)}/{arxiv_id.filename}v{arxiv_id.version}"


class SourceStore():
    """Service for source related files.

    Example
    -------

        sstore = SourceStore(LocalObjectStore("/data/"))
        aid = '2012.12345v1'
        src = sstore.get_src(Identifier(aid))
        print(f"Length of source for {aid} is {src.size} bytes")

    """

    def __init__(self, objstore: ObjectStore):
        self.objstore = objstore

    def source_exists(self,
                      arxiv_id: Identifier,
                      docmeta: DocMetadata) -> bool:
        """Does the source exist for this `arxiv_id` and `docmeta`?"""
        return bool(self.get_src_for_docmeta(arxiv_id, docmeta))


    def get_src(self, arxiv_id: Identifier, is_current: bool) -> Optional[FileObj]:
        pattern = src_path_prefix(arxiv_id, is_current)
        items = list(self.objstore.list(pattern))
        if len(items) > MAX_ITEMS_IN_PATTERN_MATCH:
            raise Exception(f"Too many src matches for {pattern}")
        if len(items) > .9 * MAX_ITEMS_IN_PATTERN_MATCH:
            logger.warning("Unexpectedly large src matches %d, max is %d",
                           len(items), MAX_ITEMS_IN_PATTERN_MATCH)

        return next((item for item in items if src_regex.match(item.name)), None)

    def get_src_pdf(self, arxiv_id: Identifier, is_current: bool) -> Optional[FileObj]:
        """Try to get the PDF file as if paper is a pdf-only source paper."""
        if is_current or not arxiv_id.has_version:
            # try from the /ftp with no number for current ver of pdf only paper
            pdf_file = self.objstore.to_obj(current_pdf_path(arxiv_id))
            if pdf_file.exists():
                return pdf_file
        else:
            # try from the /orig with version number for a pdf only paper
            pdf_file = self.objstore.to_obj(previous_pdf_path(arxiv_id))
            if pdf_file.exists():
                return pdf_file

        return None

    def get_src_ps(self, arxiv_id: Identifier, is_current: bool) -> Optional[FileObj]:
        """Try to get the PS file as if paper is a PS-only source paper."""
        if is_current:
            # try from the /ftp with no number for current ver of pdf only paper
            # TODO: this should use current_ps_path() from arxiv-base but we
            # need this fixed and updgrading arxiv-base is going to be a bit of work
            archive = arxiv_id.archive if arxiv_id.is_old_id else 'arxiv'
            path = f"ftp/{archive}/papers/{arxiv_id.yymm}/{arxiv_id.filename}.ps.gz"
            ps_file = self.objstore.to_obj(path)
            if ps_file.exists():
                return ps_file
        else:
            # try from the /orig with version number for a pdf only paper
            # TODO: this should use previous_ps_path() from arxiv-base but we
            # need this fixed and updgrading arxiv-base is going to be a bit of work
            archive = arxiv_id.archive if arxiv_id.is_old_id else 'arxiv'
            path = f"orig/{archive}/papers/{arxiv_id.yymm}/{arxiv_id.filename}v{arxiv_id.version}.ps.gz"
            ps_file = self.objstore.to_obj(path)
            if ps_file.exists():
                return ps_file

        return None


    def get_src_for_version(self, arxiv_id: Identifier, version: VersionEntry) -> Optional[FileObj]:
        return self.get_src(arxiv_id, version.is_current)

    def get_src_for_docmeta(self,
                            arxiv_id: Identifier,
                            docmeta: DocMetadata) -> Optional[FileObj]:
        """Gets the src for the arxiv_id.

        Lists through possible extensions to find source file.

        Returns `FileObj` if found, `None` if not."""
        if arxiv_id.has_version and arxiv_id.version == docmeta.highest_version():
            return self.get_src(arxiv_id, True)
        elif not arxiv_id.has_version:
            return self.get_src(Identifier(arxiv_id.id), True)
        else:
            return self.get_src(arxiv_id, False)
        

    def get_ancillary_files(self, docmeta: DocMetadata) -> List[dict]:
        """Get list of ancillary file names and sizes.

        Parameters
        ----------
        docmeta : DocMetadata
            Item to get the ancillary files for.

        Returns
        -------
        List[Dict]
            List of Dict where each dict is a file name and size.
        """
        version = docmeta.version
        source_type = docmeta.version_history[version - 1].source_flag
        anc_files: List[dict] = []
        if not source_type.includes_ancillary_files:
            return anc_files
        return list_ancillary_files(self.get_src_for_docmeta(docmeta.arxiv_identifier, docmeta))
