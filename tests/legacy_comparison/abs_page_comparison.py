import sys
sys.path.append('') #BDC34: some how I need this under pipenv to get to browse


import os
from functools import partial
from multiprocessing import Pool
import requests
from typing import Iterator

from browse.services.document.metadata import AbsMetaSession
from tests import path_of_for_test

ABS_FILES = path_of_for_test('data/abs_files')



def paperid_iterator( path ) :
    """Return an iterator of paperId strings for all abs found below path."""
    ids = []
    for (dir_name, subdir_list, file_list) in os.walk(path):
        for fname in file_list:
            fname_path = os.path.join(dir_name, fname)
            if os.stat(fname_path).st_size == 0:
                continue
            if not fname_path.endswith('.abs'):
                continue
            ids.append(AbsMetaSession.parse_abs_file(filename=fname_path).arxiv_id)

    return ids


# Should end with /
ng_abs_base_url = 'http://localhost:5000/abs/'

# Should end with /
legacy_abs_base_url = 'https://beta.arxiv.org/abs/'


def fetch_and_compare_abs(compare_res_fn , paperid ):
    ng_url = ng_abs_base_url + paperid
    legacy_url = legacy_abs_base_url + paperid
    return compare_res_fn(ng_url=ng_url, legacy_url=legacy_url,
                          ng_res=requests.get(ng_url), legacy_res=requests.get(legacy_url),
                          paperid=paperid)


def compare_res(ng_url=None, legacy_url=None,
                      ng_res=None, legacy_res=None,
                      paperid=None):
    print( f'Paper: {paperid} ng_url:{ng_url} status: {ng_res.status_code} legacy_url: {legacy_url} status: {legacy_res.status_code}')


with Pool(10) as p:
    p.map( partial( fetch_and_compare_abs, compare_res), paperid_iterator(ABS_FILES))

