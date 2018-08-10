import itertools
import sys
# BDC34: some how I need this under pipenv to get to browse, not sure why
sys.path.append('')

from tests.legacy_comparison.comparison_types import res_comparison_fn, text_comparison_fn, html_comparison_fn, \
    res_arg_dict, text_arg_dict, html_arg_dict
from tests.legacy_comparison.response_comparisons import compare_status

import os
from functools import partial
from multiprocessing import Pool
import requests
from typing import Iterator, List, Callable, TypeVar

from browse.services.document.metadata import AbsMetaSession
from tests import path_of_for_test

from bs4 import BeautifulSoup

ABS_FILES = path_of_for_test('data/abs_files')


res_comparisons: List[res_comparison_fn] = [compare_status]
text_comparisons: List[text_comparison_fn] = []
html_comparisons: List[html_comparison_fn] = []


def paperid_iterator(path: str) -> List[str]:
    """Return an iterator of paperId strings for all abs found below path."""
    ids = []
    for (dir_name, subdir_list, file_list) in os.walk(path):
        for fname in file_list:
            fname_path = os.path.join(dir_name, fname)
            if os.stat(fname_path).st_size == 0:
                continue
            if not fname_path.endswith('.abs'):
                continue
            ids.append(AbsMetaSession.parse_abs_file(
                filename=fname_path).arxiv_id)
    return ids


# Should end with /
ng_abs_base_url = 'http://localhost:5000/abs/'

# Should end with /
legacy_abs_base_url = 'https://beta.arxiv.org/abs/'


T = TypeVar('T')


def fetch_and_compare_abs(compare_res_fn: Callable[[res_arg_dict], List[T]], paperid: str) -> List[T]:
    ng_url = ng_abs_base_url + paperid
    legacy_url = legacy_abs_base_url + paperid

    res_dict: res_arg_dict = {'ng_url': ng_url,
                              'legacy_url': legacy_url,
                              'ng_res': requests.get(ng_url),
                              'legacy_res': requests.get(legacy_url),
                              'paperid': paperid}

    return compare_res_fn(res_dict)


def run_compare_response(res_args: res_arg_dict) -> List[str]:

    text_dict: text_arg_dict = {**res_args, **{'ng_text': res_args['ng_res'].text,
                                               'legacy_text': res_args['legacy_res'].text}}

    def call_it(fn: Callable[[text_arg_dict], str]) -> str:
        try:
            return fn(text_dict)
        except Exception as ex:
            return str(ex)

    return list(filter(None, itertools.chain(
        map(call_it, res_comparisons), run_compare_text(text_dict))))


def run_compare_text(text_args: text_arg_dict) -> Iterator[str]:

    html_dict: html_arg_dict = {**text_args, **{'ng_html': BeautifulSoup(text_args['ng_text'], 'html.parser'),
                                                'legacy_html': BeautifulSoup(text_args['legacy_text'], 'html.parser')}}

    def call_it(fn: Callable[[html_arg_dict], str]) -> str:
        try:
            return fn(html_dict)
        except Exception as ex:
            return str(ex)

    return filter(None, itertools.chain(
        map(call_it, text_comparisons), run_compare_html(html_dict)))


def run_compare_html(html_args: html_arg_dict) -> Iterator[str]:
    def call_it(fn: Callable[[html_arg_dict], str]) -> str:
        try:
            return fn(html_args)
        except Exception as ex:
            return str(ex)

    return filter(None, map(call_it, html_comparisons))


papers = ['0704.0001', '0704.0600']
# papers = paperid_iterator(ABS_FILES)
with Pool(10) as p:
    compare = partial(fetch_and_compare_abs, run_compare_response)
    results = p.imap(compare, papers)
    for result in results:
        # TODO need to replace this with writing to a report file or something
        print(result)
