"""Representations URL routes in arXiv system."""
from browse.domain import DocMetadata

# TODO This belongs in some configuration file

MAIN_SITE = 'http://dev.arxiv.org'


def main_site(param: str) -> str:
    return MAIN_SITE + param


def pdf(item: DocMetadata) -> str:
    """ Retunrs URL to PDF for the item """
    return main_site('/pdf/' + item.arxiv_id)
