from typing import Optional
import abc
from dataclasses import dataclass

from browse.services import HasStatus
from browse.domain.identifier import Identifier

@dataclass
class PrevNextResult:
    """Result for prevnext service."""

    previous_id: Optional[Identifier] = None
    """Direct URL to previous paper.

    If usecontroller is false and this is None, there is no previous paper
    """

    next_id: Optional[Identifier] = None
    """Direct URL to next paper.

    If usecontroller is false and this is None, there is no next paper
    """

    usecontroller: bool = False
    """If True, use the prevnext controller, don't use direct URLs to papers."""


class PrevNextService(abc.ABC, HasStatus):
    """Abstract PrevNext service."""

    @abc.abstractmethod
    def prevnext(self, arxiv_id: Identifier, context: Optional[str]) -> PrevNextResult:
        """Get the previous and next ids for a given id.

        Returning None means the controller"""

