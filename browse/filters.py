"""Browse jinja filters."""
import html
import re
from typing import Union

from markupsafe import Markup

JinjaFilterInput = Union[Markup, str]
"""
   Jinja filters will receive their text input as either
   a Markup object or a str. It is critical for proper escaping to
   to ensure that str is correctly HTML escaped.

   Markup is decoded from str so this type is redundant but
   the hope is to make it clear what is going on to arXiv developers.
"""


def entity_to_utf(text: str) -> str:
    """Convert HTML entities to unicode.

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
