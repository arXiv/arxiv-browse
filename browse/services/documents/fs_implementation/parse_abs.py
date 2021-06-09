"""Parse fields from a single arXiv abstract (.abs) file."""

import os
import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from pytz import timezone
from dateutil.tz import tzutc, gettz
from dateutil import parser

from arxiv import taxonomy
from browse.domain import License
from browse.domain.metadata import Archive, AuthorList, Category, \
    DocMetadata, Group, SourceType, Submitter, VersionEntry
from browse.domain.identifier import Identifier
from browse.services.documents.base_documents import \
    AbsException, AbsParsingException, AbsNotFoundException

ARXIV_BUSINESS_TZ = timezone('US/Eastern')

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


def parse_abs_file(filename: str) -> DocMetadata:
    """Parse an arXiv .abs file."""
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
        _parse_metadata_fields(key_value_block=misc_fields)

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
        = _parse_version_entries(arxiv_id=arxiv_id,
                                 version_entry_list=parsed_version_entries)

    arxiv_identifier = Identifier(arxiv_id=arxiv_id)

    # named (key-value) fields
    if not all(rf in fields for rf in REQUIRED_FIELDS):
        raise AbsParsingException('missing required field(s)')

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
        # private=private  # TODO, not implemented
    )


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
        except (ValueError, TypeError) as ex:
            raise AbsParsingException(
                f'Could not parse submitted date {sd} as datetime') from ex

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
