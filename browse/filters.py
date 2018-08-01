"""Browse jinja filters."""
import re
from urllib import parse
from jinja2 import Markup, escape
from flask import url_for
from typing import Match, Callable


# TODO tests for these

def doi_urls(clickthrough_url_for: Callable[[str], str], text: str) -> str:
    """Creates links to one or more DOIs.

    clickthrough_url_for is a Callable that takes the URL and returns a clickthrough URL.
    An example of this is in factory.py
    For testing this could be the identity function:
    value = doi_urls( lambda x: x , 'test text bla bla bla')
    """
    result = text
    doi_list = []

    def single_doi_link(match: Match[str]) -> str:
        # should only get called on match
        quoted_doi = parse.quote_plus(match.group(0))
        doi_url = clickthrough_url_for(f'https://dx.doi.org/{quoted_doi}')
        return f'<a href="{doi_url}">{escape(match.group(0))}</a>'

    for segment in re.split(r'[;,]?\s+', text):
        doi_link = re.sub(r'^10\.\d{4,5}\/\S+$', single_doi_link, segment)
        doi_list.append(doi_link)
    if doi_list:
        result = str.join(' ', doi_list)

    result = Markup(result)
    return result


def arxiv_id_urls(text:str) -> str:
    """Will link either arXiv:<internal_id> or <internal_id> with the full
    text as the anchor but the link to just /abs/<internal_id>.
    However, we do not link viXra:<like_our_internal_id>.
    In most cases this should happen after url_filter.
    """
    print( "text in arxiv_id_filter is " + text )
    def arxiv_id_link(match: Match[str]) -> str:
        url_path = url_for('browse.abstract', arxiv_id=match.group(5))
        url = f'{match.group(1)}<a href="{url_path}">{match.group(2)}</a>'
        return url

    # TODO: consider supporting more than just new ID patterns?
    new_id_re = r'([a-z-]+(.[A-Z][A-Z])?\/\d{7}|\d{4}\.\d{4,5})(v\d+)?'
    id_re = re.compile(r'(^|[^/A-Za-z-])((arXiv:|(?<!viXra:))(%s))' % new_id_re)
    result = re.sub(id_re, arxiv_id_link, text, re.IGNORECASE)
    return Markup(result)

