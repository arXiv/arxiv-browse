"""Includes function for calculating text similarity."""
from abstract_comparisons import lev_similarity
from comparison_types import BadResult, text_arg_dict


def text_similarity(text_arg: text_arg_dict) -> BadResult:
    """Compute Levenshtein similarity of text."""
    sim = lev_similarity(text_arg['ng_text'], text_arg['legacy_text'])
    if sim < 0.74:
        res = f"text_sim for {text_arg['paper_id']}  = {sim}"
        return BadResult(text_arg['paper_id'], 'text_similarity', res)
    else:
        return None
