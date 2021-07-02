"""Functions that support determination of dissemination formats."""
import os
import re
from operator import itemgetter
from typing import Dict, List

import tarfile
from tarfile import ReadError, CompressionError

from ..format_codes import VALID_SOURCE_EXTENSIONS

import logging
logger = logging.getLogger(__name__)


def formats_from_source_file_name(source_file_path: str) -> List[str]:
    """Get list of formats based on source file name."""
    if not source_file_path:
        return []
    for extension in VALID_SOURCE_EXTENSIONS:
        if source_file_path.endswith(extension[0]) \
                and isinstance(extension[1], list):
            return extension[1]
    return []


def list_ancillary_files(tarball_path: str) -> List[Dict]:
    """Return a list of ancillary files in a tarball (.tar.gz file)."""
    if not tarball_path or not tarball_path.endswith('.tar.gz') \
       or not os.path.isfile(tarball_path):
        return []

    anc_files = []
    try:
        tf = tarfile.open(tarball_path, mode='r')
        for member in \
                (m for m in tf if re.search(r'^anc\/', m.name) and m.isfile()):
            name = re.sub(r'^anc\/', '', member.name)
            size_bytes = member.size
            anc_files.append({'name': name, 'size_bytes': size_bytes})
    except (ReadError, CompressionError):
        # TODO: log this?, no probably raise and let caller handle what to do
        return []
    if len(anc_files) > 1:
        anc_files = sorted(anc_files, key=itemgetter('name'))
    return anc_files
