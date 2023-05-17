"""Functions related to articles.

These are focused on using the GS bucket abs and source files."""

import logging
import re
from collections.abc import Callable
from typing import Dict, List, Literal, Optional, Tuple, Union

from arxiv.identifier import Identifier
from arxiv.legacy.papers.dissemination.reasons import FORMATS
from browse.domain.metadata import DocMetadata, VersionEntry
from browse.domain import fileformat

from browse.services.documents.base_documents import (
    AbsDeletedException, AbsNotFoundException, AbsVersionNotFoundException,
    DocMetadataService)
from browse.services.documents.config.deleted_papers import DELETED_PAPERS

from browse.services.key_patterns import (abs_path_current_parent,
                           abs_path_orig_parent,
                           current_pdf_path, previous_pdf_path,
                           ps_cache_pdf_path)
from browse.services.object_store import ObjectStore
from browse.services.object_store.fileobj import FileObj

logger = logging.getLogger(__file__)


class Deleted():
    def __init__(self, msg: str):
        self.msg = msg


class CannotBuildPdf():
    def __init__(self, msg: str):
        self.msg = msg


Conditions = Union[
    Literal["WITHDRAWN",  # Where the version is a WDR
            "ARTICLE_NOT_FOUND",  # Where there is no article
            "VERSION_NOT_FOUND",  # Where article exists but not version
            "NO_SOURCE",  # Article and version exists but no source exists
            "UNAVAIABLE",  # Where the PDF unexpectedly does not exist
            "NOT_PDF",  # format that doens't serve a pdf
            ],
    Deleted,
    CannotBuildPdf]

AbsConditions = Union[Literal["ARTICLE_NOT_FOUND",
                              "VERSION_NOT_FOUND",
                              "NO_ID"],
                      Deleted]


FormatHandlerReturn = Union[Conditions, FileObj]

FHANDLER = Callable[[fileformat.FileFormat, Identifier, DocMetadata, VersionEntry],
                    FormatHandlerReturn]
"""Type format handler should return."""


cannot_gen_pdf_regex = re.compile('H|O|X', re.IGNORECASE)
"""Regex for use aginst source_type for formats that cannot serve a PDF,
these are HTML, ODF and DOCX"""

RE_DATE_COMPONENTS = re.compile(
    r'^Date\s*(?::|\(revised\s*(?P<version>.*?)\):)\s*(?P<date>.*?)'
    r'(?:\s+\((?P<size_kilobytes>\d+)kb,?(?P<source_type>.*)\))?$')

v_regex = re.compile(r'.*v(\d+)')

_src_regex = re.compile(r'.*(\.tar\.gz|\.pdf|\.ps\.gz|\.gz|\.div\.gz|\.html\.gz)')

def _path_to_version(path: FileObj) -> int:
    mtch = v_regex.search(path.name)
    if mtch:
        return int(mtch.group(1))
    else:
        return 0


def _is_deleted(id: str) -> Optional[str]:
    """Checks if an id is for a deleted paper.

    Expects a ID without a version such as quant-ph/0411165 or 0901.4014 or 1203.23434.
    """
    if not id:
        return None
    else:
        return DELETED_PAPERS.get(id, None)


def _unset_reasons(str: str, fmt:FORMATS) -> Optional[str]:
    pass


class ArticleStore():
    def __init__(self,
                 metaservice: DocMetadataService,
                 objstore: ObjectStore,
                 reasons: Callable[[str, FORMATS], Optional[str]] = _unset_reasons,
                 is_deleted: Callable[[str], Optional[str]] = _is_deleted
                 ):
        self.metadataservice = metaservice
        self.objstore: ObjectStore = objstore
        self.reasons = reasons
        self.is_deleted = is_deleted

        self.format_handlers: Dict[fileformat.FileFormat, FHANDLER] = {
            #            formats.src_orig: self._src_orig,
            #            formats.src_targz: self._src_targz,
            fileformat.pdf: self._pdf,
            #            formats.ps: self._ps,
            #            formats.htmlgz: self._htmlgz,
        }

    def status(self) -> Tuple[Literal["GOOD", "BAD"], str]:
        """Indicates the health of the service.

        Returns a tuple of either ("GOOD",'') or ("BAD","Some human readable message")

        The human readable message might be displayed publicly so do
        not put sensitive information in it.
        """
        stats: List[Tuple[str, Literal["GOOD", "BAD"], str]] = []
        osstat, osmsg = self.objstore.status()
        stats.append((str(type(self.objstore)), osstat, osmsg))

        try:
            self.reasons('bogusid', 'pdf')
            stats.append(('pdf_reasons', 'GOOD', ''))
        except Exception as ex:
            stats.append(('pdf_reasons', 'BAD', str(ex)))

        try:
            self.is_deleted('2202.00001')
            stats.append(('is_deleted', 'GOOD', ''))
        except Exception as ex:
            stats.append(('is_deleted', 'BAD', str(ex)))

        if all([stat[1] == 'GOOD' for stat in stats]):
            return ('GOOD', '')

        msgs = [f"{styp} bad due to \"{msg}\"" for styp, stat, msg in stats
                if stat != 'GOOD']
        return ('BAD', ' and '.join(msgs))

    def dissemination(self,
                      format: fileformat.FileFormat,
                      arxiv_id: Identifier,
                      docmeta: Optional[DocMetadata] = None) \
            -> Union[Conditions, FileObj]:
        """Gets a `FileObj` for a `Format` for an `arxiv_id`.

        If `doc` is not passed it will be looked up.

        If the `FileObj` is not available for the `arxiv_id` a `Conditions`
        will be returned.
        """
        if not format or not arxiv_id:
            raise ValueError("Must pass a format and arxiv_id")
        if format not in self.format_handlers:
            raise ValueError(f"Format {format.id} not in format handlers")

        deleted = self.is_deleted(arxiv_id.id)
        if deleted:
            return Deleted(deleted)

        try:
            if docmeta is None:
                docmeta = self.metadataservice.get_abs(arxiv_id.id)
        # Not excpeting AbsParsingException or AbsException since that is bad
        # data that we want to know about and fix.
        except AbsNotFoundException:
            return "ARTICLE_NOT_FOUND"
        except AbsVersionNotFoundException:
            return "VERSION_NOT_FOUND"
        except AbsDeletedException:
            return Deleted('')

        if arxiv_id.has_version:
            version = docmeta.get_version(arxiv_id.version)
        else:
            version = docmeta.get_version(docmeta.highest_version())
        if not version:
            return "VERSION_NOT_FOUND"

        if version.is_withdrawn:
            return "WITHDRAWN"

        handler_fn = self.format_handlers[format]
        fileobj = handler_fn(format, arxiv_id, docmeta, version)
        if not fileobj:
            return "UNAVAIABLE"
        else:
            return fileobj

    def _source_exists(self, arxiv_id: Identifier, doc: DocMetadata) -> bool:
        """Does the source exist for this `arxiv_id` and `doc`?"""
        if not arxiv_id.has_version or arxiv_id.version == doc.highest_version():
            parent = abs_path_current_parent(arxiv_id)
        else:
            parent = abs_path_orig_parent(arxiv_id)

        pattern = parent + '/' + arxiv_id.filename
        items = list(self.objstore.list(pattern))
        if len(items) > 1000:
            logger.warning("list of matches to is_withdrawn was %d, unexpectedly large", len(items))
            return True  # strange but don't get into handling a huge list

        # does any obj key match with any extension?
        return any(map(lambda item: _src_regex.match(item.name), items))

    def _src_orig(self, format: fileformat.FileFormat, arxiv_id: Identifier, docmeta: DocMetadata) -> FormatHandlerReturn:

        raise Exception("Not implemented")

    def _src_targz(self, format: fileformat.FileFormat, arxiv_id: Identifier, docmeta: DocMetadata) -> FormatHandlerReturn:
        raise Exception("Not implemented")

    def _pdf(self, format: fileformat.FileFormat, arxiv_id: Identifier, docmeta: DocMetadata, version: VersionEntry) -> FormatHandlerReturn:
        """Handles getting the `FielObj` for a PDF request."""
        if version.source_type.cannot_pdf:
            return "NOT_PDF"
        if format.id != 'pdf':
            return "NOT_PDF"

        res = self.reasons(arxiv_id.idv, format.id)
        if res:
            return CannotBuildPdf(res)

        ps_cache_pdf = self.objstore.to_obj(ps_cache_pdf_path(format.id, arxiv_id, version.version))  # type: ignore
        if ps_cache_pdf.exists():
            return ps_cache_pdf

        if not arxiv_id.has_version or arxiv_id.version == docmeta.highest_version():
            # try from the /ftp with no number for current ver of pdf only paper
            pdf_file = self.objstore.to_obj(current_pdf_path(arxiv_id))
            if pdf_file.exists():
                return pdf_file
        else:
            # try from the /orig with version number for a pdf only paper
            pdf_file=self.objstore.to_obj(previous_pdf_path(arxiv_id))
            if pdf_file.exists():
                return pdf_file

        if not self._source_exists(arxiv_id, docmeta):
            return "NO_SOURCE"

        logger.debug("No PDF found for %s, source exists and is not WDR, tried %s", arxiv_id.idv,
                     [str(ps_cache_pdf), str(pdf_file)])
        return "UNAVAIABLE"

    def _ps(self, format: fileformat.FileFormat, arxiv_id: Identifier, docmeta: DocMetadata) -> FormatHandlerReturn:
        raise Exception("Not implemented")

    def _htmlgz(self, format: fileformat.FileFormat, arxiv_id: Identifier, docmeta: DocMetadata) -> FormatHandlerReturn:
        raise Exception("Not implemented")
