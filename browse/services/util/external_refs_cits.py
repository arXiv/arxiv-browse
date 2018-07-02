"""Utility functions for external reference and citation resources."""
from datetime import date

from browse.services.document.config.external_refs_cits import \
    INSPIRE_REF_CIT_CATEGORIES
from browse.domain.metadata import DocMetadata


def include_inspire_link(docmeta: DocMetadata) -> bool:
    """Check whether to include INSPIRE reference/citation link on abs page."""
    if not docmeta:
        return False
    identifier = docmeta.arxiv_identifier
    primary_category = docmeta.primary_category.id
    orig_publish_date = date(identifier.year, identifier.month, 1)
    if primary_category in INSPIRE_REF_CIT_CATEGORIES and \
            orig_publish_date >= INSPIRE_REF_CIT_CATEGORIES[primary_category]:
        return True
    return False
