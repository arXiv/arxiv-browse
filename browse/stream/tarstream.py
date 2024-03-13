"""Streamng tar files."""

from io import BytesIO
import tarfile
from typing import Callable, Iterator, List

from arxiv.files import FileObj

BUFFER_SIZE = 16 * 1024  # bytes, similar to tarfile.copyfileobj()


class _FileStream():
    def __init__(self) -> None:
        self.buffer = BytesIO()
        self.offset = 0

    def write(self, s: bytes) -> None:
        self.buffer.write(s)
        self.offset += len(s)

    def tell(self) -> int:
        return self.offset

    def close(self) -> None:
        self.buffer.close()

    def pop(self) -> bytes:
        data = self.buffer.getvalue()
        self.buffer.close()
        self.buffer = BytesIO()
        return data


def _to_tarinfo(fileobj: FileObj) -> tarfile.TarInfo:
    tarinfo = tarfile.TarInfo(fileobj.name)
    tarinfo.mtime = int(fileobj.updated.timestamp())
    tarinfo.size = fileobj.size
    return tarinfo


def tar_stream_gen(files: List[FileObj],
                   to_tarinfo: Callable[[FileObj], tarfile.TarInfo] = _to_tarinfo)\
        -> Iterator[bytes]:
    """Returns an `iterator[bytes]` over the bytes of a .tar made up of the
    items in `file_list`.

    This will be gzipped."""
    buffer = _FileStream()
    tar = tarfile.TarFile.open('no_file_name',
                               mode='w|gz',
                               fileobj=buffer)  # type: ignore
    if tar.fileobj is None:
        raise Exception("Tar has None for fileobj")

    for fileobj in files:
        tarinfo = to_tarinfo(fileobj)
        tar.addfile(tarinfo)
        yield buffer.pop()

        with fileobj.open('rb') as fp:
            while True:
                blk = fp.read(BUFFER_SIZE)
                if len(blk) > 0:
                    tar.fileobj.write(blk)
                    yield buffer.pop()
                if len(blk) < BUFFER_SIZE:
                    # taken from tarfile.TarFile.addfile()
                    blocks, remainder = divmod(tarinfo.size, tarfile.BLOCKSIZE)
                    if remainder > 0:
                        tar.fileobj.write(
                            tarfile.NUL * (tarfile.BLOCKSIZE - remainder))
                        yield buffer.pop()
                        blocks += 1

                    tar.offset += blocks * tarfile.BLOCKSIZE
                    break

    tar.close()
    yield buffer.pop()
