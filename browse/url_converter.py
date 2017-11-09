"""URL conversion for paths containing arXiv IDs."""

import re
from werkzeug.routing import BaseConverter, ValidationError


class ArXivConverter(BaseConverter):
    """Route converter for arXiv IDs."""

    CATEGORIES = [
        "acc-phys", "adap-org", "alg-geom", "ao-sci", "astro-ph", "atom-ph",
        "bayes-an", "chao-dyn", "chem-ph", "cmp-lg", "comp-gas", "cond-mat",
        "cs", "dg-ga", "funct-an", "gr-qc", "hep-ex", "hep-lat", "hep-ph",
        "hep-th", "math", "math-ph", "mtrl-th", "nlin", "nucl-ex", "nucl-th",
        "patt-sol", "physics", "plasm-ph", "q-alg", "q-bio", "quant-ph",
        "solv-int", "supr-con", "eess", "econ"
    ]

    regex = ("((?:(?:(?:%s)(?:[.][A-Z]{2})?/[0-9]{2}(?:0[1-9]|1[0-2])"
             "\\d{3}(?:[vV]\\d+)?))|(?:(?:[0-9]{2}(?:0[1-9]|1[0-2])[.]"
             "\\d{4,5}(?:[vV]\\d+)?)))" % '|'.join(CATEGORIES))

    def to_python(self, value: str) -> str:
        """Parse URL path part to Python rep (str)."""
        m = re.match(self.regex, value)
        if not m:
            raise ValidationError('Not a valid arXiv ID')
        return m.group(1)

    def to_url(self, value: str) -> str:
        """Cast Python rep (str) to URL path part."""
        return value
