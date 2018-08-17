""" Script to compare abs pages from NG and beta.arxiv.org

To run this I do:
Open terminal:
cd arxiv-browse
pipenv sync
FLASK_APP=app.py FLASK_DEBUG=1 pipenv run flask run

In another terminal:
cd arxiv-browse
pipenv sync
pipenv shell
python tests/legacy_comparison/abs_page_comparison.py

To reset the analysis to start over, add the `--reset` arg.

Improvements:
 Real comparisons, Only one toy comparision right now.
 Better reporting format, right now the comparisons produce just strings.
 Local caching of results (both ng and legacy) to speed up runtime.
"""

import argparse
from dataclasses import dataclass
import itertools
import sys
# BDC34: some how I need this under pipenv to get to browse, not sure why
sys.path.append('')

from tests.legacy_comparison.comparison_types import res_comparison_fn, \
    text_comparison_fn, html_comparison_fn, res_arg_dict, text_arg_dict,\
    html_arg_dict
from tests.legacy_comparison.response_comparisons import compare_status

import os
from functools import partial
import logging
from multiprocessing import Pool
import requests
from typing import Callable, Iterator, List, TypeVar

from browse.services.document.metadata import AbsMetaSession
from tests import path_of_for_test

from bs4 import BeautifulSoup

ABS_FILES = path_of_for_test('data/abs_files')
LOG_FILE_NAME = 'legacy_comparison.log'
VISITED_ABS_FILE_NAME = 'visited.log'

# List of comparison functions to run on response
res_comparisons: List[res_comparison_fn] = [compare_status]

# List of comparison functions to run on text of response
text_comparisons: List[text_comparison_fn] = []

# List of comparison functions to run on HTML parsed text of response
html_comparisons: List[html_comparison_fn] = []


def paperid_iterator(path: str, excluded: List[str]) -> List[str]:
    """Return an iterator of paperId strings for all abs found below path."""
    ids = []
    for (dir_name, subdir_list, file_list) in os.walk(path):
        for fname in file_list:
            fname_path = os.path.join(dir_name, fname)
            if os.stat(fname_path).st_size == 0:
                continue
            if not fname_path.endswith('.abs'):
                continue
            aid = AbsMetaSession.parse_abs_file(filename=fname_path).arxiv_id
            if aid not in excluded:
                ids.append(aid)
    return ids


# Should end with /
ng_abs_base_url = 'http://localhost:5000/abs/'

# Should end with /
legacy_abs_base_url = 'https://beta.arxiv.org/abs/'


T = TypeVar('T')


@dataclass
class Result:
    paper_id: str
    message: str
    __slots__ = ['paper_id', 'message']


def fetch_and_compare_abs(
        compare_res_fn: Callable[[res_arg_dict], List[Result]], paper_id: str
) -> List[Result]:
    ng_url = ng_abs_base_url + paper_id
    legacy_url = legacy_abs_base_url + paper_id

    res_dict: res_arg_dict = {'ng_url': ng_url,
                              'legacy_url': legacy_url,
                              'ng_res': requests.get(ng_url),
                              'legacy_res': requests.get(legacy_url),
                              'paperid': paper_id}

    return list(map(lambda msg: Result(paper_id, msg), compare_res_fn(res_dict)))


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


def main() -> None:
    parser = argparse.ArgumentParser(description='Compare ng browse to legacy browse')
    parser.add_argument('--reset', default=False, const=True, action='store_const', dest='reset')
    args = parser.parse_args()
    visited: List[str] = []
    if args.reset:
        print('Restarting analysis and deleting logs!')
        if os.path.exists(LOG_FILE_NAME):
            os.remove(LOG_FILE_NAME)
        if os.path.exists(VISITED_ABS_FILE_NAME):
            os.remove(VISITED_ABS_FILE_NAME)
    else:
        print('Continuing analysis')
        with open(VISITED_ABS_FILE_NAME, 'r') as visited_fh:
            visited = [line.rstrip() for line in visited_fh.readlines()]

    logging.basicConfig(filename=LOG_FILE_NAME, level=logging.INFO)
    # papers = paperid_iterator(ABS_FILES, excluded=visited)[:5]
    papers = paperid_iterator(ABS_FILES, excluded=visited)
    with open(VISITED_ABS_FILE_NAME, 'a') as visited_fh:
        with Pool(50) as pool:
            compare = partial(fetch_and_compare_abs, run_compare_response)
            results = pool.imap(compare, papers)
            for result in sum(results, []):
                visited_fh.write(f'{result.paper_id}\n')
                print(result.message)


if __name__ == '__main__':
    main()
