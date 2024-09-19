from urllib.parse import urlparse

import google.cloud.storage as storage

from arxiv.files.object_store import ObjectStore, GsObjectStore, LocalObjectStore

def get_global_object_store(path: str, global_name: str) -> ObjectStore:
    """Creates an object store from given path."""
    store = globals().get(global_name)
    if store is None:
        uri = urlparse(path)
        if uri.scheme == "gs":
            gs_client = storage.Client()
            store = GsObjectStore(gs_client.bucket(uri.netloc))
        else:
            store = LocalObjectStore(path)
        globals()[global_name] = store
    return store