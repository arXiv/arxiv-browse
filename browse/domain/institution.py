"""Representations of arXiv member insitution."""
from dataclasses import dataclass, field


@dataclass
class Institution:
    """Represents an arXiv member insitution."""

    """Name of the insitution."""
    name: str = field(default_factory=str)
