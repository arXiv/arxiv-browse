"""Representations of arXiv document metadata."""
import collections

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from browse.domain.identifier import Identifier
from browse.domain.license import License


@dataclass
class SourceType:
    """Represents arXiv article source file type."""

    code: str = field(default_factory=str)
    """Internal code for the source type."""

    """TODO: need source mappings"""


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


@dataclass
class AuthorList:
    """Represents author names."""

    raw: str = field(default_factory=str)
    """Raw author field string."""


@dataclass
class DocMetadata:
    """Class for representing the core arXiv document metadata."""

    """TODO: stricter typing?"""

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

    primary_category: str = field(default_factory=str)
    """Primary category."""

    secondary_categories: List[str] = field(default_factory=list)
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

    private: bool = field(default=False)
    """TODO: NOT IMPLEMENTED """
    """ Description from arxiv classic: 
    Flag set by init_from_file to indicate that the abstract file exists
    authentication for pre-publication access to papers should check for an undef
    return from init_from_file and then check private to see if an authentication
    redirect is required."""

    def __post_init__(self) -> None:

        if not hasattr(self, 'license') or self.license is None:
            self.license = License()
        elif isinstance(self.license, str):
            self.license = License(self.license)
        elif not isinstance(self.license, License):
            raise TypeError(
                "metadata should have str,Licnese or None as self.license "
                + "but it was " + str(type(self.license)))

    def highest_version(self)-> int:
        """ Return highest version number from metadata.

        This is determined by counting the entries in the {history}. Return 1 if
        the metadata is private. Returns undef if this object is not initialized."""
        if self.private:
            return 1
        if not isinstance(self.version_history, collections.Iterable):
            raise ValueError('version_history was not an Iterable for %s' % self.arxiv_id_v)
        return max(map(lambda ve: ve.version, self.version_history))


    def get_datetime_of_version(self, version: Optional[int])->Optional[datetime]:
        """ Returns python datetime of version.

        version:
            Version to get datetime of. Must be in range 1..highest_version. Uses highest_version if not specified.
        """
        if not version:
            version = self.highest_version()

        versions = (v for v in self.version_history if v.version == version)
        if len(versions) > 1:
            raise ValueError('%s version_history had more than one version %i' % (self.arxiv_id, version))
        if len(versions) == 0:
            return None
        else:
            return versions[0].version.submitted_date

