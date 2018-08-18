import logging

from tests.legacy_comparison.abstract_comparisons import lev_similarity
from tests.legacy_comparison.comparison_types import html_arg_dict


def html_similarity(html_arg: html_arg_dict) -> str:
    sim = lev_similarity(
        html_arg['ng_html'].prettify().encode('utf-8').decode('ascii', 'ignore'),
        html_arg['legacy_html'].prettify().encode('utf-8').decode('ascii', 'ignore')
    )
    res = f"html_pretty_sim for {html_arg['paperid']} = {sim}"
    if sim < 0.69:
        logging.warning(res)
    return res

# html_comparison_fn = Callable[[Any],
#                               TypedDict('html_comparison_args',
#                                         {'ng_url': str,
#                                          'legacy_url': str,
#                                          'ng_html': BeautifulSoup,
#                                          'legacy_html': BeautifulSoup,
#                                          'paperid': str})]

#def compare_abs_fields()
