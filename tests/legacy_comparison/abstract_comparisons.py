from weighted_levenshtein import lev


def lev_similarity(aa: str, bb: str) -> float:
    """
    :param aa: first string
    :param bb: second string
    :return: The similarity of the two strings (0=bad, 1=match):
             1- lev(aa,bb)/max(len(aa), len(bb))
    """

    # Since weighted levenshtein can't handle unicode,
    # convert to ASCII first:

    def convert_to_ascii(text: str, label: str) -> str:
        try:
            text_out = text.encode('ascii', 'ignore')
            return text_out
        except Exception as ex:
            raise Exception(f'Could not encode f{label}: f{aa}') from ex

    aa = convert_to_ascii(aa, 'aa')
    bb = convert_to_ascii(bb, 'bb')

    # TODO, consider penalizing whitespace alterations less
    return 1.0 - lev(aa, bb)/max(len(aa), len(bb))
