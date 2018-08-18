from weighted_levenshtein import lev


def lev_similarity(aa: str, bb: str) -> float:
    """
    :param aa: first string
    :param bb: second string
    :return: The similarity of the two strings (0=bad, 1=match):
             1- lev(aa,bb)/max(len(aa), len(bb))
    """
    # TODO, consider penalizing whitespace alterations less
    return 1.0 - lev(aa, bb)/max(len(aa), len(bb))
