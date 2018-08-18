import logging

from tests.legacy_comparison.abstract_comparisons import lev_similarity
from tests.legacy_comparison.comparison_types import text_arg_dict


def text_similarity(text_arg: text_arg_dict) -> str:
    sim = lev_similarity(text_arg['ng_text'], text_arg['legacy_text'])
    res = f"text_sim for {text_arg['paperid']}  = {sim}"
    if sim < 0.62:
        logging.warning(res)
    return res
