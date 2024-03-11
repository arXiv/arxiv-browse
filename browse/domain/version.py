"""Representations of a version of a document."""
from typing import Literal, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

SOURCE_FORMAT = Literal["tex", "ps", "html", "pdf", "withdrawn", "pdftex", "docx"]
"""All values used in DB for the source_format column.

Excluding NULL."""


@dataclass
class SourceFlag:
    """Represents arXiv article source file type."""

    code: str
    """Internal code for the source type."""

    __slots__ = ['code']

    @property
    def ignore(self) -> bool:
        """Withdarawn. All files auto ignore. No paper available."""
        return self.code is not None and 'I' in self.code

    @property
    def source_encrypted(self)->bool:
        """
        Source is encrypted and should not be made available.
        """
        return self.code is not None and 'S' in self.code

    @property
    def ps_only(self)->bool:
        """
        Multi-file PS submission. It is not necessary to indicate P with single file PS
        since in this case the source file has .ps.gz extension.
        """
        return self.code is not None and 'P' in self.code

    @property
    def pdflatex(self)->bool:
        """
        A TeX submission that must be processed with PDFlatex
        """
        return self.code is not None and 'D' in self.code

    @property
    def html(self)->bool:
        """
        Multi-file HTML submission.
        """
        return self.code is not None and 'H' in self.code

    @property
    def includes_ancillary_files(self)->bool:
        """
        Submission includes ancillary files in the /anc directory
        """
        return self.code is not None and 'A' in self.code

    @property
    def dc_pilot_data(self)->bool:
        """
        Submission has associated data in the DC pilot system
        """
        return self.code is not None and 'B' in self.code

    @property
    def docx(self)->bool:
        """
        Submission in Microsoft DOCX (Office Open XML) format
        """
        return self.code is not None and 'X' in self.code

    @property
    def odf(self)->bool:
        """
        Submission in Open Document Format
        """
        return self.code is not None and 'O' in self.code

    @property
    def pdf_only(self)->bool:
        """
        PDF only submission with .tar.gz package. (likely because of anc files)
        """
        return self.code is not None and 'F' in self.code

    @property
    def cannot_pdf(self) -> bool:
        """
        Is this version unable to produce a PDF?
        Does not take into account withdarawn.
        """
        return self.code is not None and self.html or self.odf or self.docx

    @property
    def is_single_file(self) -> bool:
        """
        Is the source for this version a single file?
        """
        return self.code is not None and '1' in self.code


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

    source_flag: SourceFlag = field(default_factory=SourceFlag)  # type: ignore
    """Source file type."""

    is_withdrawn: bool = False
    """Is the version withdrawn."""

    source_format: Optional[SOURCE_FORMAT] = None
    """Source format."""

    is_current: bool = False
    """Is the version the highest existing version?"""

    @property
    def withdrawn_or_ignore(self) -> bool:
        return self.source_flag.ignore or self.is_withdrawn

    def formats(self) -> List[str]:
        if self.is_withdrawn or self.size_kilobytes == 0:
            return []

        if self.source_flag.ignore:
            if not self.source_flag.source_encrypted:
                return ['src']
            else:
                return []

        formats = []
        if self.source_flag.ps_only or self.source_format == "ps":
            formats.extend(['pdf', 'ps'])
        elif self.source_flag.pdflatex or self.source_format == "pdflatex":
            formats.extend(['pdf', 'src'])
        elif self.source_flag.pdf_only or self.source_format == "pdfonly":
            formats.extend(['pdf'])
        elif self.source_flag.html or self.source_format == "html":
            formats.extend(['html'])
        elif self.source_flag.docx or self.source_format == "docx":
            formats.extend(['pdf'])
        else:
            formats.extend(['pdf', 'ps', 'src'])

        # other is added for display purposes maybe move to controller or template?
        formats.extend(['other'])
        return formats
