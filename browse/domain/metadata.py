"""Representations of arXiv document metadata."""
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from browse.domain.identifier import Identifier
from browse.domain.license import License
from arxiv import taxonomy


@dataclass
class SourceType():
    """Represents arXiv article source file type."""

    code: str = field(default_factory=str)
    """Internal code for the source type."""

    """TODO: need source mappings"""


@dataclass
class Submitter():
    """Represents the person who submitted an arXiv article."""

    name: str = field(default_factory=str)
    """Full name."""

    email: str = field(default_factory=str)
    """Email address."""


@dataclass
class VersionEntry():
    """Represents a single arXiv article version history entry."""

    version: int

    raw: str
    """Raw history entry, e.g. as parsed from .abs file."""

    submitted_date: datetime
    """Date for the entry."""

    size_kilobytes: int = 0
    """Size of the article source, in kilobytes."""

    source_type: SourceType = field(default_factory=SourceType)
    """Source file type."""


@dataclass
class AuthorList():
    """Represents author names."""

    raw: str = field(default_factory=str)
    """Raw author field string."""


@dataclass
class Category():
    """Represents an arXiv category."""

    id: str = field(default_factory=str)
    """The category identifier (e.g. cs.DL)."""
    name: str = field(init=False)
    """The name of the category (e.g. Digital Libraries)."""

    def __post_init__(self):
        """Get the full category name."""
        if self.id in taxonomy.CATEGORIES:
            self.name = taxonomy.CATEGORIES[self.id]['name']


@dataclass
class Archive(Category):
    """Represents an arXiv archive."""

    def __post_init__(self):
        """Get the full archive name."""
        if self.id in taxonomy.ARCHIVES:
            self.name = taxonomy.ARCHIVES[self.id]['name']


@dataclass
class Group(Category):
    """Represents an arXiv group."""

    def __post_init__(self):
        """Get the full group name."""
        if self.id in taxonomy.ARCHIVES:
            self.name = taxonomy.ARCHIVES[self.id]['name']


@dataclass
class DocMetadata():
    """Class for representing the core arXiv document metadata."""

    arxiv_id: str = field(default_factory=str)
    """arXiv paper identifier"""

    arxiv_id_v: str = field(default_factory=str)
    """Identifier and version ex. 1402.12345v2"""

    arxiv_identifier: Identifier = field(default_factory=Identifier)

    title: str = field(default_factory=str)
    abstract: str = field(default_factory=str)

    authors: AuthorList = field(default_factory=AuthorList)
    """Article authors."""

    submitter: Submitter = field(default_factory=Submitter)
    """Submitter of the article."""

    categories: str = field(default_factory=str)
    """Article classification (raw string)."""

    primary_category: Category = field(default_factory=Category)
    """Primary category."""
    primary_archive: Archive = field(init=False)
    primary_group: Group = field(init=False)

    secondary_categories: List[Category] = field(default_factory=list)
    """Secondary categor(y|ies)."""

    journal_ref: Optional[str] = None
    """Report number."""

    report_num: Optional[str] = None
    """Report number."""

    doi: Optional[str] = None
    """Digital Object Identifier (DOI)."""

    acm_class: Optional[str] = None
    """Association for Computing Machinery (ACM) classification(s)."""

    msc_class: Optional[str] = None
    """American Mathematical Society Mathematics Subject (MSC)
       classification(s)."""

    license: License = field(default=None)
    """License associated with the article."""

    proxy: Optional[str] = None
    """Proxy submitter"""

    comments: Optional[str] = None
    """Submitter- and/or administrator-provided comments about the article."""

    version_history: List[VersionEntry] = field(default_factory=list)
    """Version history, consisting of at least one version history entry."""

    version: int = 1
    """Version of this paper."""

    def __post_init__(self) -> None:
        """Post-initialization for license."""
        if not hasattr(self, 'license') or self.license is None:
            self.license = License()
        elif isinstance(self.license, str):
            self.license = License(self.license)
        elif not isinstance(self.license, License):
            raise TypeError(
                "metadata should have str,Licnese or None as self.license "
                + "but it was " + str(type(self.license)))
        self.primary_archive = Archive(
            id=taxonomy.CATEGORIES[self.primary_category.id]['in_archive'])
        self.primary_group = Group(
            id=taxonomy.ARCHIVES[self.primary_archive.id]['in_group'])

    def get_browse_context_list(self) -> List[str]:
        """Get the list of archive/category IDs to generate browse context."""
        # TODO: this really should be based on the "minimal" list of categories
        options = {}
        options[self.primary_category.id] = True
        options[taxonomy.CATEGORIES[self.primary_category.id]['in_archive']] = True
        for category in self.secondary_categories:
            options[category.id] = True
            options[taxonomy.CATEGORIES[category.id]['in_archive']] = True
        return sorted(options.keys())
