"""Paths to files in the legacy arXiv FS."""

from typing import Optional, List, Dict

from browse.services.anypath import to_anypath, APath

from arxiv.identifier import Identifier

from .formats import list_ancillary_files
from ..format_codes import has_ancillary_files, VALID_SOURCE_EXTENSIONS


class FSDocMetaPaths():
    """Class for paths to files in the legacy arXiv FS."""

    def __init__(self,
                 latest_versions_path: str,
                 original_versions_path: str) -> None:
        """Initialize"""
        self.latest_versions_path = to_anypath(latest_versions_path).resolve()
        if not self.latest_versions_path or not self.latest_versions_path.exists():
            raise ValueError('Path to latest .abs versions '
                            f'{latest_versions_path} does not exist')
        if not self.latest_versions_path.is_dir():
            raise ValueError('Path to latest .abs versions'
                             f' {latest_versions_path} is not a directory')

        self.original_versions_path = to_anypath(original_versions_path).resolve()
        if not self.original_versions_path or not self.original_versions_path.exists():
            raise ValueError('Path to original .abs versions '
                               f'"{original_versions_path}" does not exist')
        if not self.original_versions_path.is_dir():
            raise ValueError('Path to original .abs versions '
                               f'"{original_versions_path}" is not a directory')


    def get_abs_file(self,
                     identifier: Identifier,
                     version: Optional[int] = None)->str:
        """Gets the absolute path to the .abs file.

        Ex. for 1408.0391 v2 -> /data/orig/arxiv/papers/1408/1408.0391v2.abs"""
        parent_path = self._get_parent_path(identifier=identifier, version=version)
        return str(parent_path.joinpath((f'{identifier.filename}.abs' if not version
                                         else f'{identifier.filename}v{version}.abs')))

    def _get_parent_path(self,
                         identifier: Identifier,
                         version: Optional[int] = None) -> APath:
        """Get the Path for FS absolute parent path of the provided identifier.

        ex For 1408.0391 v2 -> /data/orig/arxiv/papers/1408/"""
        # TODO Check if this is correct in the case of vN is the latest version for the item
        # ex. say 1408.0391 has versions 1 through 5. The abs for v5 is in /data/ftp/arxiv/papers/1408
        ver_path =self.latest_versions_path if not version else self.original_versions_path

        return ver_path.joinpath(('arxiv' if not identifier.is_old_id or identifier.archive is None
                                  else identifier.archive),
                                 'papers',
                                 identifier.yymm)

    def get_parent_path(self,
                        identifier: Identifier,
                        version: Optional[int] = None) -> str:
        """Get the FS absolute parent path of the provided identifier.

        ex For 1408.0391 v2 -> /data/orig/arxiv/papers/1408/"""
        return str(self._get_parent_path(identifier, version))

    def get_source_path(self,
                         identifier: Identifier,
                         version: Optional[int] = None,
                         is_latest: Optional[bool] = True
                         ) -> Optional[str]:
        """Get the absolute path of this DocMetadata's source.

        Returns the first file found that seems like a source file in _parent_path.

        Ex. for 1408.0391 v2 -> /data/orig/arxiv/papers/1408/1408.0391v2.tar.gz"""
        file_noex = identifier.filename
        if not is_latest:
            parent_path = self._get_parent_path(identifier, version)
            file_noex = f'{file_noex}v{version}'
        else:
            parent_path = self._get_parent_path(identifier)

        for extension in VALID_SOURCE_EXTENSIONS:
            possible_path = parent_path.joinpath(f'{file_noex}{extension[0]}')
            if possible_path.is_file():
                return str(possible_path)
        return None
