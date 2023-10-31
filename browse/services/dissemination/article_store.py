"""Functions related to articles.

These are focused on using the GS bucket abs and source files."""

import logging
import re
from collections.abc import Callable
from typing import Dict, List, Literal, Optional, Tuple, Union, Iterable

from browse.domain.identifier import Identifier
from arxiv.legacy.papers.dissemination.reasons import FORMATS
from browse.domain import fileformat
from browse.domain.metadata import DocMetadata, VersionEntry
from browse.services.documents.base_documents import (
    AbsDeletedException, AbsNotFoundException, AbsVersionNotFoundException,
    DocMetadataService)
from browse.services.documents.config.deleted_papers import DELETED_PAPERS

from browse.services.documents.format_codes import (
    formats_from_source_file_name, formats_from_source_flag)
from browse.services.key_patterns import (abs_path_current_parent,
                                          abs_path_orig_parent,
                                          current_pdf_path, previous_pdf_path,
                                          ps_cache_pdf_path,
                                          current_ps_path, previous_ps_path,
                                          ps_cache_ps_path, ps_cache_html_path)
from browse.services.object_store import ObjectStore
from browse.services.object_store.fileobj import FileObj, FileFromTar

from .source_store import SourceStore
from .ancillary_files import list_ancillary_files

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


FormatHandlerReturn = Union[Conditions, FileObj]

FHANDLER = Callable[[Identifier, DocMetadata, VersionEntry],
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


Acceptable_Format_Requests = Union[fileformat.FileFormat, Literal["e-print"]]
"""Possible formats to request from the `ArticleStore`.

The format `e-print` is a reqeust to get the article's original source data.
"""

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
            -> Union[Conditions, Tuple[FileObj, fileformat.FileFormat, DocMetadata, VersionEntry],Tuple[List[FileObj], fileformat.FileFormat, DocMetadata, VersionEntry]]:
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
        fileobj = handler_fn(arxiv_id, docmeta, version)
        if not fileobj:
            return "UNAVAILABLE"
        if isinstance(fileobj, FileObj):
            return (fileobj, self.sourcestore.get_src_format(docmeta, fileobj), docmeta, version)
        if isinstance(fileobj, Iterable): #html requests return an iterable of files in the folder
            return (fileobj, format, docmeta, version)
        else:
            return fileobj

    def get_dissemination_formats(self,
                                  docmeta: DocMetadata,
                                  format_pref: Optional[str] = None,
                                  add_sciencewise: bool = False,
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
        add_sciencewise : bool
            Specify whether to include 'sciencewise_pdf' format in list.
        src_file: Optional[FileObj]
            What src file to use in the format check. This will be
            looked up if it is `None`

        Returns
        -------
        List[str]
            A list of format strings.
        """
        formats: List[str] = []

        # first, get possible list of formats based on available source file
        if src_file is None:
            src_file = self.sourcestore.get_src(docmeta.arxiv_identifier, docmeta)

        source_file_formats: List[str] = []
        if src_file is not None:
            source_file_formats = \
                formats_from_source_file_name(src_file.name)
        if source_file_formats:
            formats.extend(source_file_formats)

            if add_sciencewise:
                if formats and formats[-1] == 'other':
                    formats.insert(-1, 'sciencewise_pdf')
                else:
                    formats.append('sciencewise_pdf')
        else:
            # check source type from metadata, with consideration of
            # user format preference and cache
            version = docmeta.version
            format_code = docmeta.version_history[version - 1].source_flag.code
            cached_ps_file = self.dissemination(fileformat.ps, docmeta.arxiv_identifier, docmeta)
            cache_flag = bool(cached_ps_file and isinstance(cached_ps_file, FileObj) \
                and cached_ps_file.size == 0 \
                and src_file \
                and src_file.updated < cached_ps_file.updated)
            source_type_formats = formats_from_source_flag(format_code,
                                                           format_pref,
                                                           cache_flag,
                                                           add_sciencewise)
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
        if ver and not ver.is_withdrawn:
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
        else:
            # try from the /orig with version number for a pdf only paper
            pdf_file=self.objstore.to_obj(previous_pdf_path(arxiv_id))
            if pdf_file.exists():
                return pdf_file

        if not self.sourcestore.source_exists(arxiv_id, docmeta):
            return "NO_SOURCE"

        logger.debug("No PDF found for %s, source exists and is not WDR, tried %s", arxiv_id.idv,
                     [str(ps_cache_pdf), str(pdf_file)])
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

        # if docmeta.source_format == 'html':
        #     #TODO Mark set src to the correct source for native html documents. use _pdf as a model. specific file name stuff goes in key_patterns.py
        #     pass
        # else:
        #     #TODO Mark set src to the correct source for latexml documents. use _pdf as a model. specific file name stuff goes in key_patterns.py
        #     pass
        path=ps_cache_html_path(arxiv_id, version.version)
        file=self.objstore.list(path)
        file_list=list(file)
    
        if len(file_list) >0:
            return file_list
        else:
            return "NO_SOURCE"
        #src = self.sourcestore.get_src(arxiv_id, docmeta) # i think works for native html originally
        
        return src if src is not None else "NO_SOURCE"