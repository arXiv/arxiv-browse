"""Functions related to articles.

These are focused on using the GS bucket abs and source files."""
import http
import logging
import re
import time
import typing
from collections.abc import Callable
from typing import Dict, List, Literal, Optional, Tuple, Union
from urllib.parse import urlparse

import requests

from arxiv.identifier import Identifier
from arxiv.legacy.papers.dissemination.reasons import FORMATS
from browse.domain import fileformat
from arxiv.document.metadata import DocMetadata, VersionEntry
from arxiv.document.exceptions import (
    AbsDeletedException, AbsNotFoundException, AbsVersionNotFoundException)
from browse.services.documents.base_documents import DocMetadataService
from browse.services.documents.config.deleted_papers import DELETED_PAPERS
from browse.services.object_store.object_store_gs import GsObjectStore
from browse.services.documents.format_codes import (
    formats_from_source_file_name, formats_from_source_flag)
from browse.services.key_patterns import (abs_path_current_parent,
                                          abs_path_orig_parent,
                                          current_pdf_path, previous_pdf_path,
                                          ps_cache_pdf_path,
                                          current_ps_path, previous_ps_path,
                                          ps_cache_ps_path, ps_cache_html_path, latexml_html_path)
from browse.services.object_store import ObjectStore
from browse.services.object_store.fileobj import FileObj, FileDoesNotExist
from .source_store import SourceStore
from .ancillary_files import list_ancillary_files
from google.cloud import storage
from flask import current_app

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
            "UNAVAILABLE",  # Where the PDF unexpectedly does not exist
            "NOT_PDF",  # format that doens't serve a pdf
            "NO_HTML" #not native HTML, no HTML conversion available
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

def from_genpdf_location(location: str) -> typing.Tuple[str, str]:
    """Translates the genpdf-api redirect location for the genpdf object store.
    returns the bucket name and key as a tuple if it is a gcp bucket.
    """
    uri = urlparse(location)
    if uri.scheme == "gs":
        return uri.netloc, uri.path if uri.path[0] != '/' else uri.path[1:]
    return ("", uri.path)

def is_genpdf_able(_arxiv_id: Identifier) -> bool:
    """Is genpdf api available for this arxiv_id?"""

    return bool(current_app.config.get("GENPDF_API_URL"))


Acceptable_Format_Requests = Union[fileformat.FileFormat, Literal["e-print"]]
"""Possible formats to request from the `ArticleStore`.

The format `e-print` is a reqeust to get the article's original source data.
"""

class ArticleStore():
    def __init__(self,
                 metaservice: DocMetadataService,
                 objstore: ObjectStore,
                 genpdf_store: ObjectStore,
                 reasons: Callable[[str, FORMATS], Optional[str]] = _unset_reasons,
                 is_deleted: Callable[[str], Optional[str]] = _is_deleted
                 ):
        self.metadataservice = metaservice
        self.objstore: ObjectStore = objstore
        self.genpdf_store: ObjectStore = genpdf_store
        self.reasons = reasons
        self.is_deleted = is_deleted
        self.sourcestore = SourceStore(self.objstore)

        self.format_handlers: Dict[Acceptable_Format_Requests, FHANDLER] = {
            fileformat.pdf: self._pdf,
            "e-print": self._e_print,
            fileformat.ps: self._ps,
            fileformat.html: self._html
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
                      format: Acceptable_Format_Requests,
                      arxiv_id: Identifier,
                      docmeta: Optional[DocMetadata] = None) \
            -> Union[Conditions, Tuple[Union[FileObj,List[FileObj]], fileformat.FileFormat, DocMetadata, VersionEntry]]:
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

        handler_fn = self.format_handlers[format]
        fileobj = handler_fn(arxiv_id, docmeta, version)
        if not fileobj:
            return "UNAVAILABLE"
        if isinstance(fileobj, FileObj):
            return (fileobj, self.sourcestore.get_src_format(docmeta, fileobj), docmeta, version) #TODO I dont think we want to always return the source format
        if isinstance(fileobj, List): #html requests return an iterable of files in the folder
            return (fileobj, format, docmeta, version) #type: ignore
        else:
            return fileobj

    def get_dissemination_formats(self,
                                  docmeta: DocMetadata,
                                  format_pref: Optional[str] = None,
                                  src_file: Optional[FileObj] = None
                                  ) -> List[str]:
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
        format_pref : str
            The format preference string.
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
            src_file = self.sourcestore.get_src(docmeta.arxiv_identifier, docmeta)

        source_file_formats: List[str] = []
        if src_file is not None:
            source_file_formats = \
                formats_from_source_file_name(src_file.name)

        if source_file_formats:
            formats.extend(source_file_formats)
        else:
            # check source type from metadata, with consideration of
            # user format preference and cache
            cached_ps_file = self.dissemination(fileformat.ps, docmeta.arxiv_identifier, docmeta)
            cache_flag = bool(cached_ps_file and isinstance(cached_ps_file, FileObj) \
                and cached_ps_file.size == 0 \
                and src_file \
                and src_file.updated < cached_ps_file.updated)

            src_flag = docmeta.get_requested_version().source_flag
            src_flag_code = '' if src_flag is None or src_flag.code is None else src_flag.code

            source_type_formats = formats_from_source_flag(src_flag_code,
                                                           format_pref,
                                                           cache_flag)
            if source_type_formats:
                formats.extend(source_type_formats)

        return formats

    def get_all_paper_formats(self, docmeta: DocMetadata) -> List[str]:
        """Returns the list of all formats that the given paper can
        be disseminated in. Takes sources format and knows what
        transformations can be applied.

        Does not include sub-formats (like types of ps) and does
        not pay attention to user preference settings.
        """
        src_fmt: str = self.sourcestore.get_src_format(docmeta).id
        formats: List[str] = []
        if (src_fmt == 'ps'):
            formats.extend([src_fmt, 'pdf'])
        elif (src_fmt == 'pdf' or src_fmt == 'html'):
            formats.append(src_fmt)
        elif (src_fmt == 'dvi'):
            formats.extend([src_fmt, 'tex-ps', 'pdf'])
        elif (src_fmt == 'tex'):
            formats.extend(['dvi', 'tex-ps', 'pdf'])
        elif (src_fmt == 'pdftex'):
            formats.append('pdf')
        elif (src_fmt == 'docx' or src_fmt == 'odf'):
            formats.extend(['pdf', src_fmt])

        ver = docmeta.get_version()
        if ver and not ver.withdrawn_or_ignore:
            formats.append('src')

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
        return self.sourcestore.get_ancillary_files(docmeta)

    def _pdf(self, arxiv_id: Identifier, docmeta: DocMetadata, version: VersionEntry) -> FormatHandlerReturn:
        """Handles getting the `FielObj` for a PDF request."""
        if version.source_flag.cannot_pdf:
            return "NOT_PDF"

        res = self.reasons(arxiv_id.idv, 'pdf')
        if res:
            return CannotBuildPdf(res)

        ps_cache_pdf = self.objstore.to_obj(ps_cache_pdf_path(arxiv_id, version.version))
        if ps_cache_pdf.exists():
            return ps_cache_pdf

        if not arxiv_id.has_version or arxiv_id.version == docmeta.highest_version():
            # try from the /ftp with no number for current ver of pdf only paper
            pdf_file = self.objstore.to_obj(current_pdf_path(arxiv_id))
            if pdf_file.exists():
                return pdf_file
            if is_genpdf_able(arxiv_id):
                return self._genpdf(arxiv_id, docmeta, version)
        else:
            # try from the /orig with version number for a pdf only paper
            pdf_file=self.objstore.to_obj(previous_pdf_path(arxiv_id))
            if pdf_file.exists():
                return pdf_file
            if is_genpdf_able(arxiv_id):
                return self._genpdf(arxiv_id, docmeta, version)

        if not self.sourcestore.source_exists(arxiv_id, docmeta):
            return "NO_SOURCE"

        logger.debug("No PDF found for %s, source exists and is not WDR, tried %s", arxiv_id.idv,
                     [str(ps_cache_pdf), str(pdf_file)])
        return "UNAVAILABLE"

    def _genpdf(self, arxiv_id: Identifier, docmeta: DocMetadata, version: VersionEntry) -> FormatHandlerReturn:
        """Gets a PDF from the genpdf-api."""
        api = current_app.config.get("GENPDF_API_URL")
        if not api:
            return "UNAVAILABLE"
        # requests.get() cannod have timeout <= 0
        timeout = max(1, current_app.config.get("GENPDF_API_TIMEOUT", 60))
        url = f"{api}/pdf/{arxiv_id.ids}?timeout={timeout}&download=false"
        logger.debug("genpdf-api request(timeout=%d): %s ", timeout, url)
        t_start = time.perf_counter()
        for _ in range(3):  # cannot be infinite loop but 500s are common when the cloud run's service is starting up.
            try:
                response: requests.Response = requests.get(url, timeout=timeout, allow_redirects=False)
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
                if not self.sourcestore.source_exists(arxiv_id, docmeta):
                    return "NO_SOURCE"
                logger.error("genpdf-api returned 404")
                return "UNAVAILABLE"

            case _:  # catch all
                logger.error("genpdf-api returned %s", str(response.status_code))
                if not self.sourcestore.source_exists(arxiv_id, docmeta):
                    return "NO_SOURCE"
                return "UNAVAILABLE"

    def _ps(self, arxiv_id: Identifier, docmeta: DocMetadata, version: VersionEntry) -> FormatHandlerReturn:
        res = self.reasons(arxiv_id.idv, 'ps')
        if res:
            return CannotBuildPdf(res)

        cached_ps = self.objstore.to_obj(ps_cache_ps_path(arxiv_id, version.version))
        if cached_ps:
            return cached_ps

        if not arxiv_id.has_version or arxiv_id.version == docmeta.highest_version():
            # try from the /ftp with no number for current ver of ps only paper
            ps_file = self.objstore.to_obj(current_ps_path(arxiv_id))
            if ps_file.exists():
                return ps_file
        else:
            # try from the /orig with version number for a ps only paper
            ps_file=self.objstore.to_obj(previous_ps_path(arxiv_id))
            if ps_file.exists():
                return ps_file

        if not self.sourcestore.source_exists(arxiv_id, docmeta):
            return "NO_SOURCE"

        logger.debug("No PS found for %s, source exists and is not WDR, tried %s", arxiv_id.idv,
                     [str(cached_ps), str(ps_file)])
        return "UNAVAILABLE"

    def _e_print(self,
                 arxiv_id: Identifier,
                 docmeta: DocMetadata, version: VersionEntry) -> FormatHandlerReturn:
        """Gets the src as submitted for the arxiv_id.

        Lists through possible extensions to find source file.

        Returns `FileObj` if found, `None` if not."""
        src = self.sourcestore.get_src(arxiv_id, docmeta)
        return src if src is not None else "NO_SOURCE"


    def _html(self, arxiv_id: Identifier, docmeta: DocMetadata, version: VersionEntry) -> FormatHandlerReturn:
        """Gets the html src as submitted for the arxiv_id. Returns `FileObj` if found, `None` if not."""
        if docmeta.source_format == 'html': # paper source is html
            path = ps_cache_html_path(arxiv_id, version.version)
            if arxiv_id.extra:  # requesting a specific file
                return self.objstore.to_obj(path + arxiv_id.extra)
            else:  # requesting list of files
                file_list=list(self.objstore.list(path))
                return file_list if file_list else "NO_SOURCE"
        else: # latex to html
            # TODO it may be expensive to recreate the GS Client each time
            latex_obj_store = GsObjectStore(storage.Client().bucket(current_app.config['LATEXML_BUCKET']))
            file=latex_obj_store.to_obj(latexml_html_path(arxiv_id, version.version))
            return file if file.exists() else "NO_HTML"
