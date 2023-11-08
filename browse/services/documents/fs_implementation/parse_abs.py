"""Parse fields from a single arXiv abstract (.abs) file."""

import re
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime

from zoneinfo import ZoneInfo
from dateutil import parser

from flask import current_app

from browse.services.anypath import to_anypath

from arxiv import taxonomy

from browse.domain.license import License
from browse.domain.metadata import Archive, AuthorList, Category, \
    DocMetadata, Group, Submitter
from browse.domain.version import VersionEntry, SourceType
from browse.domain.identifier import Identifier
from browse.services.documents.base_documents import \
    AbsException, AbsParsingException, AbsNotFoundException


RE_ABS_COMPONENTS = re.compile(r'^\\\\\n', re.MULTILINE)
RE_FROM_FIELD = re.compile(
    r'(?P<from>From:\s*)(?P<name>[^<]+)?\s+(<(?P<email>.*)>)?')
RE_DATE_COMPONENTS = re.compile(
    r'^Date\s*(?::|\(revised\s*(?P<version>.*?)\):)\s*(?P<date>.*?)'
    r'(?:\s+\((?P<size_kilobytes>\d+)kb,?(?P<source_type>.*)\))?$')

RE_REP_COMPONENTS = re.compile(
    r'^replaced with revised version\s*(?P<date>.*?)'
    r'(?:\s+\((?P<size_kilobytes>\d+)kb,?(?P<source_type>.*)\))?$')

RE_FIELD_COMPONENTS = re.compile(
    r'^(?P<field>[-a-z\)\(]+\s*):\s*(?P<value>.*)', re.IGNORECASE)
RE_ARXIV_ID_FROM_PREHISTORY = re.compile(
    r'(Paper:\s+|arXiv:)(?P<arxiv_id>\S+)')


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

Note the absence of 'categories' as a required field. A subset of version-
affixed .abs files with the old identifiers predate the introduction of
categories and therefore do not have a "Categories:" line; only the (higher-
level) archive and group can be be inferred, and this must be done via the
identifier itself.

The latest versions of these papers should always have the "Categories:" line.
"""


_fs_tz: Optional[ZoneInfo] = None
"""FS timezone if in a flask app."""


def parse_abs_file(filename: str) -> DocMetadata:
    """Parse an arXiv .abs file.

    The modified time on the abs file will be used as the modified time for the
    abstract. It will be pulled from `flask.config` if in a app_context. It
    can be specified with tz arg.
    """
    absfile = to_anypath(filename)
    try:
        with absfile.open(mode='r', encoding='latin-1') as absf:
            raw = absf.read()
            if current_app:
                modified = datetime.fromtimestamp(absfile.stat().st_mtime, tz=_get_tz())
            else:
                modified = datetime.fromtimestamp(absfile.stat().st_mtime)
            modified = modified.astimezone(ZoneInfo("UTC"))
            return parse_abs(raw, modified)

    except FileNotFoundError:
        raise AbsNotFoundException
    except UnicodeDecodeError as e:
        raise AbsParsingException(f'Failed to decode .abs file "{filename}": {e}')



def parse_abs(raw: str, modified:datetime) -> DocMetadata:
    """Parse an abs with fields and an abstract."""

    # There are two main components to an .abs file that contain data,
    # but the split is expected to return four components.
    components = RE_ABS_COMPONENTS.split(raw)
    if len(components) > 4:
            components = alt_component_split(components)

    abstract = components[2]
    abs = parse_abs_top(components[1], modified, abstract)
    missing = [rf for rf in REQUIRED_FIELDS if not hasattr(abs, rf) or not getattr(abs, rf)]
    if missing:
        raise AbsParsingException(f"missing required field(s) {','.join(missing)}")
    return abs




def parse_abs_top(raw: str, modified:datetime, abstract:str) -> DocMetadata:
    """Parse just the fields part of the abs.

    The top section is the field section of the abs data before the abstract.

    An abstract may be passed in so it is added to the DocMetadata when constructed. The
    abstract cannot be added later since the DocMetadata class is frozen.

    `raw` is expected to not have surrounding `\\` delimiters.
    """
    prehistory, misc_fields = re.split(r'\n\n', raw)

    fields: Dict[str, Any] = \
        _parse_metadata_fields(key_value_block=misc_fields)

    id_match = RE_ARXIV_ID_FROM_PREHISTORY.match(prehistory)

    if not id_match:
        raise AbsParsingException(
            'Could not extract arXiv ID from prehistory component.')

    arxiv_id = id_match.group('arxiv_id')

    # cleanup and create list of prehistory entries
    prehistory = re.sub(r'^.*\n', '', prehistory)
    parsed_version_entries = [line for line in re.split(r'\n', prehistory)
                              if line.startswith("Date") or line.startswith("replaced with revised")]

    # submitter data
    from_match = RE_FROM_FIELD.match(prehistory)
    if not from_match or not from_match.group('name'):
        name = ''
        email = 'email-not-provided'
    else:
        name = from_match.group('name').rstrip()
        email = from_match.group('email')

    # get the version history for this particular version of the document
    if parsed_version_entries:
        (version, version_history, arxiv_id_v) \
            = _parse_version_entries(arxiv_id=arxiv_id,
                                     version_entry_list=parsed_version_entries)
        arxiv_identifier = Identifier(arxiv_id=arxiv_id_v)
    else:
        raise AbsParsingException('At least one version entry expected.')

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
        else:
            raise AbsException(f"Invalid caregory {category_list[0]}")
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
        arxiv_identifier=arxiv_identifier,
        title=fields['title'],
        abstract=abstract,
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
        # private=private  # TODO, not implemented
    )

def _parse_version_entries(arxiv_id: str, version_entry_list: List) \
        -> Tuple[int, List[VersionEntry], str]:
    """Parse the version entries from the arXiv .abs file."""
    version_count = 0
    version_entries = list()
    for parsed_version_entry in version_entry_list:
        version_count += 1
        date_match = RE_DATE_COMPONENTS.match(parsed_version_entry) or RE_REP_COMPONENTS.match(parsed_version_entry)
        if not date_match:
            raise AbsParsingException(
                'Could not extract date components from date line.')
        try:
            sd = date_match.group('date')
            submitted_date = parser.parse(date_match.group('date'))
        except (ValueError, TypeError) as ex:
            raise AbsParsingException(
                f'Could not parse submitted date {sd} as datetime') from ex

        source_type = SourceType(code=date_match.group('source_type'))
        kb = int(date_match.group('size_kilobytes'))
        ve = VersionEntry(
            raw=date_match.group(0),
            source_type=source_type,
            size_kilobytes=kb,
            submitted_date=submitted_date,
            version=version_count,
            is_withdrawn=kb == 0 or source_type.ignore
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


def alt_component_split(components: List[str]) -> List[str]:
    r"""Alternative split to accomidate extra \\ in the abstract.
        ex of abstract portion:
        u_t = \Delta u
        \\
        v_t = \Delta v
        ARXIVNG-3128"""
    if len(components) <= 4:
        raise AbsParsingException(
            'Unexpected number of components parsed from .abs.')
    alt_comp = []
    abstract = ""
    for idx, itm in enumerate(components):
        if idx < 2:
            alt_comp.append(itm)
        if idx == 2:
            abstract += itm
        if idx > 2 and itm:
            abstract += r" \\ " + itm  # Add back in \\ stripped by split

    alt_comp.append(abstract)
    alt_comp.append('')
    return alt_comp


def _get_tz() -> ZoneInfo:
    """Gets the timezone from the flask current_app."""
    global _fs_tz
    if _fs_tz is None:
        _fs_tz = ZoneInfo(current_app.config["FS_TZ"])

    return _fs_tz
