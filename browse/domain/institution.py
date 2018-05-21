"""Representations of arXiv member insitution."""
from typing import Optional
from dataclasses import dataclass


@dataclass
class Institution:
    """Represents an arXiv member insitution."""

    name: Optional[str] = None
    """Name of the insitution."""
