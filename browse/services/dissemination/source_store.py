"""Service to get source for an article."""

import html
import logging
import re
from typing import Optional

from arxiv.identifier import Identifier
from browse.domain.fileformat import FileFormat, dvigz, htmlgz, \
    pdf, psgz, ps, docx, odf, targz
from browse.domain.metadata import DocMetadata

from browse.services.object_store import FileObj, ObjectStore
from .key_patterns import abs_path_current_parent, abs_path_orig_parent

logger = logging.getLogger(__file__)

src_regex = re.compile(r'.*(\.tar\.gz|\.pdf|\.ps\.gz|\.gz|\.div\.gz|\.html\.gz)')

MAX_ITEMS_IN_PATTERN_MATCH = 1000
"""This uses pattern matching on all the keys in an itmes directory. If
the number if items is very large the was probably a problem"""


class SourceStore():
    """Service for source related files."""

    def __init__(self, objstore: ObjectStore):
        self.objstore = objstore

    def source_exists(self,
                      arxiv_id: Identifier,
                      docmeta: DocMetadata) -> bool:
        """Does the source exist for this `arxiv_id` and `docmeta`?"""
        return bool(self.get_src(arxiv_id, docmeta))

    def get_src(self,
                arxiv_id: Identifier,
                docmeta: DocMetadata) -> Optional[FileObj]:
        """Gets the src for the arxiv_id.

        Lists through possible extensions to find source file.

        Returns `FileObj` if found, `None` if not."""
        if not arxiv_id.has_version \
           or arxiv_id.version == docmeta.highest_version():
            parent = abs_path_current_parent(arxiv_id)
        else:
            parent = abs_path_orig_parent(arxiv_id)

        pattern = parent + '/' + arxiv_id.filename
        items = list(self.objstore.list(pattern))
        if len(items) > MAX_ITEMS_IN_PATTERN_MATCH:
            raise Exception(f"Too many src matches for {pattern}")
        if len(items) > .9 * MAX_ITEMS_IN_PATTERN_MATCH:
            logger.warning("Unexpectedly large src matches %d, max is %d",
                           len(items), MAX_ITEMS_IN_PATTERN_MATCH)

        item = next((item for item in items if src_regex.match(item.name)),
                    None)  # does any obj key match with any extension?
        return item

    def get_src_format(self,
                       docmeta: DocMetadata,
                       src_file: Optional[FileObj] = None) -> FileFormat:
        if src_file is None:
            src_file = self.get_src(docmeta.arxiv_identifier, docmeta)
        if src_file is None or src_file.name is None:
            raise ValueError(f"Must have  src_file and it must have a name for {docmeta.arxiv_identifier}")

        if src_file.name.endswith(".ps.gz"):
            return psgz
        if src_file.name.endswith(".pdf"):
            return pdf
        if src_file.name.endswith(".html.gz"):
            return htmlgz
        if src_file.name.endswith(".dvi.gz"):
            return dvigz

        # Otherwise look at the special info in the metadata
        # for help
        if not docmeta.arxiv_identifier.has_version:
            vent = docmeta.get_version(docmeta.highest_version())
        else:
            vent = docmeta.get_version(docmeta.arxiv_identifier.version)

        if not vent:
            raise Exception(f"No version entry for {docmeta.arxiv_identifier}")

        srctype = vent.source_type

        if srctype.ps_only:
            return ps
        elif srctype.html:
            return htmlgz
        elif srctype.pdflatex:
            raise Exception("Not pdflatex format yet implemented")
            #  return pdftex
        elif srctype.docx:
            return docx
        elif srctype.odf:
            return odf
        elif srctype.pdf_only:
            return pdf
        else:
            return targz  # this is tex in a tgz file

    # def src_includes_ancillary(self):
    #     pass

    # def src_ancillary_list(self):
    #     pass

    # def get_src_file(self, docmeta: DocMetadata, version: VersionEntry):
    #     pass
