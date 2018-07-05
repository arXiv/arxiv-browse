"""Utility functions for external reference and citation resources."""
import re
from datetime import date
from typing import Optional

from browse.services.document.config.external_refs_cits import \
    INSPIRE_REF_CIT_CATEGORIES, DBLP_ARCHIVES, DBLP_START_DATE
from browse.domain.metadata import DocMetadata


def include_inspire_link(docmeta: DocMetadata) -> bool:
    """Check whether to include INSPIRE reference/citation link on abs page."""
    if not docmeta:
        return False
    identifier = docmeta.arxiv_identifier
    orig_publish_date = date(identifier.year, identifier.month, 1)
    primary_category = docmeta.primary_category.id
    if primary_category in INSPIRE_REF_CIT_CATEGORIES and \
            orig_publish_date >= INSPIRE_REF_CIT_CATEGORIES[primary_category]:
        return True
    return False


def include_dblp_section(docmeta: DocMetadata) -> bool:
    """Check whether DBLP section should be included based only on metadata."""
    if not docmeta:
        return False
    identifier = docmeta.arxiv_identifier
    orig_publish_date = date(identifier.year, identifier.month, 1)
    primary_archive = docmeta.primary_archive.id
    print(f'primary archive: {primary_archive}')
    if primary_archive in DBLP_ARCHIVES and \
            orig_publish_date >= DBLP_START_DATE:
        return True
    return False


def get_dblp_bibtex_path(url: str) -> Optional[str]:
    """Get the end of the DBLP bibtex URL path based on the listing path."""
    if not url:
        return None
    try:
        (response_type, dblp_id) = url.split('#')
        type_match = re.search(r'(\/journals\/|conf\/[^/]+)', response_type)
        if type_match:
            if re.search('journals', type_match.group(0)):
                return f'journals/corr/{dblp_id}'
            else:
                return f'{type_match.group(0)}/{dblp_id}'
        else:
            return None
    except ValueError:
        return None
    return None
