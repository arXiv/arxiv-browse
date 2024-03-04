"""Legacy DB backed core metadata service."""
from datetime import timezone
from typing import List, Optional, Union, Tuple

import sqlalchemy
from arxiv import taxonomy
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm.exc import NoResultFound

from arxiv.identifier import Identifier
from arxiv.taxonomy import Category, Archive, Group
from arxiv.license import License
from arxiv.document.metadata import DocMetadata, AuthorList, Submitter
from arxiv.document.exceptions import AbsException
from arxiv.document.version import SourceFlag, VersionEntry
from arxiv.db import session
from arxiv.db.models import Metadata
from arxiv.document.exceptions import (
    AbsDeletedException, AbsNotFoundException, AbsVersionNotFoundException)
from browse.services.documents.base_documents import DocMetadataService
from browse.services.documents.config.deleted_papers import DELETED_PAPERS
from dateutil.tz import tzutc


class DbDocMetadataService(DocMetadataService):
    """Class for arXiv document metadata service."""


    def __init__(self, db: sqlalchemy.engine.base.Engine) -> None:
        """Initialize the DB document metadata service."""
        self.db = db


    def get_abs(self, arxiv_id: Union[str, Identifier]) -> DocMetadata:
        """Get the .abs metadata for the specified arXiv paper identifier.

        Parameters
        ----------
        arxiv_id : str
            The arXiv identifier string.

        Returns
        -------
        :class:`DocMetadata`
        """
        identifier = arxiv_id if isinstance(arxiv_id, Identifier) else Identifier(arxiv_id=arxiv_id)
        if identifier.id in DELETED_PAPERS:
            raise AbsDeletedException(DELETED_PAPERS[identifier.id])

        all_versions: List[Metadata] = (session.query(Metadata).filter(Metadata.paper_id == identifier.id)).all()
        if not all_versions:
            raise AbsNotFoundException(identifier.id)

        latest = next((ver for ver in all_versions if ver.is_current))
        if identifier.has_version:
            ver_of_interest = next((ver for ver in all_versions if ver.version == identifier.version), None)
            if not ver_of_interest:
                raise AbsVersionNotFoundException(identifier.idv)
        else:
            ver_of_interest = latest

        return _to_docmeta(all_versions, latest, ver_of_interest, identifier)


    def service_status(self) -> List[str]:
        try:
            res = session.query(Metadata).limit(1).first()
            if not res:
                return [f"{__name__}: Nothing in arXiv_metadata table"]
            if not hasattr(res, 'document_id'):
                return [f"{__name__}: arXiv_metadata lacks document_id"]
        except NoResultFound:
            return [f"{__name__}: No Metadata rows found in db"]
        except (OperationalError, DBAPIError) as ex:
            return [f"{__name__}: Error executing test query count on Metadata: {ex}"]
        except Exception as ex:
            return [f"{__name__}: Problem with DB: {ex}"]

        return []


def _to_docmeta(all_versions: List[Metadata], latest: Metadata, ver_of_interest: Metadata, identifier: Identifier) -> DocMetadata:
    """Convert a Metadata object from the DB to a DocMetadata object."""
    version_history = list()

    for ver in all_versions:
        size_kilobytes = 0
        if ver.source_size is not None:
            size_kilobytes = round(ver.source_size / 1024)

            # ie: 2310.08262v1 where source_size is 484 bytes
            if size_kilobytes == 0 and ver.source_size > 0:
                size_kilobytes = 1

        entry = VersionEntry(version=ver.version,
                             raw='',
                             size_kilobytes=size_kilobytes,
                             submitted_date=ver.created.replace(tzinfo=timezone.utc),  # verified as UTC in DB
                             source_flag=SourceFlag(ver.source_flags),
                             source_format=ver.source_format,
                             is_withdrawn=ver.is_withdrawn or ver.source_format == "withdrawn"
                                          or ver.source_size == 0)
        version_history.append(entry)

    doc_license: License = License() if not ver_of_interest.license else License(recorded_uri=ver_of_interest.license)

    modified = ver_of_interest.updated or ver_of_interest.created
    modified = modified.replace(tzinfo=timezone.utc)  # Verified as UTC in DB
    primary_category, secondary_categories, primary_archive = _classification_for_metadata(identifier, latest)

    this_version = DocMetadata(
        raw_safe='',
        abstract=ver_of_interest.abstract,
        arxiv_id=ver_of_interest.paper_id,
        arxiv_id_v=ver_of_interest.paper_id + 'v' + str(ver_of_interest.version),
        arxiv_identifier = identifier,
        title = ver_of_interest.title,
        modified=modified,
        authors=AuthorList(ver_of_interest.authors),
        submitter=Submitter(name=ver_of_interest.submitter_name,
                            email=ver_of_interest.submitter_email),
        source_format=ver_of_interest.source_format,
        journal_ref=ver_of_interest.journal_ref or None,
        report_num=ver_of_interest.report_num or None,
        doi=ver_of_interest.doi or None,
        acm_class=ver_of_interest.acm_class or None,
        msc_class=ver_of_interest.msc_class or None,
        proxy=ver_of_interest.proxy or None,
        comments=ver_of_interest.comments or None,
        version=ver_of_interest.version,
        license=doc_license,
        version_history=version_history,

        is_definitive=ver_of_interest.is_current,
        is_latest=ver_of_interest.is_current,

        # Below are all from the latest version
        # On the abs page the convention is to display all versions as having these fields with values from the latest
        categories = latest.abs_categories,
        primary_category = primary_category,
        secondary_categories = secondary_categories,
        primary_archive = primary_archive,
        primary_group=Group(taxonomy.ARCHIVES[primary_archive.id]['in_group']),
    )

    return this_version


def _classification_for_metadata(identifier: Identifier, metadata: Metadata) -> Tuple[Optional[Category], List[Category], Archive]:
    if not metadata.abs_categories:
        raise AbsException(f"No categories found for {metadata.id}v{metadata.version}")

    primary_category = None
    secondary_categories = []
    category_list = metadata.abs_categories.split()
    if category_list and len(category_list) > 1:
        secondary_categories = [Category(x) for x in category_list[1:]]
    if category_list[0] in taxonomy.CATEGORIES:
        primary_category = Category(category_list[0])
        primary_archive = Archive(taxonomy.CATEGORIES[primary_category.id]['in_archive'])
    else:
        primary_archive = taxonomy.ARCHIVES.get(metadata.paper_id.split("/")[0],None)
        if not primary_archive:
            raise AbsException(f'Cannot infer archive from identifier {metadata.paper_id}')

    return primary_category, secondary_categories, primary_archive
