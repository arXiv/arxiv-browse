"""arxiv browse services."""
from typing import Protocol, List


class HasStatus(Protocol):
    def service_status(self)->List[str]:
        """Check for problems, return emtpy list if there are none"""
        pass
