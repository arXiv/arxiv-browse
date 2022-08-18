"""Define comparison types."""
from dataclasses import dataclass
from typing import Callable, Optional

import requests
from bs4 import BeautifulSoup
from mypy_extensions import TypedDict


@dataclass
class BadResult:
    """Dataclass for maintaining information about a comparison result."""

    paper_id: str
    comparison: str
    message: str
    legacy: str = ''
    ng: str = ''
    similarity: float = 1


res_arg_dict = TypedDict('res_arg_dict',
                         {'ng_url': str,
                          'legacy_url': str,
                          'ng_res': requests.Response,
                          'legacy_res': requests.Response,
                          'paper_id': str})

res_comparison_fn = Callable[[res_arg_dict], Optional[BadResult]]

text_arg_dict = TypedDict('text_arg_dict',
                          {'ng_url': str,
                           'legacy_url': str,
                           'ng_res': requests.Response,
                           'legacy_res': requests.Response,
                           'ng_text': str,
                           'legacy_text': str,
                           'paper_id': str})

text_comparison_fn = Callable[[text_arg_dict], Optional[BadResult]]

html_arg_dict = TypedDict('html_arg_dict',
                          {'ng_url': str,
                           'legacy_url': str,
                           'ng_res': requests.Response,
                           'legacy_res': requests.Response,
                           'ng_text': str,
                           'legacy_text': str,
                           'ng_html': BeautifulSoup,
                           'legacy_html': BeautifulSoup,
                           'paper_id': str})

html_comparison_fn = Callable[[html_arg_dict], Optional[BadResult]]
