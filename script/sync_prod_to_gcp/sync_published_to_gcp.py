"""Uplaods from CIT SFS to Google Storage based on a publish log.

ex.
```sh
python sync_to_arxiv_produciton.py /data/new/logs/publish_221101.log
```

The PUBLISHLOG fiels can be found on the legacy FS at
/data/new/logs/publish_YYMMDD.log

This works by parsing the PUBLISHLOG file for new and rep entries,
those are put in the `todo_q` queue.

Then for each of these `arxiv_id`s it will check that the PDF file for
the `arxiv_id` exists in the `/data/ps_cache`. If it does not it will
request the `arxiv_id` via HTTP from the arxiv.org site and wait until
the `/data/ps_cache` file exists.

Once that returns the PDF will be uploaded to the GS bucket.

# Alternative

This uses the SFS but there is a technique to get the files in a
manner similar to the mirrors. If we did this we could copy the
publish file to GS and then kick off a CloudRun job to do the sync.
"""
import os.path
# pylint: disable=locally-disabled, line-too-long, logging-fstring-interpolation, global-statement

import sys
import argparse
import re
import threading
from threading import Thread
from queue import Queue, Empty
import requests
from time import sleep, perf_counter
from datetime import datetime
import signal
import json
from typing import List, Tuple

from pathlib import Path

from identifier import Identifier
from digester import digest_from_filepath, get_file_mtime

overall_start = perf_counter()

from google.cloud import storage

import logging.handlers
import logging

logging.basicConfig(level=logging.WARNING, format='%(message)s (%(threadName)s)')
logger = logging.getLogger(__file__)
logger.setLevel(logging.WARNING)

import logging_json

CATEGORY = "category"
SEVERITY = "severity"

LOG_FORMAT_KWARGS = {
    "fields": {
        "timestamp": "asctime",
        "level": "levelname",
    },
    "message_field_name": "message",
    "datefmt": "%Y-%m-%dT%H:%M:%SZ"
}



GS_BUCKET = 'arxiv-production-data'
GS_KEY_PREFIX = '/ps_cache'

PS_CACHE_PREFIX = '/cache/ps_cache/'
FTP_PREFIX = '/data/ftp/'
ORIG_PREIFX = '/data/orig/'

ENSURE_UA = 'periodic-rebuild'

ENSURE_HOSTS = [
    # ('web2.arxiv.org', 40),
    # ('web3.arxiv.org', 40),
    # ('web4.arxiv.org', 40),
    ('web5.arxiv.org', 8),
    ('web6.arxiv.org', 8),
    ('web7.arxiv.org', 8),
    ('web8.arxiv.org', 8),
    ('web9.arxiv.org', 8),
]
"""Tuples of form HOST, THREADS_FOR_HOST"""

ENSURE_CERT_VERIFY = False

PDF_WAIT_SEC = 60 * 3
"""Maximum sec to wait for a PDF to be created"""

todo_q: Queue = Queue()
uploaded_q: Queue = Queue()  # number of files uploaded
summary_q: Queue = Queue()

RUN = True
DONE = False


def handler_stop_signals(signum, frame):
    """Stop threads on ctrl-c, mostly useful during testing"""
    global RUN
    RUN = False


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)


def ms_since(start: float) -> int:
    return int((perf_counter() - start) * 1000)


def make_todos(filename) -> List[dict]:
    """Reades `filename` and figures out what work needs to be done for the sync.
    This only uses data from the publish file.

    It returns a list work to do as dicts like:

        {'submission_id': 1234, 'paper_id': 2202.00234, 'type': 'new',
         'actions': [('upload', '/some/dir/2202.00234.abs'),
                     ('upload', '/cache/xyz/2202.00234.pdf')]
    """

    # These regexs are more file focusec, they should do both legacy ids and modern ids
    new_r = re.compile(r"^.* new submission\n.* paper_id: (.*)$", re.MULTILINE)
    abs_r = re.compile(r"^.* absfile: (.*)$", re.MULTILINE)
    src_pdf_r = re.compile(r"^.* Document source: (.*.pdf)$", re.MULTILINE)
    src_html_r = re.compile(r"^.* Document source: (.*.html.gz)$", re.MULTILINE)
    src_tex_r = re.compile(r"^.* Document source: (.*.gz)$", re.MULTILINE)

    rep_r = re.compile(r"^.* replacement for (.*)\n.*\n.* old version: (\d*)\n.* new version: (\d*)", re.MULTILINE)
    wdr_r = re.compile(r"^.* withdrawal of (.*)\n.*\n.* old version: (\d*)\n.* new version: (\d*)", re.MULTILINE)
    # dead code: cross_r = re.compile(r"^.* cross for (.*)$")
    cross_r = re.compile(r" cross for (.*)")
    jref_r = re.compile(r" journal ref for (.*)")
    test_r = re.compile(r" Test Submission\. Skipping\.")

    todo = []

    def upload_abs_acts(rawid):
        """Makes upload actions for abs when only an id is available, ex cross or jref"""
        arxiv_id = Identifier(rawid)
        archive = ('arxiv' if not arxiv_id.is_old_id else arxiv_id.archive)
        return [('upload', f"{FTP_PREFIX}/{archive}/papers/{arxiv_id.yymm}/{arxiv_id.filename}.abs")]

    def upload_abs_src_acts(arxiv_id, txt):
        """Makes upload actions for abs and source"""
        absm = abs_r.search(txt)
        pdfm = src_pdf_r.search(txt)
        texm = src_tex_r.search(txt)
        htmlm = src_html_r.search(txt)

        actions: List[Tuple[str, str]] = []
        if absm:
            actions = [('upload', absm.group(1))]

        if pdfm:
            actions.append(('upload', pdfm.group(1)))
        elif htmlm:  # must be before tex due to pattern overlap
            actions.append(('upload', htmlm.group(1)))
        elif texm:
            actions.append(('upload', texm.group(1)))
            actions.append(('build+upload', f"{arxiv_id.id}v{arxiv_id.version}"))
        else:
            logger.error("Could not determine source for submission {arxiv_id}",
                         extra={SEVERITY: "warning", CATEGORY: "internal", "arxiv_id": arxiv_id})

        return actions

    def rep_version_acts(txt):
        """Makes actions for replacement.

        Don't try to move on the GCP, just sync to GCP so it is idempotent."""
        move_r = re.compile(r"^.* Moved (.*) => (.*)$", re.MULTILINE)
        return [('upload', m.group(2)) for m in move_r.finditer(txt)]

    sub_start_r = re.compile(r".* submission (\d*)$")
    sub_end_r = re.compile(r".*Finished processing submission ")
    subs, in_sub, txt, sm = [], False, '', None
    with open(filename) as fh:
        for line in fh.readlines():
            if in_sub:
                if sm is not None and sub_end_r.match(line):
                    subs.append((sm.group(1), txt + line))
                    txt, sm, in_sub = '', None, False
                else:
                    txt = txt + line
            else:
                sm = sub_start_r.match(line)
                if sm:
                    in_sub = True

    for subid, txt in subs:
        m = test_r.search(txt)
        if m:
            continue
        m = new_r.search(txt)
        if m:
            arxiv_id = Identifier(f"{m.group(1)}v1")
            todo.append({'submission_id': subid, 'paper_id': m.group(1), 'type': 'new',
                         'actions': upload_abs_src_acts(arxiv_id, txt)})
            continue
        m = rep_r.search(txt)
        if m:
            arxiv_id = Identifier(f"{m.group(1)}v{m.group(3)}")
            todo.append({'submission_id': subid, 'paper_id': m.group(1), 'type': 'rep',
                         'actions': rep_version_acts(txt) + upload_abs_src_acts(arxiv_id, txt)})
            continue
        m = wdr_r.search(txt)
        if m:
            arxiv_id = Identifier(f"{m.group(1)}v{m.group(3)}")
            # withdrawals don't need the pdf synced since they should lack source
            actions = list(
                filter(lambda tt: tt[0] != 'build+upload', rep_version_acts(txt) + upload_abs_src_acts(arxiv_id, txt)))
            todo.append({'submission_id': subid, 'paper_id': m.group(1), 'type': 'wdr',
                         'actions': actions})
            continue
        m = cross_r.search(txt)
        if m:
            todo.append({'submission_id': subid, 'paper_id': m.group(1), 'type': 'cross',
                         'actions': upload_abs_acts(m.group(1))})
            continue
        m = jref_r.search(txt)
        if m:
            todo.append({'submission_id': subid, 'paper_id': m.group(1), 'type': 'jref',
                         'actions': upload_abs_acts(m.group(1))})
            continue

    return todo


def path_to_bucket_key(pdf) -> str:
    """Handels both source and cache files. Should handle pdfs, abs, txt
    and other types of files under these directories. Bucket key should
    not start with a /"""
    if str(pdf).startswith('/cache/'):
        return str(pdf).replace('/cache/', '')
    elif str(pdf).startswith('/data/'):
        return str(pdf).replace('/data/', '')
    else:
        raise ValueError(f"Cannot convert PDF path {pdf} to a GS key")


def ensure_pdf(session, host, arxiv_id):
    """Ensures PDF exits for arxiv_id.

    Check on the ps_cache.  If it does not exist, request it and wait
    for the PDF to be built.

    TODO Not sure if it is possible to have a paper that was a TeX
    source on version N but then is PDF Source on version N+1.

    Returns tuple with pdf_file, url, msec

    arxiv_id must have a version.

    This does not check if the arxiv_id is PDF source.
    """

    def pdf_cache_path(arxiv_id) -> Path:
        """Gets the PDF file in the ps_cache. Returns Path object."""
        archive = ('arxiv' if not arxiv_id.is_old_id else arxiv_id.archive)
        return Path(f"{PS_CACHE_PREFIX}/{archive}/pdf/{arxiv_id.yymm}/{arxiv_id.filename}v{arxiv_id.version}.pdf")

    def arxiv_pdf_url(host, arxiv_id) -> str:
        """Gets the URL that would be used to request the pdf for the arxiv_id"""
        return f"https://{host}/pdf/{arxiv_id.filename}v{arxiv_id.version}.pdf"

    pdf_file, url = pdf_cache_path(arxiv_id), arxiv_pdf_url(host, arxiv_id)

    start = perf_counter()

    if not pdf_file.exists():
        start = perf_counter()
        headers = {'User-Agent': ENSURE_UA}
        logger.debug("Getting %s", url)
        resp = session.get(url, headers=headers, stream=True, verify=ENSURE_CERT_VERIFY)
        # noinspection PyStatementEffect
        [line for line in resp.iter_lines()]  # Consume resp in hopes of keeping alive session
        if resp.status_code != 200:
            msg = f"ensure_pdf: GET status {resp.status_code} {url}"
            logger.warning(msg,
                           extra={SEVERITY: "error", CATEGORY: "download",
                                  "url": url, "status_code": resp.status_code, "pdf_file": str(pdf_file)})
            raise (Exception(msg))
        start_wait = perf_counter()
        while not pdf_file.exists():
            if perf_counter() - start_wait > PDF_WAIT_SEC:
                msg = f"No PDF, waited longer than {PDF_WAIT_SEC} sec {url}"
                logger.warning(msg,
                               extra={SEVERITY: "error", CATEGORY: "download",
                                      "url": url, "pdf_file": str(pdf_file)})
                raise (Exception(msg))
            else:
                sleep(0.2)
        if pdf_file.exists():
            logger.debug(
                f"ensure_file_url_exists: {str(pdf_file)} requested {url} status_code {resp.status_code} {ms_since(start)} ms")
            return (pdf_file, url, None, ms_since(start))
        else:
            raise (Exception(f"ensure_pdf: Could not create {pdf_file}. {url} {ms_since(start)} ms"))
    else:
        logger.debug(f"ensure_file_url_exists: {str(pdf_file)} already exists")
        return (pdf_file, url, "already exists", ms_since(start))


def upload_pdf(gs_client, ensure_tuple):
    """Uploads a PDF from ps_cache to GS_BUCKET"""
    return upload(gs_client, ensure_tuple[0], path_to_bucket_key(ensure_tuple[0])) + ensure_tuple


def upload(gs_client, localpath, key):
    """Upload a file to GS_BUCKET"""

    def mime_from_fname(filepath):
        if filepath.suffix == '.pdf':
            return 'application/pdf'
        if filepath.suffix == '.gz':
            return 'application/gzip'
        if filepath.suffix == '.abs':
            return 'text/plain'
        else:
            return ''

    start = perf_counter()

    bucket = gs_client.bucket(GS_BUCKET)
    blob = bucket.get_blob(key)
    if blob is None or blob.size != localpath.stat().st_size:
        destination = bucket.blob(key)
        with open(localpath, 'rb') as fh:
            destination.upload_from_file(fh, content_type=mime_from_fname(localpath))
            logger.debug(
                f"upload: completed upload of {localpath} to gs://{GS_BUCKET}/{key} of size {localpath.stat().st_size}")
        sha_value = digest_from_filepath(localpath)
        try:
            destination.metadata = {"localpath": localpath, "mtime": get_file_mtime(localpath), "sha256": sha_value}
            destination.update()
        except:
            pass
        return ("upload", localpath, key, "uploaded", ms_since(start), localpath.stat().st_size)
    else:
        logger.debug(f"upload: Not uploading {localpath}, gs://{GS_BUCKET}/{key} already on gs")
        return ("upload", localpath, key, "already_on_gs", ms_since(start), 0)


def sync_to_gcp(todo_q, host):
    """Target for theads that gets jobs off of the todo queue and does job actions."""
    tl_data = threading.local()
    tl_data.session, tl_data.gs_client = requests.Session(), storage.Client()

    while RUN:
        start = perf_counter()
        try:
            job = todo_q.get(block=False)
            if not job:
                logger.error("todo_q.get() returned {job}",
                             extra={"job": repr(job), SEVERITY: "error", CATEGORY: "internal"})
                continue
            if not job.get('paper_id', None):
                logger.error("todo_q.get() job lacked paper_id, skipping",
                             extra={"job": repr(job), SEVERITY: "error", CATEGORY: "internal"})
                continue
        except Empty:  # queue is empty and thread is done
            break

        logger.debug("doing %s", job['paper_id'])
        job_details = {"job": repr(job), "paper_id": job['paper_id']}
        for action, item in job['actions']:
            extra = {"action": action, "item": repr(item)}
            try:
                res = ()
                if action == 'build+upload':
                    res = upload_pdf(tl_data.gs_client, ensure_pdf(tl_data.session, host, Identifier(item)))
                if action == 'upload':
                    res = upload(tl_data.gs_client, Path(item), path_to_bucket_key(item))

                summary_q.put((job['paper_id'], ms_since(start)) + res)
            except Exception as ex:
                extra.update({SEVERITY: "error", CATEGORY: "upload"})
                extra.update(job_details)
                logger.exception(f"Problem during {job['paper_id']} {action} {item}",
                                 extra=extra)
                summary_q.put((job['paper_id'], ms_since(start), "failed", str(ex)))
        todo_q.task_done()


# #################### MAIN #################### #

def main(args):
    global RUN, DONE
    if not args.d:
        storage.Client()  # will fail if no auth setup
    if args.v:
        logger.setLevel(logging.INFO)

    if args.json_log_dir and os.path.exists(args.json_log_dir):
        json_logHandler = logging.handlers.RotatingFileHandler(os.path.join(args.json_log_dir, "sync-to-gcp.log"),
                                                               maxBytes=4 * 1024 * 1024,
                                                               backupCount=10)
        json_formatter = logging_json.JSONFormatter(**LOG_FORMAT_KWARGS)
        json_logHandler.setFormatter(json_formatter)
        logger.addHandler(json_logHandler)
        pass

    logger.info(f"Starting at {datetime.now().isoformat()}", extra={SEVERITY: "normal", CATEGORY: "status"})

    [todo_q.put(item) for item in make_todos(args.filename)]

    if args.d:
        todo = list(todo_q.queue)
        if args.test:
            logger.info("Dry run no changes made",
                        extra={SEVERITY: "normal", CATEGORY: "status", "todos": len(todo)})
            return todo
        print(json.dumps(todo, indent=2))
        print(f"{len(todo)} submissions (some may be test submissions)")
        sys.exit(1)

    logger.debug("made todo_q, getting size")
    overall_size = todo_q.qsize()
    logger.debug('Made %d todos', overall_size)

    threads = []
    for host, n_th in ENSURE_HOSTS:
        ths = [Thread(target=sync_to_gcp, args=(todo_q, host)) for _ in range(0, n_th)]
        threads.extend(ths)
        [t.start() for t in ths]

    logger.debug("started %d threads", len(threads))

    while RUN and not todo_q.empty():
        sleep(0.2)

    logger.debug("todo_q is now empty")

    DONE = True
    RUN = False
    logger.debug("wating to join threads")
    [th.join() for th in threads]
    logger.debug("Threads done joining")

    for row in sorted(list(summary_q.queue), key=lambda tup: tup[0]):
        summary = map(str, row)
        logger.info(','.join(summary),
                    extra={SEVERITY: "normal", CATEGORY: "status", "summary": repr(summary)})

    logger.info(f"Done at {datetime.now().isoformat()}",
                extra={SEVERITY: "normal", CATEGORY: "status"})
    duration = perf_counter() - overall_start

    logger.info(f"Overall time: {duration:.2f} sec for {overall_size} submissions",
                extra={SEVERITY: "normal", CATEGORY: "status", "duration": str(duration)})


if __name__ == "__main__":
    ad = argparse.ArgumentParser(epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ad.add_argument('--test', help='test mode', action='store_true')
    ad.add_argument('--json-log-dir', help='Additional JSON logging', default='/var/log/e-prints')
    ad.add_argument('-v', help='verbose', action='store_true')
    ad.add_argument('-d', help="Dry run no action", action='store_true')
    ad.add_argument('filename')
    args = ad.parse_args()
    main(args)
