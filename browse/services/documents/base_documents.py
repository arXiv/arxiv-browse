"""Base classes for the abstracts service."""

import abc
from typing import Dict, List, Optional

from browse.domain.metadata import DocMetadata

class DocMetadataService(abc.ABC):
    """Class for arXiv document abstract metadata service."""

    @abc.abstractmethod
    def get_abs(self, arxiv_id: str) -> DocMetadata:
        """Get the .abs metadata for the specified arXiv paper identifier.

        Parameters
        ----------
        arxiv_id : str
            The arXiv identifier string.

        Returns
        -------
        :class:`DocMetadata`
        """

    @abc.abstractmethod
    def get_dissemination_formats(self,
                                  docmeta: DocMetadata,
                                  format_pref: Optional[str] = None,
                                  add_sciencewise: bool = False,
                                  quick: bool = False) -> List[str]:
        """Get a list of formats that can be disseminated for this DocMetadata.

        Several checks are performed to determine available dissemination
        formats:
            1. a check for source files with specific, valid file name
               extensions (i.e. for a subset of the allowed source file name
               extensions, the dissemintation formats are predictable)
            2. if formats cannot be inferred from the source file, inspect the
               source type in the document metadata.

        Format names are strings. These include 'src', 'pdf', 'ps', 'html',
        'pdfonly', 'other', 'dvi', 'ps(400)', 'ps(600)', 'nops'.

        Parameters
        ----------
        docmeta : :class:`DocMetadata`
        format_pref : str
            The format preference string.
        add_sciencewise : bool
            Specify whether to include 'sciencewise_pdf' format in list.
        quick: bool
            If True just check the download formats via the source types in the `DocMetadata`

        Returns
        -------
        List[str]
            A list of format strings.
        """

    @abc.abstractmethod
    def get_ancillary_files(self, docmeta: DocMetadata) \
            -> List[Dict]:
        """Get list of ancillary file names and sizes."""


class AbsException(Exception):
    """Error class for general arXiv .abs exceptions."""


class AbsNotFoundException(FileNotFoundError):
    """Error class for arXiv .abs file not found exceptions."""


class AbsVersionNotFoundException(FileNotFoundError):
    """Error class for arXiv .abs file version not found exceptions."""


class AbsParsingException(OSError):
    """Error class for arXiv .abs file parsing exceptions."""


class AbsDeletedException(Exception):
    """Error class for arXiv papers that have been deleted."""
