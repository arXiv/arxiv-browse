import argparse
import itertools
import sys
import traceback
import os
import re
from functools import partial
from multiprocessing import Pool
from typing import Callable, Iterator, List, Set, Tuple, Dict

import requests
from bs4 import BeautifulSoup

sys.path.append('')  # BDC34: some how I need this under pipenv to get to browse, not sure why
sys.setrecursionlimit(10000)

from tests.legacy_comparison.comparison_types import res_comparison_fn, \
    text_comparison_fn, html_comparison_fn, res_arg_dict, text_arg_dict, \
    html_arg_dict, BadResult
from tests.legacy_comparison.html_comparisons import author_similarity,dateline_similarity, history_similarity,\
    title_similarity,subject_similarity, comments_similarity, extra_services_similarity, head_similarity
from tests.legacy_comparison.response_comparisons import compare_status
from tests.legacy_comparison.text_comparisons import text_similarity
from browse.services.document.metadata import AbsMetaSession
from tests import path_of_for_test


""" Script to compare abs pages from NG and arxiv.org

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
To run a short test add '--short' arg.

To skip ancillary file comparisons: '--skip-ancillary'

Improvements:
 Better reporting format, right now the comparisons produce just strings. 
"""

ABS_FILES = path_of_for_test('data/abs_files')
LOG_FILE_NAME = 'legacy_comparison.org'
VISITED_ABS_FILE_NAME = 'visited.log'

# List of comparison functions to run on response
res_comparisons: List[res_comparison_fn] = [compare_status]

# List of comparison functions to run on text of response
text_comparisons: List[text_comparison_fn] = [text_similarity]

# List of comparison functions to run on HTML parsed text of response
html_comparisons: List[html_comparison_fn] = [
    author_similarity,
    dateline_similarity,
    history_similarity,
    title_similarity,
    subject_similarity,
    comments_similarity,
    extra_services_similarity,
    head_similarity,
]


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
legacy_abs_base_url = 'https://arxiv.org/abs/'


def fetch_abs(compare_res_fn: Callable[[res_arg_dict], List[BadResult]], paper_id: str) -> Tuple[Dict, List[BadResult]]:
    ng_url = ng_abs_base_url + paper_id
    legacy_url = legacy_abs_base_url + paper_id

    res_dict: res_arg_dict = {'ng_url': ng_url,
                              'legacy_url': legacy_url,
                              'ng_res': requests.get(ng_url),
                              'legacy_res': requests.get(legacy_url),
                              'paper_id': paper_id}
    compare_config = {'ng_url': ng_url,
                      'legacy_url': legacy_url,
                      'paper_id': paper_id}
    return compare_config, list(compare_res_fn(res_dict))


def run_compare_response(skips: Set[str], res_args: res_arg_dict) -> Iterator[BadResult]:
    """ This is also where we do most of the cleaning on text, for things
    we know that we do not want to compare."""
    legacy_text = res_args['legacy_res'].text
    legacy_text = strip_by_delim(legacy_text, '<!-- Piwik -->',  '<!-- End Piwik Code -->')
    legacy_text = strip_by_delim(legacy_text, '<!--\nfunction toggleList',  '//-->')

    if 'skip_anc' in skips:
        legacy_text = strip_by_delim(legacy_text, '<div class="ancillary">',  '<!--end ancillary-->')

    text_dict: text_arg_dict = {**res_args, **{'ng_text': res_args['ng_res'].text,
                                               'legacy_text': legacy_text}}

    def call_it(fn: Callable[[text_arg_dict], BadResult]) -> BadResult:
        # noinspection PyBroadException
        try:
            return fn(text_dict)
        except Exception as ex:
             return BadResult(res_args['paper_id'], 'run_compare_response', traceback.format_exc())

    return filter(None, itertools.chain(
        map(call_it, res_comparisons), run_compare_text(text_dict)))


def run_compare_text(text_args: text_arg_dict) -> Iterator[BadResult]:
    html_dict = process_text(text_args)

    def call_it(fn: Callable[[html_arg_dict], BadResult]) -> BadResult:
        # noinspection PyBroadException
        try:
            return fn(html_dict)
        except Exception as ex:
            return BadResult(text_args['paper_id'], 'run_compare_text', traceback.format_exc())

    return filter(None, itertools.chain(
        map(call_it, text_comparisons), run_compare_html(html_dict)))


def run_compare_html(html_args: html_arg_dict) -> Iterator[BadResult]:
    def call_it(fn: Callable[[html_arg_dict], BadResult]) -> BadResult:
        # noinspection PyBroadException
        try:
            return fn(html_args)
        except Exception as ex:
            return BadResult(html_args['paper_id'], 'run_compare_html', traceback.format_exc())

    return filter(None, map(call_it, html_comparisons))


def rm_email_hash(text: str) -> str:
    return re.sub(r'show-email/\w+/', 'show-email/', text)


def process_text(text_args: text_arg_dict) -> html_arg_dict:
    text_args['ng_text'] = ' '.join(text_args['ng_text'].split())
    text_args['legacy_text'] = ' '.join(text_args['legacy_text'].split())

    text_args['ng_text'] = rm_email_hash(text_args['ng_text'])
    text_args['legacy_text'] = rm_email_hash(text_args['legacy_text'])

    html_dict: html_arg_dict = {**text_args, **{
        'ng_html': BeautifulSoup(text_args['ng_text'], 'html.parser'),
        'legacy_html': BeautifulSoup(text_args['legacy_text'], 'html.parser')
    }}

    return html_dict


def main() -> None:
    parser = argparse.ArgumentParser(description='Compare ng browse to legacy browse')
    parser.add_argument('--reset', default=False, const=True, action='store_const', dest='reset')
    parser.add_argument('--short', default=False, const=True, action='store_const', dest='short')
    parser.add_argument('--skip-ancillary', default=False, const=True, action='store_const', dest='skip_anc')
    args = parser.parse_args()
    visited: List[str] = []
    skip_checks: Set[str] = set()
    if args.reset:
        print('Restarting analysis and deleting logs!')
        if os.path.exists(LOG_FILE_NAME):
            os.remove(LOG_FILE_NAME)
        if os.path.exists(VISITED_ABS_FILE_NAME):
            os.remove(VISITED_ABS_FILE_NAME)
    else:
        if os.path.exists(VISITED_ABS_FILE_NAME):
            print('Continuing analysis')
            with open(VISITED_ABS_FILE_NAME, 'r') as visited_fh:
                visited = [line.rstrip() for line in visited_fh.readlines()]
 
    if args.short:
        papers = paperid_iterator(ABS_FILES, excluded=visited)[:5]
    else:
        papers = paperid_iterator(ABS_FILES, excluded=visited)

    if args.skip_anc:
        skip_checks.add('skip_anc')

    run_selected_compare_response = partial(run_compare_response, skip_checks)

    with open(VISITED_ABS_FILE_NAME, 'a') as visited_fh:
        with open(LOG_FILE_NAME, 'w')as report_fh:
            with Pool(10) as pool:
                fetch_and_compare_fn = partial(fetch_abs, run_selected_compare_response)
                completed_jobs = pool.imap(fetch_and_compare_fn, papers)
                for job in completed_jobs:
                    (config, bad_results) = job
                    visited_fh.write(f"{config['paper_id']}\n")
                    write_comparison(report_fh, (config,bad_results))


def write_comparison(report_fh, result: Tuple[Dict, List[BadResult]])-> None:
    (config, bad_results) = result
    if not bad_results:
        report_fh.write(f"* {config['paper_id']}: okay.\n")
        return
    report_fh.write(f"* {config['paper_id']}: not okay, had {len(bad_results)} bad results.\n")
    for br in bad_results:
        report_fh.write(format_bad_result(br))


def format_bad_result(bad: BadResult)->str:
    rpt = f"** {bad.comparison}\n" \
          f"{bad.message} "
    if bad.similarity:
        rpt = rpt + f"sim: {bad.similarity}\n"
    else:
        rpt = rpt + "\n"

    if bad.legacy or bad.ng:
        rpt = rpt + f"Legacy: '{bad.legacy}'\nNG: '{bad.ng}'\n"

    return rpt


def strip_by_delim(text: str, start: str, end: str) -> str:

    if (start in text) and (end in text):
        def find_start() -> int:
            return text.index(start)

        def find_end() -> int:
            return text.index(end) + len(end)

        return text[:find_start()] + text[find_end():]
    else:
        return text


if __name__ == '__main__':
    main()
