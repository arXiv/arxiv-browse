"""Browse jinja filters."""
import re
from urllib import parse
from typing import Callable, Match, Optional, Union

from jinja2 import Markup, escape
from jinja2._compat import text_type
from jinja2.utils import _digits, _letters, _punctuation_re  # type: ignore
from jinja2.utils import _simple_email_re, _word_split_re  # type: ignore
from flask import url_for
import html

from browse.services.util.tex2utf import tex2utf


JinjaFilterInput = Union[Markup, str]
"""Jinja filters will receive their text input as either
   a Markup object or a str. It is critical for proper escaping to
   to ensure that str is correctly HTML escaped.
   
   Markup is decnded from str so this type is redundent but
   the hope is to make it clear what is going on to arXiv developers.
"""


def doi_urls(clickthrough_url_for: Callable[[str], str], text: JinjaFilterInput) -> Markup:
    """Creates links to one or more DOIs.

    clickthrough_url_for is a Callable that takes the URL and returns
    a clickthrough URL.

    An example of this is in factory.py
    While this is called clickthrough_url_for it could be any str -> str fn.
    For testing this could be the identity function:
    value = doi_urls( lambda x: x , 'test text bla bla bla')

    """
    # How does this ensure escaping?
    # Two cases:
    #  1. we get a markup object for text, ex from a previously filter stage
    #  2. we get a raw str for text, ex meta.abstract
    # In both of cases the value in result ends up escaped after
    # this conditional.
    # Then we sub DOI with HTML elements, and return the result as Markup()

    if hasattr(text, '__html__') and hasattr(text, 'unescape'):
        result = text
    else:
        result = Markup(escape(text))

    doi_list = []

    def single_doi_link(match: Match[str]) -> str:
        # should only get called on match
        # match is NOT jinja Markup
        quoted_doi = parse.quote_plus(match.group(0))

        doi_url = clickthrough_url_for(f'https://dx.doi.org/{quoted_doi}')
        return Markup(f'<a href="{doi_url}">{escape(match.group(0))}</a>')

    slt = re.split(r'([;,]?\s+)', result.unescape())
    for segment in slt:
        if re.match(r'^10\.\d{4,5}\/\S+$', segment):
            doi_link = re.sub(r'^10\.\d{4,5}\/\S+$', single_doi_link, segment)
            doi_list.append(doi_link)
        else:
            doi_list.append(escape(segment))
    if doi_list:
        result = ''.join(doi_list)

    return Markup(result)



def arxiv_urlize(
        text: JinjaFilterInput, trim_url_limit: Optional[int] = None,
        rel: Optional[str] = None, target: Optional[str] = None
) -> Markup:
    """Like jinja2 urlize but uses link text of 'this http URL'.

    Based directly on jinja2 urlize;
    Copyright (c) 2009 by the Jinja Team, see AUTHORS in
    https://github.com/pallets/jinja or other distribution of jinja2
    for more details.

    The main purpose of using a modified version of urlize, is, for now,
    to replace the URL link (just the URL itself in urlize) with
    "this http URL" to save space and maintain feature parity with legacy
    arXiv code. Thus, for now, trim_url_limit is not used. Additionally,
    escape checks and Markup wrapping are performed.

    Converts any URLs in text into clickable links. Works on http://,
    https:// and www. links. Links can have trailing punctuation (periods,
    commas, close-parens) and leading punctuation (opening parens) and
    it'll still do the right thing.
    If trim_url_limit is not None, the URLs in link text will be limited
    to trim_url_limit characters.
    If nofollow is True, the URLs in link text will get a rel="nofollow"
    attribute.
    If target is not None, a target attribute will be added to the link.
    """
    if hasattr(text, '__html__'):
        result = text
    else:
        result = Markup(escape(text))

    # Note: currently unused; using link_text instead
    # trim_url = lambda x, limit=trim_url_limit: limit is not None \
    #    and (x[:limit] + (len(x) >=limit and '...'
    #    or '')) or x
    link_text = 'this http URL'

    words = _word_split_re.split(text_type(escape(result)))
    rel_attr = rel and ' rel="%s"' % text_type(escape(rel)) or ' rel="noopener"'
    target_attr = target and ' target="%s"' % escape(target) or ''

    for i, word in enumerate(words):
        match = _punctuation_re.match(word)
        if match:
            lead, middle, trail = match.groups()
            if middle.startswith('www.') or (
                    '@' not in middle and
                    not middle.startswith('http://') and
                    not middle.startswith('https://') and
                    middle and
                    middle[0] in _letters + _digits and (
                        middle.endswith('.org') or
                        middle.endswith('.net') or
                        middle.endswith('.com')
                    )):
                # in jinja2 urlize, an additional last argument is
                # trim_url(middle)
                middle = '<a href="http://%s"%s%s>%s</a>' % \
                    (middle, rel_attr, target_attr, link_text)
            if middle.startswith('http://') or \
                    middle.startswith('https://'):
                # in jinja2 urlize, an additional last argument is
                # trim_url(middle)
                middle = '<a href="%s"%s%s>%s</a>' \
                         % (middle, rel_attr, target_attr, link_text)
            if '@' in middle and not middle.startswith('www.') and \
                    ':' not in middle and _simple_email_re.match(middle):
                middle = '<a href="mailto:%s">%s</a>' % (middle, middle)
            if lead + middle + trail != word:
                words[i] = lead + middle + trail
    result = u''.join(words)
    return Markup(result)


def line_feed_to_br(text: JinjaFilterInput) -> Markup:
    """Lines that start with two spaces should be broken"""

    if hasattr(text, '__html__'):
        etxt = text
    else:
        etxt = Markup(escape(text))

    # if line starts with spaces, replace the white space with <br\>
    br = re.sub(r'((?<!^)\n +)', '\n<br />', etxt)  
    dedup = re.sub(r'\n\n', '\n', br)  # skip if blank
    return Markup(dedup)


def arxiv_id_urls(text: JinjaFilterInput) -> Markup:
    """
    Link either arXiv:<internal_id> or <internal_id> with text as anchor.

    The link is simply to /abs/<internal_id>; However, we do not link to
    viXra:<looks_like_our_internal_id>.

    In most cases this should happen after jinja's urlize().
    """
    # Need to escape: if jinja sends us raw txt, needs it,
    # if jinja sends us Markup, it has no affect
    if hasattr(text, '__html__'):
        etxt = text
    else:
        etxt = Markup(escape(text))

    def arxiv_id_link(match: Match[str]) -> str:
        url_path = url_for('browse.abstract', arxiv_id=match.group(4))
        url = f'{match.group(1)}<a href="{url_path}">{match.group(2)}</a>'
        return url

    # TODO: consider supporting more than just new ID patterns?
    new_id_re = r'([a-z-]+(.[A-Z][A-Z])?\/\d{7}|\d{4}\.\d{4,5})(v\d+)?'
    id_re = re.compile(
        r'(^|[^/A-Za-z-])((arXiv:|(?<!viXra:))(%s))' %
        new_id_re, re.IGNORECASE)
    result = re.sub(id_re, arxiv_id_link, etxt)
    return Markup(result)


def entity_to_utf(text: str) -> str:
    """Converts HTML entities to unicode.  

    For example '&amp;' becomes '&'.

    Must be first filter in list because it does not do anything to a
    Markup. On a Markup object it will do nothing and just return the
    input Markup.

    DANGEROUS because this is basically an unescape.
    It tries to avoid junk like <script> but it is a bad idea.
    This MUST NEVER BE USED ON USER PROVIDED INPUT. Submission titles etc.

    """

    if hasattr(text, '__html__'):
        return text
    
    without_lt = re.sub('<', 'XXX_LESS_THAN_XXX', text)
    without_lt_gt = re.sub('>', 'XXX_GREATER_THAN_XXX', without_lt)

    unes = html.unescape(without_lt_gt)

    with_lt = re.sub('XXX_LESS_THAN_XXX', '&lt;', unes)
    with_lt_gt = re.sub('XXX_GREATER_THAN_XXX', '&gt;', with_lt)

    return Markup(with_lt_gt)


def tex_to_utf(text: JinjaFilterInput) -> Markup:
    """Wraps tex2utf as a filter."""

    if hasattr(text, '__html__'):
        etxt = text
    else:
        etxt = Markup(escape(text))
    return Markup(tex2utf(etxt))
