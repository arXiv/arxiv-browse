"""Functions related to articles.

These are focused on using the GS bucket abs and source files."""
import http
import logging
import re
import time
from collections.abc import Callable
from typing import Dict, List, Literal, Optional, Tuple, Union, get_args
from urllib.parse import urlparse

import requests
from arxiv.document.exceptions import (
    AbsDeletedException, AbsNotFoundException, AbsVersionNotFoundException)
from arxiv.document.metadata import DocMetadata, VersionEntry
from arxiv.files import FileObj, fileformat
from arxiv.files.key_patterns import (current_pdf_path, previous_pdf_path,
                                      ps_cache_pdf_path,
                                      current_ps_path, previous_ps_path,
                                      ps_cache_ps_path, ps_cache_html_path, latexml_html_path)
from arxiv.files.object_store import ObjectStore
from arxiv.formats import (
    formats_from_source_file_name, formats_from_source_flag)
from arxiv.identifier import Identifier
from arxiv.legacy.papers.dissemination.reasons import FORMATS, reasons, get_reasons_data
from flask import current_app
from gcp.service_auth.gcp_service_auth import GcpIdentityToken
from google.auth.exceptions import DefaultCredentialsError

from browse.services.documents.base_documents import DocMetadataService
from browse.services.documents.config.deleted_papers import DELETED_PAPERS
from .source_store import SourceStore

logger = logging.getLogger(__file__)


Acceptable_Format_Requests = Union[fileformat.FileFormat, Literal["e-print"]]
"""Possible formats to request from the `ArticleStore`.

The format `e-print` is a reqeust to get the article's original source data.
"""

class Deleted():
    def __init__(self, msg: str):
        self.msg = msg


class CannotBuildPdf():
    def __init__(self, msg: str, fmt: Acceptable_Format_Requests):
        self.msg = msg
        if isinstance(fmt, str):
            self.fmt = str(fmt)
        else:
            self.fmt = fmt.id


Conditions = Union[
    Literal["WITHDRAWN",  # Where the version is a WDR
            "ARTICLE_NOT_FOUND",  # Where there is no article
            "VERSION_NOT_FOUND",  # Where article exists but not version
            "NO_SOURCE",  # Article and version exists but no source exists
            "UNAVAILABLE",  # Where the PDF unexpectedly does not exist
            "NOT_PDF",  # format that doens't serve a pdf
            "NO_HTML", #not native HTML, no HTML conversion available
            "NOT_PUBLIC" #where the author has decided not to make the source of the paper public
            ],
    Deleted,
    CannotBuildPdf]
"""Return conditions for the result of `dissemination()`.

The intent of using a `Union` instead of raising exceptions is that they can be
type checked.
"""


AbsConditions = Union[Literal["ARTICLE_NOT_FOUND",
                              "VERSION_NOT_FOUND",
                              "NO_ID"],
                      Deleted]

FormatHandlerReturn = Union[Conditions, FileObj, List[FileObj]]

FHANDLER = Callable[[Identifier, DocMetadata, VersionEntry],
                    FormatHandlerReturn]
"""Type format handler should return."""

RE_DATE_COMPONENTS = re.compile(
    r'^Date\s*(?::|\(revised\s*(?P<version>.*?)\):)\s*(?P<date>.*?)'
    r'(?:\s+\((?P<size_kilobytes>\d+)kb,?(?P<source_type>.*)\))?$')

v_regex = re.compile(r'.*v(\d+)')

_src_regex = re.compile(r'.*(\.tar\.gz|\.pdf|\.ps\.gz|\.gz|\.div\.gz|\.html\.gz)')


MAX_ITEMS_IN_PATTERN_MATCH = 1000
"""This uses pattern matching on all the keys in an itmes directory. If
the number if items is very large the was probably a problem"""

def _path_to_version(path: FileObj) -> int:
    mtch = v_regex.search(path.name)
    if mtch:
        return int(mtch.group(1))
    else:
        return 0


def _is_deleted(arxiv_id: str) -> str:
    """Checks if an id is for a deleted paper.

    Expects an arxiv ID without a version such as quant-ph/0411165 or 0901.4014 or 1203.23434.
    """
    return arxiv_id and DELETED_PAPERS.get(arxiv_id, "")


def from_genpdf_location(location: str) -> Tuple[str, str]:
    """Translates the genpdf-api redirect location for the genpdf object store.
    returns the bucket name and key as a tuple if it is a gcp bucket.
    """
    uri = urlparse(location)
    if uri.scheme == "gs":
        return uri.netloc, uri.path if uri.path[0] != '/' else uri.path[1:]
    return ("", uri.path)

def is_genpdf_able(_arxiv_id: Identifier) -> bool:
    """Is genpdf api available for this arxiv_id?"""

    return bool(current_app.config.get("GENPDF_API_URL")) and bool(current_app.config.get("GENPDF_SERVICE_URL"))


class ArticleStore():
    def __init__(self,
                 metaservice: DocMetadataService,
                 cache_store: ObjectStore,
                 src_store: ObjectStore,
                 genpdf_store: ObjectStore,
                 latexml_store: ObjectStore,
                 reasons_data: Dict[str, str] = {},
                 is_deleted: Callable[[str], str] = _is_deleted,
                 ):
        """

        Parameters
        ----------
        metaservice: A DocMetadataService instance to get metadata about papers.

        cache_store: cache of PDF, PS and HTML

        src_store: store for PDF from papers with PDF only source.

        genpdf_store: ObjectStore setup to point to the genpdf storage.

        latexml_store: ObjectStore setup to point to the latexml storage.

        reasons_data: Dict of reasons for lack of specific paper's PDFs.

        is_deleted: Dict of Paper ids that are deleted.
        """
        self.metadataservice = metaservice
        self.cache_store: ObjectStore = cache_store
        self.genpdf_store: ObjectStore = genpdf_store
        self.latexml_store: ObjectStore = latexml_store
        self.is_deleted = is_deleted
        self.source_store = SourceStore(src_store)
        self.reasons_data = reasons_data

        self.format_handlers: Dict[Acceptable_Format_Requests, FHANDLER] = {
            fileformat.pdf: self._pdf,
            "e-print": self._e_print,
            fileformat.ps: self._ps,
            fileformat.html: self._html
        }

        self.service_identity = None
        genpdf_api = current_app.config.get("GENPDF_API_URL")
        genpdf_api
        genpdf_service_url = current_app.config.get("GENPDF_SERVICE_URL")
        if genpdf_api and genpdf_service_url:
            try:
                self.service_identity = GcpIdentityToken(genpdf_service_url, logger=logger)
            except DefaultCredentialsError:
                logger.error("No default SA credentials. If this is development, try setting GOOGLE_APPLICATION_CREDENTIALS")

    def status(self) -> Tuple[Literal["GOOD", "BAD"], str]:
        """Indicates the health of the service.

        Returns a tuple of either ("GOOD",'') or ("BAD","Some human readable message")

        The human readable message might be displayed publicly so do
        not put sensitive information in it.
        """
        
        stats: List[Tuple[str, Literal["GOOD", "BAD"], str]] = []
        osstat, osmsg = self.cache_store.status()
        stats.append((str(type(self.cache_store)), osstat, osmsg))

        try:
            reasons(self.reasons_data, 'bogusid', 'pdf')
            stats.append(('pdf_reasons', 'GOOD', ''))
        except Exception as ex:
            stats.append(('pdf_reasons', 'BAD', str(ex)))

        try:
            self.is_deleted('2202.00001')
            stats.append(('is_deleted', 'GOOD', ''))
        except Exception as ex:
            stats.append(('is_deleted', 'BAD', str(ex)))

        if all([stat[1] == 'GOOD' for stat in stats]):
            return 'GOOD', ''

        msgs = [f"{styp} bad due to \"{msg}\"" for styp, stat, msg in stats
                if stat != 'GOOD']
        return 'BAD', ' and '.join(msgs)

    def get_source(self, arxiv_id: Identifier, docmeta: Optional[DocMetadata] = None) \
            -> Union[Conditions, Tuple[Union[FileObj,List[FileObj]], DocMetadata, VersionEntry]]:
        """Gets the source for a paper_id and version."""
        return self.dissemination("e-print", arxiv_id, docmeta)

    def dissemination(self,
                      format: Acceptable_Format_Requests,
                      arxiv_id: Identifier,
                      docmeta: Optional[DocMetadata] = None) \
            -> Union[Conditions, Tuple[Union[FileObj,List[FileObj]], DocMetadata, VersionEntry]]:
        """Gets a `FileObj` for a `Format` for an `arxiv_id`.

        If `docmeta` is not passed it will be looked up. When the `docmeta` is
        not passed this method will check for the existance of the article and
        version. If they are not found a `Condition` will be returned,
        `AbsVersionNotFoundException` and `AbsNotFoundException` will not be
        thrown.

        If the `FileObj` is not available for the `arxiv_id` a `Conditions` will
        be returned. The intent of using `Conditions` instead of raising
        exceptions is that they can be type checked.

        `path` is additional data for html and anc requests.
        """
        
        if not format or not arxiv_id:
            raise ValueError("Must pass a format and arxiv_id")
        if format != "e-prints" and format not in self.format_handlers:
            raise ValueError(f"Format {format} not in format handlers")

        deleted = self.is_deleted(arxiv_id.id)
        if deleted:
            return Deleted(deleted)

        if reason := self.reasons(arxiv_id, format):
            return CannotBuildPdf(reason, format)

        try:
            if docmeta is None:
                docmeta = self.metadataservice.get_abs(arxiv_id.id)
        # Not excepting AbsParsingException or AbsException since that is bad data that we want to know about and fix.
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

        if version.withdrawn_or_ignore:
            return "WITHDRAWN"
       
        if version.source_flag.source_encrypted and format!=fileformat.pdf and format!=fileformat.html:
            return "NOT_PUBLIC"

        handler_fn = self.format_handlers[format]
        fileobj = handler_fn(arxiv_id, docmeta, version)
        if not fileobj:
            return "UNAVAILABLE"
        if isinstance(fileobj, FileObj):
            return (fileobj, docmeta, version) 
        if isinstance(fileobj, List): #html requests return an iterable of files in the folder
            return (fileobj, docmeta, version)
        else:
            return fileobj

    def get_dissemination_formats(self, docmeta: DocMetadata, src_file: Optional[FileObj] = None) -> List[str]:
        """Get a list of possible formats for a `DocMetadata`.

        Several checks are performed to determine available formats:
            1. a check for source files with specific, valid file name
               extensions (i.e. for a subset of the allowed source file name
               extensions, the dissemintation formats are predictable)
            2. if formats cannot be inferred from the source file, inspect the
               source type in the document metadata.

        Format names are strings. These include 'src', 'pdf', 'ps', 'html',
        'pdfonly', 'other', 'dvi', 'ps(400)', 'ps(600)', 'nops'.

        Parameters
        ----------
        docmeta : :class:`DocMetadata`
        src_file: Optional[FileObj]
            What src file to use in the format check. This will be
            looked up if it is `None`

        Returns
        -------
        List[str]
            A list of format strings.
        """
        formats: List[str] = []
        version: VersionEntry = docmeta.get_requested_version()
        if version.withdrawn_or_ignore or version.size_kilobytes <= 0:
            return formats

        # first, get possible list of formats based on available source file
        if src_file is None:
            src_file = self.source_store.get_src_for_docmeta(docmeta.arxiv_identifier, docmeta)

        source_file_formats: List[str] = []
        if src_file is not None:
            source_file_formats = \
                formats_from_source_file_name(src_file.name)

        if source_file_formats:
            formats.extend(source_file_formats)
        else:
            # check source type from metadata
            src_flag = docmeta.get_requested_version().source_flag
            src_flag_code = '' if src_flag is None or src_flag.code is None else src_flag.code

            source_type_formats = formats_from_source_flag(src_flag_code)
            if source_type_formats:
                formats.extend(source_type_formats)

        return formats

    def get_ancillary_files(self, docmeta: DocMetadata) -> List[Dict]:
        """Get list of ancillary file names and sizes.

        Parameters
        ----------
        docmeta : DocMetadata
            DocMetadata to get the ancillary files for.

        Returns
        -------
        List[Dict]
            List of Dict where each dict is a file name and size.
        """
        return self.source_store.get_ancillary_files(docmeta)

    def _pdf(self, arxiv_id: Identifier, docmeta: DocMetadata, version: VersionEntry) -> FormatHandlerReturn:
        """Handles getting the `FielObj` for a PDF request."""
        if version.source_flag.cannot_pdf:
            return "NOT_PDF"

        ps_cache_pdf = self.cache_store.to_obj(ps_cache_pdf_path(arxiv_id, version.version))
        if ps_cache_pdf.exists():
            return ps_cache_pdf

        current = version.is_current or not arxiv_id.has_version or arxiv_id.version == docmeta.highest_version()
        pdf_file = self.source_store.get_src_pdf(arxiv_id, current)
        if pdf_file and pdf_file.exists():
            return pdf_file

        if is_genpdf_able(arxiv_id):
            return self._genpdf(arxiv_id, docmeta, version)

        if not self.source_store.source_exists(arxiv_id, docmeta):
            return "NO_SOURCE"

        logger.debug("No PDF found for %s, source exists and is not WDR, tried %s", arxiv_id.idv,
                     [str(ps_cache_pdf), str(pdf_file)])
        return "UNAVAILABLE"

    def _genpdf(self, arxiv_id: Identifier, docmeta: DocMetadata, version: VersionEntry) -> FormatHandlerReturn:
        """Gets a PDF from the genpdf-api."""
        genpdf_api = current_app.config.get("GENPDF_API_URL")
        if not genpdf_api:
            return "UNAVAILABLE"
        # requests.get() cannod have timeout <= 0
        timeout = max(1, current_app.config.get("GENPDF_API_TIMEOUT", 60))
        url = f"{genpdf_api}/pdf/{arxiv_id.ids}?timeout={timeout}&download=false"
        headers = {}
        if self.service_identity:
            try:
                headers["Authorization"] = f"Bearer {self.service_identity.token}"
            except Exception as exc:
                logger.warning("Acquiring auth token for genpdf failed. %s", str(exc), exc_info=True)
        logger.debug("genpdf-api request(timeout=%d): %s ", timeout, url)
        t_start = time.perf_counter()
        for _ in range(3):  # cannot be infinite loop but 500s are common when the cloud run's service is starting up.
            try:
                response: requests.Response = \
                    requests.get(url, timeout=timeout, allow_redirects=False, headers=headers)
                break
            except ConnectionError as _exc:
                logger.warning("The HTTP connection is reset. Retrying...")
                time.sleep(0.1) # just a fraction is enough
                continue
            except Exception as _exc:
                logger.warning("genpdf-api access failed", exc_info=True)
                return "UNAVAILABLE"
        t_end = time.perf_counter()
        logger.debug("genpdf-api responded in %f seconds", t_end - t_start)

        # Normal operation is a redirect to the bucket

        match response.status_code:
            case http.HTTPStatus.FOUND:
                bucket_url = response.headers.get('location')
                if not bucket_url:
                    logger.error("Redirect did not provide location")
                    return "UNAVAILABLE"
                _bucket_name, obj_key = from_genpdf_location(bucket_url)
                return self.genpdf_store.to_obj(obj_key)

            case http.HTTPStatus.OK:
                # Sadly, if you get 200, error out as this is not expected
                logger.error("genpdf-api should not return 200. Check URL and turn off download")
                raise NotImplementedError("Cannot support getting PDF")

            case http.HTTPStatus.REQUEST_TIMEOUT:
                logger.error("genpdf-api request timed out: duration=%f", t_end - t_start)
                return "UNAVAILABLE"

            case http.HTTPStatus.NOT_FOUND:
                if not self.source_store.source_exists(arxiv_id, docmeta):
                    return "NO_SOURCE"
                logger.error("genpdf-api returned 404")
                return "UNAVAILABLE"

            case _:  # catch all
                logger.error("genpdf-api returned %s", str(response.status_code))
                if not self.source_store.source_exists(arxiv_id, docmeta):
                    return "NO_SOURCE"
                return "UNAVAILABLE"

    def _ps(self, arxiv_id: Identifier, docmeta: DocMetadata, version: VersionEntry) -> FormatHandlerReturn:
        cached_ps = self.cache_store.to_obj(ps_cache_ps_path(arxiv_id, version.version))
        if cached_ps:
            return cached_ps

        current = version.is_current or not arxiv_id.has_version or arxiv_id.version == docmeta.highest_version()
        src_ps = self.source_store.get_src_ps(arxiv_id, current)
        if src_ps and src_ps.exists():
            return src_ps

        if not self.source_store.source_exists(arxiv_id, docmeta):
            return "NO_SOURCE"

        logger.debug("No PS found for %s, source exists and is not WDR", arxiv_id.idv)
        return "UNAVAILABLE"

    def _e_print(self,
                 arxiv_id: Identifier,
                 docmeta: DocMetadata, version: VersionEntry) -> FormatHandlerReturn:
        """Gets the src as submitted for the arxiv_id.

        Lists through possible extensions to find source file.

        Returns `FileObj` if found, `None` if not."""
        src = self.source_store.get_src_for_docmeta(arxiv_id, docmeta)
        return src if src is not None else "NO_SOURCE"


    def _html(self, arxiv_id: Identifier, docmeta: DocMetadata, version: VersionEntry) -> FormatHandlerReturn:
        """Gets the html src as submitted for the arxiv_id. Returns `FileObj` if found, `None` if not."""
        if docmeta.source_format == 'html' or version.source_flag.html: # paper source is html
            # note: the preprocessed html is expected to exist in the ps_cache
            path = ps_cache_html_path(arxiv_id, version.version)
            if arxiv_id.extra:  # requesting a specific file
                return self.cache_store.to_obj(path + arxiv_id.extra.removeprefix("/"))
            else:  # requesting list of files
                file_list = list(self.cache_store.list(path))
                return file_list if file_list else "NO_SOURCE"
        else: # latex to html
            file = self.latexml_store.to_obj(latexml_html_path(arxiv_id, version.version))
            return file if (file is not None and file.exists()) else "NO_HTML"

    def reasons(self, arxiv_id: Identifier, format: Acceptable_Format_Requests) -> Optional[str]:
        if not arxiv_id or not format or isinstance(format, str):
            return None
        fmt = format.id
        if fmt in get_args(FORMATS):
            return reasons(self.reasons_data, arxiv_id.idv, fmt)  # type: ignore
        else:
            return None
        
