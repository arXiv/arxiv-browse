"""Parse fields from a single arXiv abstract (.abs) file."""
import os
import re
from pytz import timezone
from dateutil import parser
from functools import wraps
from browse.domain.metadata import DocMetadata, Submitter, SourceType, \
    VersionEntry
from browse.domain.identifier import Identifier, IdentifierException
from browse.context import get_application_config, get_application_global

ARXIV_BUSINESS_TZ = timezone('US/Eastern')

RE_ABS_COMPONENTS = re.compile(r'^\\\\\n', re.MULTILINE)
RE_FROM_FIELD = re.compile(
    r'From:\s*(?P<name>[^<]+)?\s*(<(?P<email>.*)>)?')
RE_DATE_COMPONENTS = re.compile(
    r'^Date\s*(?::|\(revised\s*(?P<version>.*?)\):)\s*(?P<date>.*?)'
    '(?:\s+\((?P<size_kilobytes>\d+)kb,?(?P<source_type>.*)\))?$')
RE_FIELD_COMPONENTS = re.compile(
    r'^(?P<field>[-a-z\)\(]+\s*):\s*(?P<value>.*)', re.IGNORECASE)
RE_ARXIV_ID_FROM_PREHISTORY = re.compile(
    r'(Paper:\s+|arXiv:)(?P<arxiv_id>\S+)')

# (non-normalized) fields that may be parsed from the key-value pairs in second
# major component of .abs file.
NAMED_FIELDS = ['Title', 'Authors', 'Categories', 'Comments', 'Proxy',
                'Report-no', 'ACM-class', 'MSC-class', 'Journal-ref',
                'DOI', 'License']
# (normalized) required parsed fields
REQUIRED_FIELDS = ['title', 'authors', 'abstract', 'categories']

class AbsException(Exception):
    """Error class for general arXiv .abs exceptions."""

    pass


class AbsParsingException(OSError):
    """Error class for arXiv .abs file parsing exceptions."""

    pass


class AbsMetaSession(object):
    """Class for representing arXiv document metadata."""

    def __init__(self, latest_versions_path: str,
                 original_versions_path: str) -> None:

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

    def _get_version(self, identifier: Identifier,
                     version: int=None) -> DocMetadata:
        path = os.path.join(
            (self.latest_versions_path if not version
             else self.original_versions_path),
            ('arxiv' if not identifier.is_old_id else identifier.archive),
            'papers',
            identifier.yymm,
            (f'{identifier.filename}.abs' if not version
             else f'{identifier.filename}v{version}.abs')
        )
        return self.parse_abs_file(filename=path)

    def get_abs(self, arxiv_id: str) -> DocMetadata:
        """Get the .abs metadata for the specified arXiv paper identifier."""
        try:
            paper_id = Identifier(arxiv_id=arxiv_id)
        except IdentifierException as e:
            return

        latest_version = self._get_version(identifier=paper_id)
        if not paper_id.has_version \
           or paper_id.version == latest_version.version:
            return latest_version

        this_version = self._get_version(identifier=paper_id,
                                         version=paper_id.version)
        this_version.version_history = latest_version.version_history
        return this_version

    @staticmethod
    def parse_abs_file(filename: str) -> DocMetadata:
        """Parse arXiv .abs file."""
        fields = {}  # type: Dict[str, Any]
        try:
            f = open(filename, 'rt')
            raw = f.read()
        except OSError as e:
            raise AbsParsingException(f'Failed to read .abs file: {e}')
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

        prehistory = re.sub(r'^.*\n', '', prehistory)
        parsed_version_entries = re.split(r'\n', prehistory)

        # submitter data
        from_match = RE_FROM_FIELD.match(parsed_version_entries.pop(0))
        if not from_match:
            raise AbsParsingException('Could not extract submitter data.')
        name = from_match.group('name')
        if name:
            name = name.rstrip()
        email = from_match.group('email') or None
        fields['submitter'] = Submitter(name=name, email=email)

        # get the version history for this particular version of the document
        if not len(parsed_version_entries) >= 1:
            raise AbsParsingException('At least one version entry expected.')
        version_count = 0
        version_entries = list()
        for parsed_version_entry in parsed_version_entries:
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

        # named (key-value) fields
        misc_fields = misc_fields.lstrip()
        field_lines = re.split(r'\n', misc_fields)
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

        if not all(rf in fields for rf in REQUIRED_FIELDS):
            raise AbsParsingException('missing required field(s)')

        # some transformations
        categories = fields['categories'].split()
        fields['primary_category'] = categories[0]
        if len(categories) > 1:
            fields['secondary_categories'] = categories[1:]

        return DocMetadata(**fields)


@wraps(AbsMetaSession.get_abs)
def get_abs(arxiv_id: str) -> DocMetadata:
    """Retrieve arxiv document metadata by id."""
    return current_session().get_abs(arxiv_id)


# TODO: consider making this private.
def get_session(app: object = None) -> AbsMetaSession:
    """Get a new session with the abstract metadata service."""
    config = get_application_config(app)
    orignal_versions_path = config.get('DOCUMENT_ORIGNAL_VERSIONS_PATH', None)
    latest_versions_path = config.get('DOCUMENT_LATEST_VERSIONS_PATH', None)

    return AbsMetaSession(latest_versions_path, orignal_versions_path)


# TODO: consider making this private.
def current_session() -> AbsMetaSession:
    """Get/create :class:`.AbsMetaSession` for this context."""
    g = get_application_global()
    if not g:
        return get_session()
    if 'abs_meta' not in g:
        g.abs_meta = get_session()    # type: ignore
    return g.abs_meta     # type: ignore
