"""FileObj for representing a file."""

import gzip
import tarfile
import io
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from types import TracebackType
import typing
from typing import BinaryIO, Optional

class BinaryMinimalFile(typing.Protocol):
    def read(self, size: Optional[int] = -1) -> bytes:
        pass

    def readline(self, size: Optional[int] = -1) -> bytes:
        pass

    def seek(self, pos: int, whence:int=io.SEEK_SET) -> int:
        pass
    def close(self)->None:
        pass

    def __enter__(self) -> 'BinaryMinimalFile':
        pass

    def __exit__(self,
                 exc_type: Optional[typing.Type[BaseException]],
                 exc_val: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> None:
        pass

    def __iter__(self) -> typing.Iterator[bytes]:
        pass

class FileObj(ABC):
    """FileObj is a subset of the methods on GS `Blob`.

    The intent here is to facilitate testing by having a thin wrapper around
    Path to allow local files for testing.

    If a new method from `Blob` is needed for use in these packages,
    add the `abstractmethod` to `FileObj` then implement a local
    version in `LocalFileObj`. The method added to `FileObj` should
    have the exact type signature as the method in `Blob`.

    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name, either path or key"""
        pass

    @abstractmethod
    def exists(self) -> bool:
        """Does the storage obj exist?

        This is not a property due to it not being a propery on GS `Blob`."""
        pass

    @abstractmethod
    def open(self, mode:str) -> BinaryMinimalFile:
        """Opens the object similar to the normal Python `open()`"""
        pass

    @property
    @abstractmethod
    def etag(self) -> str:
        """Gets the etag for the storage object"""
        pass

    @property
    @abstractmethod
    def size(self) -> int:
        """Size in bytes"""
        pass

    @property
    @abstractmethod
    def updated(self) -> datetime:
        """Datetime object of last modified"""


class FileDoesNotExist(FileObj):
    """Represents a file that does not exist"""

    def __init__(self, item: str):
        self.item = item

    @property
    def name(self) -> str:
        return self.item

    def exists(self) -> bool:
        return False

    def open(self, mode:str) -> BinaryMinimalFile:
        raise Exception("File does not exist")

    @property
    def etag(self) -> str:
        raise Exception("File does not exist")

    @property
    def size(self) -> int:
        raise Exception("File does not exist")

    @property
    def updated(self) -> datetime:
        raise Exception("File does not exist")

    def __repr__(self) -> str:
        return f"FileDoesNotExist({self.item})"


class LocalFileObj(FileObj):
    """File object backed by local files.

    The goal here is to have LocalFileObj mimic `Blob` in the
    methods and properties that are used.
    """

    def __init__(self, item: Path):
        self.item = item

    @property
    def name(self) -> str:
        return self.item.name

    def exists(self) -> bool:
        return self.item.exists()

    def open(self, *args, **kwargs) -> BinaryIO:  # type: ignore
        return self.item.open(*args, **kwargs)  # type: ignore

    @property
    def etag(self) -> str:
        return "FAKE_ETAG"

    @property
    def size(self) -> int:
        return self.item.stat().st_size

    @property
    def updated(self) -> datetime:
        return datetime.fromtimestamp(self.item.stat().st_mtime,
                                      tz=timezone.utc)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"<LocalFileObj Path={self.item}>"


class MockStringFileObj(FileObj):
    """File object backed by a utf-8 `str`."""

    def __init__(self, name: str, data: str):
        self._name = name
        self._data = bytes(data, 'utf-8')
        self._size = len(self._data)

    @property
    def name(self) -> str:
        return self._name

    def exists(self) -> bool:
        return True

    def open(self, mode:str) -> BinaryMinimalFile:
        return io.BytesIO(self._data)

    @property
    def etag(self) -> str:
        return "FAKE_ETAG"

    @property
    def size(self) -> int:
        return self._size

    @property
    def updated(self) -> datetime:
        return datetime.fromtimestamp(0, tz=timezone.utc)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"<MockFileObj name={self.name}>"


class UngzippedFileObj(FileObj):
    """File object backed by different file object and un-gzipped."""

    def __init__(self, gzipped_file: FileObj):
        self._fileobj = gzipped_file
        self._size = -1

    @property
    def name(self) -> str:
        if self._fileobj.name.endswith(".gz"):
            return self._fileobj.name[:-3]
        elif self._fileobj.name.endswith(".gzip"):
            return self._fileobj.name[:-5]
        else:
            return self._fileobj.name

    def exists(self) -> bool:
        return self._fileobj.exists()

    def open(self, mode:str) -> BinaryMinimalFile:
        return gzip.GzipFile(filename="",
                             mode=mode,
                             fileobj=self._fileobj.open(mode))

    @property
    def etag(self) -> str:
        return self._fileobj.etag

    @property
    def size(self) -> int:
        if self._size >= 0:
            return self._size
        else:
            # Seems gzip files will have the size as the last 4 bytes of the
            # file.  That won't record file sizes larger than 4Gb and there may
            # be other quirks.  So for now we get it by reading and unzipping
            # the whole file.
            with self._fileobj.open("rb") as unzip_f:
                size = unzip_f.seek(0, io.SEEK_END)
                self._size = size
            return self._size

    @property
    def updated(self) -> datetime:
        return self._fileobj.updated

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"<GunzipFileObj fileobj={self._fileobj}>"


class FileNotFound(Exception):
    """Raised when a `path` cannot be found in a tar."""


class FileFromTar(FileObj):
    """Single file from a tar `FileObj`."""

    def __init__(self, tar_file: FileObj, path: str):
        self._fileobj = tar_file
        self._path = path
        self._size = -1
        self._path_exists: Optional[bool] = None
        self._tarinfo: Optional[tarfile.TarInfo] = None

    @property
    def name(self) -> str:
        return self._path

    def exists(self) -> bool:
        """Returns `True` if `tar_file` exists and a member exists at `path` in
        the tar.

        This extracts and saves the tarinfo. That records the offset into
        the tar file. So it should not be too inefficient.
        """
        if self._path_exists is not None:
            return self._path_exists

        if not self._fileobj.exists():
            self._path_exists = False
            return False

        with self._fileobj.open("rb") as fh:
            with tarfile.open(fileobj=fh, mode="r") as tar:  # type: ignore
                try:
                    self._tarinfo = tar.getmember(self._path)
                    self._path_exists = True
                    self._size = self._tarinfo.size
                    return True
                except KeyError:
                    self._path_exists = False
                    return False

    def open(self, mode:str) -> BinaryMinimalFile:
        # Why does this not use `with`? Because after the return it would be out of the with scope
        # and the file will be closed and unusable.
        fh = self._fileobj.open(mode)
        tfh = tarfile.open(fileobj=fh, mode="r")  # type: ignore
        try:
            if self._tarinfo is None:
                member = tfh.getmember(self._path)
            else:
                member = self._tarinfo
        except KeyError:
            raise FileNotFound(f"could not find {self._path} in tar")
        ef = tfh.extractfile(member)
        if ef:
            return typing.cast(BinaryMinimalFile, ef)
        else:
            raise FileNotFound(f"could not extract {self._path} in tar")

    @property
    def etag(self) -> str:
        raise Exception("Not implemented due to it being inefficent")

    @property
    def size(self) -> int:
        """This is only set after `open()` or `exists()` were called."""
        return self._size

    @property
    def updated(self) -> datetime:
        return self._fileobj.updated

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"<FileFromTar fileobj={self._fileobj} path={self._path}>"



DEFAULT_IO_SIZE = 8 * 1024 * 1024


class BinaryMinimalFileTransformed(BinaryMinimalFile):
    """A file like object that includes a transform."""

    def __init__(self, inner_io: BinaryMinimalFile, transform: typing.Callable[[bytes], bytes]):
        self.transform = transform
        self.io = inner_io
        self.buffer = b""
        self.at_start = True
        super().__init__()

    def readline(self, size: Optional[int] = -1) -> bytes:
        if size is None or size <= 0:
            size = DEFAULT_IO_SIZE
        if not self.buffer:
            data = self.read(size)
            self.buffer = data + self.buffer

        lines = self.buffer.split(b"\n")
        line = lines[0]
        self.buffer = b"\n".join(lines[1:])
        return line

    def read(self, size: Optional[int] = -1) -> bytes:
        if size is None or size <= 0:
            size = DEFAULT_IO_SIZE

        self.at_start = False
        while True:
            data = self.io.readline(size)
            self.buffer = self.buffer + self.transform(data)
            if not data or len(self.buffer) >= size:
                break

        if len(self.buffer) <= size:
            to_return = self.buffer
            self.buffer = b""
            return to_return
        else:
            to_return = self.buffer[:size]
            self.buffer = self.buffer[size:]
            return to_return

    def seek(self, pos: int, whence: int = io.SEEK_SET) -> int:
        if not self.at_start:
            raise RuntimeError("Cannot seek after reading")
        if whence != io.SEEK_SET:
            raise ValueError("whence is not supported")
        data = self.read(pos)
        return len(data)

    def close(self) -> None:
        self.io.close()
        self.buffer = b""
        self.at_start = True

    def __enter__(self) -> 'BinaryMinimalFile':
        return self

    def __exit__(self,
                 exc_type: Optional[typing.Type[BaseException]],
                 exc_val: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> None:
        self.close()

    def __iter__(self) -> typing.Iterator[bytes]:
        for line in self.io:
            yield self.transform(line)




class FileTransform(FileObj):
    """A `FileObj` that applies a transform to the original data."""

    def __init__(self, file: FileObj, transform: typing.Callable[[bytes], bytes]):
        self.fileobj = file
        self.transform = transform

    @property
    def name(self) -> str:
        return self.fileobj.name

    def exists(self) -> bool:
        return self.fileobj.exists()

    def open(self, mode:str) -> BinaryMinimalFile:
        return BinaryMinimalFileTransformed(self.fileobj.open('rb'), self.transform)

    @property
    def etag(self) -> str:
            return self.fileobj.etag
    @property
    def size(self) -> int:
        """This is only set after `open()` or `exists()` were called."""
        # TODO Size is going to be a lie.
        return self.fileobj.size

    @property
    def updated(self) -> datetime:
        return self.fileobj.updated

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"<FileProcessed fileobj={self.fileobj} transform={self.transform}>"


