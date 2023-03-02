"""Functions that support determintation of dissemination formats."""
import os
import re
from operator import itemgetter
from typing import Dict, List

import tarfile
from tarfile import ReadError, CompressionError
from cloudpathlib.anypath import to_anypath

from ..format_codes import VALID_SOURCE_EXTENSIONS

import logging
logger = logging.getLogger(__name__)


def formats_from_source_file_name(source_file_path: str) -> List[str]:
    """Get list of formats based on source file name."""
    if not source_file_path:
        return []
    for extension in VALID_SOURCE_EXTENSIONS:
        if str(source_file_path).endswith(extension[0]) \
                and isinstance(extension[1], list):
            return extension[1]
    return []


def list_ancillary_files(tarball_path: str) -> List[Dict]:
    """Return a list of ancillary files in a tarball (.tar.gz file)."""
    if not tarball_path or not tarball_path.endswith('.tar.gz'):
        return []
    tarf=to_anypath(tarball_path)
    if not tarf or not tarf.is_file():
        return []

    anc_files = []
    try:
        with tarf.open(mode='rb') as fh:
            tf = tarfile.open(fileobj=fh, mode='r')
            for member in \
                    (m for m in tf if re.search(r'^anc\/', m.name) and m.isfile()):
                name = re.sub(r'^anc\/', '', member.name)
                size_bytes = member.size
                anc_files.append({'name': name, 'size_bytes': size_bytes})
    except (ReadError, CompressionError) as ex:
        raise Exception(f"Problem while working with tar file {tarball_path}") from ex

    return sorted(anc_files, key=itemgetter('name'))
