"""Functions to work with ancillary files"""

import re
import tarfile
from operator import itemgetter
from tarfile import CompressionError, ReadError
from typing import Dict, List, Optional

from browse.services.object_store.fileobj import FileObj



def list_ancillary_files(tarball: Optional[FileObj]) -> List[Dict]:
    """Return a list of ancillary files in a tarball (.tar.gz file)."""
    if not tarball or not tarball.name.endswith('.tar.gz') or not tarball.exists():
        return []

    anc_files = []
    try:
        with tarball.open(mode='rb') as fh:
            tf = tarfile.open(fileobj=fh, mode='r')  # type: ignore
            for member in \
                    (m for m in tf if re.search(r'^anc\/', m.name) and m.isfile()):
                name = re.sub(r'^anc\/', '', member.name)
                size_bytes = member.size
                anc_files.append({'name': name, 'size_bytes': size_bytes})
    except (ReadError, CompressionError) as ex:
        raise Exception(f"Problem while working with tar {tarball}") from ex

    return sorted(anc_files, key=itemgetter('name'))
