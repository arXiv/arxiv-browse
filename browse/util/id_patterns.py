r"""Patterns and functions to detect arXiv ids and Urls in text.

Functions to detech arXiv ids, URLs and DOI in text.
Functions to transform them to <a> tags.

These were originally jinja filters but became a little too big
for that so they were split out and made more general so they didn't
rely on the Flask context.

These all use expect input of Markup or non-markup text and return
Markup objects. This is because the <a> that get added need to avoid
double escaping.

There are several classes of patterns we want to match but there is
some overlap in these patterns. To avoid looking for and parsing HTML in each 
jinja filter, detecting these patterns is combined.

So far we are looking for:
DOIs            DOI: 10.1145/0001234.1234567
arXiv IDS:      1234.12345 1234.12345v1 hep-ph1307.1843
HTTP URLs:      http://something.org/myPaper/1234.12345
FTP URLs:       ftp://example.com/files/1234.12345

Just matching for arXiv ids with \d{4}\.\d{4,5} will match several of
these. To deal with this we are priortizing the matches and
interupting once one is found.

We should probably match DOIs first because they are the source of a
lot of false positives for arxiv matches.
"""
from typing import Optional, List, Pattern, Match, Tuple, Callable
import re
from dataclasses import dataclass

from urllib.parse import quote
from jinja2 import Markup, escape

from arxiv import taxonomy


@dataclass
class Matchable:
    """Class for paterns"""
    examples: List[str]
    pattern: Pattern


def _identity(x: str)->str:
    """identity funciton for default in some places"""
    return x


doi_patterns = [
    Matchable(['10.1145/0001234.1234567'],
              re.compile(r'(?P<doi>10.\d{4,9}/[-._;()/:A-Z0-9]+)', re.I))
]
"""List of Matchable for DOIs in text.

We should probably match DOIs first because they are the source of a
lot of false positives for arxiv matches.

Only using the most general express from
https://www.crossref.org/blog/dois-and-matching-regular-expressions/
"""

_archive = '|'.join([re.escape(key) for key in taxonomy.ARCHIVES.keys()])
"""string for use in Regex for all arXiv archives"""

_category = '|'.join([re.escape(key) for key in taxonomy.CATEGORIES.keys()])

basic_arxiv_id_patterns = [
    Matchable(['math/0501233', 'hep-ph/0611734', 'gr-qc/0112123'],
              re.compile(r'(?P<arxiv_id>(%s)\/\d{2}[01]\d{4}(v\d*)?)'
                         % _archive, re.I)),
    Matchable(['1609.05068', '1207.1234v1', '1207.1234', '1807.12345',
               '1807.12345v1', '1807.12345v12'],
              re.compile(r'(?<![\d=])(?P<arxiv_id>\d{4}\.\d{4,5}(v\d*)?)',
                         re.I)),
    Matchable(['math.GR/0601136v3', 'math.GR/0601136'],
              re.compile(r'(?P<arxiv_id>(%s)\/\d{2}[01]\d{4}(v\d*)?)'
                         % _category, re.I))
]

OKCHARS = r'([a-z0-9,_.\-~:]|%[a-f0-9]*)'
"""Chacters that are acceptable during PATH, QUERY and ANCHOR parts"""

HOST_NAME = r'(?:[a-z0-9][a-z0-9\-.:]+[a-z0-9])'
"""Regex used to match host names in arXiv urlize.

This is not a perfect regex for a host name, It accepts only a sub-set
of hostnames to meet the needs of arxiv.

HOST_NAME must end with a simplified character to avoid capturing a
period.
"""

PATH = rf'(?P<PATH>(/{OKCHARS}*)+)?'
"""Regex for path part of URLs for use in urlize"""

QUERY = rf'(?P<QUUERY>\?(&?({OKCHARS}*(={OKCHARS}*)?))*)?'
"""Regex for query part of URLs for use in urlize"""

ANCHOR = rf'(?P<ANCHOR>#{OKCHARS}*)?'
"""Regex for anchor part of URLs for use in urlize"""


URLINTEXT_PAT = re.compile(r'(?P<url>(?:https?://)'
                           f'{HOST_NAME}{PATH}{QUERY}{ANCHOR})',
                           re.I)
"""Regex to match URLs in text."""

FTP_PAT = re.compile(r'(?P<url>(?:ftp://)'
                     f'{HOST_NAME}{PATH}{QUERY})',
                     re.I)
"""Regex to match FTP URLs in text."""

basic_url_patterns = [
    Matchable(['http://something.com/bla'], URLINTEXT_PAT),
    Matchable(['ftp://something.com/bla'], FTP_PAT)
]
"""List of Matchable to use when finding URLs in text"""

bad_arxiv_id_patterns = [
    re.compile('vixra', re.I)
]
"""List of Regex patterns that will cause matching to be skipped for
the token."""

dois_ids_and_urls = basic_url_patterns + doi_patterns + basic_arxiv_id_patterns
"""List of Matchable to use when finding DOIs, arXiv IDs, and URLs.

URLs are first because some URLs contain DOIs or arXiv IDS.  

DOI are before arXiv ids because many DOIs are falsely matched by the
arxiv_id patterns.
"""


_bad_endings = ['.', ',', ':', ';', '&', '(', '[', '{']
"""These should not appear at the end of URLs because they are likely
part of the surrounding text"""


def _find_match(patterns: List[Matchable], token: str)-> Optional[Tuple[Match, Matchable]]:
    """Find first in patterns that is found in txt."""
    for chgMtch in patterns:
        if chgMtch.pattern.flags:
            fnd = re.search(chgMtch.pattern, token)
        else:
            fnd = re.search(chgMtch.pattern, token, re.I)
        if fnd is not None:
            return (fnd, chgMtch)
    return None


def _transform_token(patterns: List[Matchable],
                     bad_patterns: List[Pattern],
                     id_to_url: Callable[[str], str],
                     doi_to_url: Callable[[str], str],
                     url_to_url: Callable[[str], str],
                     token: str) -> str:
    """Transform a token from text to one of the Matchables.

    This only transforms against the first of Matchable matched.
    Matching on this token will be skipped if any of the bad_patterns
    match the token (that is re.search).
    """

    id_to_url = id_to_url or (lambda x: x)
    doi_to_url = doi_to_url or (lambda x: x)
    url_to_url = url_to_url or (lambda x: x)

    for pattern in bad_patterns:
        if re.search(pattern, token):
            return token

    mtch = _find_match(patterns, token)
    if mtch is None:
        return token

    (match, _) = mtch
    keys = match.groupdict().keys()
    if 'arxiv_id' in keys:
        (front, back) = _arxiv_id_sub(match, id_to_url)
    elif 'doi' in keys:
        (front, back) = _doi_sub(match, doi_to_url)
    elif 'url' in keys:
        (front, back) = _url_sub(match, url_to_url)
    else:
        # unclear how to substitute in for this match
        return token

    if back:
        t_back = _transform_token(patterns, bad_patterns,
                                  id_to_url, doi_to_url, url_to_url, back)
        return front + Markup(t_back)
    else:
        return front


def _arxiv_id_sub(match: Match, id_to_url: Callable[[str], str])->Tuple[Markup, str]:
    """Returns match.string transformed for a arxiv id match"""
    m = match.group('arxiv_id')
    if m[-1] in _bad_endings:
        arxiv_url = id_to_url(m)[:-1]
        anchor = m[:-1]
        back = m[-1] + match.string[match.end():]
    else:
        arxiv_url = id_to_url(m)
        anchor = m
        back = match.string[match.end():]

    front = match.string[0:match.start()]
    return (Markup(f'{front}<a href="{arxiv_url}">{anchor}</a>'), back)


def _doi_sub(match: Match, doi_to_url: Callable[[str], str])->Tuple[Markup, str]:
    """Returns match.string transformed for a DOI match"""
    doi = match.group('doi')
    if(doi[-1] in _bad_endings):
        back = match.string[match.end():] + doi[-1]
        doi = doi[:-1]
    else:
        back = match.string[match.end():]

    quoted_doi = quote(doi, safe='/')
    doi_url = f'https://dx.doi.org/{quoted_doi}'
    doi_url = doi_to_url(doi_url)

    anchor = escape(doi)
    front = match.string[0:match.start()]
    return (Markup(f'{front}<a href="{doi_url}">{anchor}</a>'), back)


def _url_sub(match: Match, url_to_url: Callable[[str], str])->Tuple[Markup, str]:
    """Returns match.string transformed for a URL match"""
    url = match.group('url')
    if url.startswith('https'):
        anchor = 'this https URL'
    elif url.startswith('http'):
        anchor = 'this http URL'
    elif url.startswith('ftp'):
        anchor = 'this ftp URL'
    else:
        anchor = 'this URL'

    front = match.string[0:match.start()]
    if url[-1] in _bad_endings:
        back = url[-1] + match.string[match.end():]
        url = url[:-1]
    else:
        back = match.string[match.end():]

    url = url_to_url(url)
    return (Markup(f'{front}<a href="{url}">{anchor}</a>'), back)


_word_split_re = re.compile(r'(\s+)')
"""Regex to split to tokens during _to_tags.

Capturing group causes the splitting spaces to be included
in the returned list.
"""


def _to_tags(patterns: List[Matchable],
             bad_patterns: List[Pattern],
             id_to_url: Callable[[str], str],
             doi_to_url: Callable[[str], str],
             url_to_url: Callable[[str], str],
             text: str)-> str:
    """Split text to tokens, do _transform_token for each, return results"""
    def transform_token(tkn: str)-> str:
        return _transform_token(patterns, bad_patterns,
                                id_to_url, doi_to_url, url_to_url,
                                tkn)

    if not hasattr(text, '__html__'):
        text = Markup(escape(text))

    words = _word_split_re.split(text)
    for i, token in enumerate(words):
        token_2 = transform_token(token)
        if token_2 != token:
            words[i] = token_2
    result = u''.join(words)
    return Markup(result)


def do_id_to_tags(id_to_url: Callable[[str], str],
                  text: str)-> str:
    """Transform arxiv ids in text to <a> tags"""
    return _to_tags(basic_arxiv_id_patterns,
                    bad_arxiv_id_patterns,
                    id_to_url, _identity, _identity,
                    text)


def do_dois_id_urls_to_tags(id_to_url: Callable[[str], str],
                            doi_to_url: Callable[[str], str],
                            text: str)-> str:
    """Transform DOIs, arxiv ids and URLs in text to <a> tags"""
    return _to_tags(dois_ids_and_urls,
                    bad_arxiv_id_patterns,
                    id_to_url, doi_to_url, _identity,
                    text)


def do_dois_to_tags(doi_to_url: Callable[[str], str], text: str)->str:
    """Transform DOIs in text to <a> tags."""
    return _to_tags(doi_patterns, [], _identity, doi_to_url, _identity, text)


def do_dois_arxiv_ids_to_tags(id_to_url: Callable[[str], str],
                               doi_to_url: Callable[[str], str],
                               text: str)->str:
    """Transform DOIs and arXiv IDs to <a> tags."""
    return _to_tags(doi_patterns + basic_arxiv_id_patterns,
                    bad_arxiv_id_patterns,
                    id_to_url, doi_to_url, _identity,
                    text)
