"""Representations of arXiv member insitution."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Institution:
    """Represents an arXiv member insitution."""

    name: Optional[str] = None
    """Name of the insitution."""

    __slots__ = ['frozen']
