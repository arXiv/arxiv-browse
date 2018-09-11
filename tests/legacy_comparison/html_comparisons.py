from functools import partial
from typing import Callable

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


def metadata_fields_similarity( html_arg: html_arg_dict) -> BadResult:
    # There should be a div.metatable
    # It may have others and if it does they must be on both NG an legacy pages.

    ng_trs = html_arg['ng_html'].find('div', 'metatable').find_all('tr')
    legacy_trs = html_arg['legacy_html'].find('div', 'metatable').find_all('tr')

    to_label = lambda tr: tr.find('td', 'label').contents
    ng_labels=set(ng_trs.map(to_label))
    legacy_labels = set(legacy_trs.map(to_label))

    if ng_labels == legacy_labels:
        return None
    else:
        return BadResult(html_arg['paper_id'],
                         "Metadata field included on NG do not match those from legacy" +
                         f"NG: {ng_labels} Legacy: {legacy_labels}")


def _strip_href( ele: BeautifulSoup ):
    for a in ele.find_all('a'):
        if a['href']:
            a['href'] = 'stripped_href'


def _element_similarity(name: str,
                        get_element: Callable[[BeautifulSoup], BeautifulSoup],
                        min_sim: float,
                        required: bool,
                        strip_href: bool,
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

    if len(legacy) != len(ng) or len(ng) != 1 or len(legacy) != 1:
        return BadResult(html_arg['paper_id'], name,
                         f"bad counts for {name} for {html_arg['paper_id']} ng: {len(ng)} legacy: {len(legacy)}")

    ng_ele = ng[0]
    legacy_ele = legacy[0]
    if strip_href :
        _strip_href(ng_ele)
        _strip_href(legacy_ele)

    sim = lev_similarity(
        ng_ele.prettify().encode('utf-8').decode('ascii', 'ignore'),
        legacy_ele.prettify().encode('utf-8').decode('ascii', 'ignore')
    )

    if sim < min_sim:
        msg = f"Elements did not meet min similarity of {min_sim}"
        return BadResult(html_arg['paper_id'], name, msg, legacy[0], ng[0], sim)
    return None


author_similarity = partial(
    _element_similarity, 'authors div', lambda bs: bs.select('.authors'), 0.9, True, True)


dateline_similarity = partial(
    _element_similarity, 'dateline div', lambda bs: bs.select('.dateline'), 0.8, True, True)


history_similarity = partial(
    _element_similarity, 'submission-history div', lambda bs: bs.select('.submission-history'), 0.9, True, True)


title_similarity = partial(
    _element_similarity, 'title div', lambda bs: bs.select('.title'), 0.9, True, False)


subject_similarity = partial(
    _element_similarity, 'subjects td', lambda bs: bs.select('.subjects'), 0.98, True, False)


comments_similarity = partial(
    _element_similarity, 'comments td', lambda bs: bs.select('.comments'), 0.9, False, False)


extra_services_similarity = partial(
    _element_similarity, 'extra-services div', lambda bs: bs.select('.extra-services'), 0.9, False, True)


head_similarity = partial(
    _element_similarity, 'head element', lambda bs: bs.select('head'), 0.85, True, True)

