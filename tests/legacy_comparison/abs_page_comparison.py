import itertools
import sys
# BDC34: some how I need this under pipenv to get to browse, not sure why
sys.path.append('')


from tests.legacy_comparison.response_comparisons import compare_status

import os
from functools import partial
from multiprocessing import Pool
import requests
from typing import Iterator

from browse.services.document.metadata import AbsMetaSession
from tests import path_of_for_test

from bs4 import BeautifulSoup

ABS_FILES = path_of_for_test('data/abs_files')

res_comparisons = [compare_status]
text_comparisons = []
html_comparisons = []


def paperid_iterator(path) -> Iterator[str]:
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


def fetch_and_compare_abs(compare_res_fn, paperid):
    ng_url = ng_abs_base_url + paperid
    legacy_url = legacy_abs_base_url + paperid
    return compare_res_fn(ng_url=ng_url, legacy_url=legacy_url,
                          ng_res=requests.get(ng_url), legacy_res=requests.get(legacy_url),
                          paperid=paperid)


def run_compare_response(ng_url: str=None,
                         legacy_url: str=None,
                         ng_res: requests.Response =None,
                         legacy_res: requests.Response =None,
                         paperid: str=None):
    # TODO run all response_comparisons
    def call_it(fn):
        try:
            return fn(ng_url=ng_url, legacy_url=legacy_url, ng_res=ng_res, legacy_res=legacy_res, paperid=paperid)
        except Exception as ex:
            return ex

    return list(filter(None,itertools.chain(
                                    map(call_it, res_comparisons),
                                    run_compare_text(ng_url=ng_url, legacy_url=legacy_url, ng_text=ng_res.text,
                                             legacy_text=legacy_res.text, paperid=paperid))))


def run_compare_text(ng_url: str=None, legacy_url: str=None,
                     ng_text: str=None, legacy_text: str=None,
                     paperid: str=None):
    def call_it(fn):
        try:
            return fn(ng_url=ng_url, legacy_url=legacy_url, ng_text=ng_text, legacy_text=legacy_text, paperid=paperid)
        except Exception as ex:
            return ex

    return filter(None,itertools.chain(
                                    map(call_it, text_comparisons),
                                    run_compare_html(ng_url=ng_url, legacy_url=legacy_url,
                                        ng_html=BeautifulSoup(ng_text, 'html.parser'),
                                        legacy_html=BeautifulSoup(legacy_text, 'html.parser'),
                                        paperid=paperid)))


def run_compare_html(ng_url: str=None, legacy_url: str=None,
                     ng_html: BeautifulSoup=None, legacy_html: BeautifulSoup=None,
                     paperid: str=None):
    def call_it(fn):
        try:
            return fn(ng_url=ng_url, legacy_url=legacy_url, ng_html=ng_html, legacy_html=legacy_html, paperid=paperid)
        except Exception as ex:
            return ex

    return itertools.filterfalse(lambda  x: x, map(call_it, html_comparisons))


#papers =  ['0704.0001', '0704.0600']
papers = paperid_iterator(ABS_FILES)
with Pool(10) as p:
    results = p.imap(partial(fetch_and_compare_abs, run_compare_response), papers)
    for result in results:
        #TODO need to replace this with writing to a report file or something
        print(result)

