"""Representations of arXiv document metadata."""
import collections
from typing import List, Optional, Iterator, Set
from datetime import datetime
from dataclasses import dataclass, field

from arxiv import taxonomy
from arxiv.base.urls import canonical_url
from browse.domain.identifier import Identifier
from browse.domain.license import License
from browse.domain.category import Category


@dataclass(frozen=True)
class SourceType:
    """Represents arXiv article source file type."""

    code: str
    """Internal code for the source type."""

    __slots__ = ['code']


@dataclass(frozen=True)
class Submitter:
    """Represents the person who submitted an arXiv article."""

    name: str
    """Full name."""

    email: str
    """Email address."""

    __slots__ = ['name', 'email']


@dataclass(frozen=True)
class VersionEntry:
    """Represents a single arXiv article version history entry."""

    version: int

    raw: str
    """Raw history entry, e.g. as parsed from .abs file."""

    submitted_date: datetime
    """Date for the entry."""

    size_kilobytes: int = 0
    """Size of the article source, in kilobytes."""

    source_type: SourceType = field(default_factory=SourceType)  # type: ignore
    """Source file type."""


@dataclass(frozen=True)
class AuthorList:
    """Represents author names."""

    raw: str
    """Raw author field string."""

    __slots__ = ['raw']

    def __str__(self) -> str:
        """Return the string representation of AuthorList."""
        return self.raw


class Archive(taxonomy.Archive):
    """Represents an arXiv archive--the middle level of the taxonomy."""


class Group(taxonomy.Group):
    """Represents an arXiv group--the highest (most general) taxonomy level."""


@dataclass(frozen=True)
class DocMetadata:
    """Class for representing the core arXiv document metadata."""

    raw_safe: str
    """The raw abs string without submitter email address."""

    arxiv_id: str
    """arXiv paper identifier string without version affix, e.g. 1810.12345."""

    arxiv_id_v: str
    """arXiv paper identifier string with version affix, e.g. 1810.12345v2."""

    arxiv_identifier: Identifier
    """arXiv Identifier for this paper. Does not include version data."""

    title: str
    abstract: str

    modified: datetime
    """Datetime this version was modified."""

    authors: AuthorList
    """Article authors."""

    submitter: Submitter
    """Submitter of the article."""

    categories: Optional[str]
    """Article classification (raw string)."""

    primary_category: Optional[Category]
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
    """Version of this article."""

    license: License = field(default_factory=License)
    """License associated with the article."""

    version_history: List[VersionEntry] = field(default_factory=list)
    """Version history, consisting of at least one version history entry."""

    is_definitive: bool = field(default=False)
    """
       Indicates whether this is the definitive DocMetadata for this article;
       i.e. it includes metadata from the latest version of the article that is
       needed for the abs page display.
    """

    is_latest: bool = field(default=False)
    """
        Indicates whether this DocMetadata is from the latest
        version of this article.
    """

    private: bool = field(default=False)
    """TODO: NOT IMPLEMENTED """
    """Description from arxiv classic: Flag set by init_from_file to
    indicate that the abstract file exists authentication for
    pre-publication access to papers should check for an undef return
    from init_from_file and then check private to see if an
    authentication redirect is required.

    """

    def __post_init__(self) -> None:
        """Post-initialization checks if is_definitive is True."""
        if self.is_definitive:
            if self.categories is None:
                raise ValueError('categories must be defined')
            if self.primary_category is None:
                raise ValueError('primary category must be defined')

    def get_browse_context_list(self) -> List[str]:
        """Get the list of archive/category IDs to generate browse context."""
        if self.arxiv_identifier.is_old_id:
            if self.arxiv_identifier.archive is not None:
                return [self.arxiv_identifier.archive]
            else:
                return []

        if self.primary_category:
            options = {
                self.primary_category.id: True,
                taxonomy.CATEGORIES[self.primary_category.id]['in_archive']: True
            }
        for category in self.secondary_categories:
            options[category.id] = True
            in_archive = taxonomy.CATEGORIES[category.id]['in_archive']
            options[in_archive] = True
        return sorted(options.keys())

    def highest_version(self) -> int:
        """Return highest version number from metadata.

        This is determined by counting the entries in the {history}.
        Return 1 if the metadata is private. Returns undef if this
        object is not initialized.
        """
        if self.private:
            return 1
        if not isinstance(self.version_history, collections.Iterable):
            raise ValueError(
                'version_history was not an Iterable for %s' % self.arxiv_id_v)
        return max(map(lambda ve: ve.version, self.version_history))

    def get_datetime_of_version(
            self, version: Optional[int]) -> Optional[datetime]:
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

    def get_secondaries(self) -> Set[Category]:
        """Unalias and deduplicate secondary categories."""
        if not self.secondary_categories or not self.primary_category:
            return set()

        def unalias(secs: Iterator[Category])->Iterator[Category]:
            return map(lambda c: Category(c.unalias()), secs)
        prim = self.primary_category.unalias()

        def de_prim(secs: Iterator[Category])->Iterator[Category]:
            return filter(lambda c: c.id != prim.id, secs)

        de_primaried = set(de_prim(unalias(iter(self.secondary_categories))))
        if not de_primaried:
            return set()
        return de_primaried

    def display_secondaries(self) -> List[str]:
        """Unalias, dedup and sort secondaries for display."""
        de_primaried = self.get_secondaries()

        def to_display(secs: List[Category]) -> List[str]:
            return list(map(lambda c: str(c.display), secs))
        return to_display(sorted(de_primaried))

    def canonical_url(self, no_version: bool = False) -> str:
        """Return canonical URL for this ID and version."""
        url: str
        if no_version:
            url = canonical_url(self.arxiv_identifier.id)
        else:
            url = canonical_url(self.arxiv_identifier.idv)
        return url
