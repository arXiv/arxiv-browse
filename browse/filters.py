"""Browse jinja filters."""
import re
from urllib import parse
from typing import Callable, Match, Optional, Union

from jinja2 import Markup, escape
from jinja2._compat import text_type
from jinja2.utils import _digits, _letters  # type: ignore
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


def single_doi_url(clickthrough_url_for: Callable[[str], str], doi: JinjaFilterInput) -> Markup:
    """DOI is made into a link.

    This expects a DOI ONLY. It should not be used on general text.

    This link is not through clickthrough. Use an additional filter in
    the template to get that.

    How does this ensure escaping? It expects just a DOI, The result
    is created as a properly escaped Markup.
    """

    doi_url = f'https://dx.doi.org/{parse.quote_plus(doi)}'
    ct_url = clickthrough_url_for(doi_url)
    return Markup(f'<a href="{ct_url}">{escape(doi)}</a>')


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

    # TODO it would be good to move this out of a jinja filter
    # and to the controller, it is only used for things coming from DBLP
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
        # Need to unescape so nothing that is tex is escaped
        return Markup(escape(tex2utf(text.unescape())))  # type: ignore
    else:
        return Markup(escape(tex2utf(text)))
