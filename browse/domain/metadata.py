"""Representations of arXiv document metadata."""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class License():
    """Represents an arXiv article license."""

    """Name of the license."""
    name: Optional[str] = None
    """URI of the license."""
    uri: Optional[str] = None


@dataclass
class SourceType():
    """Represents arXiv article source file type."""

    """Internal code for the source type."""
    code: str = field(default_factory=str)

    """TODO: need source mappings"""


@dataclass
class Submitter():
    """Represents the person who submitted an arXiv article."""

    """Full name."""
    name: str = field(default_factory=str)

    """Email address."""
    email: str = field(default_factory=str)


@dataclass
class VersionEntry():
    """Represents a single arXiv article version history entry."""

    version: int

    """Raw history entry, e.g. as parsed from .abs file."""
    raw: str

    """Date for the entry."""
    submitted_date: datetime

    """Size of the article source, in kilobytes."""
    size_kilobytes: int = 0

    """Source file type."""
    source_type: SourceType = field(default_factory=SourceType)


@dataclass
class AuthorList():
    """Represents author names."""

    """Raw author field string."""
    raw: str = field(default_factory=str)


@dataclass
class DocMetadata():
    """Class for representing the core arXiv document metadata."""

    """arXiv paper identifier"""
    """TODO: stricter typing?"""
    arxiv_id: str = field(default_factory=str)
    arxiv_id_v: str = field(default_factory=str)

    title: str = field(default_factory=str)
    abstract: str = field(default_factory=str)

    """Article authors."""
    authors: AuthorList = field(default_factory=AuthorList)

    """Submitter of the article."""
    submitter: Submitter = field(default_factory=Submitter)

    """Article classification (raw string)."""
    categories: str = field(default_factory=str)
    """Primary category."""
    primary_category: str = field(default_factory=str)
    """Secondary categor(y|ies)."""
    secondary_categories: List[str] = None

    """Journal reference."""
    journal_ref: Optional[str] = None

    """Report number."""
    report_num: Optional[str] = None

    """Digital Object Identifier (DOI)."""
    doi: Optional[str] = None

    """Association for Computing Machinery (ACM) classification(s)."""
    acm_class: Optional[str] = None

    """American Mathematical Society Mathematics Subject (MSC)
       classification(s)."""
    msc_class: Optional[str] = None

    """License associated with the article."""
    # license: License = field(default_factory=License)
    license: Optional[str] = None

    """Proxy."""
    proxy: Optional[str] = None

    """Submitter- and/or administrator-provided comments about the article."""
    comments: Optional[str] = None

    """Version history, consisting of at least one version history entry."""
    version_history: List[VersionEntry] = field(default_factory=list)

    """Version of this paper."""
    version: int = 1
