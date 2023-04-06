"""Representations of a version of a document."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class SourceType:
    """Represents arXiv article source file type."""

    code: str
    """Internal code for the source type."""

    __slots__ = ['code']

    @property
    def ignore(self) -> bool:
        """Withdarawn. All files auto ignore. No paper available."""
        return 'I' in self.code

    @property
    def source_encrypted(self)->bool:
        """
        Source is encrypted and should not be made available.
        """
        return 'S' in self.code

    @property
    def ps_only(self)->bool:
        """
        Multi-file PS submission. It is not necessary to indicate P with single file PS
        since in this case the source file has .ps.gz extension.
        """
        return 'P' in self.code

    @property
    def pdflatex(self)->bool:
        """
        A TeX submission that must be processed with PDFlatex
        """
        return 'D' in self.code

    @property
    def html(self)->bool:
        """
        Multi-file HTML submission.
        """
        return 'H' in self.code

    @property
    def includes_ancillary_files(self)->bool:
        """
        Submission includes ancillary files in the /anc directory
        """
        return 'A' in self.code

    @property
    def dc_pilot_data(self)->bool:
        """
        Submission has associated data in the DC pilot system
        """
        return 'B' in self.code

    @property
    def docx(self)->bool:
        """
        Submission in Microsoft DOCX (Office Open XML) format
        """
        return 'X' in self.code

    @property
    def odf(self)->bool:
        """
        Submission in Open Document Format
        """
        return 'O' in self.code

    @property
    def PDF_only(self)->bool:
        """
        PDF only submission with .tar.gz package. (likely because of anc files)
        """
        return 'F' in self.code

    @property
    def cannot_pdf(self) -> bool:
        """
        Is this version unable to produce a PDF?
        Does not take into account withdarawn.
        """
        return self.html or self.odf or self.docx


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

    @property
    def is_withdrawn(self) -> bool:
        return self.source_type.ignore
