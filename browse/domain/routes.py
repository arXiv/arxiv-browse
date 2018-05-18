"""Representations URL routes in arXiv system."""
from browse.domain import DocMetadata


def main_site(param: str) -> str:
    return 'https://arxiv.org' + param


def pdf(item: DocMetadata) -> str:
    """ Retunrs URL to PDF for the item """
    if isinstance(item, DocMetadata):
        return main_site('/pdf/' + item.id)
