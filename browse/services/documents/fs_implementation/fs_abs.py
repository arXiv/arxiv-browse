"""File system backed core metadata service."""
import os
from typing import Dict, List, Optional
import dataclasses

from browse.domain.metadata import DocMetadata
from browse.domain.identifier import Identifier
from browse.services.documents.config.deleted_papers import DELETED_PAPERS

from browse.services.documents.base_documents import DocMetadataService, \
    AbsDeletedException, AbsNotFoundException, \
    AbsVersionNotFoundException

from . import cache
from .legacy_fs_paths import FSDocMetaPaths
from .parse_abs import parse_abs_file
from .formats import formats_from_source_file_name
from ..format_codes import formats_from_source_type

class FsDocMetadataService(DocMetadataService):
    """Class for arXiv document metadata service."""
    fs_paths: FSDocMetaPaths

    def __init__(self,
                 latest_versions_path: str,
                 original_versions_path: str) -> None:
        """Initialize the FS document metadata service."""
        self.fs_paths = FSDocMetaPaths(latest_versions_path, original_versions_path)

    def get_abs(self, arxiv_id: str) -> DocMetadata:
        """Get the .abs metadata for the specified arXiv paper identifier.

        Parameters
        ----------
        arxiv_id : str
            The arXiv identifier string.

        Returns
        -------
        :class:`DocMetadata`
        """
        paper_id = Identifier(arxiv_id=arxiv_id)

        if paper_id.id in DELETED_PAPERS:
            raise AbsDeletedException(DELETED_PAPERS[paper_id.id])

        latest_version = self._abs_for_version(identifier=paper_id)
        if not paper_id.has_version \
           or paper_id.version == latest_version.version:
            return dataclasses.replace(latest_version,
                                       is_definitive=True,
                                       is_latest=True)

        try:
            this_version = self._abs_for_version(identifier=paper_id,
                                                 version=paper_id.version)
        except AbsNotFoundException as e:
            if paper_id.is_old_id:
                raise

            raise AbsVersionNotFoundException(e) from e

        # Several fields need to reflect the latest version's data
        combined_version: DocMetadata = dataclasses.replace(
            this_version,
            version_history=latest_version.version_history,
            categories=latest_version.categories,
            primary_category=latest_version.primary_category,
            secondary_categories=latest_version.secondary_categories,
            primary_archive=latest_version.primary_archive,
            primary_group=latest_version.primary_group,
            is_definitive=True,
            is_latest=False)

        return combined_version

    # Maybe this should move to formats.py?

    def get_dissemination_formats(self,
                                  docmeta: DocMetadata,
                                  format_pref: Optional[str] = None,
                                  add_sciencewise: bool = False) -> List[str]:
        """Get a list of formats that can be disseminated for this DocMetadata.

        Several checks are performed to determine available dissemination
        formats:
            1. a check for source files with specific, valid file name
               extensions (i.e. for a subset of the allowed source file name
               extensions, the dissemintation formats are predictable)
            2. if formats cannot be inferred from the source file, inspect the
               source type in the document metadata.

        Format names are strings. These include 'src', 'pdf', 'ps', 'html',
        'pdfonly', 'other', 'dvi', 'ps(400)', 'ps(600)', 'nops'.

        Parameters
        ----------
        docmeta : :class:`DocMetadata`
        format_pref : str
            The format preference string.
        add_sciencewise : bool
            Specify whether to include 'sciencewise_pdf' format in list.

        Returns
        -------
        List[str]
            A list of format strings.
        """
        formats: List[str] = []

        # first, get possible list of formats based on available source file
        source_file_path = self.fs_paths.get_source_path(docmeta.arxiv_identifier,
                                                         int(docmeta.version),
                                                         docmeta.is_latest)
        source_file_formats: List[str] = []
        if source_file_path is not None:
            source_file_formats = \
                formats_from_source_file_name(source_file_path)
        if source_file_formats:
            formats.extend(source_file_formats)

            if add_sciencewise:
                if formats and formats[-1] == 'other':
                    formats.insert(-1, 'sciencewise_pdf')
                else:
                    formats.append('sciencewise_pdf')

        else:
            # check source type from metadata, with consideration of
            # user format preference and cache
            version = docmeta.version
            format_code = docmeta.version_history[version - 1].source_type.code
            cached_ps_file_path = cache.get_cache_file_path(docmeta, 'ps')
            cache_flag = False
            if cached_ps_file_path \
                    and os.path.getsize(cached_ps_file_path) == 0 \
                    and source_file_path \
                    and os.path.getmtime(source_file_path) \
                    < os.path.getmtime(cached_ps_file_path):
                cache_flag = True

            source_type_formats = formats_from_source_type(format_code,
                                                           format_pref,
                                                           cache_flag,
                                                           add_sciencewise)
            if source_type_formats:
                formats.extend(source_type_formats)

        return formats

    def get_ancillary_files(self, docmeta: DocMetadata) \
            -> List[Dict]:
        """Get list of ancillary file names and sizes."""
        version = docmeta.version
        code = docmeta.version_history[version - 1].source_type.code
        return self.fs_paths.get_ancillary_files(code,
                                                 docmeta.arxiv_identifier,
                                                 docmeta.version)

    def _abs_for_version(self, identifier: Identifier,
                         version: Optional[int] = None) -> DocMetadata:
        """Get a specific version of a paper's abstract metadata.

        if version is None then get the latest version."""        
        path = self.fs_paths.get_abs_file(identifier, version)
        return parse_abs_file(filename=path)

