"""Representations of arXiv document metadata."""
from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class License():
    """Represents an arXiv article license."""

    """Name of the license."""
    name: str = field(default_factory=str)
    """URI of the license."""
    uri: str = field(default_factory=str)


@dataclass
class SourceType():
    """Represents arXiv article source file type."""

    """Internal code for the source type."""
    code: str = field(default_factory=str)

    """TODO: need source mappings"""


@dataclass
class Submitter:
    """Represents the person who submitted an arXiv article."""

    """Full name."""
    name: str = field(default_factory=str)

    """Email address."""
    email: str = field(default_factory=str)


@dataclass
class VersionEntry():
    """Represents a single arXiv article version history entry."""

    """Raw history entry, e.g. as parsed from .abs file."""
    raw: str = field(default_factory=str)

    """Date for the entry."""
    date: datetime = field(default_factory=datetime)

    """Submitter associated with this entry."""
    submitter: Submitter = field(default_factory=Submitter)

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

    """arXiv paper identifier.z"""
    """TODO: strict typing"""
    paper_id: str = field(default_factory=str)

    """Title of the article."""
    title: str = field(default_factory=str)

    """Summary of the article."""
    abstract: str = field(default_factory=str)

    """Article authors."""
    authors: AuthorList = field(default_factory=AuthorList)

    """Submitter of the article."""
    submitter: Submitter = field(default_factory=Submitter)

    """Article classification."""
    article_classification: str = field(default_factory=str)

    """Journal reference."""
    journal_ref: str = field(default_factory=str)

    """Report number."""
    report_num: str = field(default_factory=str)

    """Digital Object Identifier (DOI)."""
    doi: str = field(default_factory=str)

    """Association for Computing Machinery (ACM) classification(s)."""
    acm_class: str = field(default_factory=str)

    """American Mathematical Society Mathematics Subject (MSC)
       classification(s)."""
    msc_class: str = field(default_factory=str)

    """License associated with the article."""
    license: License = field(default_factory=License)

    """Submitter- and/or administrator-provided comments about the article."""
    comments: str = field(default_factory=str)

    """Version history, consisting of at least one version history entry."""
    version_history: List[VersionEntry] = field(default_factory=list)
