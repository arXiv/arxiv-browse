from typing import Callable, Any
from mypy_extensions import TypedDict
from bs4 import BeautifulSoup
import requests

res_arg_dict = TypedDict('res_arg_dict',
                         {'ng_url': str,
                          'legacy_url': str,
                          'ng_res': requests.Response,
                          'legacy_res': requests.Response,
                          'paperid': str})

res_comparison_fn = Callable[[res_arg_dict], Any]

text_arg_dict = TypedDict('text_arg_dict',
                          {'ng_url': str,
                           'legacy_url': str,
                           'ng_res': requests.Response,
                           'legacy_res': requests.Response,
                           'ng_text': str,
                           'legacy_text': str,
                           'paperid': str})

text_comparison_fn = Callable[[text_arg_dict], Any]

html_arg_dict = TypedDict('html_arg_dict',
                          {'ng_url': str,
                           'legacy_url': str,
                           'ng_res': requests.Response,
                           'legacy_res': requests.Response,
                           'ng_text': str,
                           'legacy_text': str,
                           'ng_html': BeautifulSoup,
                           'legacy_html': BeautifulSoup,
                           'paperid': str})

html_comparison_fn = Callable[[html_arg_dict], Any]
