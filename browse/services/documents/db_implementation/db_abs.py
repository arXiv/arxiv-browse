"""Legacy DB backed core metadata service."""
from dataclasses import replace
from typing import Dict, List, Optional, Union
from zoneinfo import ZoneInfo

import sqlalchemy
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import Query
from sqlalchemy.orm.exc import NoResultFound

from browse.domain.identifier import Identifier
from browse.domain.metadata import DocMetadata
from browse.domain.version import SourceType, VersionEntry
from browse.services.database.models import Metadata
from browse.services.documents.base_documents import (
    AbsDeletedException, AbsNotFoundException, AbsVersionNotFoundException,
    DocMetadataService)
from browse.services.documents.config.deleted_papers import DELETED_PAPERS
from dateutil.tz import tzutc

from ..format_codes import formats_from_source_type
from .convert import to_docmeta


class DbDocMetadataService(DocMetadataService):
    """Class for arXiv document metadata service."""


    def __init__(self,
                 db: sqlalchemy.engine.base.Engine,
                 business_tz:str) -> None:
        """Initialize the DB document metadata service."""
        self.db = db
        zz =  ZoneInfo(business_tz)
        if zz is None:
            raise ValueError("Must pass a valid timzone")
        self.business_tz = zz

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

        if isinstance(arxiv_id, Identifier):
            paper_id = arxiv_id
        else:
            paper_id = Identifier(arxiv_id=arxiv_id)

        if paper_id.id in DELETED_PAPERS:
            raise AbsDeletedException(DELETED_PAPERS[paper_id.id])

        latest_version = self._abs_for_version(identifier=paper_id)
        if not paper_id.has_version \
           or paper_id.version == latest_version.version:
            return replace(latest_version,
                           is_definitive=True,
                           is_latest=True)

        try:
            this_version = self._abs_for_version(identifier=paper_id,
                                                 version=paper_id.version)
        except AbsNotFoundException as e:
            if paper_id.is_old_id:
                raise
            else:
                raise AbsVersionNotFoundException(e) from e

        # Several fields need to reflect the latest version's data
        combined_version: DocMetadata = replace(
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


    def _abs_for_version(self, identifier: Identifier,
                         version: Optional[int] = None) -> DocMetadata:
        """Get a specific version of a paper's abstract metadata.

        if version is None then get the latest version."""
        if version:
            res = (Metadata.query
                   .filter( Metadata.paper_id == identifier.id)
                   .filter( Metadata.version == identifier.version )).first()
        else:
            res = (Metadata.query
                   .filter(Metadata.paper_id == identifier.id)
                   .filter(Metadata.is_current == 1)).first()
        if not res:
            raise AbsNotFoundException(identifier.id)

        # Gather version history metadata from each document version
        # entry in database.
        version_history = list()

        all_versions = (Metadata.query
               .filter(Metadata.paper_id == identifier.id)
               )

        for ver in all_versions:
            size_kilobytes = int(ver.source_size / 1024 + .5) if ver.source_size is not None else 0
            created_tz = ver.created.replace(tzinfo=tzutc())
            entry = VersionEntry(version=ver.version,
                                 raw='',
                                 size_kilobytes=size_kilobytes,
                                 submitted_date=created_tz,
                                 source_type=SourceType(ver.source_flags),
                                 is_withdrawn=ver.is_withdrawn
                                 )
            version_history.append(entry)

        return to_docmeta(res, identifier, version_history, self.business_tz)

    def service_status(self)->List[str]:
        try:
            res = Metadata.query.limit(1).first()
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
