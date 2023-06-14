"""Functions that support determination of dissemination formats."""
import os
import re
from operator import itemgetter
from typing import Dict, List

import tarfile
from tarfile import ReadError, CompressionError
from browse.services.anypath import to_anypath

from ..format_codes import VALID_SOURCE_EXTENSIONS

import logging
logger = logging.getLogger(__name__)




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
