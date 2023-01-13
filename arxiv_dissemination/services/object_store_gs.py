"""ObjectStore that uses Google GS buckets"""


from typing import Iterator

from collections.abc import Iterator

from google.cloud.storage.blob import Blob
from google.cloud.storage.bucket import Bucket

from .object_store import ObjectStore, FileObj, FileDoesNotExist

# This causes the `Blob` class to be considered a subclass of `FileObj`
FileObj.register(Blob)


class GsObjectStore(ObjectStore):
    def __init__(self, bucket:Bucket):
        if not bucket:
            raise ValueError("Must set a bucket")
        self.bucket = bucket

    def to_obj(self, key:str) -> FileObj:
        """Gets the `Blob` fom google-cloud-storage.

        Returns `FileDoesNotExist` if there is no object at the key."""
        blob = self.bucket.get_blob(key)
        if not blob:
            return FileDoesNotExist("gs://" + self.bucket.name + '/' + key)
        else:
            return blob

    def list(self, prefix: str) -> Iterator[FileObj]:
        """Gets listing of keys with prefix.

        `prefix` should be just a path to a file name. Example:
        'ps_cache/arxiv/pdf/1212/1212.12345' or
        'ftp/cs/papers/0012/0012007'.
        """
        return self.bucket.client.list_blobs(self.bucket, prefix=prefix)
