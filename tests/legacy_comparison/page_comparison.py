"""Browse page comparison tests."""
import archive_config
from text_comparisons import text_similarity
from response_comparisons import compare_status
from html_comparisons import html_similarity, metadata_fields_similarity, \
    archive_h1_similarity, archive_catchup, archive_search, archive_by_year, \
    archive_browse, archive_bogus
from comparison_types import res_comparison_fn, \
    text_comparison_fn, html_comparison_fn, res_arg_dict, text_arg_dict, \
    html_arg_dict, BadResult
import argparse
import sys
import traceback
import os
from functools import partial
import multiprocessing_on_dill as mp
from typing import Callable, Iterator, List, Set, Tuple, Dict, Any
import gzip
import logging
import json

import requests
from bs4 import BeautifulSoup

# BDC34: some how I need this under pipenv to get to browse, not sure why
sys.path.append('')
sys.setrecursionlimit(10000)


""" Script to compare pages from NG and beta.arxiv.org

To run this I do:
Open terminal:
cd arxiv-browse
pipenv sync
FLASK_APP=app.py FLASK_DEBUG=1 pipenv run flask run

In another terminal:
cd arxiv-browse
pipenv sync
pipenv shell
python tests/legacy_comparison/page_comparison.py

To reset the analysis to start over, add the `--reset` arg.
To run a short test add '--short' arg.

To skip ancillary file comparisons: '--skip-ancillary'

Improvements:
 Better reporting format, right now the comparisons produce just strings.
"""

logging.basicConfig(filename="page_comparison.log", level=logging.DEBUG)

# This just renames None nicely, they are tests that passed
SUCCESS = None

LOG_FILE_NAME = 'legacy_comparison.org'


# TODO abstract this or move this out
VISITED_FILE_NAME = 'visited.log'


def ident(x):
    """Return identity."""
    return x


configs = {
    'archive': {  # I'd like to do something with modules but it doesn't pickle.
        'comparisons': [compare_status,
                        html_similarity,
                        archive_h1_similarity,
                        archive_browse,
                        archive_catchup,
                        archive_search,
                        archive_by_year,
                        ],
        'ng_id_to_url_fn': archive_config.ng_id_to_url_fn,
        'legacy_id_to_url_fn': archive_config.legacy_id_to_url_fn,
        'ng_txt_trans_fn': ident,
        'legacy_txt_trans_fn': ident,
    }
}

# id file is one id per line


def _id_generator_from_file(path: str, excluded: List[str]) -> Iterator[str]:
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

# TODO generalize
# Should end with /
#ng_abs_base_url = 'http://localhost:5000/abs/'
#ng_abs_base_url = 'https://beta.arxiv.org/abs/'

# TODO generalize
# Should end with /
#legacy_abs_base_url = 'https://beta.arxiv.org/abs_classic/'


def fetch_pages(config: Dict, id: str) -> Dict:
    """Fetch NG and Legacy."""
    ng_url = config['ng_id_to_url_fn'](id)
    legacy_url = config['legacy_id_to_url_fn'](id)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    ng_res = requests.get(ng_url, headers=headers)
    legacy_res = requests.get(legacy_url, headers=headers)

    ng_text = config['ng_txt_trans_fn'](ng_res.text)
    legacy_text = config['ng_txt_trans_fn'](legacy_res.text)

    res_dict: res_arg_dict = {
        'id': id,
        'ng_url': ng_url,
        'legacy_url': legacy_url,
    }

    # to avoid json problems
    with_html = {
        **res_dict,
        'ng_res': ng_res,
        'legacy_res': legacy_res,
        'ng_text': ng_text,
        'legacy_text': legacy_text,
        'ng_html': BeautifulSoup(ng_text, 'html.parser'),
        'legacy_html': BeautifulSoup(legacy_text, 'html.parser'),
    }
    return (res_dict, compare_response(config,
                                       with_html))


def compare_response(config: Dict,
                     res_args: res_arg_dict) -> Iterator[BadResult]:
    """Do the response comparisions, the kick off the text comparisions."""
#    protected_comps = [protect(fn) for fn in config['comparisons']]
    protected_comps = config['comparisons']
    logging.debug(f"about to do compares for {res_args['id']}")
    return filter(SUCCESS, [fn(res_args) for fn in protected_comps])


def multi_ws_to_single_ws(txt: str) -> str:
    """Convert multiple whitespaces to single space."""
    return ' '.join(txt.split())  # white space to single spaces


def main() -> None:
    """Run comparisons with provided arguments."""
    parser = argparse.ArgumentParser(
        description='Compare ng pages to legacy pages')
    parser.add_argument('--idfile', default=False, )
    parser.add_argument('--reset', default=False, const=True,
                        action='store_const', dest='reset')
    parser.add_argument('--short', default=False, const=True,
                        action='store_const', dest='short')
    parser.add_argument('--config', default=False)
    args = parser.parse_args()

    print('Starting config')
    if args.config not in configs.keys():
        raise ValueError(
            f"No config named '{args.config}' choose one of [{' '.join(configs.keys())}]")
    else:
        print(f'Using config {args.config}')
        active_config = configs[args.config]
    print('done with config')

    visited: Set[str] = []
    if args.reset:
        print('Restarting analysis and deleting logs!')
        if os.path.exists(LOG_FILE_NAME):
            os.remove(LOG_FILE_NAME)
        if os.path.exists(VISITED_FILE_NAME):
            os.remove(VISITED_FILE_NAME)
    else:
        if os.path.exists(VISITED_FILE_NAME):
            print('Continuing analysis')
            with open(VISITED_FILE_NAME, 'r') as visited_fh:
                visited = {line.rstrip() for line in visited_fh.readlines()}

    ids = _id_generator_from_file(args.idfile, excluded=visited)

    if args.short:
        n = 0
        total = 10
        logging.info(f'Doing short list of {n}')

        def done() -> bool:
            nonlocal n
            if n >= total:
                return True
            n = n + 1
            return False
    else:
        def done() -> bool:
            return False

    f_then_c = partial(fetch_pages, active_config)

    with open(VISITED_FILE_NAME, 'a', buffering=1) as visited_fh:
        logging.debug(
            f'Opened {VISITED_FILE_NAME} to find already visited ids')
        with open(LOG_FILE_NAME, 'w', buffering=1)as report_fh:
            logging.debug(f'Opened {LOG_FILE_NAME} to write report to')
            with mp.Pool(4) as pool:
                completed_jobs \
                    = pool.imap_unordered(f_then_c, ids)

                def done_job(job):
                    (res_dict, bad_results) = job
                    logging.debug(f"completed {res_dict['id']}")
                    visited_fh.write(f"{res_dict['id']}\n")
                    write_comparison_org(
                        report_fh, (res_dict, list(bad_results)))
                    if done():
                        logging.info("done and existing")
                        exit(0)

                [done_job(job) for job in completed_jobs]


def protect(fn: Callable[[Any], BadResult]) -> Callable[[Any], BadResult]:
    """Return function that will not throw."""
    def protected(res_args: Dict) -> BadResult:
        # noinspection PyBroadException
        try:
            return fn(res_args)
        except Exception as ex:
            return BadResult(res_args['id'], "name unknown", traceback.format_exc())
    return protected


def _serialize_obj(obj):
    """JSON serializer for objects not serializable by default json code."""
    return obj.__dict__


def write_comparison(report_fh, result: Tuple[Dict, List[BadResult]]) -> None:
    """Write output for comparison."""
    (config, bad_results) = result
    logging.debug("writing report for %s", config['id'])
    report_fh.write(json.dumps(config, sort_keys=True) + "\n")
    if bad_results:
        report_fh.write(json.dumps(bad_results, sort_keys=True,
                                   default=_serialize_obj) + "\n")
    else:
        report_fh.write("no bad results\n")


def write_comparison_org(report_fh, result: Tuple[Dict, List[BadResult]]) \
        -> None:
    """Write comparison results."""
    (config, bad_results) = result
    logging.debug("writing report for %s", config['id'])
    report_fh.write(f"* {config['id']} \n")

    report_fh.write(f"** config for {config['id']}\n")
    report_fh.write(json.dumps(config, sort_keys=True) + "\n")

    report_fh.write("** Results\n")
    if bad_results:
        for result in bad_results:
            report_fh.write(f"*** {result.comparison} \n")
            #report_fh.write( json.dumps(result, sort_keys=True, default=_serialize_obj) + "\n")
            report_fh.write(result.message + "\n")
            report_fh.write(f"**** NG value: \n{result.ng}\n")
            report_fh.write(f"**** Legacy value: \n{result.legacy}\n")
    else:
        report_fh.write("No bad results\n")


def format_bad_result(bad: BadResult) -> str:
    """Format a BadResult object."""
    rpt = f"** {bad.comparison}\n" \
          f"{bad.message} "
    if bad.similarity:
        rpt = rpt + f"sim: {bad.similarity}\n"
    else:
        rpt = rpt + "\n"

    if bad.legacy or bad.ng:
        rpt = rpt + f"Legacy: '{bad.legacy}'\nNG: '{bad.ng}'\n"

    return rpt


def dict_from_module(module):
    """
    Create a dict from a module.

    This is just to get around passing the config to the pool.
    """
    context = {}
    for setting in required_keys:
        context[setting] = getattr(module, setting)
    return context


if __name__ == '__main__':
    main()
