"""ABC of the object store service."""

from abc import ABC, abstractmethod
from typing import IO, Iterable, Tuple, Literal
from datetime import datetime


class FileObj(ABC):
    """FileObj is a subset of the methods on GS `Blob`.

    The intent here is to facilitate testing by having a thin wrapper around Path
    to allow local files for testing.

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


class ObjectStore(ABC):
    """ABC for an object store"""

    @abstractmethod
    def to_obj(self, key: str) -> FileObj:
        """Gets a `FileObj` given a key"""
        pass

    @abstractmethod
    def list(self, dir: str) -> Iterable[FileObj]:
        """Gets a listing similar to what would be returned by `Client.list_blobs()`

        `dir` should end with a /
        """
        pass

    @abstractmethod
    def status() -> Tuple[Literal["GOOD","BAD"], str]:
        """Indicates the health of the service.

        Returns a tuple of either ("GOOD",'') or ("BAD","Some human readable message")

        The human readable message might be displayed publicly so do
        not put sensitive information in it.
        """
        pass

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
