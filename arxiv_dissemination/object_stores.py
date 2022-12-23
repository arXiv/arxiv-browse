"""Thin wrappers around the object stores."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import IO, Iterable
from datetime import datetime, timezone
from pathlib import Path

from google.cloud.storage.blob import Blob
from google.cloud.storage.bucket import Bucket


class FileObj(ABC):
    """FileObj is a subset of the methods on GS Blob.

    The intent here is to facilitate testing by having a thin wrapper around Path
    to allow local files for testing.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name, either path or key"""
        pass

    @abstractmethod
    def exists(self) -> bool:
        """Does the storage obj exist?"""
        pass

    @abstractmethod
    def open(self,  *args, **kwargs) -> IO:
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


FileObj.register(Blob)


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

    def open(self, *args, **kwargs) -> IO:
        return self.item.open(*args, **kwargs)

    @property
    def etag(self) -> str:
        return "FAKE_ETAG"

    @property
    def size(self) -> int:
        return self.item.stat().st_size

    @property
    def updated(self) -> datetime:
        return datetime.fromtimestamp(self.item.stat().st_mtime, tz=timezone.utc)



class FileDoesNotExist(FileObj):
    """Represents a file that does not exist"""

    def __init__(self, item: str):
        self.item = item

    @property
    def name(self):
        return self.item

    def exists(self):
        return False

    def open(self, *args, **kwargs) -> IO:
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

    def __repr__(self):
        return f"FileDoesNotExist({self.item})"


def to_obj_gs(bucket: Bucket, key:str) -> FileObj:
    """Gets the `Blob` fom google-cloud-storage"""
    blob = bucket.get_blob(key)
    if not blob:
        return FileDoesNotExist("gs://" + bucket.name + '/' + key)
    else:
        return blob


def to_obj_local(prefix: str, key:str) -> FileObj:
    """Gets a `LocalFileObj` from local file system"""
    item = Path(prefix + key)
    if not item or not item.exists():
        return FileDoesNotExist(prefix + key)
    else:
        return LocalFileObj(Path(item))


def local_list(dir: str, prefix:str) -> Iterator[FileObj]:
    """Gets a listing similar to what would be returned by `Client.list_blobs()`

    `dir` should end with a /

    `prefix` should be just a path to a file name. Example:
    'ps_cache/arxiv/pdf/1212/1212.12345' or
    'ftp/cs/papers/0012/0012007'.
    """
    parent, file = Path(dir+prefix).parent, Path(dir+prefix).name
    return (LocalFileObj(item) for item in Path(parent).glob(f"{file}*"))

def gs_list(bucket: Bucket, prefix: str) -> Iterator[FileObj]:
    """Gets listing of keys with prefix.

    `prefix` should be just a path to a file name. Example:
    'ps_cache/arxiv/pdf/1212/1212.12345' or
    'ftp/cs/papers/0012/0012007'.
    """
    return bucket.client.list_blobs(bucket, prefix=prefix)
