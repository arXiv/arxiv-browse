"""Service to get source for an article."""

import logging
import re
from typing import Optional

from arxiv.identifier import Identifier
from browse.domain.metadata import DocMetadata
from browse.domain.fileformat import pdf, htmlgz, psgz, dvigz, FileFormat

from .fileobj import FileObj
from .key_patterns import abs_path_current_parent, abs_path_orig_parent
from .object_store import ObjectStore


logger = logging.getLogger(__file__)

src_regex = re.compile(r'.*(\.tar\.gz|\.pdf|\.ps\.gz|\.gz|\.div\.gz|\.html\.gz)')

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
        if len(items) > 1000:
            # This seems like it must be a mistake if the quantity is this large
            raise Exception(f"Very large number of src matches for {pattern}")
        if len(items) > 300:
            logger.warning("Unexpectedly large Number of src matches %d",
                           len(items))

        item = next((item for item in items if src_regex.match(item.name)),
                    None)  # does any obj key match with any extension?
        return item

    def get_src_format(self,
                       arxiv_id: Identifier,
                       docmeta: DocMetadata) -> Optional[FileFormat]:
        src_file = self.get_src(arxiv_id, docmeta)
        if  src_file is None or src_file.name is None:
            return None
        if src_file.name.endswith("/\.ps\.gz$/"):
            return psgz
        if src_file.name.endswith("/\.pdf/"):
            return pdf
        if src_file.name.endswith("/\.html\.gz/"):
            return htmlgz
        if src_file.name.endswith("/\.dvi\.gz/"):
            return dvigz

        # Otherwise look at the special info in the metadata
        # for help

            # } elsif ($special =~ /P/i) {
          #     $type='ps';
          #   } elsif ($special =~ /H/i) {
          #     $type='html';
          #   } elsif ($special =~ /D/i) {
          #     $type='pdftex';
          #   } elsif ($special =~ /X/i) {
          #     $type='docx';
          #   } elsif ($special =~ /O/i) {
          #     $type='odf';
          #   } elsif ($special =~ /F/i) {
          #     $type='pdf';
          #   } else {
          #     $type='tex'
          #   }
          # }
          # return($type);
          #}

        return None

    # def src_includes_ancillary(self):
    #     pass

    # def src_ancillary_list(self):
    #     pass

    # def get_src_file(self, docmeta: DocMetadata, version: VersionEntry):
    #     pass
