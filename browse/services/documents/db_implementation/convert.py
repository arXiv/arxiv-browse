from typing import List
from zoneinfo import ZoneInfo

from arxiv import taxonomy
from browse.domain.metadata import (Archive, AuthorList, Category, DocMetadata,
                                    Group, Identifier, License, Submitter,
                                    VersionEntry)
from browse.services.database.models import Metadata
from browse.services.documents.base_documents import AbsException


def to_docmeta(dbmd: Metadata,
               version_history: List[VersionEntry],
               business_tz: ZoneInfo) -> DocMetadata:
    """Convert a Metadata object from the DB to a DocMetadata object

    The business_tz is the timezone used with the datas in the DB. These are
    usually US/Eastern.

    """
    # This is from parse_abs.py
    arxiv_identifier = Identifier(dbmd.paper_id)

    primary_category = None
    secondary_categories = []
    if dbmd.abs_categories:
        category_list = dbmd.abs_categories.split()
        if category_list and len(category_list) > 1:
            secondary_categories = [
                Category(x) for x in category_list[1:]
                if (category_list and len(category_list) > 1)]
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
        License() if not dbmd.license else License(
            recorded_uri=dbmd.license)

    utc = ZoneInfo("UTC")
    submitted = dbmd.created
    submitted.replace(tzinfo=business_tz)
    submitted = submitted.astimezone(utc)

    modified = dbmd.updated or dbmd.created

    modified.replace(tzinfo=business_tz)
    modified = modified.astimezone(utc)

    return DocMetadata(
        raw_safe='-no-raw-since-sourced-from-db-',
        abstract=dbmd.abstract,
        arxiv_id=dbmd.paper_id,
        arxiv_id_v=dbmd.paper_id + 'v' + str(dbmd.version),
        arxiv_identifier = Identifier(dbmd.paper_id),
        title = dbmd.title,
        modified=modified,
        authors=AuthorList(dbmd.authors),
        submitter=Submitter(name=dbmd.submitter_name,
                            email=dbmd.submitter_email),
        categories=dbmd.abs_categories,
        primary_category=primary_category,
        primary_archive=primary_archive,
        primary_group=Group(taxonomy.ARCHIVES[primary_archive.id]['in_group']),
        secondary_categories=secondary_categories,
        journal_ref=dbmd.journal_ref or None,
        report_num=dbmd.report_num or None,
        doi=dbmd.doi or None,
        acm_class=dbmd.acm_class or None,
        msc_class=dbmd.msc_class or None,
        proxy=dbmd.proxy or None,
        comments=dbmd.comments or None,
        version=dbmd.version,
        license=doc_license,
        version_history=version_history,
        is_definitive=False,
        is_latest=dbmd.is_current
        )
