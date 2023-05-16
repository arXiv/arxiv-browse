"""arxiv browse services."""
from typing import Protocol, List

from cloudpathlib import CloudPath
from pathlib import Path
from typing import Union

from browse.services.object_store import FileObj

APath = Union[Path, CloudPath]
"""Type to use with cloudpathlib.anypath.to_anypath"""




class HasStatus(Protocol):
    def service_status(self)->List[str]:
        """Check for problems, return emtpy list if there are none"""
        pass


def fs_check(path:Union[APath, FileObj]) -> List[str]:
    """Checks for a file system for use in `HasStatus.service_status()`"""
    try:
        path.exists()
    except Exception as ex:
        return [f"Could not access due to {ex}"]

    return []
