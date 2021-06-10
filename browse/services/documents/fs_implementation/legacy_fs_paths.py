"""Paths to files in the legacy arXiv FS."""

from typing import Optional, List, Dict
import os

from browse.domain.identifier import Identifier

from .formats import VALID_SOURCE_EXTENSIONS, has_ancillary_files, list_ancillary_files

class FSDocMetaPaths():
    """Class for paths to files in the legacy arXiv FS."""

    def __init__(self,
                 latest_versions_path: str,
                 original_versions_path: str) -> None:
        """Initialize"""
        if not os.path.isdir(latest_versions_path):
            raise ValueError('Path to latest .abs versions '
                               f'"{latest_versions_path}" does not exist')
        if not os.path.isdir(original_versions_path):
            raise ValueError('Path to original .abs versions '
                               f'"{original_versions_path}" does not exist')

        self.latest_versions_path = os.path.realpath(latest_versions_path)
        self.original_versions_path = os.path.realpath(original_versions_path)


    def get_abs_file(self,
                     identifier: Identifier,
                     version: Optional[int] = None)->str:
        """Gets the absolute path to the .abs file.

        Ex. for 1408.0391 v2 -> /data/orig/arxiv/papers/1408/1408.0391v2.abs"""
        parent_path = self.get_parent_path(identifier=identifier,
                                           version=version)
        return os.path.join(parent_path,
                            (f'{identifier.filename}.abs' if not version
                             else f'{identifier.filename}v{version}.abs'))
    
    def get_parent_path(self,
                        identifier: Identifier,
                        version: Optional[int] = None) -> str:
        """Get the FS absolute parent path of the provided identifier.

        ex For 1408.0391 v2 -> /data/orig/arxiv/papers/1408/"""
        parent_path = os.path.join(
            (self.latest_versions_path if not version
             else self.original_versions_path),
            ('arxiv' if not identifier.is_old_id or identifier.archive is None
             else identifier.archive),
            'papers',
            identifier.yymm,
        )
        return parent_path

    def get_source_path(self,
                         identifier: Identifier,
                         version: Optional[int] = None,
                         is_latest: Optional[bool] = True
                         ) -> Optional[str]:
        """Get the absolute path of this DocMetadata's source.

        Ex. for 1408.0391 v2 -> /data/orig/arxiv/papers/1408/1408.0391v2.tar.gz"""
        file_noex = identifier.filename
        if not is_latest:
            parent_path = self.get_parent_path(identifier, version)
            file_noex = f'{file_noex}v{version}'
        else:
            parent_path = self.get_parent_path(identifier)

        for extension in VALID_SOURCE_EXTENSIONS:
            possible_path = os.path.join(
                parent_path,
                f'{file_noex}{extension[0]}')
            if os.path.isfile(possible_path):
                return possible_path
        return None

    
    def get_ancillary_files(self,
                            source_type_code: str,
                            identifier: Identifier,
                            version: Optional[int],
                            is_latest: Optional[bool]= True,
                            ) -> List[Dict]:
        """Get list of ancillary file names and sizes.

        source_type_code: value ofdocmeta.source_type.code
        """
        if has_ancillary_files(source_type_code):
            source_file_path = self.get_source_path(identifier,version,is_latest)
            if source_file_path is not None:
                return list_ancillary_files(source_file_path)
            else:
                return []
        return []


