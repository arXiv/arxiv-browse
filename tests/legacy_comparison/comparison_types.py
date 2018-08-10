from typing import Callable, Any
from mypy_extensions import TypedDict
from bs4 import BeautifulSoup
import requests

res_comparison_fn = Callable[[Any],
                             TypedDict('response_comparison_args',
                                       {'ng_url': str,
                                        'legacy_url': str,
                                        'ng_res': requests.Response,
                                        'legacy_res': requests.Response,
                                        'paperid': str})]

text_comparison_fn = Callable[[Any],
                              TypedDict('text_comparison_args',
                                        {'ng_url': str,
                                         'legacy_url': str,
                                         'ng_text': str,
                                         'legacy_text': str,
                                         'paperid': str})]

html_comparison_fn = Callable[[Any],
                              TypedDict('html_comparison_args',
                                        {'ng_url': str,
                                         'legacy_url': str,
                                         'ng_html': BeautifulSoup,
                                         'legacy_html': BeautifulSoup,
                                         'paperid': str})]
