"""ABC of the object store service."""

from abc import ABC, abstractmethod
from typing import Iterable, Literal, Tuple

from .fileobj import FileObj


class ObjectStore(ABC):
    """ABC for an object store"""

    @abstractmethod
    def to_obj(self, key: str) -> FileObj:
        """Gets a `FileObj` given a key"""
        pass

    @abstractmethod
    def list(self, dir: str) -> Iterable[FileObj]:
        """Gets a listing similar to returned by `Client.list_blobs()`

        `dir` should end with a /
        """
        pass

    @abstractmethod
    def status(self) -> Tuple[Literal["GOOD", "BAD"], str]:
        """Indicates the health of the service.

        Returns a tuple of either ("GOOD",'') or ("BAD","Some human readable
        message")

        The human readable message might be displayed publicly so do
        not put sensitive information in it.

        """
        pass
