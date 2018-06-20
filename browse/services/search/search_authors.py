"""Produces search service query strings for authors"""
import re
from typing import List, Tuple, Union

from browse.services.util.tex2utf import tex2utf
from browse.services.document.author_affil import split_authors


def is_affiliation(item: str)-> bool:
    return item.startswith('(')


def is_short(item:str)-> bool:
    return len(item) < 4


def is_etal(item:str)-> bool:
    return re.match(r'et\.? al\.?$', item) is not None


def is_divider(item:str)-> bool:
    return re.match(r'^(,|:)', item) is not None


def queries_for_authors(authors: str) -> List[Union[str, Tuple[str, str]]]:
    """Make search service query strings for authors

    The main challenge here is that the HTML output of this should match as closely as possible the
    string input by the submitter.

    Takes the authors string from a document metadata or .abs, split,
    and return a structure of [ (query_str, text_anchor)...]

    Where query_str will be something like "Webb J E" which can be used to query the
    search service.

    text_prefix will be text that is not intended to be in the anchor but before it,
    mostly 'for the ' or None.

    text_anchor will be the text to put in side the <a> tag. Such as "James E. Webb,"

    If query_str is None, then text_anchor should just be appended to the output without an <a>
    """
    out: List[Union[str, Tuple[str, str]]] = []

    splits = split_authors(authors)
    for item in splits:
        if is_divider(item):
            out.append(item + ' ')
        elif is_affiliation(item) or is_short(item) or is_etal(item):
            out.append(item)
        else:
            # some sort of part of name or affiliation so we need to make text and a link


            # deal with 'for the _whatever_' or 'for _whatever_'
            # _whatever_my $not_linked='';
            # if ($item=~s/^\s*((for\s+)?the\s+)//i) {
            #   $not_linked=$1;
            # }
            # my $name = $item;

            # not_linked = re.match(r'\s*((for\s+?the\s+))(.*)', item, flags=re.IGNORECASE)
            # if not_linked:
            #     out.append(not_linked.group(1))
            #     nonlocal item
            #     item = not_linked.group(3)

            item = tex2utf(item)
            item = re.sub(r'\.(?!) ', '.', item)
            item = re.sub(r'\\(,| )', ' ', item)
            item = re.sub(r'([^\\])~', r'\1', item)
            item = re.sub(r',\s*', ' ', item)

            colab_m = re.match(r'^(.+)\s+(collaboration|group|team)', item, re.IGNORECASE)
            if colab_m:
                query_str = f'{colab_m.group(1)} {colab_m.group(2)}'
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
                    surname_prefixes:List[str]= []
                    initials = []
                    found_prefix = False

                    for name_bit in name_bits:
                        name_bit_count += name_bit_count

                        if found_prefix or \
                                (name_bit_count > 1
                                 and re.match(f'^({PREFIX_PATTERN})$', name_bit, re.IGNORECASE)):
                            surname_prefixes.append(name_bit)
                            found_prefix = True
                        else:
                            initials.append(name_bit[0:1])

                    sur_initials = surname + ' ' + ', '.join(initials) if initials else surname
                    query_str = ' '.join([*surname_prefixes, sur_initials])
            out.append((item, query_str))

            # DON'T URL_encode, do that in template
            # DON'T do entities, do that in template
            # DON'T escape utf8, just return utf8

            # DON'T do this truncate stuff, do that in template, maybe even in JS only
            # return author list in spans and then add JS to collapse if needed.

    return out
