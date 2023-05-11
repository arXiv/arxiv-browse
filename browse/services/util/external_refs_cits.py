"""Utility functions for external reference and citation resources."""
import re
from datetime import date
from typing import Optional

from browse.domain.identifier import Identifier
from browse.services.document.config.external_refs_cits import \
    INSPIRE_REF_CIT_CATEGORIES, DBLP_ARCHIVES, DBLP_START_DATE
from browse.domain.metadata import DocMetadata
from browse.domain.category import Category


def get_orig_publish_date(ident: Identifier) -> Optional[date]:
    """Retrieve the original publication date."""
    if ident.year is not None and ident.month is not None:
        return date(ident.year, ident.month, 1)
    else:
        return None


def inspire_category(category: Category,
                     orig_publish_date: date)-> bool:
    """Get if inspire is in effect for category and date."""
    return bool(category and
                category.id in INSPIRE_REF_CIT_CATEGORIES
                and orig_publish_date >=
                INSPIRE_REF_CIT_CATEGORIES[category.id])


def include_inspire_link(docmeta: DocMetadata) -> bool:
    """Check whether to include INSPIRE reference/citation link on abs page."""
    orig_publish_date = get_orig_publish_date(docmeta.arxiv_identifier)
    if not orig_publish_date:
        return False

    if docmeta.primary_category and inspire_category(docmeta.primary_category,
                                                     orig_publish_date):
        return True

    cats = docmeta.secondary_categories
    return len([cat for cat in cats
                if inspire_category(cat, orig_publish_date)]) > 0


def include_dblp_section(docmeta: DocMetadata) -> bool:
    """Check whether DBLP section should be included based only on metadata."""
    identifier = docmeta.arxiv_identifier
    orig_publish_date = get_orig_publish_date(identifier)
    today = date.today()
    this_month = date(today.year, today.month, 1)
    primary_archive = docmeta.primary_archive.id
    if orig_publish_date is not None:
        date_test: bool = orig_publish_date < this_month
        in_dblp_test: bool = primary_archive in DBLP_ARCHIVES
        return date_test and in_dblp_test
    else:
        return False


def get_dblp_bibtex_path(url: str) -> Optional[str]:
    """Get the end of the DBLP BibTeX URL path based on the listing path."""
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


def get_computed_dblp_listing_path(docmeta: DocMetadata) -> Optional[str]:
    """Get the DBLP listing path based on the metadata."""
    identifier = docmeta.arxiv_identifier
    orig_publish_date = get_orig_publish_date(identifier)
    if orig_publish_date >= DBLP_START_DATE and identifier.id is not None:
        if identifier.is_old_id:
            dblp_id = f'abs-cs-{identifier.filename}'
        else:
            dashed_id = identifier.id.replace('.', '-', 1)
            dblp_id = f'abs-{dashed_id}'
        return f'db/journals/corr/corr{identifier.yymm}.html#{dblp_id}'
    else:
        return None
