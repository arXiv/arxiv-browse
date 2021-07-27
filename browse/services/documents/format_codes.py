"""Shared functions that support determination of dissemination formats."""
import re
from typing import List, Optional

import logging
logger = logging.getLogger(__name__)


VALID_SOURCE_EXTENSIONS = [
    ('.tar.gz', None),
    ('.pdf', ['pdfonly']),
    ('.ps.gz', ['pdf', 'ps']),
    ('.gz', None),
    ('.dvi.gz', None),
    ('.html.gz', ['html'])
]
"""List of tuples containing the valid source file name extensions and
their corresponding dissemination formats.  There are minor
performance implications in the ordering when doing filesystem
lookups, so the ordering here should be preserved."""

VALID_SOURCE_FORMATS = {
    'docx': ['pdf', 'other'],
    'html': ['html', 'other'],
    'pdf': ['pdfonly'],
    'pdftex': None,
    'ps': ['pdf', 'ps'],
    'tex': None,
    'withdrawn': ['src']
}
"""Dict of source format strings and their corresponding dissemination formats."""

def formats_from_source_type(source_type: str,
                             format_pref: Optional[str] = None,
                             cache_flag: bool = False,
                             add_sciencewise: bool = False) -> List[str]:
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
    formats = []
    if not source_type:
        source_type = ''
    if not format_pref:
        format_pref = ''
    has_encrypted_source = re.search('S', source_type, re.IGNORECASE)
    has_ignore = re.search('I', source_type, re.IGNORECASE)
    has_ps_only = re.search('P', source_type, re.IGNORECASE)
    has_pdflatex = re.search('D', source_type, re.IGNORECASE)
    has_pdf_only = re.search('F', source_type, re.IGNORECASE)
    has_html = re.search('H', source_type, re.IGNORECASE)
    has_docx_or_odf = re.search(r'[XO]', source_type, re.IGNORECASE)
    has_src_pref = format_pref and re.search('src', format_pref)
    append_other = False
    logger.debug(f'In formats_from_source_type: source_type is '
                 f'"{source_type}", format_pref is {format_pref} cache_flag is {cache_flag}')

    if has_ignore and not has_encrypted_source:
        formats.append('src')
    elif has_ps_only:
        formats.extend(['pdf', 'ps', 'other'])
    elif has_pdflatex:
        # PDFtex has source so honor src preference
        if has_src_pref and not has_encrypted_source:
            formats.append('src')
        formats.extend(['pdf', 'other'])
    elif has_pdf_only:
        formats.extend(['pdf', 'other'])
    elif has_html:
        formats.extend(['html', 'other'])
    elif has_docx_or_odf:
        formats.extend(['pdf', 'other'])
    elif cache_flag:
        # this is the case where the source is not newer than the cache file
        # and the cache file is empty
        formats.extend(['nops', 'other'])
    else:
        if re.search('pdf', format_pref):
            formats.append('pdf')
        elif re.search('400', format_pref):
            formats.append('ps(400)')
        elif re.search('600', format_pref):
            formats.append('ps(600)')
        elif re.search('fname=cm', format_pref):
            formats.append('ps(cm)')
        elif re.search('fname=CM', format_pref):
            formats.append('ps(CM)')
        elif re.search('dvi', format_pref):
            formats.append('dvi')
        elif has_src_pref:
            if not has_encrypted_source:
                formats.append('src')
            formats.extend(['pdf', 'ps'])
        else:
            formats.extend(['pdf', 'ps'])

        append_other = True

    if add_sciencewise:
        formats.append('sciencewise_pdf')

    if append_other:
        formats.append('other')

    return formats


def has_ancillary_files(source_type: str) -> bool:
    """Check source type for indication of ancillary files."""
    if not source_type:
        return False
    return re.search('A', source_type, re.IGNORECASE) is not None
