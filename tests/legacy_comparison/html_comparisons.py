from functools import partial
from typing import Callable, List

import re

from tests.legacy_comparison.abstract_comparisons import lev_similarity
from tests.legacy_comparison.comparison_types import html_arg_dict, BadResult

from bs4 import BeautifulSoup


def html_similarity(html_arg: html_arg_dict) -> BadResult:
    sim = lev_similarity(
        html_arg['ng_html'].prettify().encode(
            'utf-8').decode('ascii', 'ignore'),
        html_arg['legacy_html'].prettify().encode(
            'utf-8').decode('ascii', 'ignore')
    )
    if sim < 0.69:
        return BadResult(html_arg['paper_id'], f"html_pretty_sim for {html_arg['paper_id']} = {sim}")
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
        return BadResult(html_arg['paper_id'],
                         "Metadata field included on NG do not match those from legacy" +
                         f"NG: {ng_labels} Legacy: {legacy_labels}")


def _strip_href(eles: BeautifulSoup):
    for ele in eles:
        for a in ele.find_all('a'):
            if a['href']:
                a['href'] = 'stripped_href'
        for link in ele.find_all('link'):
            if link['href']:
                link['href'] = 'stripped_href'
        for meta in ele.find_all('meta'):
            if meta['content']:
                meta['content'] = 'stripped_content'
        for script in ele.find_all('script'):
            if script['src']:
                script['src'] = 'stripped_src'
    return eles


def _element_similarity(name: str,
                        get_element: Callable[[BeautifulSoup], BeautifulSoup],
                        min_sim: float,
                        required: bool,
                        check_counts: bool,
                        html_arg: html_arg_dict) -> BadResult:
    """ Uses get_element to select an element of the BS doc on both NG and Legacy do a similarity. """
    legacy = get_element(html_arg['legacy_html'])
    ng = get_element(html_arg['ng_html'])

    if required:
        if len(ng) == 0 and len(legacy) == 0:
            return BadResult(html_arg['paper_id'], name,
                             f"Missing field {name} for {html_arg['paper_id']} from NG and Legacy")
        if len(ng) == 0:
            return BadResult(html_arg['paper_id'], name,
                             f"Missing field {name} for {html_arg['paper_id']} from NG")
        if len(legacy) == 0:
            return BadResult(html_arg['paper_id'], name,
                             f"Missing field {name} for {html_arg['paper_id']} from legacy")

    if check_counts and (len(legacy) != len(ng)):
        return BadResult(html_arg['paper_id'], name,
                         f"bad counts for {name} for {html_arg['paper_id']} ng: {len(ng)} legacy: {len(legacy)}")

    ng_ele_txt = ng[0].prettify().encode('utf-8').decode('ascii', 'ignore')
    legacy_ele_txt = legacy[0].prettify().encode(
        'utf-8').decode('ascii', 'ignore')
    sim = lev_similarity(ng_ele_txt, legacy_ele_txt)

    if sim < min_sim:
        msg = f"Elements did not meet min similarity of {min_sim}"
        return BadResult(html_arg['paper_id'], name, msg, legacy_ele_txt, ng_ele_txt, sim)
    return None


def strip_dig(eles: List[BeautifulSoup]):
    for ele in eles:
        for dig in ele.find_all(title=re.compile('digg', re.I)):
            dig.extract()
    return eles


author_similarity = partial(
    _element_similarity, 'authors div', lambda bs: _strip_href(bs.select('.authors')), 0.9, True, True)


dateline_similarity = partial(
    _element_similarity, 'dateline div', lambda bs: _strip_href(bs.select('.dateline')), 0.8, True, True)


history_similarity = partial(
    _element_similarity, 'submission-history div', lambda bs: _strip_href(bs.select('.submission-history')), 0.9, True, True)


title_similarity = partial(
    _element_similarity, 'title div', lambda bs: bs.select('.title'), 0.9, True, True)


subject_similarity = partial(
    _element_similarity, 'subjects td', lambda bs: bs.select('.subjects'), 0.98, True, True)


comments_similarity = partial(
    _element_similarity, 'comments td', lambda bs: bs.select('.comments'), 0.9, False, True)


extra_services_similarity = partial(
    _element_similarity, 'extra-services div', lambda bs: _strip_href(strip_dig(bs.select('.extra-services'))), 0.9, False, False)


head_similarity = partial(
    _element_similarity, 'head element', lambda bs: _strip_href(bs.select('head')), 0.80, True, True)
