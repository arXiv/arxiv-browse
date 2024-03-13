"""Document cache service."""
import os
import re
from functools import wraps
from typing import Optional

from browse.services.anypath import to_anypath

from arxiv.base.globals import get_application_config, get_application_global

from arxiv.document.metadata import DocMetadata
from browse.services.anypath import APath

from flask import Flask

# Formats that currently reside in the cache filesystem
CACHE_FORMATS = ['dvi', 'html', 'other', 'pdf', 'ps']


class DocumentCacheException(Exception):
    """Error class for general arXiv document cache exceptions."""


class DocumentCacheFormatException(Exception):
    """Error class for invalid document catch format exceptions."""


class DocumentCacheSession():
    """Document cache session class."""

    def __init__(self, document_cache_path: str) -> None:
        """Initialize the document cache session."""
        self.document_cache_path:APath = to_anypath(document_cache_path).resolve()

        if not self.document_cache_path.is_dir():
            raise DocumentCacheException(f'Path to document cache {document_cache_path} does '\
                                         'not exist or is not a directory')


    def get_cache_file_path(self, docmeta: DocMetadata, cache_format: str)\
            -> Optional[APath]:
        """Get the absolute path of the cache file/directory if it exists."""
        if cache_format not in CACHE_FORMATS:
            raise DocumentCacheFormatException('Invalid cache file format: '
                                               f'{cache_format}')
        identifier = docmeta.arxiv_identifier
        # parent_path = to_anypath('/'.join([
        #     self.document_cache_path,
        #     ('arxiv' if not identifier.is_old_id or identifier.archive is None
        #      else identifier.archive),
        #     cache_format,
        #     identifier.yymm,
        #     f'{identifier.filename}v{docmeta.version}']))

        parent_path: APath = (self.document_cache_path /
            ('arxiv' if not identifier.is_old_id or identifier.archive is None
             else identifier.archive) /
            cache_format /
            identifier.yymm /
            f'{identifier.filename}v{docmeta.version}' )

        if cache_format == 'html' and parent_path.is_dir():
            return parent_path  # HTML is directory-based

        extension = f'.{cache_format}'
        if re.match(r'^other', cache_format):
            extension = '.ps.gz'
            return None  # TODO is this correct? extension is unused?
        elif type == 'ps':
            extension = f'{extension}.gz'
            cache_file_path = to_anypath(f'{str(parent_path)}{extension}')
            if cache_file_path.is_file():
                return cache_file_path
        else:
            return None
        return None


@wraps(DocumentCacheSession.get_cache_file_path)
def get_cache_file_path(docmeta: DocMetadata, format: str) -> Optional[APath]:
    """Get the absolute path of the cache file/directory if it exists."""
    return current_session().get_cache_file_path(docmeta, format)


def get_session(app: Optional[Flask] = None) -> DocumentCacheSession:
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
        setattr(g, 'doc_cache', get_session())
    assert hasattr(g, 'doc_cache')
    assert isinstance(g.doc_cache, DocumentCacheSession)
    return g.doc_cache
