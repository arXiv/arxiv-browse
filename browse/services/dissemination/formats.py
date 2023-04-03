"""Formats of byte streams that can be requested from Items."""


from dataclasses import dataclass, field
from typing import List, Literal, Optional

Checks = Literal[
    "NOT_ON_REASONS",  # check that the itmes in not on the REASONS list
    "AVAILABLE_AS_PDF", # a check that the item can possibly be in the PDF format
    "AVAILABLE_AS_PS",  # a check that the item can possibly be in the PS format
    "AVAILABLE_AS_HTML", # a check that the item can possibly be in the HTML format
]


@dataclass
class Format:
    name: str
    """Id for format"""

    file_extension: Optional[str] = None
    """Expected file extension for this format"""

    mime_type: Optional[str] = None
    """Mime type of this format."""

    content_encoding: Optional[str] = None
    """HTTP content encoding of this format. ex gzip"""

    extra_checks: List[Checks] = field(default_factory=list)
    """Checks to run after the normal checks like "does this item exist" and
    before returning."""


src_orig = Format("e-print")
"""Source in its original format. May be .tar.gz, .pdf .ps.gs .gz .div.gz or .html.gz"""

src_targz = Format("targz", ".tar.gz", "application/gzip")
"""Source of an item in tarred and gzipped.

This is all of the original source tarred and gzipped."""

pdf = Format("pdf", ".pdf", "application/pdf", ["NOT_ON_REASONS","AVAILABLE_AS_PDF"])
"""Item as a PDF. Either compiled if LaTeX or original PDF if a PDF submission"""

ps = Format("ps", ".ps.gz", "application/postscript", "gzip",
            ["NOT_ON_REASONS", "AVAILABLE_AS_PS"])
"""Item as a PS if possible."""

htmlgz = Format("htmlgz", ".html.gz", "text/html", "gzip",
                ["AVAILABLE_AS_HTML"])
"""HTML GZ bundle for an item."""
