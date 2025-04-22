"""Define comparison types."""
from dataclasses import dataclass
from typing import Callable, Optional, TypedDict

import requests
from bs4 import BeautifulSoup

@dataclass
class BadResult:
    """Dataclass for maintaining information about a comparison result."""

    paper_id: str
    comparison: str
    message: str
    legacy: str = ''
    ng: str = ''
    similarity: float = 1


class res_arg_dict(TypedDict):
    ng_url: str
    legacy_url: str
    ng_res: requests.Response
    legacy_res: requests.Response
    paper_id: str

res_comparison_fn = Callable[[res_arg_dict], Optional[BadResult]]

class text_arg_dict(TypedDict):
    ng_url: str
    legacy_url: str
    ng_res: requests.Response
    legacy_res: requests.Response
    ng_text: str
    legacy_text: str
    paper_id: str

text_comparison_fn = Callable[[text_arg_dict], Optional[BadResult]]

class html_arg_dict (TypedDict):
    ng_url: str
    legacy_url: str
    ng_res: requests.Response
    legacy_res: requests.Response
    ng_text: str
    legacy_text: str
    ng_html: BeautifulSoup
    legacy_html: BeautifulSoup
    paper_id: str

html_comparison_fn = Callable[[html_arg_dict], Optional[BadResult]]
