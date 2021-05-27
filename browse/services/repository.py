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
from browse.domain import License
from browse.domain.metadata import Archive, AuthorList, Category, \
    DocMetadata, Group, SourceType, Submitter, VersionEntry
from browse.domain.identifier import Identifier, IdentifierException
from browse.services.util.formats import VALID_SOURCE_EXTENSIONS, \
    formats_from_source_file_name, formats_from_source_type, \
    has_ancillary_files, list_ancillary_files
from browse.services.document import cache
from abc import ABC
from typing import Any, Dict, List, Optional, Tuple

from browse.domain.metadata import Archive, AuthorList, Category, \
    DocMetadata, Group, SourceType, Submitter, VersionEntry
from browse.domain.identifier import Identifier, IdentifierException


RE_ABS_COMPONENTS = re.compile(r'^\\\\\n', re.MULTILINE)
RE_FROM_FIELD = re.compile(
    r'(?P<from>From:\s*)(?P<name>[^<]+)?\s+(<(?P<email>.*)>)?')
RE_DATE_COMPONENTS = re.compile(
    r'^Date\s*(?::|\(revised\s*(?P<version>.*?)\):)\s*(?P<date>.*?)'
    r'(?:\s+\((?P<size_kilobytes>\d+)kb,?(?P<source_type>.*)\))?$')
RE_FIELD_COMPONENTS = re.compile(
    r'^(?P<field>[-a-z\)\(]+\s*):\s*(?P<value>.*)', re.IGNORECASE)
RE_ARXIV_ID_FROM_PREHISTORY = re.compile(
    r'(Paper:\s+|arXiv:)(?P<arxiv_id>\S+)')

NAMED_FIELDS = ['Title', 'Authors', 'Categories', 'Comments', 'Proxy',
                'Report-no', 'ACM-class', 'MSC-class', 'Journal-ref',
                'DOI', 'License']


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


class AbstractRepository(ABC):
    """Short summary."""

    # @ABC.abstractmethod
    # def get_document_metadata(self, identifier: Identifier) -> DocMetadata:
    #     raise NotImplementedError

    @ABC.abstractmethod
    def get_version_metadata(self, reference) -> DocMetadata:
        raise NotImplementedError

    @ABC.abstractmethod
    def get_next_id(self, reference) -> DocMetadata:
        raise NotImplementedError

    @ABC.abstractmethod
    def get_previous_id(self, reference) -> DocMetadata:
        raise NotImplementedError


class LegacyFilesystemRepository(AbstractRepository):

    def __init__(self, latest_versions_path: str,
                 original_versions_path: str) -> None:
        """Short summary.

        Parameters
        ----------
        latest_versions_path : str
            Path to latest versions of document metadata.
        original_versions_path : str
            Path to previous versions of document metadata.

        """
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

        def get_version_metadata(self, identifier: Identifier,
                                 version: Optional[int] = None) -> DocMetadata:
            """Get a specific version of a paper's abstract metadata.

            Parameters
            ----------
            identifier : Identifier
                Description of parameter `identifier`.
            version : Optional[int]
                Description of parameter `version`.

            Returns
            -------
            DocMetadata
                Description of returned object.

            """

            parent_path = self._get_parent_path(identifier=identifier,
                                                version=version)
            path = os.path.join(parent_path,
                                (f'{identifier.filename}.abs' if not version
                                 else f'{identifier.filename}v{version}.abs'))
            return self._parse_abs_file(filename=path)

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

    def _parse_abs_file(self, filename: str) -> DocMetadata:
        """Parse arXiv .abs file."""
        try:
            with open(filename, mode='r', encoding='latin-1') as absf:
                raw = absf.read()
        except FileNotFoundError:
            raise AbsNotFoundException
        except UnicodeDecodeError as e:
            # TODO: log this
            raise AbsParsingException(
                f'Failed to decode .abs file "{filename}": {e}')

        # TODO: clean up
        modified = datetime.fromtimestamp(
            os.path.getmtime(filename), tz=gettz('US/Eastern'))
        modified = modified.astimezone(tz=tzutc())

        # there are two main components to an .abs file that contain data,
        # but the split must always return four components
        components = RE_ABS_COMPONENTS.split(raw)
        if not len(components) == 4:
            raise AbsParsingException(
                'Unexpected number of components parsed from .abs.')

        # everything else is in the second main component
        prehistory, misc_fields = re.split(r'\n\n', components[1])

        fields: Dict[str, Any] = \
            self._parse_metadata_fields(key_value_block=misc_fields)

        # abstract is the first main component
        fields['abstract'] = components[2]

        id_match = RE_ARXIV_ID_FROM_PREHISTORY.match(prehistory)

        if not id_match:
            raise AbsParsingException(
                'Could not extract arXiv ID from prehistory component.')

        arxiv_id = id_match.group('arxiv_id')

        prehistory = re.sub(r'^.*\n', '', prehistory)
        parsed_version_entries = re.split(r'\n', prehistory)

        # submitter data
        from_match = RE_FROM_FIELD.match(parsed_version_entries.pop(0))
        if not from_match:
            raise AbsParsingException('Could not extract submitter data.')
        name = from_match.group('name')
        if name is not None:
            name = name.rstrip()
        email = from_match.group('email')

        # get the version history for this particular version of the document
        if not len(parsed_version_entries) >= 1:
            raise AbsParsingException('At least one version entry expected.')

        (version, version_history, arxiv_id_v) \
            = AbsMetaSession._parse_version_entries(
                arxiv_id=arxiv_id,
                version_entry_list=parsed_version_entries)

        arxiv_identifier = Identifier(arxiv_id=arxiv_id)

        # named (key-value) fields
        if not all(rf in fields for rf in REQUIRED_FIELDS):
            raise AbsParsingException(f'missing required field(s)')

        # some transformations
        category_list: List[str] = []
        primary_category = None

        if 'categories' in fields and fields['categories']:
            category_list = fields['categories'].split()
            if category_list[0] in taxonomy.CATEGORIES:
                primary_category = Category(category_list[0])
                primary_archive = \
                    Archive(
                        taxonomy.CATEGORIES[primary_category.id]['in_archive'])
            elif arxiv_identifier.is_old_id:
                primary_archive = Archive(arxiv_identifier.archive)
        elif arxiv_identifier.is_old_id:
            primary_archive = Archive(arxiv_identifier.archive)
        else:
            raise AbsException('Cannot infer archive from identifier.')

        doc_license: License = \
            License() if 'license' not in fields else License(
                recorded_uri=fields['license'])
        raw_safe = re.sub(RE_FROM_FIELD, r'\g<from>\g<name>', raw, 1)

        return DocMetadata(
            raw_safe=raw_safe,
            arxiv_id=arxiv_id,
            arxiv_id_v=arxiv_id_v,
            arxiv_identifier=Identifier(arxiv_id=arxiv_id),
            title=fields['title'],
            abstract=fields['abstract'],
            authors=AuthorList(fields['authors']),
            submitter=Submitter(name=name, email=email),
            categories=fields['categories'] if 'categories' in fields else None,
            primary_category=primary_category,
            primary_archive=primary_archive,
            primary_group=Group(
                taxonomy.ARCHIVES[primary_archive.id]['in_group']),
            secondary_categories=[
                Category(x) for x in category_list[1:]
                if (category_list and len(category_list) > 1)
            ],
            journal_ref=None if 'journal_ref' not in fields
            else fields['journal_ref'],
            report_num=None if 'report_num' not in fields
            else fields['report_num'],
            doi=None if 'doi' not in fields else fields['doi'],
            acm_class=None if 'acm_class' not in fields else
            fields['acm_class'],
            msc_class=None if 'msc_class' not in fields else
            fields['msc_class'],
            proxy=None if 'proxy' not in fields else fields['proxy'],
            comments=fields['comments'] if 'comments' in fields else None,
            version=version,
            license=doc_license,
            version_history=version_history,
            modified=modified
        )

    def _parse_version_entries(arxiv_id: str, version_entry_list: List) \
            -> Tuple[int, List[VersionEntry], str]:
        """Parse the version entries from the arXiv .abs file."""
        version_count = 0
        version_entries = list()
        for parsed_version_entry in version_entry_list:
            version_count += 1
            date_match = RE_DATE_COMPONENTS.match(parsed_version_entry)
            if not date_match:
                raise AbsParsingException(
                    'Could not extract date components from date line.')
            try:
                sd = date_match.group('date')
                submitted_date = parser.parse(date_match.group('date'))
            except (ValueError, TypeError):
                raise AbsParsingException(
                    f'Could not parse submitted date {sd} as datetime')

            source_type = SourceType(code=date_match.group('source_type'))
            ve = VersionEntry(
                raw=date_match.group(0),
                source_type=source_type,
                size_kilobytes=int(date_match.group('size_kilobytes')),
                submitted_date=submitted_date,
                version=version_count
            )
            version_entries.append(ve)

        return (
            version_count,
            version_entries,
            f"{arxiv_id}v"
            f"{version_entries[-1].version}")

    def _parse_metadata_fields(key_value_block: str) -> Dict[str, str]:
        """Parse the key-value block from the arXiv .abs string."""
        key_value_block = key_value_block.lstrip()
        field_lines = re.split(r'\n', key_value_block)
        field_name = 'unknown'
        fields_builder: Dict[str, str] = {}
        for field_line in field_lines:
            field_match = RE_FIELD_COMPONENTS.match(field_line)
            if field_match and field_match.group('field') in NAMED_FIELDS:
                field_name = field_match.group(
                    'field').lower().replace('-', '_')
                field_name = re.sub(r'_no$', '_num', field_name)
                fields_builder[field_name] = field_match.group(
                    'value').rstrip()
            elif field_name != 'unknown':
                # we have a line with leading spaces
                fields_builder[field_name] += re.sub(r'^\s+', ' ', field_line)
        return fields_builder

    def _get_parent_path(self, identifier: Identifier,
                         version: Optional[int] = None) -> str:
        """Get the absolute parent path of the provided identifier."""
        parent_path = os.path.join(
            (self.latest_versions_path if not version
             else self.original_versions_path),
            ('arxiv' if not identifier.is_old_id or identifier.archive is None
             else identifier.archive),
            'papers',
            identifier.yymm,
        )
        return parent_path

    def _get_source_path(self, docmeta: DocMetadata) -> Optional[str]:
        """Get the absolute path of this DocMetadata's source file."""
        identifier = docmeta.arxiv_identifier
        version = docmeta.version
        file_noex = identifier.filename
        if not docmeta.is_latest:
            parent_path = self._get_parent_path(identifier, version)
            file_noex = f'{file_noex}v{version}'
        else:
            parent_path = self._get_parent_path(identifier)

        for extension in VALID_SOURCE_EXTENSIONS:
            possible_path = os.path.join(
                parent_path,
                f'{file_noex}{extension[0]}')
            if os.path.isfile(possible_path):
                return possible_path
        return None
