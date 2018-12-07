"""Class that represents a single category."""

from typing import Union, List
from dataclasses import dataclass, field

from arxiv import taxonomy


class Category(taxonomy.Category):
    """Represents an arXiv category."""
