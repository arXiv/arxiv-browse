"""
arxiv browse metadata service.

Provides routines to parse filesystem-based arXiv abstract (.abs) files.
"""
import os
import re
from pytz import timezone
from dateutil import parser
from functools import wraps
from typing import Dict, List, Optional

from browse.domain.identifier import Identifier, IdentifierException
from browse.domain.license import License
from browse.domain.metadata import DocMetadata, Submitter, SourceType, \
    VersionEntry, Category
from arxiv.base.globals import get_application_config, get_application_global
from browse.services.document.config import DELETED_PAPERS

ARXIV_BUSINESS_TZ = timezone('US/Eastern')

RE_ABS_COMPONENTS = re.compile(r'^\\\\\n', re.MULTILINE)
RE_FROM_FIELD = re.compile(
    r'From:\s*(?P<name>[^<]+)\s*(<(?P<email>.*)>)?')
RE_DATE_COMPONENTS = re.compile(
    r'^Date\s*(?::|\(revised\s*(?P<version>.*?)\):)\s*(?P<date>.*?)'
    r'(?:\s+\((?P<size_kilobytes>\d+)kb,?(?P<source_type>.*)\))?$')
RE_FIELD_COMPONENTS = re.compile(
    r'^(?P<field>[-a-z\)\(]+\s*):\s*(?P<value>.*)', re.IGNORECASE)
RE_ARXIV_ID_FROM_PREHISTORY = re.compile(
    r'(Paper:\s+|arXiv:)(?P<arxiv_id>\S+)')

# (non-normalized) fields that may be parsed from the key-value pairs in second
# major component of .abs file.
NAMED_FIELDS = ['Title', 'Authors', 'Categories', 'Comments', 'Proxy',
                'Report-no', 'ACM-class', 'MSC-class', 'Journal-ref',
                'DOI', 'License', '']
# (normalized) required parsed fields
REQUIRED_FIELDS = ['title', 'authors', 'abstract', 'categories']


# List of tuples containing the valid source file name extensions and their
# corresponding dissemintation formats.
# There are minor performance implications in the ordering when doing
# filesystem lookups, so the ordering here should be preserved.
VALID_SOURCE_EXTENSIONS = [
                            ('.tar.gz', None),
                            ('.pdf', ['pdfonly']),
                            ('.ps.gz', ['pdf', 'ps']),
                            ('.gz', None),
                            ('.dvi.gz', None),
                            ('.html.gz', ['html'])
                          ]


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


class AbsMetaSession(object):
    """Abstract metadata session class."""

    def __init__(self, latest_versions_path: str,
                 original_versions_path: str) -> None:
        """Set the filesystem paths the to be used with AbsMetaSession."""
        if not os.path.isdir(latest_versions_path):
            raise AbsException(f'Path to latest .abs versions '
                               '"{latest_versions_path}" does not exist'
                               )
        if not os.path.isdir(original_versions_path):
            raise AbsException(f'Path to original .abs versions '
                               '"{original_versions_path}" does not exist'
                               )

        self.latest_versions_path = os.path.realpath(latest_versions_path)
        self.original_versions_path = os.path.realpath(original_versions_path)

    def get_abs(self, arxiv_id: str) -> DocMetadata:
        """
        Get the .abs metadata for the specified arXiv paper identifier.

        Parameters
        ----------
        arxiv_id : str
            The arXiv identifier string.

        Returns
        -------
        :class:`DocMetadata`

        """
        try:
            paper_id = Identifier(arxiv_id=arxiv_id)
        except IdentifierException:
            raise

        if paper_id.id in DELETED_PAPERS:
            raise AbsDeletedException(DELETED_PAPERS[paper_id.id])

        latest_version = self._get_version(identifier=paper_id)
        if not paper_id.has_version \
           or paper_id.version == latest_version.version:
            return latest_version

        try:
            this_version = self._get_version(identifier=paper_id,
                                             version=paper_id.version)
        except AbsNotFoundException as e:
            if paper_id.is_old_id:
                raise
            else:
                raise AbsVersionNotFoundException(e)

        this_version.version_history = latest_version.version_history
        return this_version

    def _next_id(self, identifier: Identifier) -> Optional['Identifier']:
        """
        Get next consecutive Identifier relative to the provided Identifier.

        Parameters
        ----------
        identifier : :class:`Identifier`

        Returns
        -------
        :class:`Identifier`
            The next Indentifier in sequence

        """
        next_id = None
        new_year = identifier.year
        new_month = identifier.month
        new_num = identifier.num + 1
        if (identifier.is_old_id and new_num > 999) \
           or (not identifier.is_old_id
               and identifier.year < 2015 and new_num > 9999) \
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

    def _next_yymm_id(self, identifier: Identifier):
        """Get the first identifier for the next month."""
        next_yymm_id = None
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

    def get_next_id(self, identifier: Identifier) -> Optional['Identifier']:
        """
        Get the next identifier in sequence if it exists in the repository.

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
        """
        Get previous consecutive Identifier relative to provided Identifier.

        Parameters
        ----------
        identifier : :class:`Identifier`

        Returns
        -------
        :class:`Identifier`
            The previous Indentifier in sequence

        """
        previous_id = None
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

    def get_previous_id(self, identifier: Identifier) -> Optional[Identifier]:
        """
        Get the previous identifier in sequence if it exists in the repository.

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

    def _get_formats_from_source(self, identifier: Identifier) -> \
            Optional[List]:
        """Get list of dissemination formats based on source file."""
        parent_path = self._get_parent_path(identifier)
        # Check the usual file extensions
        for extension in VALID_SOURCE_EXTENSIONS:
            # We only care to check for those that have corresponding
            # dissemination formats
            if not isinstance(extension[1], (list,)):
                continue
            possible_path = os.path.join(
                parent_path,
                f'{identifier.filename}{extension[0]}')
            print(f'Checking {possible_path} exists')
            if os.path.isfile(possible_path):
                print(f'{possible_path} exists')
                return extension[1]
        return None

    def get_dissemination_formats(self, docmeta: DocMetadata) -> List[str]:
        """
        Get a list of formats that can be disseminated for this DocMetadata.

        Several checks are performed to determine available dissemination
        formats:
            1. a check for source files with specific, valid file name
               extensions (i.e. for a subset of the allowed source file name
               extensions, the dissemintation formats are predictable)
            2. if formats cannot be inferred from source file, inspect the
               source type in the document metadata.

        Format names are strings. These include 'src', 'pdf', 'ps', 'html',
        'pdfonly', 'other', 'dvi', 'ps(400)', 'ps(600)', 'nops'.

        Parameters
        ----------
        docmeta : :class:`DocMetadata`

        Returns
        -------
        List[str]
            A list of format strings.

        """
        formats = []
        has_other = False
        # first, get possible list of formats based on available source file
        formats_from_source = self._get_formats_from_source(
            docmeta.arxiv_identifier)
        if formats_from_source:
            formats.extend(formats_from_source)
        else:
            try:
                v = docmeta.version
                code = docmeta.version_history[v-1].source_type.code
            except Exception as e:
                print(f'Caught exception {e}')
            print(f'source type code is {code}')
            has_encrypted_source = re.search('S', code, re.IGNORECASE)
            # TODO: get 'xxx-ps-defaults' preference
            ps_defaults = ''
            if re.search('I', code, re.IGNORECASE):
                if not has_encrypted_source:
                    formats.append('src')
            elif re.search('P', code, re.IGNORECASE):
                formats.extend(['pdf', 'ps', 'other'])
            elif re.search('D', code, re.IGNORECASE):
                # PDFtex has source so honor src preference
                if re.search('src', ps_defaults) and not has_encrypted_source:
                    formats.append('src')
                formats.extend(['pdf', 'other'])
            elif re.search('F', code, re.IGNORECASE):
                formats.extend(['pdf', 'other'])
            elif re.search('H', code, re.IGNORECASE):
                formats.extend(['html', 'other'])
            elif re.search(r'[XO]', code, re.IGNORECASE):
                formats.extend(['pdf', 'other'])
            # TODO PS cache check
            # elsif  -z "$cache.ps.gz" && !source_newer_than_cache_files($version,'ps')) {
            # elif os.path.getsize == 0
            #       formats.extend(['nops', 'other'])
            else:
                if re.search('pdf', ps_defaults):
                    formats.append('pdf')
                elif re.search('400', ps_defaults):
                    formats.append('ps(400)')
                elif re.search('600', ps_defaults):
                    formats.append('ps(600)')
                elif re.search('fname=cm', ps_defaults):
                    formats.append('ps(cm)')
                elif re.search('fname=CM', ps_defaults):
                    formats.append('ps(CM)')
                elif re.search('dvi', ps_defaults):
                    formats.append('dvi')
                elif re.search('src', ps_defaults):
                    if not has_encrypted_source:
                        formats.append('src')
                    formats.extend(['pdf', 'ps'])
                else:
                    formats.extend(['pdf', 'ps'])

                has_other = True

        # TODO - ScienceWISE annotated PDF
        # if has_annotated_pdf:
        #     formats.append('sciencewise_pdf')

        if has_other:
            formats.append('other')

        return formats

    @staticmethod
    def parse_abs_file(filename: str) -> DocMetadata:
        """Parse arXiv .abs file."""
        fields = {}  # type: Dict[str, Any]

        try:
            with open(filename) as absf:
                raw = absf.read()
        except FileNotFoundError:
            raise AbsNotFoundException
        except UnicodeDecodeError as e:
            raise AbsParsingException(
                f'Failed to decode .abs file "{filename}": {e}')

        # there are two main components to an .abs file that contain data,
        # but the split must always return four components
        components = RE_ABS_COMPONENTS.split(raw)
        if not len(components) == 4:
            raise AbsParsingException(
                'Unexpected number of components parsed from .abs.')

        # abstract is the first main component
        fields['abstract'] = components[2]

        # everything else is in the second main component
        prehistory, misc_fields = re.split(r'\n\n', components[1])
        id_match = RE_ARXIV_ID_FROM_PREHISTORY.match(prehistory)

        if not id_match:
            raise AbsParsingException(
                'Could not extract arXiv ID from prehistory component.')

        fields['arxiv_id'] = id_match.group('arxiv_id')
        fields['arxiv_identifier'] = Identifier(arxiv_id=fields['arxiv_id'])

        prehistory = re.sub(r'^.*\n', '', prehistory)
        parsed_version_entries = re.split(r'\n', prehistory)

        # submitter data
        from_match = RE_FROM_FIELD.match(parsed_version_entries.pop(0))
        if not from_match:
            raise AbsParsingException('Could not extract submitter data.')
        name = from_match.group('name').rstrip()
        email = from_match.group('email') or None
        fields['submitter'] = Submitter(name=name, email=email)

        # get the version history for this particular version of the document
        if not len(parsed_version_entries) >= 1:
            raise AbsParsingException('At least one version entry expected.')

        AbsMetaSession._parse_version_entries(
            fields=fields,
            version_entry_list=parsed_version_entries
        )
        # named (key-value) fields
        AbsMetaSession._parse_metadata_fields(fields=fields,
                                              key_value_block=misc_fields)
        if 'categories' not in fields and fields['arxiv_identifier'].is_old_id:
            fields['categories'] = fields['arxiv_identifier'].archive

        if not all(rf in fields for rf in REQUIRED_FIELDS):
            raise AbsParsingException(f'missing required field(s)')

        # some transformations
        categories = fields['categories'].split()
        fields['primary_category'] = Category(id=categories[0])
        fields['secondary_categories'] = [
            Category(id=x) for x in categories[1:] if len(categories) > 1
        ]
        if 'license' in fields:
            fields['license'] = License(recorded_uri=fields['license'])

        return DocMetadata(**fields)

    def _get_version(self, identifier: Identifier,
                     version: int = None) -> DocMetadata:
        """Get a specific version of a paper's abstract metadata."""
        parent_path = self._get_parent_path(identifier=identifier,
                                            version=version)
        path = os.path.join(parent_path,
                            (f'{identifier.filename}.abs' if not version
                             else f'{identifier.filename}v{version}.abs'))
        return self.parse_abs_file(filename=path)

    def _get_parent_path(self, identifier: Identifier,
                         version: int = None) -> str:
        """Get the absolute parent path of the provided identifier."""
        parent_path = os.path.join(
            (self.latest_versions_path if not version
             else self.original_versions_path),
            ('arxiv' if not identifier.is_old_id else identifier.archive),
            'papers',
            identifier.yymm,
        )
        return parent_path

    @staticmethod
    def _parse_version_entries(fields: Dict, version_entry_list: List) -> None:
        """Parse the version entries from the arXiv .abs file."""
        version_count = 0
        version_entries = list()
        for parsed_version_entry in version_entry_list:
            version_count += 1
            date_match = RE_DATE_COMPONENTS.match(parsed_version_entry)
            if not date_match:
                raise AbsParsingException(
                    'Could not extract date componenents from date line.')
            try:
                sd = date_match.group('date')
                submitted_date = parser.parse(date_match.group('date'))
            except (ValueError, TypeError):
                raise 'AbsParsingError'(
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

        fields['version'] = version_count
        fields['version_history'] = version_entries
        fields['arxiv_id_v'] = f"{fields['arxiv_id']}v" \
                               f"{version_entries[-1].version}"

    @staticmethod
    def _parse_metadata_fields(fields: Dict, key_value_block: str) -> None:
        """Parse the key-value block from the arXiv .abs string."""
        key_value_block = key_value_block.lstrip()
        field_lines = re.split(r'\n', key_value_block)
        field_name = 'unknown'
        for field_line in field_lines:
            field_match = RE_FIELD_COMPONENTS.match(field_line)
            if field_match and field_match.group('field') in NAMED_FIELDS:
                field_name = field_match.group(
                    'field').lower().replace('-', '_')
                field_name = re.sub(r'_no$', '_num', field_name)
                fields[field_name] = field_match.group('value').rstrip()
            elif field_name != 'unknown':
                # we have a line with leading spaces
                fields[field_name] += re.sub(r'^\s+', ' ', field_line)
        return fields


@wraps(AbsMetaSession.get_dissemination_formats)
def get_dissemination_formats(docmeta: DocMetadata) -> List:
    """Get list of dissemination formats."""
    return current_session().get_dissemination_formats(docmeta)


@wraps(AbsMetaSession.get_next_id)
def get_next_id(identifier: Identifier) -> Identifier:
    """Retrieve next arxiv document metadata by id."""
    return current_session().get_next_id(identifier)


@wraps(AbsMetaSession.get_previous_id)
def get_previous_id(identifier: Identifier) -> Identifier:
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
        g.abs_meta = get_session()    # type: ignore
    return g.abs_meta     # type: ignore
