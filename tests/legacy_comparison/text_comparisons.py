import logging

from tests.legacy_comparison.abstract_comparisons import lev_similarity
from tests.legacy_comparison.comparison_types import text_arg_dict


<<<<<<< c3e5b3a8872cccc32e5c6d8dbbbf791fddeef9ec
def text_similarity(text_arg: text_arg_dict) -> str:
    sim = lev_similarity(text_arg['ng_text'], text_arg['legacy_text'])
    res = f"text_sim for {text_arg['paperid']}  = {sim}"
    if sim < 0.74:
        logging.warning(res)
    # else:
    #     logging.info(res)
    return res
=======
def text_similarity(text_arg: text_arg_dict) -> BadResult:
    sim = lev_similarity(text_arg['ng_text'], text_arg['legacy_text'])
    if sim < 0.74:
        res = f"text_sim for {text_arg['paper_id']}  = {sim}"
        return BadResult(text_arg['paper_id'], 'text_similarity', res)
    else:
        return None
>>>>>>> Fixing bug with legacy comparison for text, and removal of hrefs
