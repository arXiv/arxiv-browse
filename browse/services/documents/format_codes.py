"""Shared functions that support determination of dissemination formats."""
import re
from typing import List, Optional, Union

import logging
import tarfile
from operator import itemgetter
from tarfile import CompressionError, ReadError
from typing import Dict

from browse.domain.version import SourceFlag
from browse.services.anypath import APath

logger = logging.getLogger(__name__)

# List of tuples containing the valid source file name extensions and their
# corresponding dissemination formats.
# There are minor performance implications in the ordering when doing
# filesystem lookups, so the ordering here should be preserved.
VALID_SOURCE_EXTENSIONS = [
    ('.tar.gz', None),
    ('.pdf', ['pdfonly']),
    ('.ps.gz', ['pdf', 'ps']),
    ('.gz', None),
    ('.dvi.gz', None),
    ('.html.gz', ['html'])
]
"""List of tuples containing the valid source file name extensions and
their corresponding dissemintation formats.  There are minor
performance implications in the ordering when doing filesystem
lookups, so the ordering here should be preserved."""


def formats_from_source_file_name(source_file_path: str) -> List[str]:
    """Get list of formats based on source file name."""
    if not source_file_path:
        return []
    for extension in VALID_SOURCE_EXTENSIONS:
        if str(source_file_path).endswith(extension[0]) \
                and isinstance(extension[1], list):
            return extension[1]
    return []


def formats_from_source_flag(source_flag: Union[str, SourceFlag]) -> List[str]:
    """Get the dissemination formats based on source type and preference.

    Source file types are represented by single-character codes:
    I - ignore
        All files auto ignore. No paper available.
    S - source encrypted
        Source is encrypted and should not be made available.
    P - PS only
        Multi-file PS submission. It is not necessary to indicate P with single
        file PS since in this case the source file has .ps.gz extension.
    D - PDFlatex
        A TeX submission that must be processed with PDFlatex
    H - HTML submissions
        Multi-file HTML submission.
    A - includes ancillary files
        Submission includes ancillary files in the /anc directory
    B - DC pilot data
        Submission has associated data in the DC pilot system
    X - DOCX
        Submission in Microsoft DOCX (Office Open XML) format
    O - ODF
        Submission in Open Document Format
    F - PDF only
        PDF-only submission with .tar.gz package (likely because of anc files)
    """
    if isinstance(source_flag, SourceFlag):
        source_flag = source_flag.code

    source_flag = source_flag if source_flag else ''
    has_encrypted_source = re.search('S', source_flag, re.IGNORECASE)
    has_ignore = re.search('I', source_flag, re.IGNORECASE)
    if has_ignore:
        if not has_encrypted_source:
            return ['src']
        else:
            return []

    has_ps_only = re.search('P', source_flag, re.IGNORECASE)
    has_pdflatex = re.search('D', source_flag, re.IGNORECASE)
    has_pdf_only = re.search('F', source_flag, re.IGNORECASE)
    has_html = re.search('H', source_flag, re.IGNORECASE)
    has_docx_or_odf = re.search(r'[XO]', source_flag, re.IGNORECASE)

    formats: list[str] = []
    if has_ps_only:
        formats.extend(['pdf', 'ps'])
    elif has_pdflatex:
        formats.extend(['pdf', 'src'])
    elif has_pdf_only:
        formats.extend(['pdf'])
    elif has_html:
        formats.extend(['html'])
    elif has_docx_or_odf:
        formats.extend(['pdf'])
    else:
        formats.extend(['pdf', 'ps', 'src'])

    formats.extend(['other'])
    return formats

def get_all_formats(src_fmt: str) -> List[str]:
        """Returns the list of all formats that the given src can
        be disseminated in. Takes sources format and knows what
        transformations can be applied.

        Does not include sub-formats (like types of ps).
        """
        formats: List[str] = []
        if src_fmt == 'ps':
            formats.extend([src_fmt, 'pdf'])
        elif src_fmt == 'pdf' or src_fmt == 'html':
            formats.append(src_fmt)
        elif src_fmt == 'dvi':
            formats.extend([src_fmt, 'tex-ps', 'pdf'])
        elif src_fmt == 'tex':
            formats.extend(['dvi', 'tex-ps', 'pdf'])
        elif src_fmt == 'pdftex':
            formats.append('pdf')
        elif src_fmt == 'docx' or src_fmt == 'odf':
            formats.extend(['pdf', src_fmt])

        if src_fmt in ['pdflatex', 'tex', 'ps', 'html']:
            formats.append('src')

        return formats

def has_ancillary_files(source_flag: str) -> bool:
    """Check source type for indication of ancillary files."""
    if not source_flag:
        return False
    return re.search('A', source_flag, re.IGNORECASE) is not None


def list_ancillary_files(tarball_path: APath) -> List[Dict]:
    """Return a list of ancillary files in a tarball (.tar.gz file)."""
    if not tarball_path or not tarball_path.suffixes == ['.tar', '.gz'] \
       or not tarball_path.is_file():
        return []

    anc_files = []
    try:
        with tarball_path.open( mode='rb') as fh:
            with tarfile.open(fileobj=fh, mode='r') as tf:
                for member in \
                        (m for m in tf if re.search(r'^anc\/', m.name) and m.isfile()):
                    name = re.sub(r'^anc\/', '', member.name)
                    size_bytes = member.size
                    anc_files.append({'name': name, 'size_bytes': size_bytes})
    except (ReadError, CompressionError) as ex:
        logger.error("Error while trying to read anc files from %s: %s", tarball_path, ex)
        return []
    if len(anc_files) > 1:
        anc_files = sorted(anc_files, key=itemgetter('name'))
    return anc_files
