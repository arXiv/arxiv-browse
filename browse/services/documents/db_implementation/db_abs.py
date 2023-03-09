"""Legacy DB backed core metadata service."""
from dataclasses import replace
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import sqlalchemy
from browse.domain.identifier import Identifier
from browse.domain.metadata import DocMetadata, SourceType, VersionEntry
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

        # TODO Probably doesn't do docmeta.version_history correctly
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
            size_kilobytes = int(ver.source_size / 1024 + .5)
            # Set UTC timezone
            created_tz = ver.created.replace(tzinfo=tzutc())
            entry = VersionEntry(version=ver.version,
                                 raw='fromdb-no-raw',
                                 size_kilobytes=size_kilobytes,
                                 submitted_date=created_tz,
                                 source_type=SourceType(ver.source_format))
            version_history.append(entry)

        return to_docmeta(res, version_history, self.business_tz)


    def get_dissemination_formats(self,
                                  docmeta: DocMetadata,
                                  format_pref: Optional[str] = None,
                                  add_sciencewise: bool = False
                                  ) -> List[str]:
        """Get a list of formats that can be disseminated for this DocMetadata.

        THIS ONLY CHECKS THE source type on the doc metadata.

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
        version = docmeta.version
        format = docmeta.version_history[version - 1].source_type.code
        return formats_from_source_type(format,
                                        format_pref,
                                        False,
                                        add_sciencewise)


    def get_ancillary_files(self, docmeta: DocMetadata) \
            -> List[Dict]:
        """Get list of ancillary file names and sizes."""
        # TODO implement get_ancillary_files
        return []
