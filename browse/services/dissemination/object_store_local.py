"""ObjectStore that uses local FS and Path"""

from pathlib import Path
from typing import Iterator, Literal, Tuple

from .fileobj import FileDoesNotExist, FileObj, LocalFileObj
from .object_store import ObjectStore


class LocalObjectStore(ObjectStore):
    """ObjectStore that uses local FS and Path"""
    def __init__(self, prefix:str):
        if not prefix:
            raise ValueError("Must have a prefix")
        if not prefix.endswith('/'):
            raise ValueError("prefix must end with /")

        self.prefix = prefix

    def to_obj(self,  key:str) -> FileObj:
        """Gets a `LocalFileObj` from local file system"""
        item = Path(self.prefix + key)
        if not item or not item.exists():
            return FileDoesNotExist(self.prefix + key)
        else:
            return LocalFileObj(Path(item))


    def list(self, key: str) -> Iterator[FileObj]:
        """Gets a listing similar to what would be returned by `Client.list_blobs()`

        `key` should end with a /

        `prefix` should be just a path to a file name. Example:
        'ps_cache/arxiv/pdf/1212/1212.12345' or
        'ftp/cs/papers/0012/0012007'.
        """
        parent, file = Path(self.prefix+key).parent, Path(self.prefix+key).name
        return (LocalFileObj(item) for item in Path(parent).glob(f"{file}*"))

    def status(self) -> Tuple[Literal["GOOD", "BAD"], str]:
        if Path(self.prefix).exists():
            return ("GOOD", "")
        else:
            return ("BAD", "Local storage path doesn't exist")

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"<LocalObjectStore {self.prefix}>"
