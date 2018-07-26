"""Browse jinja filters."""
import re
from jinja2 import evalcontextfilter, Markup, escape
from flask import url_for
from typing import Match
from urllib import quote_plus


def _escape_special_chracters(text: str) -> str:
    result = text
    result = re.sub(r'&(?!amp;)', '&amp;', result)
    result = re.sub(r'<', '&lt;', result)
    result = re.sub(r'>', '&gt;', result)
    return result

@evalcontextfilter
def doi_filter(eval_ctx, text: str) -> str:

    def single_doi_link(match: Match[str]) -> str:
        doi_url = f'https://dx.doi.org/{quote_plus(match.group(0))}'
        # return f'<a href="{doi_url}">{_escape_special_chracters()}
    for segment in re.split(r'[;,]?\s+', text):
        result = re.sub(r'^10\.\d{4,5}\/\S+$', segment)

    if eval_ctx.autoescape:
        result = Markup(result)

@evalcontextfilter
def url_filter(eval_ctx, text: str) -> str:
    """Create links to generic URLs and (new) arXiv identifiers."""
    def arxiv_id_link(match: Match[str]) -> str:
        url_path = url_for('browse.abstract', arxiv_id=match.group(5))
        url = f'{match.group(1)}<a href="{url_path}">{match.group(2)}</a>'
        return url

    result = re.sub(r'((ftp|https?)://[^\[\]*{}()\s",>&;]+)\s',
                    r'<a href="\g<1>">this \g<2> URL</a>',
                    text,
                    re.IGNORECASE)
    new_id_re = r'([a-z-]+(.[A-Z][A-Z])?\/\d{7}|\d{4}\.\d{4,5})(v\d+)?'
    id_re = re.compile(
        r'(^|[^/A-Za-z-])((arXiv:|(?<!viXra:))(%s))' % new_id_re)
    result = re.sub(id_re, arxiv_id_link, result)
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


@evalcontextfilter
def abstract_filter(eval_ctx, text: str) -> str:
    """Line breaks and URL filtering for abstract field."""
    result = ''
    for (idx, line) in enumerate(text.split('\n')):
        if not re.search(r'\S', line):
            # ignore blank lines
            next
        line = _escape_special_chracters(line)
        line = url_filter(eval_ctx, line)

        if idx > 0:
            line = re.sub(r'^\s+', '<br/>', line)
        result = f'{result}{line}\n'
    if eval_ctx.autoescape:
        result = Markup(result)
    return result if result else text
