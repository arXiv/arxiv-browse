from tests.legacy_comparison.abstract_comparisons import lev_similarity
from tests.legacy_comparison.comparison_types import text_arg_dict, BadResult


def text_similarity(text_arg: text_arg_dict) -> BadResult:
    if lev_similarity(text_arg['ng_text'], text_arg['legacy_text']) < 0.74:
        res = f"text_sim for {text_arg['paperid']}  = {sim}"
        return BadResult(text_arg['paper_id'], 'text_similarity', res)
    else:
        return None
