"""File system backed core metadata service."""

from typing import List, Optional, Union
import dataclasses

from arxiv.document.metadata import DocMetadata
from arxiv.document.parse_abs import parse_abs_file
from arxiv.identifier import Identifier
from arxiv.document.exceptions import (
    AbsDeletedException, 
    AbsNotFoundException,
    AbsVersionNotFoundException
)
from browse.services.documents.config.deleted_papers import DELETED_PAPERS
from arxiv.files.anypath import fs_check

from browse.services.documents.base_documents import DocMetadataService

from .legacy_fs_paths import FSDocMetaPaths

class FsDocMetadataService(DocMetadataService):
    """Class for arXiv document metadata service."""
    fs_paths: FSDocMetaPaths

    def __init__(self,
                 latest_versions_path: str,
                 original_versions_path: str) -> None:
        """Initialize the FS document metadata service."""
        self.fs_paths = FSDocMetaPaths(latest_versions_path, original_versions_path)

    def get_abs(self, arxiv_id: Union[str, Identifier]) -> DocMetadata:
        """Get the .abs metadata for the specified arXiv paper identifier.

        Parameters
        ----------
        arxiv_id : str
            The arXiv identifier string.

        Returns
        -------
        :class:`DocMetadata`
        """
        if isinstance(arxiv_id, Identifier):
            paper_id = arxiv_id
        else:
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

    def _abs_for_version(self, identifier: Identifier,
                         version: Optional[int] = None) -> DocMetadata:
        """Get a specific version of a paper's abstract metadata.

        if version is None then get the latest version."""        
        path = self.fs_paths.get_abs_file(identifier, version)
        return parse_abs_file(filename=path)



    def service_status(self)->List[str]:
        probs = fs_check(self.fs_paths.latest_versions_path)
        probs.extend(fs_check(self.fs_paths.original_versions_path))
        return ["FsDocMetadataService: {prob}" for prob in probs]
