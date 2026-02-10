"""arxiv browse."""

from arxiv.integration.fastly.headers import add_surrogate_key
from werkzeug.datastructures import Headers



def b_add_surrogate_key(headers: dict[str,str]|Headers, keys: list[str]) -> Headers:
    # Fix for the type. Adds `Headers` to acceptable args. Probability should put in arxiv-base
    return add_surrogate_key(dict(headers), keys)
