"""
Time the following for the paper ids in the file in arg1:

Get the pdfs from the cdn,
get the pdfs from beta.arxiv.org as current version
get the pdfs from bet.arxiv.org with version number
"""


import requests
import sys
from time import perf_counter, sleep
import re
import pandas as pd

urls = []
with open(sys.argv[1], 'rt') as fh:
    urls = fh.readlines()

urls = [url.strip() for url in urls]
reex = re.compile(r'arxiv\/(?P<id>.*\.pdf)')
pdfs = [url.replace('gs://arxiv-production-ps-cache/pdf/arxiv/', '') for url in urls]

def id_to_beta_with_v_url(id):
    return f'https://beta.arxiv.org/pdf/{id}', []

_without_v = re.compile(r'(\d{4}.\d{4})(v\d*).pdf')


def id_to_id_and_v(id):
    match = _without_v.search(id)
    if not match:
        raise ValueError(f"ID id did not match regex")
    else:
        idpart = match[1]
        vpart = match[2]
        return (idpart, vpart)

def id_to_beta_without_v_url(id):
    idpart, _ = id_to_id_and_v(id)
    return f'https://beta.arxiv.org/pdf/{idpart}.pdf', []

def id_to_cdn_url(id):
    return f'https://download.arxiv.org/pdf/arxiv/{id}', []


ARXIV_HEADERS = {'User-Agent':'periodic-rebuild'}


def id_to_arxiv_with_v_url(id):
    return f'https://arxiv.org/pdf/{id}', ARXIV_HEADERS

def id_to_arxiv_without_v_url(id):
    return f'https://arxiv.org/pdf/{id}', ARXIV_HEADERS

tests = [
    ('beta version download', id_to_beta_with_v_url,
     """Requests to beta.arxiv.org/pdf with the version number."""),
    ('beta current download', id_to_beta_without_v_url,
     "Requests to bet.arxiv.org/pdf without a version number."),
    ('CDN download', id_to_cdn_url,
     "Requests to CDN at download.arxiv.org/pdf"),
    ('CDN download 2nd pass', id_to_cdn_url,
     "Requests to CDN 2nd run after cache has been warmed"),
    ('arxiv.org version download', id_to_arxiv_with_v_url,
     "Reqeusts to arxiv.org/pdf with a version number."),
    ('arxiv.org current download', id_to_arxiv_without_v_url,
     "Reqeusts to arxiv.org/pdf without a version number."),
    ]

data ={'pdfs': pdfs}

verbose = 1
for test_name, req_fn, desc in tests:
    print(f'Starting "{test_name}"')
    timings = []
    bytes_per_sec = []
    responses = {}
    data[test_name] = dict(timings=timings, desc=desc, responses=responses)

    for pdf in pdfs:
        url, headers = req_fn(pdf)
        start = perf_counter()
        bytes = 0
        if verbose:
            print(f'about to get {url}')
        else:
            print('.', end='')
        try:
            resp = requests.get(url, headers=headers)
            bytes =len(resp.content)
            responses[pdf] = dict(url = url, headers = {key:resp.headers[key] for key in resp.headers},
                                  status_code = resp.status_code)
        except Exception as ex:
            responses[pdf] = dict(url =url, error = f"{test_name} {url} failed with {ex}")

        dt = perf_counter() - start
        timings.append(dt)
        responses[pdf]['time'] = dt

        bps =bytes / dt
        bytes_per_sec.append(bps)
        responses[pdf]['bytes_per_sec'] = bps

        sleep(0.5)

    data[test_name]['summary_dt'] = pd.DataFrame(timings).describe().to_dict()
    data[test_name]['summary_byte_per_sec'] = pd.DataFrame(bytes_per_sec).describe().to_dict()

import json
data_json = json.dumps(data, sort_keys=True, indent=4)

with open('results.json','wt') as df:
    df.write(data_json)
