"""Formats of byte streams that can be requested from Items."""


from dataclasses import dataclass, field
from typing import List, Literal, Optional


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

    def __hash__(self)->int:
        return hash(self.name)

src_orig = Format("e-print")
"""Source in its original format. May be .tar.gz, .pdf .ps.gs .gz .div.gz or .html.gz"""

src_targz = Format("targz", ".tar.gz", "application/gzip")
"""Source of an item in tarred and gzipped.

This is all of the original source tarred and gzipped."""

pdf = Format("pdf", ".pdf", "application/pdf")
"""Item as a PDF. Either compiled if LaTeX or original PDF if a PDF submission"""

ps = Format("ps", ".ps.gz", "application/postscript", "gzip")
"""Item as a PS if possible."""

htmlgz = Format("htmlgz", ".html.gz", "text/html", "gzip")
"""HTML GZ bundle for an item."""
