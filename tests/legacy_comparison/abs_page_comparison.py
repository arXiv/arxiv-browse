"""Abs page comparison tests."""
import argparse
import gzip
import itertools
import json
import logging
import os
import re
import sys
import traceback
from functools import partial
from multiprocessing import Pool
from typing import Callable, Dict, Iterator, List, Set, Tuple

import requests
from bs4 import BeautifulSoup

from arxiv.document.parse_abs import parse_abs_file

from comparison_types import (
    BadResult,
    html_arg_dict,
    html_comparison_fn,
    res_arg_dict,
    res_comparison_fn,
    text_arg_dict,
    text_comparison_fn,
)
from html_comparisons import (
    ancillary_similarity,
    author_similarity,
    bookmarks_similarity,
    comments_similarity,
    dateline_similarity,
    dblp_similarity,
    extra_full_text_similarity,
    extra_general_similarity,
    extra_ref_cite_similarity,
    head_similarity,
    history_similarity,
    subject_similarity,
    title_similarity,
)
from response_comparisons import compare_status
from text_comparisons import text_similarity


# BDC34: some how I need this under pipenv to get to browse, not sure why
sys.path.append('')
sys.setrecursionlimit(10000)





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
To run a short test add '--short' arg.

To skip ancillary file comparisons: '--skip-ancillary'

Improvements:
 Better reporting format, right now the comparisons produce just strings.
"""

logging.basicConfig(filename="abs_page_comparison.log", level=logging.DEBUG)

ABS_FILES = 'tests/data/abs_files'
LOG_FILE_NAME = 'legacy_comparison.org'
VISITED_ABS_FILE_NAME = 'visited.log'

# List of comparison functions to run on response
res_comparisons: List[res_comparison_fn] = [compare_status]

# List of comparison functions to run on text of response
#text_comparisons: List[text_comparison_fn] = [text_similarity]
text_comparisons: List[text_comparison_fn] = []

# List of comparison functions to run on HTML parsed text of response
html_comparisons: List[html_comparison_fn] = [
    author_similarity,
    dateline_similarity,
    history_similarity,
    title_similarity,
    subject_similarity,
    comments_similarity,
    # in 2019-04-16: not checking head due to changes to css and feedback collector etc
#    head_similarity, #
    extra_full_text_similarity,
    ancillary_similarity,
    extra_ref_cite_similarity,
    extra_general_similarity,
    dblp_similarity,
# in 2019-04-16: not checking bookmarks due to dropping delicious
#    bookmarks_similarity
]



def _paperid_generator_from_file(path: str, excluded: List[str])->Iterator[str]:
    if 'gzip' in path or 'gz' in path:
        with gzip.open(path, 'rt') as f:
            for line in f:
                aid = line.strip()
                if aid not in excluded:
                    logging.debug(f'yielding id {aid}')
                    yield aid
    else:
        with open(path, 'rt') as f:
            for line in f:
                aid = line.strip()
                if aid not in excluded:
                    logging.debug(f'yielding id {aid}')
                    yield aid



def paperid_generator(path: str, excluded: List[str]) -> Iterator[str]:
    """Generate an arXiv paper ID."""
    for ( dir_name, subdir_list, file_list) in os.walk(path):
        for fname in file_list:
            fname_path = os.path.join(dir_name, fname)
            print(f'looking at {fname_path}')
            if os.stat(fname_path).st_size != 0 and fname_path.endswith('.abs'):
                aid = parse_abs_file(filename=fname_path).arxiv_id
                logging.debug(f'yielding id {aid}')
                yield aid


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
            aid = parse_abs_file(filename=fname_path).arxiv_id
            if aid not in excluded:
                ids.append(aid)
    logging.debug(f'finished getting the ids count:{len(ids)}')
    return ids


# Should end with /
#ng_abs_base_url = 'http://localhost:5000/abs/'
ng_abs_base_url = 'https://beta.arxiv.org/abs/'

# Should end with /
legacy_abs_base_url = 'https://beta.arxiv.org/abs_classic/'


def fetch_abs(compare_res_fn: Callable[[res_arg_dict], List[BadResult]], paper_id: str) -> Tuple[Dict, List[BadResult]]:
    """Fetch an abs page."""
    ng_url = ng_abs_base_url + paper_id
    legacy_url = legacy_abs_base_url + paper_id

    res_dict: res_arg_dict = {'ng_url': ng_url,
                              'legacy_url': legacy_url,
                              'ng_res': requests.get(ng_url),
                              'legacy_res': requests.get(legacy_url),
                              'paper_id': paper_id,
                              'id': paper_id}
    compare_config = {'ng_url': ng_url,
                      'legacy_url': legacy_url,
                      'paper_id': paper_id,
                      'id': paper_id}
    return compare_config, list(compare_res_fn(res_dict))


def run_compare_response(skips: Set[str], res_args: res_arg_dict) -> Iterator[BadResult]:
    """
    Compare responses.

    This is also where we do most of the cleaning on text, for things
    we know that we do not want to compare.
    """
    legacy_text = res_args['legacy_res'].text
    ng_text = res_args['ng_res'].text

    legacy_text = strip_by_delim(legacy_text, '<!-- Piwik -->',  '<!-- End Piwik Code -->')
    legacy_text = strip_by_delim(
        legacy_text,
        '<script type="text/javascript">\n<!--\nfunction toggleList',
        '//-->\n</script>'
    )

    if 'skip_anc' in skips:
        legacy_text = strip_by_delim(legacy_text, '<div class="ancillary">',  '<!--end ancillary-->')

    text_dict: text_arg_dict = {**res_args, **{'ng_text': ng_text, 'legacy_text': legacy_text}}

    def call_it(fn: Callable[[text_arg_dict], BadResult]) -> BadResult:
        # noinspection PyBroadException
        try:
            return fn(text_dict)
        except Exception as ex:
             return BadResult(res_args['paper_id'], 'run_compare_response', traceback.format_exc())

    logging.debug(f"about to do compares for {res_args['paper_id']}")

    return filter(None, itertools.chain(
        map(call_it, res_comparisons), run_compare_text(text_dict)))


def run_compare_text(text_args: text_arg_dict) -> Iterator[BadResult]:
    """Run the text comparison."""
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
    """Run comparison against HTML."""
    logging.debug(f'about to run HTML compares for {html_args["paper_id"]}')

    def call_it(fn: Callable[[html_arg_dict], BadResult]) -> BadResult:
        # noinspection PyBroadException
        try:
            return fn(html_args)
        except Exception as ex:
            return BadResult(html_args['paper_id'], 'run_compare_html', traceback.format_exc())

    rv = filter(None, map(call_it, html_comparisons))
    logging.debug(f'done with HTML compares for {html_args["paper_id"]}')
    return rv


def rm_email_hash(text: str) -> str:
    """Remove the hash from the email link."""
    return re.sub(r'show-email/\w+/', 'show-email/', text)


def process_text(text_args: text_arg_dict) -> html_arg_dict:
    """Process text for comparison."""
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
    """Run the abs page comparison with provided arguments."""
    parser = argparse.ArgumentParser(
        description='Compare ng browse to legacy browse')
    parser.add_argument('--ids', default=False, )
    parser.add_argument('--reset', default=False, const=True,
                        action='store_const', dest='reset')
    parser.add_argument('--short', default=False, const=True,
                        action='store_const', dest='short')
    parser.add_argument('--skip-ancillary', default=False, const=True,
                        action='store_const', dest='skip_anc')
    args = parser.parse_args()
    visited: Set[str] = []
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
                visited = {line.rstrip() for line in visited_fh.readlines()}

    if args.ids:
        papers = _paperid_generator_from_file(args.ids, excluded=visited)
    else:
        papers = paperid_iterator(ABS_FILES, excluded=visited)

    if args.skip_anc:
        skip_checks.add('skip_anc')

    run_selected_compare_response = partial(run_compare_response, skip_checks)

    if args.short:
        n=0
        total = 10
        logging.info(f'Doing short list of {n}')
        def done()->bool:
            nonlocal n
            if n >= total:
                return True
            n = n + 1
            return False
    else:

        def done()->bool:
            return False

    with open(VISITED_ABS_FILE_NAME, 'a', buffering=1) as visited_fh:
        logging.debug(f'Opened {VISITED_ABS_FILE_NAME} to find visited abs')
        with open(LOG_FILE_NAME, 'w', buffering=1)as report_fh:
            logging.debug(f'Opened {LOG_FILE_NAME} to write report to')
            with Pool(5) as pool:
                fetch_and_compare_fn = partial(fetch_abs,
                                               run_selected_compare_response)
                completed_jobs = pool.imap_unordered(fetch_and_compare_fn, papers)

                def done_job( job ):
                    (config, bad_results) = job
                    logging.debug(f"completed {config['paper_id']}")
                    visited_fh.write(f"{config['paper_id']}\n")
                    write_comparison(report_fh, (config,bad_results))
                    if done():
                        logging.info("done and existing")
                        exit(0)

                [done_job(job) for job in completed_jobs]


def _serialize(obj):
    """JSON serializer for objects not serializable by default json code."""
    return obj.__dict__


def write_comparison(report_fh, result: Tuple[Dict, List[BadResult]])-> None:
    """Write comparison output."""
    (config, bad_results) = result
    logging.debug("writing report for %s", config['paper_id'])
    if bad_results:
        # data = json.dumps( [ config, bad_results],  sort_keys=True, default=_serialize)
        # report_fh.write( data + "\n")

        report_fh.write(f"* paper {config['paper_id']}\n")
        for br in bad_results:
            if 'GOOD' not in br.message:
                report_fh.write( format_bad_result( br ) )



def format_bad_result(bad: BadResult)->str:
    """Format the BadResult object to a readable string."""
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
    """Strip text by delimiter."""
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
