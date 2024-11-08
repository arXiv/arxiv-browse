from pathlib import Path
from urllib.parse import urlparse

import google.cloud.storage as storage
from arxiv.files import FileObj

from arxiv.files.object_store import ObjectStore, GsObjectStore, LocalObjectStore


def _path_to_store(path: str) -> ObjectStore:
    uri = urlparse(path)
    if uri.scheme == "gs":
        gs_client = storage.Client()
        return GsObjectStore(gs_client.bucket(uri.netloc))
    else:
        return LocalObjectStore(path)


def one_time_file(path:str) -> FileObj:
    """Get a file without making a global file store.

    Only use this for files that are loaded at app start up time.
    Do not use this for an `ObjectStore` that would be reused during the life of the app as it
    is inefficient to make the `storage.Client`."""
    uri = urlparse(path)
    if uri.scheme == "gs":
        store = _path_to_store(path)
        return store.to_obj(uri.path)
    else:
        yy = Path(path)
        return _path_to_store(str(yy.parent)).to_obj(yy.name)

def get_global_object_store(path: str, global_name: str) -> ObjectStore:
    """Creates an object store from given path."""
    store = globals().get(global_name)
    if store is None:
        store = _path_to_store(path)
        globals()[global_name] = store
    return store
