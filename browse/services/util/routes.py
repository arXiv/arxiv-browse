"""Representations URL routes in arXiv system."""
import urllib

from browse.domain import DocMetadata

# TODO This belongs in some configuration file

MAIN_SITE = 'http://arxiv.org'


def main_site(param: str) -> str:
    return MAIN_SITE + param


def pdf(item: DocMetadata) -> str:
    """ Retunrs URL to PDF for the item """
    return main_site('/pdf/' + item.arxiv_id)


def search_author(author_query: str) -> str:
    """Returns URL for author in arxiv search.
    ex.
    https://arxiv.org/search?searchtype=author&query=Berger%2C+E+L
    """
    return main_site("/search?searchtype=author&query=" + urllib.parse.quote_plus(author_query))
