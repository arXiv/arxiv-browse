"""function to open eihter local files or storage bucket files"""
from pathlib import Path
from typing import Union, List
from contextvars import ContextVar

from cloudpathlib import CloudPath
from cloudpathlib.gs import GSClient

from google.cloud.storage import Client as StorageClient

APath = Union[Path, CloudPath]
"""Type to use with anypath.to_anypath"""


def to_anypath(item: Union[str, Path]) -> APath:
    """A thread safe `to_anypath()`

    This function uses a separate cloudpathlib client for each thread. And
    also sets cloudpathlib's caching to remove the cached file right after the
    `open()` is closed.

    Rational:

    GCP CloudRun uses a RAM FS so everything written to disk ends up using
    memory.

    cloudpathlib is not thread safe if a single `Client` is used across multiple
    threads. As of 2023-06 when it writes and deletes from its cache there is no
    code to check for race conditions. Ex `Client.clear_cache()`.

    Flask apps run multi threaded.

    So we have two problems:

    1. a shared cloudpathlib obj is not thread safe and we must use threads
    2. we'll fill up memory with cloudpathlib's default caching
    """
    if isinstance(item, CloudPath) or isinstance(item, Path):
        return item
    if not item:
        raise ValueError("cannot make a path from empty")
    if item.startswith("gs:"):
        tlgsc: GSClient = _gscloudpath_client()
        return tlgsc.CloudPath(item)  # type: ignore
    if item.startswith("s3://") or item.startswith("az:"):
        raise ValueError("s3 and az are not supported")
    else:
        return Path(item)


def fs_check(path:APath, expect_dir:bool=True) -> List[str]:
    """Checks for a file system for use in `HasStatus.service_status()`"""
    try:
        if expect_dir:
            if not path.is_dir():
                return [f"{path} does not appear to be a directory"]
        else:
            if not path.is_file():
                return [f"{path} does not appear to be a file"]
    except Exception as ex:
        return [f"Could not access due to {ex}"]

    return []


_global_gs_client: StorageClient = None


def _gs_client() -> StorageClient:
    """Gets a Google storage client.

    These appear to be thread safe so we can share this. The start up of the
    a GS Client takes a bit of time (~ 1.5 sec?).
    """
    global _global_gs_client
    if not _global_gs_client:
        _global_gs_client = StorageClient()

    return _global_gs_client


_tlocal_gscloudpath: ContextVar[GSClient] = ContextVar('_cloutpath_client')
"""Thead local GSCloudPathClient."""


def _gscloudpath_client() -> GSClient:
    """Gets a per thread `CloudPathClient`

    Uses a [`ContextVar`](https://docs.python.org/3/library/contextvars.html#contextvars.ContextVar)
    to store a pre thread CloudPathClient.

    Why not use werkzeug's `ProxyObject`? The docs describe `ProxyObject` as a
    "wrapper around `ContextVar` to make it easier to work with". Since we are
    not using it for anything complex it seems we don't need the additional ease
    `ProxyObject` provides.
    """
    thread_local_client = _tlocal_gscloudpath.get(None)
    if thread_local_client:
        return thread_local_client

    # Each GSClient will use a thread safe `tempdir.TemporaryDirectory`
    # close_file casues the cache to be cleared on file close
    tlgsc = GSClient(storage_client=_gs_client(),
                     file_cache_mode="close_file")
    _tlocal_gscloudpath.set(tlgsc)
    return tlgsc
