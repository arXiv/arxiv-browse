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
publishing file to GS and then kick off a CloudRun job to do the sync.
"""
import os.path

import sys
import argparse
import re
import threading
import typing
from threading import Thread
from queue import Queue, Empty
import requests
from time import sleep, perf_counter, gmtime, strftime as time_strftime

from datetime import datetime, timezone
import signal
import json
from typing import List, Tuple

from pathlib import Path

from google.api_core import retry
from google.cloud.storage.retry import DEFAULT_RETRY as STORAGE_RETRY

from identifier import Identifier

from digester import get_file_mtime

overall_start = perf_counter()

from google.cloud import storage

import logging.handlers
import logging

logging.basicConfig(level=logging.WARNING, format='%(message)s (%(threadName)s)')
logger = logging.getLogger(__file__)
logger.setLevel(logging.WARNING)

import logging_json
import hashlib
import base64


class Overloaded503Exception(Exception):
    """Raised when the response to /pdf is a 503, indicating a need to slow down calls to server."""
    pass

class WebnodeException(Exception):
    """raised when webnode returns non-200"""
    status_code: int

    def __init__(self, *args, **kwargs) -> None:
        if "status_code" in kwargs:
            self.status_code = kwargs.pop("status_code")
        else:
            self.status_code = 0
        super().__init__(*args, **kwargs)
    pass


# PDF_RETRY_EXCEPTIONS = [Overloaded503Exception, requests.exceptions.ConnectionError, requests.exceptions.Timeout]
# take out the timeout - make timeout shorter
# This is okay as the queue based submission upload retries aftre backoff so no need to
# wait long. It will come back in a 30-40 seconds
PDF_RETRY_EXCEPTIONS = [Overloaded503Exception, requests.exceptions.ConnectionError]
HTML_RETRY_EXCEPTIONS = PDF_RETRY_EXCEPTIONS
CATEGORY = "category"

GS_BUCKET = 'arxiv-production-data'
GS_KEY_PREFIX = '/ps_cache'

CACHE_PREFIX = '/cache/'
PS_CACHE_PREFIX = '/cache/ps_cache/'
FTP_PREFIX = '/data/ftp/'
ORIG_PREFIX = '/data/orig/'
DATA_PREFIX = '/data/'
REUPLOADS = {}

ENSURE_UA = 'periodic-rebuild'

CONCURRENCY_PER_WEBNODE = [
    ('web5.arxiv.org', 1),
    ('web6.arxiv.org', 1),
    ('web8.arxiv.org', 1),
    ('web9.arxiv.org', 1),
]
"""Tuples of form HOST, THREADS_FOR_HOST

The THREADS_FOR_HOST controls the maximum concurrent requests to a web node when
making HTTP GET requests to /pdf.

The code at /pdf has a hard coded limit to the maximum number of PDF build jobs
on the VM it will allow. It will send a HTTP response of 503 if there are too
many.  As of 2023-10 the limit is 5.
"""

ENSURE_CERT_VERIFY = False

PDF_WAIT_SEC = 60 * 5
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

#####

LOG_FORMAT_KWARGS = {
    "fields": {
        "timestamp": "asctime",
        "level": "levelname",
    },
    "message_field_name": "message",
    # time.strftime has no %f code "datefmt": "%Y-%m-%dT%H:%M:%S.%fZ%z",
}


class ArxivSyncJsonFormatter(logging_json.JSONFormatter):
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        return time_strftime("%Y-%m-%dT%H:%M:%S", ct) + ".%03d" % record.msecs + time_strftime("%z", ct)

    pass


#####

def ms_since(start: float) -> int:
    return int((perf_counter() - start) * 1000)


def make_todos(filename, generate=True) -> List[dict]:
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
            if generate:
                actions.append(('build_html+upload', f"{arxiv_id.id}v{arxiv_id.version}"))
        elif texm:
            actions.append(('upload', texm.group(1)))
            if generate:
                actions.append(('build_pdf+upload', f"{arxiv_id.id}v{arxiv_id.version}"))
        else:
            logger.error(f"Could not determine source for submission {arxiv_id}",
                         extra={CATEGORY: "internal", "arxiv_id": arxiv_id})

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
                filter(lambda tt: tt[0] != 'build_pdf+upload', rep_version_acts(txt) + upload_abs_src_acts(arxiv_id, txt)))
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
    if str(pdf).startswith(CACHE_PREFIX):
        return str(pdf).replace(CACHE_PREFIX, '')
    elif str(pdf).startswith(DATA_PREFIX):
        return str(pdf).replace(DATA_PREFIX, '')
    else:
        logging.error(f"path_to_bucket_key: {pdf} does not start with {CACHE_PREFIX} or {DATA_PREFIX}")
        raise ValueError(f"Cannot convert PDF path {pdf} to a GS key")
    
def path_to_bucket_key_html(html) -> str:
    if str(html).startswith(CACHE_PREFIX):
        return str(html).replace(CACHE_PREFIX, '')
    elif str(html).startswith(DATA_PREFIX):
        return str(html).replace(DATA_PREFIX, '')
    else:
        logging.error(f"path_to_bucket_key: {html} does not start with {CACHE_PREFIX} or {DATA_PREFIX}")
        raise ValueError(f"Cannot convert PDF path {html} to a GS key")

@retry.Retry(predicate=retry.if_exception_type(*HTML_RETRY_EXCEPTIONS), initial=2, maximum=4, deadline=10)
def get_html(session, html_url) -> None:
    start = perf_counter()
    headers = {'User-Agent': ENSURE_UA}
    logger.debug("Getting %s", html_url)
    resp = session.get(html_url, headers=headers, stream=True, verify=ENSURE_CERT_VERIFY)
    # noinspection PyStatementEffect
    [line for line in resp.iter_lines()]  # Consume resp in hopes of keeping alive session
    html_ms: int = ms_since(start)
    if resp.status_code == 503:
        msg = f"ensure_pdf: GET status 503, server overloaded {html_url}"
        logger.warning(msg,
                       extra={CATEGORY: "download",
                              "url": html_url, "status_code": resp.status_code, "ms": html_ms})
        raise Overloaded503Exception(msg)
    if resp.status_code != 200:
        msg = f"ensure_pdf: GET status {resp.status_code} {html_url}"
        logger.warning(msg,
                       extra={CATEGORY: "download",
                              "url": html_url, "status_code": resp.status_code, "ms": html_ms})
        raise WebnodeException(msg, status_code=resp.status_code)
    else:
        logger.info(f"ensure_pdf: Success GET status {resp.status_code} {html_url}",
                    extra={CATEGORY: "download",
                           "url": html_url, "status_code": resp.status_code, "ms": html_ms})


@retry.Retry(predicate=retry.if_exception_type(*PDF_RETRY_EXCEPTIONS), initial=2, maximum=4, deadline=10)
def get_pdf(session, pdf_url, timeout=0) -> None:
    start = perf_counter()
    headers = {'User-Agent': ENSURE_UA}
    logger.debug("Getting %s", pdf_url)
    resp = session.get(pdf_url, headers=headers, stream=True, verify=ENSURE_CERT_VERIFY, timeout=timeout)
    # noinspection PyStatementEffect
    [line for line in resp.iter_lines()]  # Consume resp in hopes of keeping alive session
    pdf_ms: int = ms_since(start)
    if resp.status_code == 503:
        msg = f"ensure_pdf: GET status 503, server overloaded {pdf_url}"
        logger.warning(msg,
                       extra={CATEGORY: "download",
                              "url": pdf_url, "status_code": resp.status_code, "ms": pdf_ms})
        raise Overloaded503Exception(msg)
    if resp.status_code != 200:
        msg = f"ensure_pdf: GET status {resp.status_code} {pdf_url}"
        logger.warning(msg,
                       extra={CATEGORY: "download",
                              "url": pdf_url, "status_code": resp.status_code, "ms": pdf_ms})
        raise WebnodeException(msg, status_code=resp.status_code)
    else:
        logger.info(f"ensure_pdf: Success GET status {resp.status_code} {pdf_url}",
                    extra={CATEGORY: "download",
                           "url": pdf_url, "status_code": resp.status_code, "ms": pdf_ms})


def is_cache_valid(cache_file: Path, timestamp: int) -> bool:
    """
    Checks the cache file exists, and newer than the timestamp
    """
    if not cache_file.exists():
        return False
    return cache_file.stat().st_mtime >= timestamp


def ensure_pdf(session, host, arxiv_id, timeout=0, protocol = "https", source_mtime=0):
    """Ensures PDF exists for arxiv_id.

    Check on the ps_cache.  If it does not exist, request it and wait
    for the PDF to be built.

    TODO Not sure if it is possible to have a paper that was a TeX
    source on version N but then is PDF Source on version N+1.

    Returns tuple with pdf_file, url, msec

    arxiv_id must have a version.

    This does not check if the arxiv_id is PDF source.
    """
    timeout = PDF_WAIT_SEC if not timeout else timeout
    archive = ('arxiv' if not arxiv_id.is_old_id else arxiv_id.archive)
    pdf_file = Path(f"{PS_CACHE_PREFIX}/{archive}/pdf/{arxiv_id.yymm}/{arxiv_id.filename}v{arxiv_id.version}.pdf")
    url = f"{protocol}://{host}/pdf/{arxiv_id.idv}.pdf"
    start = perf_counter()

    if pdf_file.exists():
        logger.debug(f"ensure_file_url_exists: {str(pdf_file)} already exists")
        return pdf_file, url, "already exists", ms_since(start)

    start = perf_counter()
    get_pdf(session, url, timeout=timeout)
    start_wait = perf_counter()
    while not pdf_file.exists():
        if perf_counter() - start_wait > timeout:
            msg = f"No PDF, waited longer than {timeout} sec {url}"
            logger.warning(msg,
                           extra={CATEGORY: "download",
                                  "url": url, "pdf_file": str(pdf_file)})
            raise WebnodeException(msg)
        else:
            sleep(0.2)
    if pdf_file.exists():
        if pdf_file.stat().st_mtime < source_mtime:
            # This probably means something funky happened on the file server, or someone
            # mokeypatched the tarball.
            logger.error(f"PDF mtime is {pdf_file.stat().st_mtime} < than source {source_mtime}",
                           extra={CATEGORY: "webnode",
                                  "url": url, "pdf_file": str(pdf_file)})
        return pdf_file, url, None, ms_since(start)
    else:
        raise WebnodeException(f"ensure_pdf: Could not create {pdf_file}. {url} {ms_since(start)} ms")


def ensure_html(session, host, arxiv_id: Identifier, timeout=None, protocol = "https",
                source_mtime = 0) -> \
    typing.Tuple[typing.List[str], str, str, typing.Union[str, None], float]:
    """Ensures HTML exists for arxiv_id.

    Check on the ps_cache.  If it does not exist, request it and wait
    for the HTML to be pre-processed.

    Returns tuple with html_file, url, msec

    arxiv_id must have a version.

    This does not check if the arxiv_id is HTML source.
    """
    timeout = PDF_WAIT_SEC if not timeout else timeout
    archive = ('arxiv' if not arxiv_id.is_old_id else arxiv_id.archive)
    html_path = Path(f"{PS_CACHE_PREFIX}/{archive}/html/{arxiv_id.yymm}/{arxiv_id.idv}/")
    url = f"{protocol}://{host}/html/{arxiv_id.id}v{arxiv_id.version}"

    def _get_files_for_html () -> List[Path]:
        files: List[Path] = []
        for root_dir, _, fs in os.walk(html_path):
            files.extend(map(lambda file: Path(os.path.join(root_dir, file)), fs))
        return files

    # get_html raises WebnodeException when the response is NOT 200.
    # Web node gets to gate-keep, IOW.
    get_html(session, url)

    start_wait = perf_counter()
    while len(files := _get_files_for_html()) < 1:
        if perf_counter() - start_wait > timeout: # TODO: Does this need to be different for html?
            msg = f"No HTML, waited longer than {timeout} sec {url}"
            logger.warning(msg,
                           extra={CATEGORY: "download",
                                  "url": url, "html_file": str(html_path)})
            raise WebnodeException(msg)
        else:
            sleep(0.2)
    if len(files) > 0:
        return [onefile.as_posix() for onefile in files], html_path.as_posix(), url, None, round(ms_since(start_wait))
    else:
        raise WebnodeException(f"ensure_pdf: Could not create {html_path}. {url} {ms_since(start_wait)} ms")


def upload_pdf(gs_client, ensure_tuple):
    """Uploads a PDF from ps_cache to GS_BUCKET"""
    return upload(gs_client, ensure_tuple[0], path_to_bucket_key(ensure_tuple[0])) + ensure_tuple

def upload_html(gs_client, ensure_tuple):
    for file in ensure_tuple[0]:
        yield upload(gs_client, file, path_to_bucket_key_html(file))


# Thread-local storage for read buffer
_thread_local = threading.local()

def get_read_buffer(size=8192):
    """Get thread-local read buffer to avoid repeated allocations"""
    if not hasattr(_thread_local, 'read_buffer') or len(_thread_local.read_buffer) != size:
        _thread_local.read_buffer = bytearray(size)
    return _thread_local.read_buffer


def get_existing_blob(bucket, key, logger):
    """Get existing blob using both get_blob() and exists() methods"""
    try:
        # First try the standard get_blob approach
        blob = bucket.get_blob(key)
        if blob is not None:
            return blob
        
        # If get_blob returns None, try the exists() method
        # This calls HEAD and may get to blob better
        blob = bucket.blob(key)
        if blob.exists():
            blob.reload()  # Populate blob propss
            return blob
            
        return None
        
    except Exception as exc:
        logger.warning(f"Error checking blob {key} existence: {exc}")
        return None


@STORAGE_RETRY
def upload(gs_client, localpath, key, upload_logger=None):
    """Upload a file to GS_BUCKET"""
    if upload_logger is None:
        upload_logger = logger
    
    def mime_from_fname(filepath):
        return {
            '.pdf': 'application/pdf',
            '.gz': 'application/gzip',
            '.abs': 'text/plain'
        }.get(filepath.suffix, '')
    
    def get_file_info(filepath):
        """Get file size and MD5 hash by reading the file"""
        md5_hash = hashlib.md5()
        file_size = 0
        buffer = get_read_buffer(8192)
        
        with open(filepath, 'rb') as f:
            while True:
                bytes_read = f.readinto(buffer)
                if bytes_read == 0:
                    break
                md5_hash.update(buffer[:bytes_read])
                file_size += bytes_read
        
        # https://cloud.google.com/storage/docs/json_api/v1/objects
        # MD5 hash of the data, encoded using base64
        return file_size, base64.b64encode(md5_hash.digest()).decode('ascii')

    start = perf_counter()
    bucket = gs_client.bucket(GS_BUCKET)
    blob = get_existing_blob(bucket, key, upload_logger)
    
    local_size, local_md5 = get_file_info(localpath)
    
    timestamp_utc = datetime.now(timezone.utc).isoformat()
    metadata = {
        "localpath": str(localpath),
        "local_md5": local_md5,
        "mtime": get_file_mtime(localpath),
        "timestamp_utc": timestamp_utc
    }            

    should_upload =  blob is None or blob.md5_hash != local_md5 or key in REUPLOADS
    if should_upload:
        blob_md5 = blob.md5_hash if blob else "No blob"
        destination = bucket.blob(key)
        with open(localpath, 'rb') as fh:
            destination.upload_from_file(fh, content_type=mime_from_fname(localpath))
        upload_logger.info(
            f"upload: completed upload of {localpath} to 'gs://{GS_BUCKET}/{key}' blob md5 {blob_md5} / local md5 {local_md5}, size {local_size}",
            extra=metadata)
        try:
            destination.metadata = {"localpath": str(localpath), "mtime": get_file_mtime(localpath)}
            destination.metadata = metadata
            destination.update()
        except BaseException:
            upload_logger.error(f"upload: could not set metadata on GS object gs://{GS_BUCKET}/{key}",
                                extra=metadata,
                                exc_info=True)
        return "upload", localpath, key, "uploaded", ms_since(start), local_size
    else:
        upload_logger.info(f"upload: Not uploading {localpath}, gs://{GS_BUCKET}/{key} already on gs",
                           extra=metadata)
        return "upload", localpath, key, "already_on_gs", ms_since(start), 0


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
                             extra={"job": repr(job), CATEGORY: "internal"})
                continue
            if not job.get('paper_id', None):
                logger.error("todo_q.get() job lacked paper_id, skipping",
                             extra={"job": repr(job), CATEGORY: "internal"})
                continue
        except Empty:  # queue is empty and thread is done
            break

        job_details = {"job": repr(job), "paper_id": job['paper_id']}
        logger.debug("doing %s", job['paper_id'], extra=job_details)
        for action, item in job['actions']:
            extra = {"action": action, "item": str(item), "job": repr(job), "paper_id": job['paper_id']}
            try:
                res = ()
                if action == 'build_pdf+upload':
                    res = upload_pdf(tl_data.gs_client, ensure_pdf(tl_data.session, host, Identifier(item)))
                if action == 'upload':
                    res = upload(tl_data.gs_client, Path(item), path_to_bucket_key(item))
                if action == 'build_html+upload':
                    for res in upload_html(tl_data.gs_client, ensure_html(tl_data.session, host, Identifier(item))):
                        summary_q.put((job['paper_id'], ms_since(start)) + res)

                if action != 'build_html+upload':
                    summary_q.put((job['paper_id'], ms_since(start)) + res)
                logger.info("success uploading %s", job['paper_id'], extra=extra)
                sleep(0.5)
            except Exception as ex:
                extra.update({CATEGORY: "upload"})
                extra.update(job_details)
                logger.error(f"Problem during {job['paper_id']} {action} {item}", extra=extra, exc_info=True)
                summary_q.put((job['paper_id'], ms_since(start), "failed", str(ex)))
        todo_q.task_done()


def log_summary(duration, overall_size):
    # Don't worry about the log level being INFO.
    # Summary is always "calm" logging. When the error happens, the log entry is generated at the spot of failure.
    dispatch = {
        "build_pdf+upload": lambda it: {"paper_id": it[0], "action": it[2], "outcome": it[5]},
        "upload": lambda it: {"paper_id": it[0], "action": it[2], "outcome": it[5]},
        "failed": lambda it: {"paper_id": it[0], "action": it[2], "error": it[3]},
        "build_html+upload": lambda it: {"paper_id": it[0], "action": it[2], "outcome": it[5]}
    }
    n_good, n_bad = 0, 0
    for row in sorted(list(summary_q.queue), key=lambda tup: tup[0]):
        summary = list(map(str, row))
        action = summary[2]
        digester = dispatch.get(action, lambda it: {"summary": repr(it)})
        summary_log = {CATEGORY: "summary"}
        summary_log.update(digester(summary))
        if action == "failed":
            logger.warning(','.join(summary), extra=summary_log)
            n_bad += 1
        else:
            logger.debug(','.join(summary), extra=summary_log)
            n_good += 1

    logger.info(
        f"Done at {datetime.now().isoformat()}. Overall time: {duration:.2f} sec"
        f" for {overall_size} submissions. Success/Failed: {n_good}/{n_bad}",
        extra={"total": overall_size, "duration": str(duration), "success": n_good, "failure": n_bad,
               CATEGORY: "summary"})


# #################### MAIN #################### #

def main(args):
    global RUN, DONE
    if args.globals:
        globals().update(eval(args.globals))
    if not (args.d or args.test):
        storage.Client()  # will fail if no auth setup
    if args.v:
        logger.setLevel(logging.INFO)
    if args.debug or args.test:
        logger.setLevel(logging.DEBUG)

    if args.json_log_dir and os.path.exists(args.json_log_dir):
        json_logHandler = logging.handlers.RotatingFileHandler(os.path.join(args.json_log_dir, "sync-to-gcp.log"),
                                                               maxBytes=4 * 1024 * 1024,
                                                               backupCount=10)
        json_formatter = ArxivSyncJsonFormatter(**LOG_FORMAT_KWARGS)
        json_formatter.converter = gmtime
        json_logHandler.setFormatter(json_formatter)
        json_logHandler.setLevel(logging.DEBUG if args.v or args.debug else logging.INFO)
        logger.addHandler(json_logHandler)
        pass

    todos = make_todos(args.filename, generate=args.generate)
    logger.info(f"Starting at {datetime.now().isoformat()} ({'bulid' if args.generate else 'no-build'}) todo count {len(todos)}",
                extra={CATEGORY: "status"})
    [todo_q.put(item) for item in todos]

    if args.d:
        todo = list(todo_q.queue)
        # Drain the to-do so other tests don't get confused.
        while not todo_q.empty():
            todo_q.get()
        if args.test:
            logger.debug("Dry run no changes made",
                         extra={CATEGORY: "status", "todos": len(todo)})
            localpath = "/foo"
            key = "bar"
            summary_q.put(("1234", 0, "upload", localpath, key, "already_on_gs", 0, 0))
            summary_q.put(("5678", 0, "failed", "bad!"))
            log_summary(perf_counter() - overall_start, 2)
            return todo
        print(json.dumps(todo, indent=2))
        print(f"{len(todo)} submissions (some may be test submissions)")
        sys.exit(1)

    logger.debug("made todo_q, getting size")
    overall_size = todo_q.qsize()
    logger.debug('Made %d todos', overall_size, extra={"n_todos": overall_size})

    threads = []
    for host, n_th in CONCURRENCY_PER_WEBNODE:
        ths = [Thread(target=sync_to_gcp, args=(todo_q, host)) for _ in range(0, n_th)]
        threads.extend(ths)
        [t.start() for t in ths]

    logger.debug("started %d threads", len(threads))

    while RUN and not todo_q.empty():
        sleep(0.2)

    logger.debug("todo_q is now empty")

    DONE = True
    RUN = False
    logger.debug("Run is complete. Waiting to join threads")
    [th.join() for th in threads]
    logger.debug("Run is complete. Threads done joining")

    # Summary report
    log_summary(perf_counter() - overall_start, overall_size)
    pass


class store_boolean(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values.lower() in ['true', 't', 'yes', 'y', '1']:
            setattr(namespace, self.dest, True)
        elif values.lower() in ['false', 'f', 'no', 'n', '0']:
            setattr(namespace, self.dest, False)
        else:
            raise argparse.ArgumentError(self, f"Invalid boolean value '{values}'")



if __name__ == "__main__":
    ad = argparse.ArgumentParser(epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ad.add_argument('--test', help='test mode', action='store_true')
    ad.add_argument('--json-log-dir', help='Additional JSON logging', default='/var/log/e-prints')
    ad.add_argument('-v', help='verbose', action='store_true')
    ad.add_argument('-d', help="Dry run no action", action='store_true')
    ad.add_argument('--debug', help='Set logging to debug', action='store_true')
    ad.add_argument('--globals', help="Global variables")
    ad.add_argument('--generate', default=True, type=str, action=store_boolean,
                    help="Generate files (default). Use =false to disable PDF/HTML gen")
    ad.add_argument('filename')
    args = ad.parse_args()
    main(args)
