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


def _element_similarity(name: str,
                        get_element: Callable[[BeautifulSoup], BeautifulSoup],
                        min_sim: float,
                        html_arg: html_arg_dict) -> BadResult:
    """ Uses get_element to select an element of the BS doc on both NG and Legacy do a similarity. """
    legacy = get_element(html_arg['legacy_html'])
    ng = get_element(html_arg['ng_html'])

    if len(ng) == 0 and len(legacy) == 0:
        return None

    if len(legacy) != len(ng) or len(ng) != 1 or len(legacy) != 1:
        return BadResult(html_arg['paper_id'], name,
                         f"bad counts for {name} for {html_arg['paper_id']} ng: {len(ng)} legacy: {len(legacy)}")

    sim = lev_similarity(
        ng[0].prettify().encode('utf-8').decode('ascii', 'ignore'),
        legacy[0].prettify().encode('utf-8').decode('ascii', 'ignore')
    )

    if sim < min_sim:
        msg = f"Elements did not meet min similarity of {min_sim}"
        return BadResult(html_arg['paper_id'], name, msg, legacy[0], ng[0], sim)
    return None


author_similarity = partial(
    _element_similarity, 'authors div', lambda bs: bs.select('.authors'), 0.80)


dateline_similarity = partial(
    _element_similarity, 'dateline div', lambda bs: bs.select('.dateline'), 0.8)


history_similarity = partial(
    _element_similarity, 'submission-history div', lambda bs: bs.select('.submission-history'), 0.8)


title_similarity = partial(
    _element_similarity, 'title div', lambda bs: bs.select('.title'), 0.9)


subject_similarity = partial(
    _element_similarity, 'subjects td', lambda bs: bs.select('.subjects'), 0.98)


comments_similarity = partial(
    _element_similarity, 'comments td', lambda bs: bs.select('.comments'), 0.8)


extra_services_similarity = partial(
    _element_similarity, 'extra-services div', lambda bs: bs.select('.extra-services'), 0.7)


head_similarity = partial(
    _element_similarity, 'head element', lambda bs: bs.select('head'), 0.7)
