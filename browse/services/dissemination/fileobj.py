"""FileObj for representing a file."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import IO


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
        """Does the storage obj exist?"""
        pass

    @abstractmethod
    def open(self,  *args, **kwargs) -> IO:  # type: ignore
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

    def open(self, *args, **kwargs) -> IO:  # type: ignore
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

    def open(self, *args, **kwargs) -> IO:  # type: ignore
        return self.item.open(*args, **kwargs) # type: ignore

    @property
    def etag(self) -> str:
        return "FAKE_ETAG"

    @property
    def size(self) -> int:
        return self.item.stat().st_size

    @property
    def updated(self) -> datetime:
        return datetime.fromtimestamp(self.item.stat().st_mtime, tz=timezone.utc)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"<LocalFileObj Path={self.item}>"
