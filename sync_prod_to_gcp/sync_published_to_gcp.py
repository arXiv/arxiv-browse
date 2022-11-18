"""Uplaods new and rep entries from a publish log.

ex

    python sync_to_arxiv_produciton.py /data/new/logs/publish_221101.log

The PUBLISHLOG fiels can be found on the legacy FS at
/data/new/logs/publish_YYMMDD.log

This works by parsing the PUBLISHLOG file for new and rep entries,
those are put in the `todo_q` queue.

Then for each of these `arxiv_id`s it will check that the PDF file for
the `arxiv_id` exists in the `/data/ps_cache`. If it does not it will
request the `arxiv_id` via HTTP from the arxiv.org site and wait until
the `/data/ps_cache` file exists.

Once that returns the PDF will be uploaded to the GS bucket.
"""

# pylint: disable=locally-disabled, line-too-long, logging-fstring-interpolation, global-statement

import sys

import re
import threading
from threading import Thread
from queue import Queue, Empty
import requests
from time import sleep, perf_counter
from datetime import datetime
import signal

from pathlib import Path

from identifier import Identifier

overall_start = perf_counter()

from google.cloud import storage

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s (%(threadName)s)')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

GS_BUCKET= 'arxiv-production-data'
GS_KEY_PREFIX = '/ps_cache'

FS_PREFIX= '/cache/ps_cache/'

ENSURE_UA = 'periodic-rebuild'

ENSURE_HOSTS = [
    ('web2.arxiv.org', 6),
    ('web3.arxiv.org', 6),
    ('web4.arxiv.org', 6),
    ('web5.arxiv.org', 2),
    ('web6.arxiv.org', 2),
    ('web7.arxiv.org', 2),
    ('web8.arxiv.org', 2),
    ('web9.arxiv.org', 2),
]
"""Tuples of form HOST, THREADS_FOR_HOST"""

ENSURE_CERT_VERIFY=False

PDF_WAIT_MAX_SEC = 60 * 8
"""Maximum seconds to wait for a PDF to be created"""

new_r = re.compile(r"^.* new submission\n.* paper_id: (.*)$", re.MULTILINE)
rep_r = re.compile(r"^.* replacement for (.*)\n.*\n.* old version: (\d*)\n.* new version: (\d*)", re.MULTILINE)
# TODO handle wdr

todo_q: Queue = Queue()
uploaded_q: Queue = Queue() # number of files uploaded
summary_q: Queue = Queue()

RUN = True
DONE = False

def handler_stop_signals(signum, frame):
    """Stop threads on ctrl-c, mostly useful during testing"""
    global RUN
    RUN = False

signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

def ms_since(start:float) -> int:
    return int((perf_counter() - start) * 1000)

def pdf_cache_path(arxiv_id) -> Path:
    """Gets the PDF file in the ps_cache. Returns Path object."""
    archive = ('arxiv' if not arxiv_id.is_old_id else arxiv_id.archive)
    return Path(f"{FS_PREFIX}/{archive}/pdf/{arxiv_id.yymm}/{arxiv_id.filename}v{arxiv_id.version}.pdf")

def pdf_src_path(arxiv_id, a_type) -> Path:
    """Gets the source file"""
    archive = ('arxiv' if not arxiv_id.is_old_id else arxiv_id.archive)
    if a_type == 'new':
        return Path(f"/data/ftp/{archive}/papers/{arxiv_id.yymm}/{arxiv_id.filename}.pdf")
    elif a_type == 'rep':
        return Path(f"/data/orig/{archive}/papers/{arxiv_id.yymm}/{arxiv_id.filename}v{arxiv_id.version}.pdf")
    elif a_type == 'prev':
        prev_v = int(arxiv_id.version) - 1
        return Path(f"/data/orig/{archive}/papers/{arxiv_id.yymm}/{arxiv_id.filename}v{prev_v}.pdf")
    else:
        return Path('/bogus/path')

def arxiv_pdf_url(host, arxiv_id) -> str:
    """Gets the URL that would be used to request the pdf for the arxiv_id"""
    return f"https://{host}/pdf/{arxiv_id.filename}v{arxiv_id.version}.pdf"


def pdf_path_to_bucket_key(pdf) -> str:
    """Handels both source and cache files. Should handle pdfs, abs, txt
    and other types of files under these directories. Bucket key should
    not start with a /"""
    if str(pdf).startswith('/cache/'):
        return str(pdf).replace('/cache/','')
    elif str(pdf).startswith('/data/'):
        return str(pdf).replace('/data/','')
    else:
        raise ValueError(f"Cannot convert PDF path {pdf} to a GS key")

def is_src_pdf(arxiv_id) -> bool:
    return pdf_src_path(arxiv_id, 'new').exists() \
        or pdf_src_path(arxiv_id, 'rep').exists() \
        or pdf_src_path(arxiv_id, 'pref').exists()

def pack_src_pdf(src_pdf:Path):
    """Back a bare src_path like a result from ensure_file_url_exists"""
    return (src_pdf, None, None, 0)

def ensure_pdf(session, host, arxiv_id, a_type):
    """Ensures PDF exits for arxiv_id.

    Check both for source pdf and on the ps_cache.  If it does not
    exist, request it and wait for the PDF to be built.

    TODO Not sure if it is possible to have a paper that was a TeX
    source on version N but then is PDF Source on version N+1.

    Returns a list of tuples with Paths that should be synced to GCP.

    """
    if is_src_pdf(arxiv_id):
        if a_type == 'new':
            logger.info(f"{arxiv_id.filename} is PDF src and new")
            return [pack_src_pdf(pdf_src_path(arxiv_id, a_type))]
        else:
            logger.info(f"{arxiv_id.filename} is PDF src and rep")
            # need to replace the file in /ftp and add a version to /orig
            return [pack_src_pdf(pdf_src_path(arxiv_id, 'new')),
                    pack_src_pdf(pdf_src_path(arxiv_id, 'prev'))]
    else:
        logger.info(f"{arxiv_id.filename} is not PDF src")
        return [ensure_file_url_exists(session, pdf_cache_path(arxiv_id), arxiv_pdf_url(host, arxiv_id))]


def ensure_file_url_exists(session, pdf_file, url):
    """General purpose ensure exits for a `url` that should produce a `pdf_file`."""
    start = perf_counter()
    if not pdf_file.exists():
        start = perf_counter()
        headers = { 'User-Agent': ENSURE_UA }
        resp = session.get(url, headers=headers, stream=True, verify=ENSURE_CERT_VERIFY)
        [line for line in resp.iter_lines()]  # Consume resp in hopes of keeping alive session
        if resp.status_code != 200:
            return (pdf_file, url, "failed: bad GET status {resp.status_code}", ms_since(start))
        start_wait = perf_counter()
        while not pdf_file.exists() and perf_counter() - start_wait < PDF_WAIT_MAX_SEC:
            sleep(0.2)
        if pdf_file.exists():
            logger.info(f"ensure_file_url_exists: {str(pdf_file)} requested {url} status_code {resp.status_code} {ms_since(start)} ms")
            return (pdf_file, url, None, ms_since(start))
        else:
            logger.error(f"ensure_file_url_exists: Could not create {pdf_file}. Requested {url} {ms_since(start)} ms")
            return (pdf_file, url, "failed: no pdf after waiting", ms_since(start))
    else:
        logger.info(f"ensure_file_url_exists: {str(pdf_file)} already exists")
        return (pdf_file, url, None, ms_since(start))


def upload_pdf(gs_client, pdf):
    """Uploads pdf to GS_BUCKET"""
    start = perf_counter()
    try:
        bucket = gs_client.bucket(GS_BUCKET)
        key = pdf_path_to_bucket_key(pdf)
        blob = bucket.get_blob(key)
        if blob is None or blob.size != pdf.stat().st_size:
            with open(pdf, 'rb') as fh:
                bucket.blob(key).upload_from_file(fh, content_type='application/pdf')
                uploaded_q.put(pdf.stat().st_size)
                logger.info(f"upload: completed upload of {pdf} to gs://{GS_BUCKET}/{key} of size {pdf.stat().st_size}")
            return (pdf, "uploaded", ms_since(start))
        else:
            logger.info(f"upload: Not uploading {pdf}, gs://{GS_BUCKET}/{key} already on gs")
            return (pdf, "already_on_gs", ms_since(start))
    except Exception:
        logger.exception()
        return (pdf, "failed", ms_since(start))

def sync_to_gcp(todo_q, host):
    """Target for theads

    Gets off of the todo queue, ensures the PDF exists and uploads the PDF.
    """
    tl_data=threading.local()
    tl_data.session = requests.Session() # cannot share Session across threads
    tl_data.gs_client = storage.Client()

    while RUN:
        start = perf_counter()
        try:
            a_type, a_id, _, v_new = todo_q.get(block=False)
        except Empty:
            break

        if not a_id or not v_new:
            logger.error("todo_q.get() did not return a arxiv id and version")
            continue

        try:
            arxiv_id = Identifier(f"{a_id}v{v_new}")
            pdf_paths = ensure_pdf(tl_data.session, host, arxiv_id, a_type)

            for pdf_file, url, ensure_err, ensure_ms in pdf_paths:
                up_msg, up_ms = (None, None)
                if not ensure_err:
                    pdf_file, up_msg, up_ms = upload_pdf(tl_data.gs_client, pdf_file)
                summary_q.put( (pdf_file, url, ensure_err, ensure_ms, up_msg, up_ms))

            todo_q.task_done()
            logger.debug(f"Total time for {a_id}v{v_new} {ms_since(start)}ms")
        except Exception:
            logger.exception(f"Problem during {a_id}v{v_new}")


# #################### MAIN #################### #

if __name__ == "__main__":
    if not len(sys.argv) > 1:
        print(sys.modules[__name__].__doc__)
        sys.exit(1)

    _test_auth_client= storage.Client() # will fail if no auth setup
    logger.info(f"Starting at {datetime.now().isoformat()}")

    with open(sys.argv[1]) as fh:
        log = fh.read()
        for idx, m in enumerate(new_r.finditer(log)):
            todo_q.put( ('new', m.group(1), None, 1))
        for m in rep_r.finditer(log):
            todo_q.put( ('rep', m.group(1), m.group(2), m.group(3)))

    overall_size = todo_q.qsize()

    threads = []
    for host, n_th in ENSURE_HOSTS:
        ths = [Thread(target=sync_to_gcp, args=(todo_q, host)) for _ in range(0, n_th)]
        threads.extend(ths)
        [t.start() for t in ths]

    while RUN and not todo_q.empty():
        sleep(0.2)

    DONE=True
    RUN=False
    [th.join() for th in threads]

    logger.info("------------------------------ summary ------------------------------")
    logger.info("| pdf_file | url | ensure_err | ensure_ms | upload_msg | upload_ms|")
    logger.info("|-----------------------------------------------------------------|")
    for pdf_file, url, ensure_err, ensure_ms, up_msg, up_ms in sorted(list(summary_q.queue)):
        logger.info(f"{pdf_file}|{url}|{ensure_err}|{ensure_ms}|{up_msg}|{up_ms}")
    logger.info("---------------------------- end summary -----------------------------")

    logger.info(f"Done at {datetime.now().isoformat()}")
    logger.info(f"Overall time: {(perf_counter()-overall_start):.2f} sec for {overall_size} submissions of type new or rep, {uploaded_q.qsize()} uploads.")
    if overall_size < uploaded_q.qsize():
        logger.info("Uploaded count maybe higher than submission count due to replacements needing to upload both to /ftp and /orig for papers with PDF source.")
    if overall_size > uploaded_q.qsize():
        logger.info("Uploaded count maybe lower than submission count due to files already synced to GCP.")
