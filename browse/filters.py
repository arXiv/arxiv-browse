"""Browse jinja filters."""
import re
from urllib import parse
from jinja2 import evalcontextfilter, Markup, escape
from flask import url_for
from typing import Match

# TODO tests for these
# TODO escape text of <a> tags?

# TODO can we use a library function for this? there must be one, Jinja escape?
# Is it just jinja.escape?
def _escape_special_chracters(text: str) -> str:
    result = text
    result = re.sub(r'&(?!amp;)', '&amp;', result)
    result = re.sub(r'<', '&lt;', result)
    result = re.sub(r'>', '&gt;', result)
    return result


def doi_urls(text: str) -> str:
    """Creates links to one or more DOIs."""
    result = text
    doi_list = []

    def single_doi_link(match: Match[str]) -> str:
        # should only get called on match
        quoted_doi = parse.quote_plus(match.group(0))
        doi_url = f'https://dx.doi.org/{quoted_doi}'
        # TODO: this needs to be turned into a clickthrough link before return
        return f'<a href="{doi_url}">{_escape_special_chracters(match.group(0))}</a>'

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


# TODO: filter_urls_ids_escape from perl; it's slightly different from above

@evalcontextfilter
def abstract_filter(eval_ctx, text: str) -> str:
    # """Line breaks and URL filtering for abstract field."""
    # result = ''
    #
    # # TODO can this be more clear?
    # for (idx, line) in enumerate(text.split('\n')):
    #     if not re.search(r'\S', line):
    #         # ignore blank lines
    #         next
    #     line = _escape_special_chracters(line)
    #     line = url_filter(eval_ctx, line)
    #
    #     if idx > 0:
    #         line = re.sub(r'^\s+', '<br/>', line)
    #     result = f'{result}{line}\n'
    # if eval_ctx.autoescape:
    #     result = Markup(result)
    # return result if result else text
    #
    return text