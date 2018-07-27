"""Representations of arXiv document metadata."""
import collections
from typing import List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field

from arxiv import taxonomy
from browse.domain.identifier import Identifier
from browse.domain.license import License


@dataclass
class SourceType:
    """Represents arXiv article source file type."""

    code: str = field(default_factory=str)
    """Internal code for the source type."""


@dataclass
class Submitter:
    """Represents the person who submitted an arXiv article."""

    name: str = field(default_factory=str)
    """Full name."""

    email: str = field(default_factory=str)
    """Email address."""


@dataclass
class VersionEntry:
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


@dataclass(frozen=True)
class AuthorList:
    """Represents author names."""

    raw: str = field(default_factory=str)
    """Raw author field string."""

    def __str__(self) -> str:
        return self.raw


@dataclass
class Category:
    """Represents an arXiv category.

    arXiv categories are arranged in a hierarchy where there are archives
    (asrto-ph, cs, math, etc.) that contain subject classes (astro-ph has
    subject classes CO, GA, etc.). We now use the term category to refer
    to any archive or archive.subject_class that one can submit to (so
    hep-th and math.IT are both categories). No subject class can be in
    more than one archive. However, our scientific advisors identify some
    categories that should appear in more than one archive because they
    bridge major subject areas. Examples include math.MP == math-ph and
    stat.TH = math.ST. These are called category aliases and the idea is
    that any article classified in one of the aliases categories also appears
    in the other, but that most of the arXiv code for display, search, etc.
    does not need to understand the break with hierarchy.
    """

    id: str
    """The category identifier (e.g. cs.DL)."""

    name: str = field(init=False)
    """The name of the category (e.g. Digital Libraries)."""

    canonical: Union['Category', None] = field(init=False)

    def __post_init__(self) -> None:
        """Get the full category name."""
        if self.id in taxonomy.CATEGORIES:
            self.name = taxonomy.CATEGORIES[self.id]['name']

        if self.id in taxonomy.ARCHIVES_SUBSUMED:
            self.canonical = Category(id=taxonomy.ARCHIVES_SUBSUMED[self.id])  # type: ignore
        else:
            self.canonical = None


@dataclass
class Archive(Category):
    """Represents an arXiv archive."""

    def __post_init__(self) -> None:
        """Get the full archive name."""
        if self.id in taxonomy.ARCHIVES:
            self.name = taxonomy.ARCHIVES[self.id]['name']


@dataclass
class Group(Category):
    """Represents an arXiv group."""

    def __post_init__(self) -> None:
        """Get the full group name."""
        if self.id in taxonomy.ARCHIVES:
            self.name = taxonomy.ARCHIVES[self.id]['name']


@dataclass
class DocMetadata:
    """Class for representing the core arXiv document metadata."""

    arxiv_id: str
    """arXiv paper identifier"""

    arxiv_id_v: str
    """Identifier and version ex. 1402.12345v2"""

    arxiv_identifier: Identifier

    title: str
    abstract: str

    authors: AuthorList
    """Article authors."""

    submitter: Submitter
    """Submitter of the article."""

    categories: str
    """Article classification (raw string)."""

    primary_category: Category
    """Primary category."""

    primary_archive: Archive
    primary_group: Group

    secondary_categories: List[Category]
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

    proxy: Optional[str] = None
    """Proxy submitter."""

    comments: Optional[str] = None
    """Submitter- and/or administrator-provided comments about the article."""

    version: int = 1
    """Version of this paper."""

    license: License = field(default_factory=License)
    """License associated with the article."""

    version_history: List[VersionEntry] = field(default_factory=list)
    """Version history, consisting of at least one version history entry."""

    private: bool = field(default=False)
    """TODO: NOT IMPLEMENTED """
    """Description from arxiv classic: Flag set by init_from_file to
    indicate that the abstract file exists authentication for
    pre-publication access to papers should check for an undef return
    from init_from_file and then check private to see if an
    authentication redirect is required.

    """

    def get_browse_context_list(self) -> List[str]:
        """Get the list of archive/category IDs to generate browse context."""
        if self.arxiv_identifier.is_old_id:
            if self.arxiv_identifier.archive is not None:
                return [self.arxiv_identifier.archive]
            else:
                return []

        options = {
            self.primary_category.id : True,
            taxonomy.CATEGORIES[self.primary_category.id]['in_archive'] : True
        }
        for category in self.secondary_categories:
            options[category.id] = True
            in_archive = taxonomy.CATEGORIES[category.id]['in_archive']
            options[in_archive] = True
        return sorted(options.keys())

    def highest_version(self)-> int:
        """Return highest version number from metadata.

        This is determined by counting the entries in the
        {history}. Return 1 if the metadata is private. Returns undef
        if this object is not initialized.
        """
        if self.private:
            return 1
        if not isinstance(self.version_history, collections.Iterable):
            raise ValueError(
                'version_history was not an Iterable for %s' % self.arxiv_id_v)
        return max(map(lambda ve: ve.version, self.version_history))

    def get_datetime_of_version(
            self, version: Optional[int])->Optional[datetime]:
        """Returns python datetime of version.

        version: Version to get datetime of. Must be in range
            1..highest_version. Uses highest_version if not specified.

        """
        if not version:
            version = self.highest_version()

        versions = list(
            v for v in self.version_history if v.version == version)
        if len(versions) > 1:
            raise ValueError(
                '%s version_history had more than one version %i' % (
                    self.arxiv_id, version))
        if not versions:
            return None
        else:
            return versions[0].submitted_date
