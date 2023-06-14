"""arxiv browse services."""
from typing import Protocol, List

from cloudpathlib import CloudPath
from pathlib import Path
from typing import Union

APath = Union[Path, CloudPath]
"""Type to use with anypath.to_anypath"""




class HasStatus(Protocol):
    def service_status(self)->List[str]:
        """Check for problems, return emtpy list if there are none"""
        pass




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
