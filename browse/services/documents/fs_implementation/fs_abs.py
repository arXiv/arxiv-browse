"""File system backed core metadata service."""

from typing import List, Union
import dataclasses


from arxiv.document.metadata import DocMetadata
from arxiv.document.parse_abs import parse_abs_file
from arxiv.identifier import Identifier
from arxiv.document.exceptions import (
    AbsDeletedException, 
    AbsNotFoundException,
    AbsVersionNotFoundException
)
from arxiv.files.object_store import ObjectStore
from arxiv.files.key_patterns import (
    abs_path_orig,
    abs_path_current
)
from browse.services.documents.config.deleted_papers import DELETED_PAPERS
from browse.services.documents.base_documents import DocMetadataService


def fs_check(abs_store: ObjectStore) -> List[str]:
    """Checks for a file system for use in `HasStatus.service_status()`"""
    try:
        status, message = abs_store.status()
        if status == 'BAD':
            return [f"{abs_store} status is BAD: {message}"]
    except Exception as ex:
        return [f"Object store status check failed due to {ex}"]

    return []


class FsDocMetadataService(DocMetadataService):
    """Class for arXiv document metadata service."""

    def __init__(self, abs_store: ObjectStore) -> None:
        """Initialize the FS document metadata service."""
        self.abs_store = abs_store

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
                                                 is_latest=False)
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

    def _abs_for_version(self, identifier: Identifier, is_latest: bool = True) -> DocMetadata:
        """Get a specific version of a paper's abstract metadata.

        if version is None then get the latest version."""        
        obj = self.abs_store.to_obj(abs_path_current(identifier)) if is_latest \
            else self.abs_store.to_obj(abs_path_orig(identifier))
        return parse_abs_file(obj)


    def service_status(self)->List[str]:
        probs = fs_check(self.abs_store)
        return [f"FsDocMetadataService: {prob}" for prob in probs]
