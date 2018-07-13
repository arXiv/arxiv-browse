"""Produces search service query strings for authors."""
import itertools
import re
from typing import List, Tuple, Union

from browse.services.util.tex2utf import tex2utf
from browse.services.document.author_affil import split_authors, PREFIX_MATCH



AuthorList = List[Union[str, Tuple[str, str]]]
"""Type alias for list of authors or strings that is used to display the author list."""


def is_affiliation(item: str)-> bool:
    """Return true if a string contains an affiliation."""
    return item.startswith('(')


def is_short(item: str)-> bool:
    """Return true if the length of string is less than 4 characters long."""
    return len(item) < 4


def is_etal(item: str)-> bool:
    """Return true if the string contains et al."""
    return re.match(r'et\.? al\.?$', item) is not None


def is_divider(item: str)-> bool:
    """Return true if the string contains a divider character."""
    return re.match(r'^(,|:)', item) is not None


def split_long_author_list(authors: AuthorList, size:int) -> Tuple[AuthorList, AuthorList]:
    """Returns two lists where the first is of size and the second is the remaining authors.

    The author list has strings which are not part of the author names, but commas between them to preserve
    the formatting that the submitter used.

    This function is used to split the list base on name count, not just list element count.
    """
    front = []
    back = []
    count = 0
    back_count = 0
    for item in authors:
        if count > size:
            back.append(item)
            if type(item) is tuple:
                back_count = back_count + 1
        else:
            front.append(item)
            if type(item) is tuple:
                count = count + 1
    return front, back, back_count



def queries_for_authors(authors: str) -> AuthorList:
    """
    Make search service query strings for authors.

    The main challenge here is that the HTML output of this should match as
    closely as possible the string input by the submitter.

    Takes the authors string from a document metadata or .abs, split,
    and return a structure of [ str|(name_text, author_search_query_str)...]

    If the item in the list is just a string, it should just be placed in the
    HTML output since it is something like whitespace, a comma or 'for the' or
    a colon.

    If a list item is a tuple, author_search_query_str will be something like
    "Webb J E" which can be used to query the search service.

    name_text will be the text to put in side the <a> tag. Such as
    "James E. Webb,"

    DON'T URL_encode, do that in template
    DON'T do entities, do that in template
    DON'T escape utf8 for HTML, just return utf8
    """
    out: AuthorList = []

    splits: List[str] = split_authors(authors)
    for i in splits:
        item = i
        if is_divider(item):
            out.append(item + ' ')
        elif is_affiliation(item) or is_short(item) or is_etal(item):
            out.append(item)
        else:
            out = [*out, *_link_for_name_or_collab(item)]
    return out


def _link_for_name_or_collab(item: str) -> AuthorList:
    out = []

    # deal with 'for the _whatever_' or 'for _whatever_'
    not_linked = re.match(r'\s*((for\s+?the\s+))(.*)',
                          item, flags=re.IGNORECASE)
    if not_linked:
        out.append(not_linked.group(1))
        item = not_linked.group(3)

    item = tex2utf(item)
    item = re.sub(r'\.(?!) ', '.', item)
    item = re.sub(r'\\(,| )', ' ', item)
    item = re.sub(r'([^\\])~', r'\1', item)
    item = re.sub(r',\s*', ' ', item)

    colab_m = re.match(r'^(.+)\s+(collaboration|group|team)',
                       item, re.IGNORECASE)
    if colab_m:
        out.append(f'{colab_m.group(1)} {colab_m.group(2)}')
    else:
        name_bits = item.split()
        if len(name_bits) == 0:
            query_str = item
        else:
            # Do not include Jr, Sr, III, etc. in search
            if re.search(r'Jr\b|Sr\b|[IV]{2, }]', name_bits[-1]):
                name_bits.pop()

            surname = name_bits.pop()

            name_bit_count = 0
            surname_prefixes = []
            initials = []
            found_prefix = False

            for name_bit in name_bits:
                name_bit_count += 1

                if (found_prefix or (name_bit_count > 1
                                     and re.match('^('+PREFIX_MATCH+')$',
                                                  name_bit, re.IGNORECASE))):
                    surname_prefixes.append(name_bit)
                    found_prefix = True
                else:
                    initials.append(name_bit[0:1])

            sur_initials = surname + ', ' + \
                ' '.join(initials) if initials else surname
            query_str = ' '.join([*surname_prefixes, sur_initials])

        out.append((item, query_str))

    return out
