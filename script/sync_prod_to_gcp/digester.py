import hashlib
import io
import os
from datetime import datetime, timezone

IO_BUFFER_1 = bytearray(2 ** 18)  # Reusable buffer to reduce allocations.
IO_VIEW_1 = memoryview(IO_BUFFER_1)

def binary_file_digest(fileobj: io.BytesIO, hasher=None) -> str:
    """You'd need to open file with binary - rb
    default hasher is sha256.
    """
    digestobj = hashlib.new("sha256" if hasher is None else hasher)
    while True:
        size = fileobj.readinto(IO_BUFFER_1)
        if size == 0:
            break  # EOF
        digestobj.update(IO_VIEW_1[:size])
        pass
    return digestobj.hexdigest()


def digest_from_filepath(localfile: str, hasher=None) -> str:
    """File digest from local file.
    default hasher is sha256.
    """
    with open(localfile, "rb") as fd:
        return binary_file_digest(fd, hasher)
    pass


def get_file_mtime(localfile: str) -> str:
    file_stat = os.stat(localfile)
    return datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc).isoformat()
