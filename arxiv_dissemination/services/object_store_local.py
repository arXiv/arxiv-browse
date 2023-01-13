"""ObjectStore that uses local FS and Path"""

from typing import IO, Iterator
from datetime import datetime, timezone
from pathlib import Path


from .object_store import ObjectStore, FileObj, FileDoesNotExist

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

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"<LocalObjectStore {self.prefix}>"


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

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"<LocalFileObj Path={self.item}>"
