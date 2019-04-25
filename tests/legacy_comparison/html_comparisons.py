from functools import partial, update_wrapper
from typing import Callable, List

import re

from abstract_comparisons import lev_similarity
from comparison_types import html_arg_dict, BadResult

from bs4 import BeautifulSoup, element


def html_similarity(html_arg: html_arg_dict) -> BadResult:
    sim = lev_similarity(
        html_arg['ng_html'].prettify(),
        html_arg['legacy_html'].prettify()
    )
    if sim < 0.69:
        return BadResult(html_arg['id'],
                         "html_similarity",
                         f"html_pretty_sim for {html_arg['id']} = {sim}")
    return None


def metadata_fields_similarity(html_arg: html_arg_dict) -> BadResult:
    # There should be a div.metatable
    # It may have others and if it does they must be on both NG an legacy pages.

    ng_trs = html_arg['ng_html'].find('div', 'metatable').find_all('tr')
    legacy_trs = html_arg['legacy_html'].find(
        'div', 'metatable').find_all('tr')

    def to_label(tr): return tr.find('td', 'label').contents
    ng_labels = set(ng_trs.map(to_label))
    legacy_labels = set(legacy_trs.map(to_label))

    if ng_labels == legacy_labels:
        return None
    else:
        return BadResult(html_arg['id'],
                         "Metadata field included on NG do not match those from legacy" +
                         f"NG: {ng_labels} Legacy: {legacy_labels}")


def _replace(tag: element.Tag, att: str, new_value: str):
    if tag and tag.attrs and att in tag.attrs:
        tag[att] = new_value


def _strip_href(eles: List[BeautifulSoup]):
    for ele in eles:
        for a in ele.find_all('a'): _replace(a,'href','stripped_href')
        for link in ele.find_all('link'): _replace(link,'href','stripped_href')
        for meta in ele.find_all('meta'): _replace(meta, 'content', 'stripped_content')
        for script in ele.find_all('script'): _replace(script,'src','stripped_src')
    return eles


def _element_similarity(name: str,
                        get_element: Callable[[BeautifulSoup], BeautifulSoup],
                        min_sim: float,
                        required: bool,
                        check_counts: bool,
                        text_trans: Callable[[str],str],
                        html_arg: html_arg_dict) -> BadResult:
    """ Uses get_element to select an element of the BS doc on both NG and Legacy do a similarity. 

    required: element must be in both NG and Legacy.
    check_counts: counts of elements must be the same in both NG and Legacy, could be 0.
"""
    legacy = get_element(html_arg['legacy_html'])
    ng = get_element(html_arg['ng_html'])

    if required:
        if len(ng) == 0 and len(legacy) == 0:
            return BadResult(html_arg['id'], name,
                             f"Missing field {name} for {html_arg['id']} from NG and Legacy")
        if len(ng) == 0:
            return BadResult(html_arg['id'], name,
                             f"Missing field {name} for {html_arg['id']} from NG")
        if len(legacy) == 0:
            return BadResult(html_arg['id'], name,
                             f"Missing field {name} for {html_arg['id']} from legacy")

    if check_counts and (len(legacy) != len(ng)):
        if ng:
            ng_ele_txt = ng[0].prettify()
        else:
            ng_ele_txt = 'MISSING'
        if legacy:
            legacy_ele_txt = legacy[0].prettify()
        else:
            legacy_ele_txt = 'MISSING'
            
        return BadResult(html_arg['id'], name,
                         f"bad counts for {name} for {html_arg['id']} ng: {len(ng)} legacy: {len(legacy)}",
                         legacy_ele_txt, ng_ele_txt)

    ng_ele_txt = ''
    legacy_ele_txt = ''

    if len(ng) > 0 and len(legacy) > 0:
        ng_ele_txt = text_trans(ng[0].prettify())
        legacy_ele_txt = text_trans(legacy[0].prettify())
        sim = lev_similarity(ng_ele_txt, legacy_ele_txt)

        if sim < min_sim:
            msg = f"Elements did not meet min similarity of {min_sim}"
            return BadResult(html_arg['id'], name, msg, legacy_ele_txt,
                             ng_ele_txt, sim)

        msg = f"GOOD: Elements did meet min similarity of {min_sim}"
        return  BadResult(html_arg['id'], name, msg, '','', sim)
    else:
        if not required:
            return None

        if len(ng) > 0:
            ng_ele_txt = ng[0].prettify()
        if len(legacy) > 0:
            legacy_ele_txt = legacy[0].prettify()

        msg = 'zero elements detected: ' \
              + f'legacy length was {len(legacy)}; ng length was {len(ng)} '
        return BadResult(html_arg['id'], name, msg, legacy_ele_txt,
                         ng_ele_txt, 0.0)


def strip_dig(eles: List[BeautifulSoup]):
    for ele in eles:
        for dig in ele.find_all(title=re.compile('digg', re.I)):
            dig.extract()
    return eles


def _strip_script_and_noscript( eles: List[BeautifulSoup]):
    for ele in eles:
        for srpt in ele.find_all('script'):
            srpt.extract()
        for nos in ele.find_all('noscript'):
            nos.extract()
    return eles


def ident(x):
    return x

author_similarity = partial(
    _element_similarity, 'authors div',
    lambda bs: _strip_href(_strip_script_and_noscript(bs.select('.authors'))),
    0.9, True, True, ident)


dateline_similarity = partial(
    _element_similarity, 'dateline div', lambda bs: _strip_href(bs.select('.dateline')), 0.8, True, True, ident)



def normalize_history(sin):
    return sin\
        .replace('GMT', '[normalized_gmt_utc]').replace('UTC', '[normalized_gmt_utc]')\
        .replace(' KB)', ' [normalized_kb])').replace('kb)', ' [normalized_kb])')


history_similarity = partial(
    _element_similarity, 'submission-history div',
    lambda bs: _strip_href(bs.select('.submission-history')),
    0.9, True, True,
    normalize_history)


title_similarity = partial(
    _element_similarity, 'title div', lambda bs: bs.select('.title'), 0.9, True, True, ident)


subject_similarity = partial(
    _element_similarity, 'subjects td', lambda bs: bs.select('.subjects'), 0.98, True, True, ident)


comments_similarity = partial(
    _element_similarity, 'comments td', lambda bs: bs.select('.comments'), 0.9, False, True, ident)

head_similarity = partial(
    _element_similarity, 'head element', lambda bs: _strip_href(bs.select('head')), 0.80, True, True, ident)

############ div.extra-services Checks #################

def ex_strip(eles: List[BeautifulSoup]):
    return _strip_href(strip_dig( eles))


extra_full_text_similarity = partial(_element_similarity, 'extra full-text div',
                                     lambda bs: ex_strip(bs.select('div.full-text')),
                                     0.9,True,True, ident)

ancillary_similarity = partial(_element_similarity, 'extra ancillary div',
                               lambda bs: ex_strip(bs.select('div.ancillary')),
                               0.9, False, True, ident)

extra_ref_cite_similarity = partial(_element_similarity, 'extra ref_cite div',
                                    lambda bs: ex_strip(bs.select('div.extra-ref-cite')),
                                    0.9, False, True, ident)

extra_general_similarity = partial(_element_similarity, 'extra extra-general div',
                                   lambda bs: ex_strip(bs.select('div.extra-general')),
                                   0.9, False, True, ident)

extra_browse_similarity = partial(_element_similarity, 'extra browse div',
                                  lambda bs: ex_strip(bs.select('div.browse')),
                                  0.9, True, True, ident)

dblp_similarity = partial(_element_similarity, 'extra DBLP div',
                          lambda bs: ex_strip(bs.select('.dblp')),
                          0.9, False, True, ident)

bookmarks_similarity = partial(_element_similarity, 'extra bookmarks div',
                               lambda bs: ex_strip(bs.select('.bookmarks')),
                               0.9, False, True, ident)

################# /archive checks ################################

archive_h1_similarity = partial(_element_similarity, 'top heading',
                               lambda bs: ex_strip(bs.select('#content > h1')),
                                0.99, True, True, ident)

archive_browse = partial(_element_similarity, 'browse',
                               lambda bs: ex_strip(bs.select('#content > ul > li:nth-child(1)')),
                               0.99, True, True, ident)

archive_catchup = partial(_element_similarity, 'archive catchup',
                               lambda bs: ex_strip(bs.select('#content > ul > li:nth-child(2)')),
                               0.99, True, True, ident)

archive_search= partial(_element_similarity, 'archive_search',
                               lambda bs: ex_strip(bs.select('#content > ul > li:nth-child(3)')),
                               0.99, True, True, ident)

archive_by_year= partial(_element_similarity, 'archive_by_year',
                               lambda bs: ex_strip(bs.select('#content > ul > li:nth-child(4)')),
                               0.99, True, True, ident)


archive_bogus= partial(_element_similarity, 'bogus_should_fail',
                               lambda bs: ex_strip(bs.select('.bogusClass')),
                               0.99, True, True, ident)


