"""Parse fields from a single arXiv abstract (.abs) file."""
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from functools import wraps
from dateutil import parser
from pytz import timezone
from datetime import datetime
from dateutil.tz import tzutc, gettz
import dataclasses

from arxiv import taxonomy
from arxiv.base.globals import get_application_config, get_application_global
from browse.domain import License
from browse.domain.metadata import Archive, AuthorList, Category, \
    DocMetadata, Group, SourceType, Submitter, VersionEntry
from browse.domain.identifier import Identifier, IdentifierException
from browse.services.document.config.deleted_papers import DELETED_PAPERS
from browse.services.util.formats import VALID_SOURCE_EXTENSIONS, \
    formats_from_source_file_name, formats_from_source_type, \
    has_ancillary_files, list_ancillary_files
from browse.services.document import cache


ARXIV_BUSINESS_TZ = timezone('US/Eastern')



NAMED_FIELDS = ['Title', 'Authors', 'Categories', 'Comments', 'Proxy',
                'Report-no', 'ACM-class', 'MSC-class', 'Journal-ref',
                'DOI', 'License']
"""
Fields that may be parsed from the key-value pairs in second
major component of .abs string. Field names are not normalized.
"""

REQUIRED_FIELDS = ['title', 'authors', 'abstract']
"""
Required parsed fields with normalized field names.

Note the absense of 'categories' as a required field. A subset of version-
affixed .abs files with the old identifiers predate the introduction of
categories and therefore do not have a "Categories:" line; only the (higher-
level) archive and group can be be inferred, and this must be done via the
identifier itself.

The latest versions of these papers should always have the "Categories:" line.
"""


class AbsException(Exception):
    """Error class for general arXiv .abs exceptions."""

    pass


class AbsNotFoundException(FileNotFoundError):
    """Error class for arXiv .abs file not found exceptions."""

    pass


class AbsVersionNotFoundException(FileNotFoundError):
    """Error class for arXiv .abs file version not found exceptions."""

    pass


class AbsParsingException(OSError):
    """Error class for arXiv .abs file parsing exceptions."""

    pass


class AbsDeletedException(Exception):
    """Error class for arXiv papers that have been deleted."""

    pass


class AbsMetaSession:
    """Class for arXiv document metadata sessions."""

    def __init__(self, latest_versions_path: str,
                 original_versions_path: str) -> None:
        """Initialize the document metadata session."""
        if not os.path.isdir(latest_versions_path):
            raise AbsException('Path to latest .abs versions '
                               f'"{latest_versions_path}" does not exist'
                               )
        if not os.path.isdir(original_versions_path):
            raise AbsException('Path to original .abs versions '
                               f'"{original_versions_path}" does not exist'
                               )

        self.latest_versions_path = os.path.realpath(latest_versions_path)
        self.original_versions_path = os.path.realpath(original_versions_path)

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
        paper_id = Identifier(arxiv_id=arxiv_id)

        if paper_id.id in DELETED_PAPERS:
            raise AbsDeletedException(DELETED_PAPERS[paper_id.id])

        latest_version = self._get_version(identifier=paper_id)
        if not paper_id.has_version \
           or paper_id.version == latest_version.version:
            return dataclasses.replace(latest_version,
                                       is_definitive=True,
                                       is_latest=True)

        try:
            this_version = self._get_version(identifier=paper_id,
                                             version=paper_id.version)
        except AbsNotFoundException as e:
            if paper_id.is_old_id:
                raise
            else:
                raise AbsVersionNotFoundException(e)

        # Several fields need to reflect the latest version's data
        combined_version: DocMetadata = dataclasses.replace(
            this_version,
            version_history=latest_version.version_history,
            categories=latest_version.categories,
            primary_category=latest_version.primary_category,
            secondary_categories=latest_version.secondary_categories,
            primary_archive=latest_version.primary_archive,
            primary_group=latest_version.primary_group,
            is_definitive=True,
            is_latest=False)

        return combined_version

    def _next_id(self, identifier: Identifier) -> Optional['Identifier']:
        """Get next consecutive Identifier relative to the provided Identifier.

        Parameters
        ----------
        identifier : :class:`Identifier`

        Returns
        -------
        :class:`Identifier`
            The next Indentifier in sequence
        """
        next_id = None
        if identifier.year is not None and \
                identifier.month is not None and \
                identifier.num is not None:
            new_year = identifier.year
            new_month = identifier.month
            new_num = identifier.num + 1
            if (identifier.is_old_id and new_num > 999) \
               or (not identifier.is_old_id
                   and identifier.year < 2015
                   and new_num > 9999) \
               or (not identifier.is_old_id
                   and identifier.year >= 2015 and new_num > 99999):
                new_num = 1
                new_month = new_month + 1
                if new_month > 12:
                    new_month = 1
                    new_year = new_year + 1

            if identifier.is_old_id:
                next_id = '{}/{:02d}{:02d}{:03d}'.format(
                    identifier.archive, new_year % 100, new_month, new_num)
            else:
                if new_year >= 2015:
                    next_id = '{:02d}{:02d}.{:05d}'.format(
                        new_year % 100, new_month, new_num)
                else:
                    next_id = '{:02d}{:02d}.{:04d}'.format(
                        new_year % 100, new_month, new_num)
            try:
                return Identifier(arxiv_id=next_id)
            except IdentifierException:
                return None
        else:
            return None

    def _next_yymm_id(self, identifier: Identifier) -> Optional[Identifier]:
        """Get the first identifier for the next month."""
        next_yymm_id = None
        if identifier.year is not None and \
                identifier.month is not None:
            new_year = identifier.year
            new_month = identifier.month + 1
            new_num = 1
            if new_month > 12:
                new_month = 1
                new_year = new_year + 1
            if identifier.is_old_id:
                next_yymm_id = '{}/{:02d}{:02d}{:03d}'.format(
                    identifier.archive, new_year % 100, new_month, new_num)
            elif new_year >= 2015:
                next_yymm_id = '{:02d}{:02d}.{:05d}'.format(
                    new_year % 100, new_month, new_num)
            else:
                next_yymm_id = '{:02d}{:02d}.{:04d}'.format(
                    new_year % 100, new_month, new_num)

            try:
                return Identifier(arxiv_id=next_yymm_id)
            except IdentifierException:
                return None
        else:
            return None

    def get_next_id(self, identifier: Identifier) -> Optional['Identifier']:
        """Get the next identifier in sequence if it exists in the repository.

        Under certain conditions this is called to generate the "next" link
        in the "browse context" portion of the abs page rendering.
        These conditions are dependent on the identifier and context; it
        emulates legacy functionality. It is recommended to deprecate
        this function once the /prevnext route is fixed (or replaced) to
        handle old identifiers correctly.

        Parameters
        ----------
        identifier : :class:`Identifier`

        Returns
        -------
        :class:`Identifier`
            The next identifier in sequence that exists in the repository.
        """
        next_id = self._next_id(identifier)
        if not next_id:
            return None

        path = self._get_parent_path(identifier=next_id)
        file_path = os.path.join(path, f'{next_id.filename}.abs')
        if os.path.isfile(file_path):
            return next_id

        next_yymm_id = self._next_yymm_id(identifier)
        if not next_yymm_id:
            return None

        path = self._get_parent_path(identifier=next_yymm_id)
        file_path = os.path.join(path, f'{next_yymm_id.filename}.abs')
        if os.path.isfile(file_path):
            return next_yymm_id

        return None

    def _previous_id(self, identifier: Identifier) -> Optional['Identifier']:
        """Get previous consecutive Identifier relative to provided Identifier.

        Parameters
        ----------
        identifier : :class:`Identifier`

        Returns
        -------
        :class:`Identifier`
            The previous Indentifier in sequence
        """
        previous_id = None
        if identifier.year is not None and \
                identifier.month is not None and \
                identifier.num is not None:
            new_year = identifier.year
            new_month = identifier.month
            new_num = identifier.num - 1
            if new_num == 0:
                new_month = new_month - 1
                if new_month == 0:
                    new_month = 12
                    new_year = new_year - 1

            if identifier.is_old_id:
                if new_num == 0:
                    new_num = 999
                previous_id = '{}/{:02d}{:02d}{:03d}'.format(
                    identifier.archive, new_year % 100, new_month, new_num)
            else:
                if new_year >= 2015:
                    if new_num == 0:
                        new_num = 99999
                    previous_id = '{:02d}{:02d}.{:05d}'.format(
                        new_year % 100, new_month, new_num)
                else:
                    if new_num == 0:
                        new_num = 9999
                    previous_id = '{:02d}{:02d}.{:04d}'.format(
                        new_year % 100, new_month, new_num)
            try:
                return Identifier(arxiv_id=previous_id)
            except IdentifierException:
                return None
        else:
            return None

    def get_previous_id(self, identifier: Identifier) -> Optional[Identifier]:
        """Get previous identifier in sequence if it exists in repository.

        Under certain conditions this is called to generate the "previous" link
        in the "browse context" portion of the abs page rendering.
        These conditions are dependent on the identifier and context; it
        emulates legacy functionality. It is recommended to deprecate
        this function once the /prevnext route is fixed (or replaced) to
        handle old identifiers correctly.

        Parameters
        ----------
        identifier : :class:`Identifier`

        Returns
        -------
        :class:`Identifier`
            The previous identifier in sequence that exists in the repository.
        """
        previous_id = self._previous_id(identifier)
        if not previous_id:
            return None

        if identifier.year == previous_id.year \
           and identifier.month == previous_id.month:
            return previous_id

        path = self._get_parent_path(previous_id)
        if not os.path.exists(path):
            return None

        for _, _, file_list in os.walk(path):
            abs_files = [f[:-4] for f in file_list if f.endswith('.abs')]
            if not abs_files:
                return None
            max_id = max(abs_files)
            try:
                if previous_id.is_old_id:
                    short_id = Identifier(
                        arxiv_id=f'{previous_id.archive}/{max_id}')
                else:
                    short_id = Identifier(arxiv_id=max_id)
                return short_id

            except IdentifierException:
                return None

        return None

    def get_dissemination_formats(self,
                                  docmeta: DocMetadata,
                                  format_pref: Optional[str] = None,
                                  add_sciencewise: bool = False) -> List[str]:
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

        Returns
        -------
        List[str]
            A list of format strings.
        """
        formats: List[str] = []

        # first, get possible list of formats based on available source file
        source_file_path = self._get_source_path(docmeta)
        source_file_formats: List[str] = []
        if source_file_path is not None:
            source_file_formats = \
                formats_from_source_file_name(source_file_path)
        if source_file_formats:
            formats.extend(source_file_formats)

            if add_sciencewise:
                if formats and formats[-1] == 'other':
                    formats.insert(-1, 'sciencewise_pdf')
                else:
                    formats.append('sciencewise_pdf')

        else:
            # check source type from metadata, with consideration of
            # user format preference and cache
            version = docmeta.version
            format_code = docmeta.version_history[version - 1].source_type.code
            cached_ps_file_path = cache.get_cache_file_path(
                docmeta,
                'ps')
            cache_flag = False
            if cached_ps_file_path \
                    and os.path.getsize(cached_ps_file_path) == 0 \
                    and source_file_path \
                    and os.path.getmtime(source_file_path) \
                    < os.path.getmtime(cached_ps_file_path):
                cache_flag = True

            source_type_formats = formats_from_source_type(format_code,
                                                           format_pref,
                                                           cache_flag,
                                                           add_sciencewise)
            if source_type_formats:
                formats.extend(source_type_formats)

        return formats

    def get_ancillary_files(self, docmeta: DocMetadata) \
            -> List[Dict]:
        """Get list of ancillary file names and sizes."""
        version = docmeta.version
        format_code = docmeta.version_history[version - 1].source_type.code
        if has_ancillary_files(format_code):
            source_file_path = self._get_source_path(docmeta)
            if source_file_path is not None:
                return list_ancillary_files(source_file_path)
            else:
                return []
        return []

@wraps(AbsMetaSession.get_ancillary_files)
def get_ancillary_files(docmeta: DocMetadata) -> List[Dict]:
    """Get list of ancillary file names and sizes."""
    return current_session().get_ancillary_files(docmeta)


@wraps(AbsMetaSession.get_dissemination_formats)
def get_dissemination_formats(docmeta: DocMetadata,
                              format_pref: Optional[str] = None,
                              add_sciencewise: bool = False) -> List:
    """Get list of dissemination formats."""
    return current_session().get_dissemination_formats(docmeta,
                                                       format_pref,
                                                       add_sciencewise)


@wraps(AbsMetaSession.get_next_id)
def get_next_id(identifier: Identifier) -> Optional[Identifier]:
    """Retrieve next arxiv document metadata by id."""
    return current_session().get_next_id(identifier)


@wraps(AbsMetaSession.get_previous_id)
def get_previous_id(identifier: Identifier) -> Optional[Identifier]:
    """Retrieve previous arxiv document metadata by id."""
    return current_session().get_previous_id(identifier)


@wraps(AbsMetaSession.get_abs)
def get_abs(arxiv_id: str) -> DocMetadata:
    """Retrieve arxiv document metadata by id."""
    return current_session().get_abs(arxiv_id)


def get_session(app: object = None) -> AbsMetaSession:
    """Get a new session with the abstract metadata service."""
    config = get_application_config(app)
    orignal_versions_path = config.get('DOCUMENT_ORIGNAL_VERSIONS_PATH', None)
    latest_versions_path = config.get('DOCUMENT_LATEST_VERSIONS_PATH', None)

    return AbsMetaSession(latest_versions_path, orignal_versions_path)


def current_session() -> AbsMetaSession:
    """Get/create :class:`.AbsMetaSession` for this context."""
    g = get_application_global()
    if not g:
        return get_session()
    if 'abs_meta' not in g:
        g.abs_meta = get_session()
    assert isinstance(g.abs_meta, AbsMetaSession)
    return g.abs_meta
