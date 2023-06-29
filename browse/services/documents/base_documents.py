"""Base classes for the abstracts service."""

import abc
from typing import Dict, List, Optional

from browse.domain.metadata import DocMetadata
from browse.services import HasStatus

class DocMetadataService(abc.ABC, HasStatus):
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
