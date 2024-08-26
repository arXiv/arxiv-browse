"""
submissions_to_gcp.py is an app that gets the published arxiv ID from the pub/sub queue on GCP,
check the files exist on CIT and uploads them to GCP bucket.

For each announced paper ID it will:
  * sync the /ftp files and ensure only current version files exist
    - if /ftp for the paper ID has any obsolete submission, it is removed.
  * sync the abs and source files to /orig if needed
    - If TeX source it will build the PDF on a CIT web node and sync those to ps_cache
    - If HTML source it will build the HTML and sync those to the ps_cache


The "upload to GCP bucket" part is from existing sync_published_to_gcp.

As a matter of fact, this borrows the most of heavy lifting part from sync_published_to_gcp.py.

The published submission queue provides the submission source file extension which is used to
upload the legacy system submissions to the GCP bucket.
"""
from __future__ import annotations
import argparse
import re
import shlex
import signal
import subprocess
import sys
import typing
from datetime import timedelta, datetime
from urllib.parse import unquote
from time import gmtime, sleep
from pathlib import Path
import requests
from dataclasses import dataclass

import json
import os
import logging.handlers
import logging
import threading
import gzip
import tarfile

from google.cloud.pubsub_v1.subscriber.message import Message
from google.cloud.pubsub_v1 import SubscriberClient
from google.cloud.storage import Client as StorageClient, Bucket, Blob
from google.cloud.storage.retry import DEFAULT_RETRY as STORAGE_RETRY
from requests.exceptions import RetryError, ReadTimeout

from identifier import Identifier

global WEBNODE_REQUEST_COUNT
WEBNODE_REQUEST_COUNT = 0

TIMEOUTS = {"PDF_TIMEOUT": 30, "HTML_TIMEOUT": 30}
def PDF_TIMEOUT():
    return TIMEOUTS["PDF_TIMEOUT"]

def HTML_TIMEOUT():
    return TIMEOUTS["HTML_TIMEOUT"]


logging.basicConfig(level=logging.INFO, format='%(message)s (%(threadName)s)')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)
import sync_published_to_gcp
sync_published_to_gcp.logger = logger

from sync_published_to_gcp import ORIG_PREFIX, FTP_PREFIX, PS_CACHE_PREFIX, upload, \
    path_to_bucket_key, ArxivSyncJsonFormatter, CONCURRENCY_PER_WEBNODE, ensure_pdf, \
    LOG_FORMAT_KWARGS, ensure_html


class IgnoredSubmission(Exception):
    """Signal for ignored submissions"""
    pass

class RemovedSubmission(Exception):
    """Signal for removed submissions"""
    pass

class MissingGeneratedFile(Exception):
    """Signal for PDF not existing on CIT webnode"""
    pass

class InvalidVersion(Exception):
    """Version string is invalid"""
    pass

class BrokenSubmission(Exception):
    """Something is very wrong"""
    pass

class ThreadLocalData:
    def __init__(self):
        self._local = threading.local()

    @property
    def storage(self):
        """The storage client object is created per thread."""
        if not hasattr(self._local, 'storage'):
            # Initialize the Storage instance for the current thread
            self._local.storage = StorageClient()

        return self._local.storage

    @property
    def session(self):
        """The storage client object is created per thread."""
        if not hasattr(self._local, 'session'):
             # Initialize the Storage instance for the current thread
             self._local.session = requests.Session()
        return self._local.session


thread_data = ThreadLocalData()

# Took this from parse_abs.py
RE_DATE_COMPONENTS = re.compile(
    r'^Date\s*(?::|\(revised\s*(?P<version>.*?)\):)\s*(?P<date>.*?)'
    r'(?:\s+\((?P<size_kilobytes>\d+)kb,?(?P<source_type>.*)\))?$')


@dataclass
class SourceFlag:
    """Represents arXiv article source file type."""

    code: str
    """Internal code for the source type."""

    __slots__ = ['code']

    @property
    def ignore(self) -> bool:
        """Withdarawn.

        All files auto ignore. No paper available.
        """
        return self.code is not None and 'I' in self.code

    @property
    def source_encrypted(self)->bool:
        """Source is encrypted and should not be made available."""
        return self.code is not None and 'S' in self.code

    @property
    def ps_only(self)->bool:
        """Multi-file PS submission.

        It is not necessary to indicate P with single file PS since in
        this case the source file has .ps.gz extension.
        """
        return self.code is not None and 'P' in self.code

    @property
    def pdflatex(self)->bool:
        """A TeX submission that must be processed with PDFlatex."""
        return self.code is not None and 'D' in self.code

    @property
    def html(self)->bool:
        """Multi-file HTML submission."""
        return self.code is not None and 'H' in self.code

    @property
    def includes_ancillary_files(self)->bool:
        """Submission includes ancillary files in the /anc directory."""
        return self.code is not None and 'A' in self.code

    @property
    def dc_pilot_data(self)->bool:
        """Submission has associated data in the DC pilot system."""
        return self.code is not None and 'B' in self.code

    @property
    def docx(self)->bool:
        """Submission in Microsoft DOCX (Office Open XML) format."""
        return self.code is not None and 'X' in self.code

    @property
    def odf(self)->bool:
        """Submission in Open Document Format."""
        return self.code is not None and 'O' in self.code

    @property
    def pdf_only(self)->bool:
        """PDF only submission with .tar.gz package.

        (likely because of anc files)
        """
        return self.code is not None and 'F' in self.code

    @property
    def cannot_pdf(self) -> bool:
        """Is this version unable to produce a PDF?

        Does not take into account withdarawn.
        """
        return self.code is not None and self.html or self.odf or self.docx

    @property
    def is_single_file(self) -> bool:
        """Is the source for this version a single file?"""
        return self.code is not None and '1' in self.code

#
# 'tex', 'pdftex', 'html', 'ps', 'pdf', 'docx', 'odf'

flag_to_source_format = {
    'D': 'pdftex',
    'H': 'html',
    'I': 'withdrawn',
    'O': 'odf',
    'P': 'ps',
    'X': 'docx'
}

src_ext_to_source_format = {
    '.html.gz': 'html',
    '.ps.gz': 'ps',
    '.pdf': 'pdf',
    '.gz': {'pdftex': 'pdftex', None: 'tex'},
    None: 'tex',
}


class SubmissionFilesState:
    """
    Given the paper ID, version, publish type and would-be src_ext, generate the desired
    file state for the submission.
    This includes the published, and (version - 1) state if it's appropriate.

    If the submission file type is uncertain, it tries to "guess" from the files on the CIT.

    Once the expectation is decided, it then maps the CIT file path to the GCP blob path.
    """
    tex_submisson_exts: typing.List[str] = [".tar.gz", ".gz"]
    submission_exts: typing.List[str] = [".tar.gz", ".gz", ".pdf", ".html.gz"]


    xid: Identifier      # paper id (aka arXiv ID)
    vxid: Identifier     # versioned paper id (aka versioned arXiv ID)
    src_ext: str         # publishing file format
    source_format: str   # submission source format (html, tex, pdf, etc.)
    source_flags: str
    single_source: bool
    archive: str         # old-style
    publish_type: str
    version: str
    log_extra: dict
    submission_source: typing.Optional[dict]

    _top_levels: dict

    _extras: typing.List[dict]

    def __init__(self, arxiv_id_str: str, version: str, publish_type: str, src_ext: str,
                 source_format: str, log_extra: dict):
        try:
            if int(version) <= 0:
                raise InvalidVersion(f"{version} is invalid")
        except:
            raise InvalidVersion(f"{version} is invalid")
        self.xid = Identifier(arxiv_id_str)  # arXiv paper ID (xid)
        self.version = version               # submission version
        # versioned ID (Versioned XID)
        self.vxid = self.xid if self.xid.has_version else Identifier(f"{arxiv_id_str}v{version}")
        self.publish_type = publish_type
        self.src_ext = src_ext
        self.log_extra = log_extra
        self.source_format = source_format
        self.source_flags = ""
        self.submission_source = None
        self.single_source = False
        self._extras = []

        self.ext_candidates = SubmissionFilesState.submission_exts.copy()
        if src_ext:
            if src_ext in self.ext_candidates[1:]:
                self.ext_candidates.remove(src_ext)
            self.ext_candidates.insert(0, src_ext)

        self.archive = 'arxiv' if not self.xid.is_old_id else self.xid.archive

        self.prev_version = 1
        try:
            self.prev_version = max(1, int(self.version) - 1)
        except:
            pass

        self._top_levels = {}
        pass

    @property
    def latest_dir(self):
        return f"{FTP_PREFIX}{self.archive}/papers/{self.xid.yymm}"

    @property
    def gz_source(self):
        return f"{FTP_PREFIX}{self.archive}/papers/{self.xid.yymm}/{self.xid.filename}.gz"

    @property
    def tgz_source(self):
        return f"{FTP_PREFIX}{self.archive}/papers/{self.xid.yymm}/{self.xid.filename}.tar.gz"

    @property
    def ps_cache_pdf_file(self):
        return f"{PS_CACHE_PREFIX}{self.vxid.archive}/pdf/{self.vxid.yymm}/{os.path.basename(self.vxid.idv)}.pdf"

    @property
    def html_root_dir(self):
        # cannot ues self
        return f"{PS_CACHE_PREFIX}{self.vxid.archive}/html/{self.vxid.yymm}/{os.path.basename(self.vxid.idv)}"

    def html_files(self, files: typing.List[str]):
        # cannot ues self
        root_dir = self.html_root_dir
        return [os.path.join(root_dir, filename) for filename in files]

    @property
    def latest_dir(self):
        return f"{FTP_PREFIX}{self.archive}/papers/{self.xid.yymm}"

    @property
    def versioned_parent(self):
        return f"{ORIG_PREFIX}{self.archive}/papers/{self.xid.yymm}"

    def source_path(self, dotext: str):
        return f"{self.latest_dir}/{self.xid.filename}{dotext}"

    def prev_source_path(self, dotext: str):
        return f"{self.versioned_parent}/{self.xid.filename}v{self.prev_version}{dotext}"

    def maybe_update_metadata(self):
        """If the source format for the submission is not given, scan the directory and decide
        the submission format.

        The way source_format, source_flags are used is chaotic.
        """

        # If somehow there is no src_ext specified, find it out from the CIT's files
        if not self.src_ext:
            for ext in self.ext_candidates:
                src_path = self.source_path(ext)
                if os.path.exists(src_path):
                    self.src_ext = ext
                    break

        if not self.source_format:
            abs_path = self.source_path(".abs")
            dates = []
            try:
                with open(abs_path, "r", encoding="utf-8") as abs_fd:
                    for line in abs_fd.readlines():
                        sline = line.strip()
                        if sline == "":
                            break
                        if sline.startswith("Date"):
                            dates.append(sline)

            except FileNotFoundError as exc:
                msg = f"abs file {abs_path} does not exist"
                logger.warning(msg)
                raise BrokenSubmission(msg) from exc

            except Exception as exc:
                msg = f"Error with {abs_path}"
                logger.warning(msg, exc_info=True)
                raise BrokenSubmission(msg) from exc

            if dates:
                parsed = RE_DATE_COMPONENTS.match(dates[-1])
                if parsed:
                    source_type = parsed.group('source_type')
                    for source_flag in source_type:
                        if source_flag in flag_to_source_format:
                            self.source_format = flag_to_source_format[source_flag]
                            continue
                        if source_flag in "SAB":
                            self.source_flags = self.source_flags + source_flag
                            continue

            # is this a single source submission?
            self.single_source = self.src_ext != ".tar.gz"

            if not self.single_source:
                # It the source format isn't decided, it's probably tex submission
                if not self.source_format:
                    self.source_format = "tex"
            else:
                if self.src_ext in src_ext_to_source_format:
                    maybe_source_format = src_ext_to_source_format[self.src_ext]
                    if isinstance(maybe_source_format, dict):
                        source_format = maybe_source_format.get(self.source_format)
                        if source_format is None:
                            self.source_format = maybe_source_format[None]
                        else:
                            self.source_format = source_format
                    else:
                        self.source_format = maybe_source_format

    @property
    def is_tex_submission(self) -> bool:
        """is a tex submssion"""
        assert(self.src_ext)
        assert(self.source_format)
        return self.source_format in ["tex", "pdftex"]

    @property
    def is_html_submission(self) -> bool:
        """is a HTML submission"""
        assert(self.src_ext)
        assert(self.source_format)
        return self.source_format == "html"


    def get_tgz_top_levels(self) -> dict:
        """
        Retrieve the top-level files in the tar.gz file
        """
        if not self._top_levels:
            tgz_source = Path(self.tgz_source)
            if tgz_source.exists():
                try:
                    with tarfile.open(tgz_source, 'r:gz') as submission:
                        self._top_levels = {name: True for name in submission.getnames()}
                except Exception as _exc:
                    logger.warning("bad tgz: %s", self.xid.ids, extra=self.log_extra,
                                   exc_info=True, stack_info=False)
        return self._top_levels


    def get_expected_files(self):
        """
        The source may not have a consistent .tar.gz name.
        Some other possibilities:

        {paperidv}.pdf pdf only submission
        {paperidv}.gz single file submisison
        {paperidv}.html.gz html source submission

        NOTE: This cannot handle this special case.
        I think there is one case in the system where there is a submission with two source files
        that the admins manually crafted. It would have: {paperidv}.pdf and {paperidv}.tar.gz
        This was to get a pdf only submission with ancillary files.
        """

        def current(t, cit): # macro!? It's just easier to read code being here
            return {"type": t, "cit": cit, "status": "current"}

        files = [current("abstract", self.source_path(".abs"))]

        if self.is_removed():
            # When a submission is removed, .abs, and the "removed" marker should be in ftp/
            files.append(current("submission", self.tgz_source))
        elif self.is_ignored():
            # When a submission is ignored, .abs, and the "removed" marker should be in ftp/
            files.append(current("submission", self.gz_source))
        else:
            # Live submission
            self.maybe_update_metadata()
            self.submission_source = self.source_path(self.src_ext)
            files.append(current("submission", self.submission_source))

            if self.is_tex_submission:
                files.append(current("pdf-cache", self.ps_cache_pdf_file))
            elif self.is_html_submission:
                # Since this is a root dir of HTML submission, no need to "upload".
                # This is just a "marker" to initiate the html file expand.
                # Later (in submission_message_to_file_state()), this triggers to ask a web node
                # for the html, and it populates the files under the self.html_root_dir
                files.append(current("html-cache", self.html_root_dir))
                pass
            pass

        if self.publish_type in ["rep", "wdr"]:
            def obsolete(t, cit):
                return {"type": t, "cit": cit, "status": "obsolete"}

            files.append(obsolete("abstract", self.prev_source_path(".abs")))

            for dotext in self.submission_exts:
                prev_source_path = self.prev_source_path(dotext)
                if os.path.exists(prev_source_path):
                    files.append(obsolete("submission", self.prev_source_path(dotext)))
                    break
            else:
                files.append(obsolete("submission", self.prev_source_path(self.src_ext)))

        for file_entry in files:
            file_entry["gcp"] = path_to_bucket_key(file_entry["cit"])

        return files + self._extras

    def register_files(self,
                       file_type: str,
                       files: typing.List[Path] | typing.List[str]) -> None:
        """
        Used for HTML submission. The actual files uploaded to the gcp bucket is unknown until
        webnode untars it. When ensure_html gets the file list, register them for the upload.
        """
        for filename in files:
            self._extras.append( {
                'type': file_type,
                'cit': str(filename),
                'gcp': path_to_bucket_key(str(filename)),
                'status': "current",
            } )

    def is_ignored(self) -> bool:
        """Is this a ignored file?

        when the gzipped source has %auto-ignored, it is an ignored.
        """
        # Ignored submission
        gz_source = Path(self.gz_source)
        if gz_source.exists():
            # Open the gzip file in read mode with text encoding set to ASCII
            try:
                with gzip.open(gz_source, 'rt', encoding='ascii') as f:
                    needle = "%auto-ignore"
                    content = f.read(len(needle))
                    if content.startswith(needle):
                        return True

            except Exception as _exc:
                logger.warning("bad .gz: %s ext %s",
                               self.xid.ids, str(self.src_ext), extra=self.log_extra,
                               exc_info=True, stack_info=False)
                raise
        return False


    def is_removed(self) -> bool:
        """Is this a removed submission?
        This is done by the tar.gz toplevels and if it has the removed.txt in it, this is a
        removed submission.
        """
        # Removed submission
        return "removed.txt" in self.get_tgz_top_levels()


    def to_payloads(self):
        return [(entry["cit"], entry["gcp"]) for entry in self.get_expected_files()]

    def get_submission_mtime(self) -> int:
        """
        Get the mtime of the submission.
        """
        if self.submission_source:
            source = Path(self.submission_source)
            return source.stat().st_mtime if source.exists() else 0
        return 0

def submission_message_to_file_state(data: dict, log_extra: dict, ask_webnode: bool = True) -> SubmissionFilesState:
    """
    Parse the submission_published message, map it to CIT files and returns the list of files.
    The schema is
    https://console.cloud.google.com/cloudpubsub/schema/detail/submission-publication?project=arxiv-production
    however, this only cares paper_id and version.
    """
    global WEBNODE_REQUEST_COUNT
    my_tag = WEBNODE_REQUEST_COUNT
    publish_type = data.get('type') # cross | jref | new | rep | wdr
    paper_id = data.get('paper_id')
    version = data.get('version')
    src_ext = data.get('src_ext')
    source_format = data.get('source_format', '')

    logger.info("Processing %s.v%s:%s", paper_id, str(version), str(src_ext), extra=log_extra)

    file_state = SubmissionFilesState(paper_id, version, publish_type, src_ext, source_format, log_extra)

    if ask_webnode:
        # If asked for PDF, make sure it exits on web node, or else signal NoPDF
        for entry in file_state.get_expected_files():
            if entry["type"] == "pdf-cache":
                # If the submission needs a PDF generated, make sure it exists at CIT
                # If not, raise NoPDF
                pdf_path = Path(entry["cit"])
                if not pdf_path.exists():
                    n_webnodes = len(CONCURRENCY_PER_WEBNODE)
                    WEBNODE_REQUEST_COUNT = (WEBNODE_REQUEST_COUNT + 1) % n_webnodes
                    host, n_para = CONCURRENCY_PER_WEBNODE[min(n_webnodes - 1, max(0, my_tag))]
                    protocol = "http" if host.startswith("localhost:") else "https"
                    try:
                        _pdf_file, _url, _1, _duration_ms = \
                            ensure_pdf(thread_data.session, host, file_state.vxid, timeout=PDF_TIMEOUT(),
                                       protocol=protocol,
                                       source_mtime=file_state.get_submission_mtime())

                    except sync_published_to_gcp.WebnodeException as exc:
                        raise MissingGeneratedFile("Failed to generate %s", pdf_path) from exc

                    except ReadTimeout as exc:
                        # This happens when failed to talk to webnode
                        raise MissingGeneratedFile("Failed to retrieve pdf: %s") from exc

                    except RetryError as exc:
                        # This happens when failed to talk to webnode
                        raise MissingGeneratedFile("Failed to retrieve pdf: %s") from exc

                    except Exception as _exc:
                        logger.warning("ensure_pdf: %s", file_state.vxid.ids, extra=log_extra,
                                       exc_info=True, stack_info=False)
                        raise

                if not pdf_path.exists():
                    raise MissingGeneratedFile(f"GDF: {file_state.ps_cache_pdf_file} does not exist")
                pass

            if entry["type"] == "html-cache":
                # When the submission is html, web node needs to okay. ensure_html() talks to
                # a web node, and when it gets 200, it returns the list of files in it.
                # The file state (self here) registers files for upload.
                html_path: Path = Path(entry["cit"])
                n_webnodes = len(CONCURRENCY_PER_WEBNODE)
                WEBNODE_REQUEST_COUNT = (WEBNODE_REQUEST_COUNT + 1) % n_webnodes
                host, n_para = CONCURRENCY_PER_WEBNODE[min(n_webnodes - 1, max(0, my_tag))]
                protocol = "http" if host.startswith("localhost:") else "https"
                try:
                    html_files, html_root, url, outcome, duration_ms = \
                        ensure_html(thread_data.session, host, file_state.vxid, timeout=HTML_TIMEOUT(),
                                    protocol=protocol,
                                    source_mtime=file_state.get_submission_mtime())
                    logger.info("ensure_html %s / %s: [%1.2f sec] %s (%d) -> %s", file_state.vxid.ids,
                                str(outcome), float(duration_ms) / 1000.0,
                                html_root, len(html_files), url,
                                extra=log_extra)
                    file_state.register_files('html-files', html_files)

                except sync_published_to_gcp.WebnodeException as _exc:
                    raise MissingGeneratedFile("Failed to generate %s", html_path) from _exc

                except Exception as _exc:
                    logger.warning("ensure_html: %s", file_state.vxid.ids, extra=log_extra,
                                   exc_info=True, stack_info=False)
                    raise

                if not html_path.exists():
                    raise MissingGeneratedFile(f"{file_state.ps_cache_pdf_file} does not exist")
                pass
    else:
        logger.info("Not asking web node means, you are not getting PDF or HTML populated, only good for development.")

    return file_state


def decode_message(message: Message) -> typing.Union[dict, None]:
    """Decodes the GCP pub/sub message"""
    log_extra = {"message_id": str(message.message_id), "app": "pubsub-test"}
    try:
        json_str = message.data.decode('utf-8')
    except UnicodeDecodeError:
        logger.error(f"bad data {str(message.message_id)}", extra=log_extra)
        return None

    try:
        data = json.loads(json_str)
    except Exception as _exc:
        logger.warning(f"bad({message.message_id}): {json_str[:1024]}", extra=log_extra)
        return None

    return data


@STORAGE_RETRY
def list_bucket_objects(gs_client, gcp_path) -> typing.List[str]:
    """
    List the objects in the gcp bucket
    """
    from sync_published_to_gcp import GS_BUCKET
    bucket: Bucket = gs_client.bucket(GS_BUCKET)
    blobs = bucket.list_blobs(prefix=str(gcp_path))
    blob: Blob
    prefix = f'/b/{GS_BUCKET}/o/'
    pl = len(prefix)
    return [ unquote(blob.path[pl:]) for blob in blobs]


@STORAGE_RETRY
def trash_bucket_objects(gs_client, objects: typing.List[str], log_extra: dict):
    """
    Delete the bucket objects.
    """
    from sync_published_to_gcp import GS_BUCKET
    bucket: Bucket = gs_client.bucket(GS_BUCKET)
    for obj in objects:
        blob = bucket.blob(obj)
        logger.debug("%s is being deleted", obj, extra=log_extra)
        blob.delete()
        logger.info("%s is deleted", obj, extra=log_extra)
    return


def submission_callback(message: Message) -> None:
    """Pub/sub event handler to upload the submission tarball and .abs files to GCP.

    Since upload() looks at the size of bucket object / CIT file to decide copy or not
    copy, this will attempt to upload the versioned and latest at the same time but the uploading
    may or may not happen.

    """
    # Create a thread-local object
    data = decode_message(message)
    if data is None:
        message.nack()
        return

    global WEBNODE_REQUEST_COUNT

    publish_type = data.get('type') # cross | jref | new | rep | wdr
    paper_id = data.get('paper_id')
    version = data.get('version')
    log_extra = {
        "message_id": str(message.message_id), "app": "pubsub", "tag": "%d" % WEBNODE_REQUEST_COUNT,
        "publish_type": str(publish_type), "arxiv_id": str(paper_id), "version": str(version)
    }

    message_age: timedelta = datetime.utcnow() - message.publish_time
    compilation_timeout = int(os.environ.get("TEX_COMPILATION_TIMEOUT_MINUTES", "30"))

    try:
        state = submission_message_to_file_state(data, log_extra)
        desired_state = state.get_expected_files()
        if not desired_state:
            logger.warning(f"There is no associated files? xid: {state.xid.ids}, mid: {str(message.message_id)}", extra=log_extra)
            message.nack()
            return

    except MissingGeneratedFile as exc:
        logger.info(str(exc), extra=log_extra)

        if message_age > timedelta(minutes=compilation_timeout):
            id = f"{paper_id}v{version}"
            try:
                slacking = subprocess.call(
                    ['/users/e-prints/bin/tex-compilation-problem-notification',
                     id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if slacking.returncode != 0:
                    logger.error("Failed to send notification: %s", id, extra=log_extra)
            except:
                logger.error('Slacking for %s did not work', id)
                pass

            help_needed = os.environ.get("TEX_COMPILATION_RECIPIENT", "help@arxiv.org")
            subject = f"Uploading of {paper_id}v{version} failed"
            mail_body = f"Hello EUST,\nSubmission uploading for {paper_id}v{version} has failed. Please resolve the issue.\n\nThis message is generated by a bot on arxiv-sync.serverfarm.cornell.edu.\n"
            cmd = ["/usr/bin/mail", "-r", "developers@arxiv.org", "-s", subject, help_needed]
            mail = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                mail.communicate(mail_body, timeout=60)
                if mail.returncode == 0:
                    # Once the email message is sent, done here.
                    message.ack()
                    logger.warning(f"Alart mail sent: {subject}", extra=log_extra)
                    return
                else:
                    logger.error("Failed to send mail: %s", shlex.join(cmd), extra=log_extra)
            except Exception as exc:
                logger.error(f"Failed: %s", shlex.join(cmd), extra=log_extra, exc_info=True)
                pass
            pass

        message.nack()
        return

    except Exception as _exc:
        logger.warning(
            f"Unknown error xid: {paper_id}, mid: {str(message.message_id)}",
            extra=log_extra, exc_info=True, stack_info=False)
        message.nack()
        return

    try:
        sync_to_gcp(state, log_extra)
        message.ack()
        # Acknowledge the message so it is not re-sent
        logger.info("ack message: %s", state.xid.ids, extra=log_extra)

    except Exception as _exc:
        logger.error("Error processing message: {exc}", exc_info=True, extra=log_extra)
        message.nack()
        pass



def sync_to_gcp(state: SubmissionFilesState, log_extra: dict) -> bool:
    """
    From the submission file state, copy the ones that should bu uploaded.

    If the /ftp's submission contains extra files, they are removed.
    """
    gs_client = thread_data.storage
    desired_state = state.get_expected_files()
    xid = state.xid
    log_extra["arxiv_id"] = xid.ids
    logger.info("Processing %s", xid.ids, extra=log_extra)

    # Existing blobs on GCP
    cit_source_root_path = state.source_path("")
    bucket_objects: typing.List[str] = \
        list_bucket_objects(gs_client, path_to_bucket_key(cit_source_root_path))

    # Objects synced to GCP
    for entry in desired_state:
        local = entry["cit"]
        remote = entry["gcp"]
        entry_type = entry['type']

        if entry_type == "html-cache":
            # "html-cache" is needed on CIT as it is the root dir of HTML submission, but
            # it is NOT a bucket object, and nothing to upload. Subsequent object copy becomes
            # effectively creating the "directory" on GCP.
            logger.debug("Skipping [%s]: %s -> %s", entry_type, local, remote, extra=log_extra)
            continue

        logger.debug("uploading [%s]: %s -> %s", entry_type, local, remote, extra=log_extra)
        upload(gs_client, Path(local), remote, upload_logger=logger)
        # Uploaded files are good ones. Subtract the valid one from the bucket objects
        if remote in bucket_objects:
            bucket_objects.remove(remote)

    # If extra exists, they are removed.
    if bucket_objects:
        trash_bucket_objects(gs_client, bucket_objects, log_extra)


def test_callback(message: Message) -> None:
    """Stand in callback to handle the pub/sub message. gets used for --test."""
    data = decode_message(message)
    if data is None:
        message.nack()
        return

    log_extra = {"message_id": str(message.message_id), "app": "pubsub-test"}
    state = submission_message_to_file_state(data, log_extra)
    logger.debug(state.xid.ids)
    sync = state.get_expected_files()
    for entry in sync:
        logger.debug(f'{entry["cit"]} -> {entry["gcp"]}')
    message.nack()
    sys.exit(0)


running = True

def signal_handler(_signal: int, _frame: typing.Any):
    """Graceful shutdown request"""
    global running
    running = False

# Attach the signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def submission_pull_messages(project_id: str, subscription_id: str, test: bool = False) -> None:
    """
    Create a subscriber client and pull messages from a Pub/Sub subscription.

    Args:
        project_id (str): Google Cloud project ID
        subscription_id (str): ID of the Pub/Sub subscription
        test (bool): Test - get one message, print it, nack, and exit
    """
    subscriber_client = SubscriberClient()
    subscription_path = subscriber_client.subscription_path(project_id, subscription_id)
    callback = test_callback if test else submission_callback
    streaming_pull_future = subscriber_client.subscribe(subscription_path, callback=callback)
    log_extra = {"app": "pubsub"}
    logger.info("Starting %s %s", project_id, subscription_id, extra=log_extra)
    with subscriber_client:
        try:
            while running:
                sleep(0.2)
            streaming_pull_future.cancel()  # Trigger the shutdown
            streaming_pull_future.result(timeout=30)  # Block until the shutdown is complete
        except TimeoutError:
            logger.info("Timeout")
            streaming_pull_future.cancel()
        except Exception as e:
            logger.error("Subscribe failed: %s", str(e), exc_info=True, extra=log_extra)
            streaming_pull_future.cancel()
    logger.info("Exiting", extra=log_extra)


if __name__ == "__main__":
    ad = argparse.ArgumentParser(epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ad.add_argument('--project',
                    help='GCP project name. Default is arxiv-production',
                    dest="project", default="arxiv-production")
    ad.add_argument('--topic',
                    help='GCP pub/sub name. The default matches with arxiv-production',
                    dest="topic", default="submission-published")
    ad.add_argument('--subscription',
                    help='Subscription name. Default is the one in production', dest="subscription",
                    default="sync-submission-from-cit-to-gcp")
    ad.add_argument('--json-log-dir',
                    help='JSON logging directory. The default is correct on the sync-node',
                    default='/var/log/e-prints')
    ad.add_argument('--debug', help='Set logging to debug. Does not invoke testing',
                    action='store_true')
    ad.add_argument('--test', help='Test reading the queue but not do anything',
                    action='store_true')
    ad.add_argument('--bucket',
                    help='The bucket name. The default is mentioned in sync_published_to_gcp so for the production, you do not need to provide this - IOW it automatically uses the same bucket as sync-to-gcp',
                    dest="bucket", default="")
    args = ad.parse_args()

    project_id = args.project
    subscription_id = args.subscription

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.json_log_dir and os.path.exists(args.json_log_dir):
        json_logHandler = logging.handlers.RotatingFileHandler(os.path.join(args.json_log_dir, "submissions.log"),
                                                               maxBytes=4 * 1024 * 1024,
                                                               backupCount=10)
        json_formatter = ArxivSyncJsonFormatter(**LOG_FORMAT_KWARGS)
        json_formatter.converter = gmtime
        json_logHandler.setFormatter(json_formatter)
        json_logHandler.setLevel(logging.DEBUG if args.debug else logging.INFO)
        logger.addHandler(json_logHandler)
        pass

    # Ensure the environment is authenticated
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        logger.error("Environment variable 'GOOGLE_APPLICATION_CREDENTIALS' is not set.")
        sys.exit(1)
    if args.bucket:
        import sync_published_to_gcp
        sync_published_to_gcp.GS_BUCKET = args.bucket

    from sync_published_to_gcp import GS_BUCKET
    logger.info("GCP bucket %s", GS_BUCKET)
    submission_pull_messages(project_id, subscription_id, test=args.test)
