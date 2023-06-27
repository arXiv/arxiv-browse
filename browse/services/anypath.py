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

    Cloudpath lib makes no attempt to be thread safe.

    This function attempts to use a seperate cloudpathlib client for each Flask
    thread.
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

    tlgsc = GSClient(storage_client=_gs_client())
    _tlocal_gscloudpath.set(tlgsc)
    return tlgsc
