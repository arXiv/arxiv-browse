"""Document cache service."""
import os
import re
from functools import wraps
from typing import Optional

from arxiv.base.globals import get_application_config, get_application_global
from browse.domain.metadata import DocMetadata


# Formats that currently reside in the cache filesystem
CACHE_FORMATS = ['dvi', 'html', 'other', 'pdf', 'ps']


class DocumentCacheException(Exception):
    """Error class for general arXiv document cache exceptions."""

    pass


class DocumentCacheFormatException(Exception):
    """Error class for invalid document catch format exceptions."""

    pass


class DocumentCacheSession():
    """Document cache session class."""

    def __init__(self, document_cache_path: str) -> None:
        """Initialize the document cache session."""
        if not os.path.isdir(document_cache_path):
            raise DocumentCacheException('Path to document cache '
                                         f'{document_cache_path} does '
                                         'not exist')
        self.document_cache_path = os.path.realpath(document_cache_path)

    def get_cache_file_path(self, docmeta: DocMetadata,
                            cache_format: str) -> Optional[str]:
        """Get the absolute path of the cache file/directory if it exists."""
        if cache_format not in CACHE_FORMATS:
            raise DocumentCacheFormatException('Invalid cache file format: '
                                               f'{cache_format}')
        identifier = docmeta.arxiv_identifier
        parent_path = os.path.join(
            self.document_cache_path,
            ('arxiv' if not identifier.is_old_id else identifier.archive),
            cache_format,
            identifier.yymm,
            f'{identifier.filename}v{docmeta.version}'
        )
        if cache_format == 'html' and os.path.isdir(parent_path):
            # HTML is directory-based
            return parent_path

        extension = f'.{cache_format}'
        if re.match(r'^other', cache_format):
            # TODO is this correct? extension is unused?
            extension = '.ps.gz'
        elif type == 'ps':
            extension = f'{extension}.gz'
            cache_file_path = f'{parent_path}{extension}'
            if os.path.isfile(cache_file_path):
                return cache_file_path
        else:
            return None


@wraps(DocumentCacheSession.get_cache_file_path)
def get_cache_file_path(docmeta: DocMetadata, format: str) -> Optional[str]:
    """Get the absolute path of the cache file/directory if it exists."""
    return current_session().get_cache_file_path(docmeta, format)


def get_session(app: object = None) -> DocumentCacheSession:
    """Get a new session with the document cache service."""
    config = get_application_config(app)
    document_cache_path = config.get('DOCUMENT_CACHE_PATH', None)

    return DocumentCacheSession(document_cache_path)


def current_session() -> DocumentCacheSession:
    """Get/create :class:`.DocumentCacheSession` for this context."""
    g = get_application_global()
    if not g:
        return get_session()
    if 'doc_cache' not in g:
        g.doc_cache = get_session()
    return g.doc_cache     # type: ignore
