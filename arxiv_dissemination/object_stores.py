"""Thin wrappers around the object stores."""

from abc import ABC, abstractmethod
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

    @abstractmethod
    def glob(self, pattern) -> Iterable["FileObj"]:
        """Glob on this path with pattern"""


FileObj.register(Blob)


class LocalFileObj(FileObj):
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

    def glob(self, patt):
        return (LocalFileObj(item) for item in self.item.glob(patt))



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

    def glob(self, _):
        raise Exist("Files not exist")

    def __repr__(self):
        return f"FileDoesNotExist({self.item})"

def to_obj_gs(bucket: Bucket, key:str) -> FileObj:
    """Gets the blob fom google-cloud-storage"""
    blob = bucket.get_blob(key)
    if not blob:
        return FileDoesNotExist(bucket.name + key)
    else:
        return blob


def to_obj_local(prefix: str, key:str) -> FileObj:
    """Gets a Path from local file system"""
    item = Path(prefix + key)
    if not item or not item.exists():
        return FileDoesNotExist(prefix + key)
    else:
        return LocalFileObj(Path(item))
