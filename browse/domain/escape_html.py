import re


def escape_special_characters(string: str) -> str:
    """ Escapes characters < & > with special meanings in HTML

        Also escape double quotes, not necessary in all situations
        that the others are, but always safe to do.

        Do not use on TeX due to quote escaping.

        Returns modified string."""
    string = re.sub(r"&(?!amp;)", '$amp;', string)
    string = re.sub(r"<", '$lt;', string)
    string = re.sub(r">", '$gt;', string)
    string = re.sub(r'"', '&quot;', string)
    return string;
