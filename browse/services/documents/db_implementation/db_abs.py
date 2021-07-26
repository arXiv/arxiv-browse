"""Legacy DB backed core metadata service."""
from typing import Dict, List, Optional
from dataclasses import replace

from browse.domain.metadata import DocMetadata, VersionEntry
from browse.domain.identifier import Identifier
from browse.services.documents.config.deleted_papers import DELETED_PAPERS

from browse.services.documents.base_documents import DocMetadataService, \
    AbsDeletedException, AbsNotFoundException , AbsVersionNotFoundException

from browse.services.database.models import Metadata

from ..format_codes import formats_from_source_type
from .convert import to_docmeta

from dateutil.tz import tzutc

class DbDocMetadataService(DocMetadataService):
    """Class for arXiv document metadata service."""


    def __init__(self,
                 db) -> None:
        """Initialize the DB document metadata service."""
        self.db = db


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

        latest_version: DocMetadata = None
        this_version: DocMetadata = None
        version_history = list()
        # Need all versions to build version history
        all_versions = (Metadata.query
                        .filter(Metadata.paper_id == paper_id.id)
                        .order_by(Metadata.version)
                        )
        if not all_versions:
            raise AbsNotFoundException(paper_id.id)

        for version in all_versions:
            # Build version entry
            size_kilobytes = int(version.source_size / 1024 + .5)
            created_tz = version.created.replace(tzinfo=tzutc())
            entry = VersionEntry(version=version.version,
                                 raw='fromdb-no-raw',
                                 size_kilobytes=size_kilobytes,
                                 submitted_date=created_tz,
                                 source_type=version.source_format)
            version_history.append(entry)

            if paper_id.has_version and paper_id.version == version.version:
                this_version = to_docmeta(version, version_history)
                if version.is_current == 1:
                    latest_version = this_version
            if version.is_current == 1 and not latest_version:
                latest_version = to_docmeta(version, version_history)

        if not paper_id.has_version \
                or paper_id.version == latest_version.version:
            return replace(latest_version,
                           version_history=version_history,
                           is_definitive=True,
                           is_latest=True)
        elif paper_id.has_version and not this_version:
            if paper_id.is_old_id:
                raise AbsNotFoundException
            else:
                raise AbsVersionNotFoundException

        # Several fields need to reflect the latest version's data
        combined_version: DocMetadata = replace(
            this_version,
            version_history=version_history,
            categories=latest_version.categories,
            primary_category=latest_version.primary_category,
            secondary_categories=latest_version.secondary_categories,
            primary_archive=latest_version.primary_archive,
            primary_group=latest_version.primary_group,
            is_definitive=True,
            is_latest=False)
        return combined_version

    def get_dissemination_formats(self,
                                  docmeta: DocMetadata,
                                  format_pref: Optional[str] = None,
                                  add_sciencewise: bool = False) -> List[str]:
        """Get a list of formats that can be disseminated for this DocMetadata.

        THIS ONLY CHECK THE source type on the doc metadata.

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
        # version = docmeta.version
        # format_code = docmeta.version_history[version - 1].source_type.code

        # # TODO cache flag?
        # cache_flag = False
        # # cached_ps_file_path = cache.get_cache_file_path(docmeta, 'ps')
        # # if cached_ps_file_path \
        # #    and os.path.getsize(cached_ps_file_path) == 0 \
        # #    and source_file_path \
        # #    and os.path.getmtime(source_file_path) \
        # #    < os.path.getmtime(cached_ps_file_path):
        # #     cache_flag = True

        # return formats_from_source_type(format_code,
        #                                 format_pref,
        #                                 cache_flag,
        #                                 add_sciencewise)
        return []

    def get_ancillary_files(self, docmeta: DocMetadata) \
            -> List[Dict]:
        """Get list of ancillary file names and sizes."""
        # TODO implement get_ancillary_files
        return []
